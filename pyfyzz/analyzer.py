#!/usr/bin/env python3

import pkgutil
import inspect
import importlib

from .models import ModuleInfo, PackageInfo, ParameterInfo, MethodInfo
from .logger import PyFyzzLogger

class PythonPackageAnalyzer:

    def __init__(self) -> None:
        self.logger = PyFyzzLogger()

    def verify_importable_package(self, pkg_name: str):
        """
        Verify if the provided package name is importable by checking against
        the list of available packages and modules.
        """
        mods_n_pkgs = [modname for _, modname, _ in pkgutil.iter_modules()]

        if pkg_name in mods_n_pkgs:
            return True
        else:
            self.logger.log(
                "error",
                f"[-] Package {pkg_name} is not found in the list of importable modules/packages."
            )
            return False

    def enumerate_package_contents(
        self, pkg_name, package, ignore_private=False
    ) -> PackageInfo:
        """
        Analyze the contents of a package or module and return structured information.
        """
        package_info = PackageInfo(name=pkg_name)

        if hasattr(package, "__path__"):
            for module_info in pkgutil.iter_modules(package.__path__):
                module_name = f"{pkg_name}.{module_info.name}"
                module = importlib.import_module(module_name)
                self.analyze_module(module_name, module, package_info, ignore_private)

        else:
            self.analyze_module(pkg_name, package, package_info, ignore_private)

        return package_info

    def analyze_module(self, module_name, module, package_info, ignore_private):
        """
        Analyze the classes, methods, and functions within a module and store
        the information in the provided PackageInfo object.
        """
        module_struct = ModuleInfo(name=module_name)

        classes = inspect.getmembers(module, inspect.isclass)
        for class_name, cls in classes:
            if cls.__module__ == module_name:
                class_methods = {}

                methods = inspect.getmembers(cls, inspect.isfunction)
                for method_name, method in methods:
                    # Ignore methods starting with _ or __ if the flag is set
                    if ignore_private and method_name.startswith("_"):
                        continue

                    parameters = []

                    signature = inspect.signature(method)

                    # Extract and store return type
                    return_type = signature.return_annotation
                    if return_type == inspect.Signature.empty:
                        return_type = "None"
                    else:
                        return_type = (
                            return_type.__name__
                            if hasattr(return_type, "__name__")
                            else str(return_type)
                        )

                    for param_name, param in signature.parameters.items():
                        # Skip the 'self' parameter
                        if param_name == "self":
                            continue

                        param_type = param.annotation
                        if param_type == inspect.Parameter.empty:
                            param_type = "Any"
                        else:
                            param_type = (
                                param_type.__name__
                                if hasattr(param_type, "__name__")
                                else str(param_type)
                            )

                        param_info = ParameterInfo(
                            name=param_name,
                            kind=param.kind.name,
                            default=(
                                param.default
                                if param.default is not inspect.Parameter.empty
                                else None
                            ),
                            param_type=param_type,
                        )
                        parameters.append(param_info)

                    method_info = MethodInfo(
                        name=method_name,
                        parameters=parameters,
                        return_type=return_type,  # Store return type
                    )

                    class_methods[method_name] = method_info

                module_struct.classes[class_name] = class_methods

        functions = inspect.getmembers(module, inspect.isfunction)
        for function_name, function in functions:
            # Ignore functions starting with _ or __ if the flag is set
            if ignore_private and function_name.startswith("_"):
                continue

            signature = inspect.signature(function)

            # Extract and store return type for standalone functions
            return_type = signature.return_annotation
            if return_type == inspect.Signature.empty:
                return_type = "None"
            else:
                return_type = (
                    return_type.__name__
                    if hasattr(return_type, "__name__")
                    else str(return_type)
                )

            function_info = MethodInfo(name=function_name, return_type=return_type)

            module_struct.functions.append(function_info)

        package_info.modules[module_name] = module_struct.classes

    def run(self, pkg_name, ignore_private=False):
        """
        Attempt to import and analyze the provided package name, returning
        structured information if successful.
        """
        try:
            package = importlib.import_module(pkg_name)
            results = self.enumerate_package_contents(pkg_name, package, ignore_private)
            return results

        except ImportError as e:
            self.logger.log("error", f"Error importing package {pkg_name}. Error: {e}")
            return None
