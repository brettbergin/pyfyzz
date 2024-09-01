#!/usr/bin/env python3

import pandas as pd
import sys

from .analyzer import PythonPackageAnalyzer
from .exporter import FileExporter
from .exporter import DatabaseExporter
from .fuzzer import Fuzzer
from .logger import PyFyzzLogger
from .arguments import Arguments
from .validators import PyFyzzInputValidator
from .models import PackageInfo
from .serializers import PackageInfoSerializer
from .serializers import FuzzResultSerializer
from typing import Tuple


def fuzz_package(logger: PyFyzzLogger, package_info: PackageInfo) -> Fuzzer:
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
    results_as_df = FuzzResultSerializer(fuzz_results=fuzzer.fuzz_results).as_dataframe()
    return results_as_dict, results_as_df


def analyze_package(logger: PyFyzzLogger, pkg_name: str, igr_priv: bool) -> PackageInfo:
    """
    Enumerates all of the package contents in the given package and returns
    a data model object representing the entire package:

    example:  package -> module(s) -> class(es) -> method(s)/function(s) -> argument(s)/parameter(s)

    returns: object(PackageInfo) or sys.exit(-1)
    """

    analyzer = PythonPackageAnalyzer()
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
    validator = PyFyzzInputValidator()

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


def main() -> None:
    """
    Main entry point for the script. Parses arguments, verifies the package,
    and performs the analysis and export.
    """

    logger = PyFyzzLogger(name="pyfyzz")
    logger.log("info", "[+] Starting pyfyzz.")

    file_exporter = FileExporter(logger=logger)
    db_exporter = DatabaseExporter(
        db_uri="mysql+mysqlconnector://appuser:meepmeep@localhost:3306/pyfyzz", 
        logger=logger
    )

    package_name, ignore_private, output_format = valid_user_input(logger)

    pkg_info, pkg_dict, pkg_df = analyze_package(
        logger, 
        pkg_name=package_name, 
        igr_priv=ignore_private
    )

    fuzz_results_dict, fuzz_results_df = fuzz_package(logger, package_info=pkg_info)

    if output_format == "json":
        file_exporter.export_to_json(pkg_dict, f"composition_{package_name}.json")
        file_exporter.export_to_json(fuzz_results_dict, f"results_{package_name}.json")

    elif output_format == "yaml":
        file_exporter.export_to_yaml(pkg_dict, f"composition_{package_name}.yaml")
        file_exporter.export_to_yaml(fuzz_results_dict, f"results_{package_name}.yaml")

    db_exporter.export_to_database(pkg_df, "compositions")
    db_exporter.export_to_database(fuzz_results_df, "results")

    logger.log("info", "[+] Fuzzer results file exportation is complete.")
    logger.log("info", "[+] Pyfyzz finished.")

    sys.exit(0)
