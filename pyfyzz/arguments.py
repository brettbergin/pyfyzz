#!/usr/bin/env python3

import argparse


class Arguments:
    def __init__(self) -> None:
        pass

    def parse_arguments(self) -> argparse.Namespace:
        """
        Parse command-line arguments for the script.
        """
        parser = argparse.ArgumentParser(
            prog="pyfyzz", description="PyFyzz: Analyze a Python package's structure."
        )

        # Create subparsers for 'scan' and 'create_pull_request'
        subparsers = parser.add_subparsers(dest="command", help="Available commands")

        # Subparser for 'scan' command
        scan_parser = subparsers.add_parser("scan", help="Scan a Python package")
        scan_parser.add_argument(
            "--package_name",
            "-p",
            type=str,
            required=True,
            help="Name of the Python package to analyze.",
        )

        # Subparser for 'github_pull_request' command
        pr_parser = subparsers.add_parser(
            "github_pull_request", help="Create a pull request"
        )
        pr_parser.add_argument(
            "--package_name",
            "-p",
            type=str,
            required=True,
            help="Name of the Python package to analyze.",
        )
        pr_parser.add_argument(
            "--record_id",
            "-r",
            type=str,
            required=True,
            help="Record ID of the Python package to create PR for.",
        )

        # Add any additional arguments specific to each subcommand if needed
        return parser.parse_args()
