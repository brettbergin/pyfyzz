#!/usr/bin/env python3

import pkgutil
import inspect
import importlib

from .models.data_models import ModuleInfo, PackageInfo, ParameterInfo, MethodInfo


class PythonPackageAnalyzer:
    def __init__(self, logger) -> None:
        self.logger = logger

    def verify_importable_package(self, pkg_name: str) -> bool:
        """
        Verify if the provided package name is importable by checking against
        the list of available packages and modules.

        returns: True or False
        """
        mods_n_pkgs = [modname for _, modname, _ in pkgutil.iter_modules()]

        if pkg_name in mods_n_pkgs:
            return True
        else:
            self.logger.log(
                "error",
                f"[-] Package {pkg_name} is not found in the list of importable modules/packages.",
            )
            return False

    def enumerate_package_contents(
        self, pkg_name: str, package: importlib.import_module  # , ignore_private=False
    ) -> PackageInfo:
        """
        Analyze the contents of a package or module and
        return a PackageInfo dataclass with the package contents.

        returns: PackageInfo
        """
        package_info = PackageInfo(name=pkg_name)
        package_info.package_filepath = inspect.getfile(package)

        if hasattr(package, "__path__"):
            for module_info in pkgutil.iter_modules(package.__path__):
                module_name = f"{pkg_name}.{module_info.name}"
                module = importlib.import_module(module_name)
                self.analyze_module(module_name, module, package_info)

        else:
            self.analyze_module(pkg_name, package, package_info)

        return package_info

    def analyze_module(
        self,
        module_name: str,
        module,
        package_info: PackageInfo,  # , ignore_private: bool
    ) -> None:
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
                        return_type=return_type,
                        method_filepath=inspect.getfile(method),
                    )

                    class_methods[method_name] = method_info

                module_struct.classes[class_name] = class_methods

        functions = inspect.getmembers(module, inspect.isfunction)
        for function_name, function in functions:

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

    def run(self, pkg_name: str) -> PackageInfo or None:
        """
        Attempt to import and analyze the provided package name, returning
        structured information if successful.
        """
        try:
            package = importlib.import_module(pkg_name)
            results = self.enumerate_package_contents(pkg_name, package)
            return results

        except ImportError as e:
            self.logger.log("error", f"Error importing package {pkg_name}. Error: {e}")
            return None
