#!/usr/bin/env python3

import json
import pandas as pd

from .models.data_models import PackageInfo, FuzzResult


class PackageInfoSerializer:
    def __init__(self, package_info: PackageInfo) -> None:
        self.package_info = package_info
        self.package_name = self.package_info.name
        self.package_filepath = self.package_info.package_filepath

    def as_dict(self) -> dict:
        output_dict = {
            "package_name": self.package_name,
            "package_filepath": self.package_filepath,
            "modules": {},
        }

        for module_name, module_info in self.package_info.modules.items():
            module_dict = {"name": module_name, "classes": {}}

            for class_name, class_info in module_info.items():
                class_dict = {"name": class_name, "methods": []}

                for method_name, method_info in class_info.items():
                    method_dict = {
                        "name": method_name,
                        "method_filepath": method_info.method_filepath,
                        "params": [],
                    }

                    for param in method_info.parameters:
                        param_dict = {
                            "name": param.name,
                            "kind": param.kind,
                            "default": param.default,
                            "param_type": param.param_type,
                        }
                        method_dict["params"].append(param_dict)

                    class_dict["methods"].append(method_dict)

                module_dict["classes"][class_name] = class_dict

            output_dict["modules"][module_name] = module_dict

        return output_dict

    def as_flattened_dict(self) -> list:
        flattened_list = []

        for module_name, module_info in self.package_info.modules.items():
            for class_name, class_info in module_info.items():
                for method_name, method_info in class_info.items():
                    if method_info.parameters:
                        for param in method_info.parameters:
                            flattened_list.append(
                                {
                                    "package_name": self.package_name,
                                    "package_filepath": self.package_filepath,
                                    "module_name": module_name,
                                    "class_name": class_name,
                                    "method_name": method_name,
                                    "method_filepath": method_info.method_filepath,
                                    "param_name": param.name,
                                    "param_kind": param.kind,
                                    "param_default": param.default,
                                    "param_type": param.param_type,
                                    "return_type": method_info.return_type,
                                }
                            )
                    else:
                        # Handle methods without parameters
                        flattened_list.append(
                            {
                                "package_name": self.package_name,
                                "package_filepath": self.package_filepath,
                                "module_name": module_name,
                                "class_name": class_name,
                                "method_name": method_name,
                                "method_filepath": method_info.method_filepath,
                                "param_name": None,
                                "param_kind": None,
                                "param_default": None,
                                "param_type": None,
                                "return_type": method_info.return_type,
                            }
                        )

        return flattened_list

    def as_dataframe(self) -> pd.DataFrame:
        return pd.DataFrame(self.as_flattened_dict())


class FuzzResultSerializer:
    def __init__(self, fuzz_results: FuzzResult) -> None:
        self.fuzz_results = fuzz_results

    def as_dict(self):
        output_dict = {"package_name": self.fuzz_results.name, "results": []}

        for method_result in self.fuzz_results.method_results:
            method_result_dict = {
                "method_name": method_result.method_name,
                "test_cases": [],
            }
            for fuzz_case in method_result.test_cases:
                method_result_dict["test_cases"].append(
                    {
                        "inputs": json.dumps(fuzz_case.inputs),
                        "return_value": fuzz_case.return_value,
                        "exception": (
                            str(fuzz_case.exception) if fuzz_case.exception else None
                        ),
                        "encoded_source": fuzz_case.encoded_source,
                    }
                )
            output_dict["results"].append(method_result_dict)
        return output_dict

    def as_flattened_dict(self) -> list:
        flattened_list = []

        for method_result in self.fuzz_results.method_results:

            for fuzz_case in method_result.test_cases:
                flattened_list.append(
                    {
                        "package_name": self.fuzz_results.name,
                        "method_name": method_result.method_name,
                        "inputs": json.dumps(fuzz_case.inputs),
                        "return_value": fuzz_case.return_value,
                        "exception": (
                            str(fuzz_case.exception) if fuzz_case.exception else None
                        ),
                        "encoded_source": fuzz_case.encoded_source,
                    }
                )

        return flattened_list

    def as_dataframe(self) -> pd.DataFrame:
        df = pd.DataFrame(self.as_flattened_dict())

        if "exception" in df.columns:
            df["exception"] = df["exception"].apply(
                lambda x: str(x) if isinstance(x, Exception) else x
            )

        if "inputs" in df.columns:
            df["inputs"] = df["inputs"].apply(
                lambda x: json.dumps(x) if isinstance(x, dict) else x
            )
        return df
