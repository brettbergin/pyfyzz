#!/usr/bin/env python3

import os
import sys
import uuid
import json
import base64

from typing import Tuple, Dict
import datetime

import pandas as pd
import requests

from .fuzzer import Fuzzer
from .logger import PyFyzzLogger
from .arguments import Arguments
from .analyzer import PythonPackageAnalyzer
from .databases import DatabaseExporter
from .validators import PyFyzzInputValidator
from .models.data_models import PackageInfo, DBOptions
from .models.orm_models import FuzzResults, PackageRecords
from .serializers import PackageInfoSerializer, FuzzResultSerializer
from .git import GithubForPyFyzz


def fuzz_package(
    logger: PyFyzzLogger, package_info: PackageInfo, openai_api_key: str
) -> Tuple[Dict, pd.DataFrame, Dict]:
    """
    Attempts to invoke the package fuzzer against the package info
    data model object we enumerated.

    returns: Fuzzer or sys.exit(-1)
    """

    fuzzer = Fuzzer(
        logger=logger, package_under_test=package_info, openai_api_key=openai_api_key
    )

    ran = fuzzer.run()
    if not ran:
        logger.log(
            "error", "[-] Fuzzer run execution did not complete successfully. Qutting."
        )
        sys.exit(-1)

    logger.log("info", "[+] Fuzzing has been completed.")

    results_as_dict = FuzzResultSerializer(fuzz_results=fuzzer.fuzz_results).as_dict()
    results_as_df = FuzzResultSerializer(
        fuzz_results=fuzzer.fuzz_results
    ).as_dataframe()

    return (results_as_dict, results_as_df, fuzzer.exception_count)


def analyze_package(
    logger: PyFyzzLogger, pkg_name: str
) -> Tuple[PackageInfo, Dict, pd.DataFrame]:
    """
    Enumerates all of the package contents in the given package and returns
    a data model object representing the entire package:

    example:  package -> module(s) -> class(es) -> method(s)/function(s) -> argument(s)/parameter(s)

    returns: object(PackageInfo) or sys.exit(-1)
    """

    analyzer = PythonPackageAnalyzer(logger=logger)
    importable = analyzer.verify_importable_package(pkg_name)

    if not importable:
        logger.log(
            "error", f"[-] Package: {pkg_name} found not to be importable. Qutting."
        )
        sys.exit(-1)
    logger.log("debug", f"[!] Package found importable into runtime: {importable}")

    pkg_info = analyzer.run(pkg_name=pkg_name)
    if not pkg_info:
        logger.log(
            "error",
            f"[-] Unable to analyze provided package. Using: {pkg_name}. Quitting.",
        )
        sys.exit(-1)
    logger.log("info", "[+] Package analysis is complete.")

    pkg_dict = PackageInfoSerializer(package_info=pkg_info).as_dict()
    pkg_df = PackageInfoSerializer(package_info=pkg_info).as_dataframe()

    return pkg_info, pkg_dict, pkg_df


def valid_user_input(logger: PyFyzzLogger) -> Tuple[str, bool, str]:
    """
    Attemnpts to validate the user input across the arguments
    provided by the caller.

    returns Tuple[str, bool, str] or sys.exit(-1)
    """

    arguments = Arguments()
    validator = PyFyzzInputValidator(logger=logger)

    args = arguments.parse_arguments()

    package_name: str = validator.validate_package_name(args.package_name)
    if not package_name:
        logger.log(
            "error",
            f"[-] Invalid package has been provided. Using: {package_name}. Qutting.",
        )
        sys.exit(-1)
    logger.log("info", f"[+] Beginning package analysis for package: {package_name}")

    return args


def publish_to_database(
    logger: PyFyzzLogger,
    pkg_name: str,
    start_t: datetime.datetime,
    pkg_df: pd.DataFrame,
    fr_df: pd.DataFrame,
    batch_job_id: str,
    discovered_methods: int,
    conn_string: str,
) -> None:
    """ """

    db_exporter = DatabaseExporter(
        db_uri=conn_string,
        logger=logger,
    )

    db_exporter.start_new_batch(
        batch_job_id,
        pkg_name,
        start_time=start_t,
        stop_time=None,
        discovered_methods_count=discovered_methods,
        batch_status="running",
    )

    url = f"https://pypi.org/pypi/{pkg_name}/json"
    r = requests.get(url)

    if r.status_code in (200, 201, 202):
        logger.log(
            "debug", f"[+] Successfully found pypi json data for package: {pkg_name}"
        )
        resp_json = json.loads(r.content)
        db_exporter.add_pip_package(data=resp_json, batch_job_id=batch_job_id)
    else:
        logger.log("debug", "[!] Unable to find package information in pypi.")

    pkg_df["batch_job_id"] = batch_job_id
    fr_df["batch_job_id"] = batch_job_id

    logger.log("info", "[+] Preparing to add package info to database.")
    db_exporter.export_to_database(pkg_df, "topologies")

    logger.log("info", "[+] Preparing to add fuzz results to database.")
    db_exporter.export_to_database(fr_df, "fuzz_results")
    return db_exporter


def scan_package(
    logger, package_name, batch_job_id, openai_api_key, conn_string
) -> datetime.datetime:
    """ """
    start_time = datetime.datetime.now()

    pkg_info, pkg_dict, pkg_df = analyze_package(logger, pkg_name=package_name)

    fuzz_results_dict, fuzz_results_df, fuzz_counts = fuzz_package(
        logger, package_info=pkg_info, openai_api_key=openai_api_key
    )

    fuzzed_method_count = len(
        list(set([res["method_name"] for res in fuzz_results_dict["results"]]))
    )

    db_exporter = publish_to_database(
        logger=logger,
        batch_job_id=batch_job_id,
        pkg_name=package_name,
        start_t=start_time,
        pkg_df=pkg_df,
        fr_df=fuzz_results_df,
        discovered_methods=fuzzed_method_count,
        conn_string=conn_string,
    )

    db_exporter.insert_batch_summary(
        counts=fuzz_counts, batch_job_id=batch_job_id, pkg_name=package_name
    )

    stop_time = datetime.datetime.now()
    db_exporter.update_job_complete(
        batch_job_id=batch_job_id, stop_time=stop_time, batch_status="completed"
    )
    return


def github_pull_request(
    logger, access_token, conn_string, package_name, pyfyzz_record_id
):
    """ """
    fyzzgit = GithubForPyFyzz(logger, access_token=access_token)
    db = DatabaseExporter(db_uri=conn_string, logger=logger)
    fyzzgit.db = db

    exception_to_report = (
        db.session.query(FuzzResults)
        .filter(
            FuzzResults.record_id == pyfyzz_record_id,
            FuzzResults.package_name == package_name,
        )
        .first()
    )

    urls = []
    if exception_to_report:
        package_info = (
            db.session.query(PackageRecords)
            .filter(PackageRecords.batch_job_id == exception_to_report.batch_job_id)
            .first()
        )

        if package_info:
            urls.append(package_info.home_page)
            urls.append(package_info.project_url)

            data = json.loads(package_info.project_urls)
            if data:
                for _, v in data.items():
                    urls.append(v)

        else:
            logger.log(
                "error",
                "[-] PyPI Package information not found in database. No Github URL to use for pull request.",
            )
            return
    else:
        logger.log(
            "error",
            "[-] Requested fuzz result not found. Nothing to create a pull request from.",
        )
        return

    urls = [
        url
        for url in list(set(urls))
        if url is not None
        and url.lower().startswith("https://github.com")
        and url.lower().endswith(package_name.lower())
        or url.lower().endswith(f"{package_name.lower()}/")
    ]

    github_url = urls[0] if len(urls) > 0 else None
    if not github_url:
        logger.log(
            "error",
            f"[-] No GitHub URL enumerated for package: {exception_to_report.package_name}. URLs: {package_info.project_urls}",
        )
        return

    clone_path = os.path.join(os.path.expanduser("~"), ".pyfyzz", f"{package_name}")

    if not os.path.exists(os.path.join(os.path.expanduser("~"), ".pyfyzz")):
        os.makedirs(os.path.join(os.path.expanduser("~"), ".pyfyzz"))

    fyzzgit.init_repo_from_url(repo_url=github_url)
    fyzzgit.create_repo_clone(
        repo_url=github_url,
        repo_name=package_name,
        clone_path=clone_path,
        new_branch_name="improvements",
    )

    fyzzgit.make_improvements(
        folder_path=clone_path,
        package_name=package_name,
        method_name=exception_to_report.method_name,
        new_method_code=base64.b64decode(
            exception_to_report.improved_source.encode("utf-8")
        ).decode("utf-8"),
    )

    return


def main() -> None:
    """
    Main entry point for the script. Parses arguments, verifies the package,
    and performs the analysis and export.
    """
    start_time = datetime.datetime.now()

    logger = PyFyzzLogger(name="pyfyzz", level="debug")
    logger.log("info", f"[+] Starting pyfyzz @: {start_time}.")

    openai_api_key = os.environ.get("OPENAI_API_KEY")
    if not openai_api_key:
        logger.log(
            "error", "[-] Unable to obtain openai API key from env vars. quitting."
        )
        sys.exit(-1)

    github_access_token = os.environ.get("GITHUB_ACCESS_TOKEN")
    if not github_access_token:
        logger.log(
            "error", "[-] Unable to obtain GitHub access token from env vars. quitting."
        )
        sys.exit(-1)

    db_user = os.environ.get("PYFYZZ_DB_USERNAME")
    if not db_user:
        logger.log(
            "error", "[-] Unable to obtain pyfyzz db username from env vars. quitting."
        )
        sys.exit(-1)

    db_passwd = os.environ.get("PYFYZZ_DB_PASSWORD")
    if not db_passwd:
        logger.log(
            "error", "[-] Unable to obtain pyfyzz db password from env vars. quitting."
        )
        sys.exit(-1)

    db = DBOptions(
        user=db_user, password=db_passwd, host="localhost", port=3306, name="pyfyzz"
    )

    conn_string = (
        f"mysql+mysqlconnector://{db.user}:{db.password}@{db.host}:{db.port}/{db.name}"
    )

    batch_job_id = str(uuid.uuid4())
    args = valid_user_input(logger)

    if args.command == "scan":
        scan_package(
            logger,
            args.package_name,
            batch_job_id,
            openai_api_key=openai_api_key,
            conn_string=conn_string,
        )

    elif args.command == "github_pull_request":
        github_pull_request(
            logger,
            access_token=github_access_token,
            conn_string=conn_string,
            package_name=args.package_name,
            pyfyzz_record_id=args.record_id,
        )

    else:
        print("No valid command provided. Use 'scan' or 'github_pull_request'.")

    stop_time = datetime.datetime.now()
    logger.log("info", f"[+] Pyfyzz finished @: {stop_time}.")
    sys.exit(0)
