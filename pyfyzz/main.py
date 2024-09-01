#!/usr/bin/env python3

import os
import sys
import uuid
from typing import Tuple, Dict

import pandas as pd

from .analyzer import PythonPackageAnalyzer
from .exporter import FileExporter, DatabaseExporter
from .fuzzer import Fuzzer
from .logger import PyFyzzLogger
from .arguments import Arguments
from .validators import PyFyzzInputValidator
from .models import PackageInfo, DBOptions
from .serializers import PackageInfoSerializer, FuzzResultSerializer


def fuzz_package(
    logger: PyFyzzLogger, package_info: PackageInfo
) -> Tuple[Dict, pd.DataFrame]:
    """
    Attempts to invoke the package fuzzer against the package info
    data model object we enumerated.

    returns: Fuzzer or sys.exit(-1)
    """

    fuzzer = Fuzzer(package_under_test=package_info)
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
    return (results_as_dict, results_as_df)


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


def publish_to_database(logger, pkg_df: pd.DataFrame, fr_df: pd.DataFrame, batch_job_id: str) -> None:
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

    pkg_df['batch_job_id'] = batch_job_id  # Add batch_job_id column to pkg_df
    fr_df['batch_job_id'] = batch_job_id  # Add batch_job_id column to fr_df

    logger.log("info", "[+] Preparing to add package info to database.")
    db_exporter.export_to_database(pkg_df, "compositions")

    logger.log("info", "[+] Preparing to add fuzz results to database.")
    db_exporter.export_to_database(fr_df, "results")


def main() -> None:
    """
    Main entry point for the script. Parses arguments, verifies the package,
    and performs the analysis and export.
    """

    logger = PyFyzzLogger(name="pyfyzz", level="debug")
    logger.log("info", "[+] Starting pyfyzz.")
    
    batch_job_id = str(uuid.uuid4()) 

    file_exporter = FileExporter(logger=logger)

    package_name, ignore_private, output_format = valid_user_input(logger)

    pkg_info, pkg_dict, pkg_df = analyze_package(
        logger, pkg_name=package_name, igr_priv=ignore_private
    )

    fuzz_results_dict, fuzz_results_df = fuzz_package(logger, package_info=pkg_info)

    if output_format == "json":
        file_exporter.export_to_json(pkg_dict, f"composition_{package_name}.json")
        file_exporter.export_to_json(fuzz_results_dict, f"results_{package_name}.json")

    elif output_format == "yaml":
        file_exporter.export_to_yaml(pkg_dict, f"composition_{package_name}.yaml")
        file_exporter.export_to_yaml(fuzz_results_dict, f"results_{package_name}.yaml")

    publish_to_database(logger, pkg_df, fuzz_results_df, batch_job_id)

    logger.log("info", "[+] Fuzzer results file exportation is complete.")
    logger.log("info", "[+] Pyfyzz finished.")

    sys.exit(0)
