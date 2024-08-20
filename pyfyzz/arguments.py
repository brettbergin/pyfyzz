import argparse


class Arguments:
    def __init__(self) -> None:
        pass

    def parse_arguments(self) -> argparse.Namespace:
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
