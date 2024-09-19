#!/usr/bin/env python3


class PyFyzzInputValidator:
    def __init__(self, logger):
        self.logger = logger

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
