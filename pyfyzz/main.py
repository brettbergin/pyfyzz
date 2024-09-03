#!/usr/bin/env python3

import os
import sys
import uuid
import json

from typing import Tuple, Dict
import datetime

import pandas as pd
import requests

from .analyzer import PythonPackageAnalyzer
from .exports import FileExporter
from .databases import DatabaseExporter
from .fuzzer import Fuzzer
from .logger import PyFyzzLogger
from .arguments import Arguments
from .validators import PyFyzzInputValidator
from .models import PackageInfo, DBOptions
from .serializers import PackageInfoSerializer, FuzzResultSerializer


def fuzz_package(
    logger: PyFyzzLogger, package_info: PackageInfo
) -> Tuple[Dict, pd.DataFrame, Dict]:
    """
    Attempts to invoke the package fuzzer against the package info
    data model object we enumerated.

    returns: Fuzzer or sys.exit(-1)
    """

    fuzzer = Fuzzer(logger=logger, package_under_test=package_info)
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
    logger: PyFyzzLogger, pkg_name: str, igr_priv: bool
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

    pkg_info = analyzer.run(pkg_name=pkg_name, ignore_private=igr_priv)
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

    ignore_private: bool = validator.validate_ignore_private(args.ignore_private)
    if not ignore_private:
        logger.log(
            "error", "[-] Ignore private argument is incorrect or malformed. Quitting."
        )
        sys.exit(-1)
    logger.log("info", f"[+] Ignoring private methods: {ignore_private}")

    output_format: str = validator.validate_output_format(args.output_format)
    if not output_format:
        logger.log("error", "[-] Invalid output format has been provided. Quitting.")
        sys.exit(-1)
    logger.log("info", f"[+] Running with file output format: {output_format}")
    return (package_name, ignore_private, output_format)


def publish_to_database(
    logger: PyFyzzLogger,
    pkg_name: str,
    start_t: datetime.datetime,
    pkg_df: pd.DataFrame,
    fr_df: pd.DataFrame,
    batch_job_id: str,
    discovered_methods: int,
) -> None:
    """ """
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

    if r.status_code in(200, 201, 202):
        resp_json = json.loads(r.content)
        db_exporter.add_pip_package(data=resp_json, batch_job_id=batch_job_id)
    else:
        logger.log("error", "[-] Unable to find package information in pypi.")


    pkg_df["batch_job_id"] = batch_job_id 
    fr_df["batch_job_id"] = batch_job_id

    logger.log("info", "[+] Preparing to add package info to database.")
    db_exporter.export_to_database(pkg_df, "topologies")

    logger.log("info", "[+] Preparing to add fuzz results to database.")
    db_exporter.export_to_database(fr_df, "fuzz_results")
    return db_exporter


def main() -> None:
    """
    Main entry point for the script. Parses arguments, verifies the package,
    and performs the analysis and export.
    """
    start_time = datetime.datetime.now()

    logger = PyFyzzLogger(name="pyfyzz", level="info")
    logger.log("info", f"[+] Starting pyfyzz @: {start_time}.")
    
    file_exporter = FileExporter(logger=logger)

    batch_job_id = str(uuid.uuid4())

    package_name, ignore_private, output_format = valid_user_input(logger)

    pkg_info, pkg_dict, pkg_df = analyze_package(
        logger, pkg_name=package_name, igr_priv=ignore_private
    )

    fuzz_results_dict, fuzz_results_df, fuzz_counts = fuzz_package(
        logger, package_info=pkg_info
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
    )

    db_exporter.insert_batch_summary(
        counts=fuzz_counts, batch_job_id=batch_job_id, pkg_name=package_name
    )

    if output_format == "json":
        file_exporter.export_to_json(pkg_dict, f"topology_{package_name}.json")
        file_exporter.export_to_json(fuzz_results_dict, f"results_{package_name}.json")

    elif output_format == "yaml":
        file_exporter.export_to_yaml(pkg_dict, f"topology_{package_name}.yaml")
        file_exporter.export_to_yaml(fuzz_results_dict, f"results_{package_name}.yaml")

    stop_time = datetime.datetime.now()
    db_exporter.update_job_complete(
        batch_job_id=batch_job_id, stop_time=stop_time, batch_status="completed"
    )

    logger.log("info", f"[+] Pyfyzz finished @: {stop_time}.")

    sys.exit(0)
