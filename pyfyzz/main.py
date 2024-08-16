#!/usr/bin/env python3

import sys
import argparse


from .analyzer import PythonPackageAnalyzer
from .exporter import FileExporter
from .fuzzer import Fuzzer


def parse_arguments():
    """
    Parse command-line arguments for the script.
    """
    parser = argparse.ArgumentParser(
        description="PyFyzz: Analyze a Python package's structure."
    )
    parser.add_argument(
        "--package_name",
        "-p",
        type=str,
        required=True,
        help="Name of the Python package to analyze.",
    )
    parser.add_argument(
        "--output_format", "-o", type=str, required=True, help="Output format to use."
    )
    parser.add_argument(
        "--ignore_private",
        "-i",
        action="store_true",
        help="Ignore internal methods or functions.",
    )
    return parser.parse_args()


def main():
    """
    Main entry point for the script. Parses arguments, verifies the package,
    and performs the analysis and export.
    """
    args = parse_arguments()

    package_name = args.package_name
    ignore_private = args.ignore_private
    output_format = args.output_format

    if not package_name or package_name == "":
        print(f"[-] Invalid package has been provided. Using: {package_name}. Qutting.")
        sys.exit(-1)
    print(f"[+] Beginning package analysis for package: {package_name}")

    if not isinstance(ignore_private, bool) or ignore_private in ["True", "False"]:
        print("[-] Ignore private argument is incorrect or malformed. Quitting.")
        sys.exit("-1")
    print(f"[+] Ignoring private methods: {ignore_private}")

    analyzer = PythonPackageAnalyzer()

    importable = analyzer.verify_importable_package(package_name)
    if not importable:
        print(f"[-] Package: {package_name} found not to be importable. Qutting.")
        sys.exit(-1)

    pkg_info = analyzer.run(pkg_name=package_name, ignore_private=ignore_private)
    if not pkg_info:
        print(
            f"[-] Unable to analyze provided package. Using: {package_name}. Quitting."
        )
        sys.exit(-1)
    print("[+] Package analysis is complete.")

    exporter = FileExporter()

    if output_format == "json":
        exporter.export_to_json(pkg_info, f"composition_{package_name}.json")

    elif output_format == "yaml":
        exporter.export_to_yaml(pkg_info, f"composition_{package_name}.yaml")

    else:
        print("[-] Invalid output format provided. Skipping output & quitting.")
        sys.exit(-1)

    fuzzer = Fuzzer(package_under_test=pkg_info)
    ran = fuzzer.run()
    if not ran:
        print("[-] Fuzzer run execution did not complete successfully. Qutting.")
        sys.exit(-1)
        
    if output_format == "json":
        fuzzer.export_results_to_json(f"results_{package_name}.json")

    if output_format == "yaml":
        fuzzer.export_results_to_yaml(f"results_{package_name}.yaml")

    sys.exit(0)
