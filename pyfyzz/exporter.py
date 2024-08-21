#!/usr/bin/env python3

import json
from dataclasses import asdict

import yaml

from .models import PackageInfo
from .logger import PyFyzzLogger


class FileExporter:
    def __init__(self) -> None:
        self.logger = PyFyzzLogger()

    def export_to_json(self, package_info: PackageInfo, file_path: str) -> None:
        """
        Export the analyzed package information to a JSON file.
        """

        def custom_default(o):
            if isinstance(o, (set, list, tuple)):
                return list(o)
            elif callable(o):
                return f"<callable {o.__name__}>"
            return str(o)

        package_dict = asdict(package_info)

        with open(file_path, "w") as json_file:
            json.dump(package_dict, json_file, indent=4, default=custom_default)

        self.logger.log(
            "info", f"[+] Package information exported to JSON file: {file_path}"
        )

    def export_to_yaml(self, package_info: PackageInfo, file_path: str) -> None:
        """
        Export the analyzed package information to a YAML file.
        """
        modules_dict = asdict(package_info).get("modules")

        package_dict = {"package": {"name": package_info.name, "modules": modules_dict}}

        with open(file_path, "w") as yaml_file:
            yaml.dump(package_dict, yaml_file, default_flow_style=False)

        self.logger.log(
            "info", f"[+] Package information exported to YAML file: {file_path}"
        )
