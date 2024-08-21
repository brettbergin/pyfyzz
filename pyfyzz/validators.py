#!/usr/bin/env python3

from .logger import PyFyzzLogger


class PyFyzzInputValidator:
    def __init__(self):
        self.logger = PyFyzzLogger()

    def validate_package_name(self, package_name: str) -> bool:
        """
        Helps validate that the package name argument is of type string
        and is not an empty value.

        returns: string(package_name) or False
        """

        if not package_name or not isinstance(package_name, str):
            self.logger.log("error", "[-] Invalid package name argument provided.")
            return False
        return package_name

    def validate_ignore_private(self, ignore_private: bool) -> bool:
        """
        Helps validate that the ignore private argument is of tupe boolean.

        returns bool(ignore_private) or False.
        """

        if ignore_private not in [True, False]:
            self.logger.log("error", f"[-] Invalid ignore private argmuent provided.")
            return False
        return ignore_private

    def validate_output_format(self, output_format: str) -> bool:
        """
        Helps validate that the output format argument value is either
        `json` or `yaml`.

        returns string(output_format) or False
        """

        if output_format.lower() not in ["json", "yaml"]:
            self.logger.log("error", f"[-] Invalid output format argument provided.")
            return False
        return output_format
