#!/usr/bin/env python3

import sys

from .analyzer import PythonPackageAnalyzer
from .exporter import FileExporter
from .fuzzer import Fuzzer
from .logger import PyFyzzLogger
from .arguments import Arguments
from .validators import PyFyzzInputValidator


def main():
    """
    Main entry point for the script. Parses arguments, verifies the package,
    and performs the analysis and export.
    """
    logger = PyFyzzLogger(name="pyfyzz")
    logger.log("info", "Starting pyfyzz.")
    arguments = Arguments()

    validator = PyFyzzInputValidator()
    args = arguments.parse_arguments()

    package_name = validator.validate_package_name(args.package_name)
    if not package_name:
        logger.log("error", f"[-] Invalid package has been provided. Using: {package_name}. Qutting.")
        sys.exit(-1)
    logger.log("info", f"[+] Beginning package analysis for package: {package_name}")

    ignore_private = validator.validate_ignore_private(args.ignore_private)
    if not ignore_private:
        logger.log("error", "[-] Ignore private argument is incorrect or malformed. Quitting.")
        sys.exit(-1) 
    logger.log("info", f"[+] Ignoring private methods: {ignore_private}")

    output_format = validator.validate_output_format(args.output_format)
    if not output_format:
        logger.log("error", "[-] Invalid output format has been provided. Quitting.")
        sys.exit(-1)
    logger.log("info", f"[+] Running with file output format: {output_format}")
    
    analyzer = PythonPackageAnalyzer()
    importable = analyzer.verify_importable_package(package_name)
    if not importable:
        logger.log("error", f"[-] Package: {package_name} found not to be importable. Qutting.")
        sys.exit(-1)
    logger.log("debug", f"[!] Package found importable into runtime: {importable}")

    pkg_info = analyzer.run(pkg_name=package_name, ignore_private=ignore_private)
    if not pkg_info:
        logger.log("error",
            f"[-] Unable to analyze provided package. Using: {package_name}. Quitting."
        )
        sys.exit(-1)
    logger.log("info", "[+] Package analysis is complete.")

    exporter = FileExporter()

    if output_format == "json":
        exporter.export_to_json(pkg_info, f"composition_{package_name}.json")

    elif output_format == "yaml":
        exporter.export_to_yaml(pkg_info, f"composition_{package_name}.yaml")

    else:
        logger.log("error", 
            "[-] Invalid output format provided. Skipping output & quitting."
        )
        sys.exit(-1)
    logger.log(
        "info", 
        "[+] Package analysis file exportation is complete."
    )

    fuzzer = Fuzzer(package_under_test=pkg_info)
    ran = fuzzer.run()
    if not ran:
        logger.log(
            "error", 
            "[-] Fuzzer run execution did not complete successfully. Qutting."
        )
        sys.exit(-1)
    
    logger.log(
        "info", 
        "[+] Fuzzing has been completed."
    )

    if output_format == "json":
        fuzzer.export_results_to_json(f"results_{package_name}.json")

    if output_format == "yaml":
        fuzzer.export_results_to_yaml(f"results_{package_name}.yaml")

    logger.log(
        "info", 
        "[+] Fuzzer results file exportation is complete."
    )

    logger.log(
        "info", 
        "[+] Pyfyzz finished."
    )

    sys.exit(0)
