#!/usr/bin/env python3

import sys
import builtins

import base64
import importlib
import inspect
from collections import defaultdict
from typing import Dict, List

import traceback

from .models.data_models import FuzzResult, MethodResult, FuzzCase
from .logger import PyFyzzLogger
from .ai import ChatGPTInterface


class Fuzzer:
    def __init__(self, logger: PyFyzzLogger, package_under_test, openai_api_key):
        self.logger = logger
        self.package_under_test = package_under_test
        self.openai_api_key = openai_api_key
        self.test_map = self._generate_test_map()
        self.has_specific_types = self._check_for_specific_types()
        self.exception_count = defaultdict(int)
        self.fuzz_results = FuzzResult(name=package_under_test.name)

        # todo -> Update API Key To OS ENV VAR
        self.ai = ChatGPTInterface(
            api_key=self.openai_api_key,
            logger=self.logger
        )

    def _check_for_specific_types(self) -> bool:
        """
        Check if any method in the package has a parameter type other than "Any".
        """
        for module_name, classes in self.package_under_test.modules.items():
            for class_name, methods in classes.items():
                for method_name, method_info in methods.items():
                    for param in method_info.parameters:
                        if param.param_type != "Any":
                            return True
        return False

    def _generate_test_map(self) -> Dict:
        """
        Generate a map of all methods/functions to be fuzzed.
        The map will contain the module name, class (if applicable), and method/function name.
        """
        test_map = {}

        for module_name, classes in self.package_under_test.modules.items():
            for class_name, methods in classes.items():
                for method_name, parameters in methods.items():
                    if class_name:
                        # Method within a class
                        full_import_path = f"{module_name}.{class_name}.{method_name}"
                    else:
                        # Standalone function
                        full_import_path = f"{module_name}.{method_name}"

                    test_map[full_import_path] = parameters

        return test_map

    def generate_import_statement(self, method_path: str) -> str:
        """
        Generate a valid Python import statement by introspecting the package structure.
        """
        components = method_path.split(".")
        package = components[0]

        # Start by assuming the path might refer to a module or class in the package
        current_module = importlib.import_module(package)
        import_path = package
        class_or_method = None

        for component in components[1:]:
            try:
                if inspect.ismodule(current_module):
                    current_module = importlib.import_module(
                        f"{import_path}.{component}"
                    )
                    import_path += f".{component}"
                elif inspect.isclass(current_module) or inspect.ismethod(
                    current_module
                ):
                    class_or_method = component
                    break
                else:
                    class_or_method = component
                    break
            except ImportError:
                class_or_method = component
                break

        if class_or_method:
            import_statement = f"from {import_path} import {class_or_method}"
        else:
            import_statement = f"import {import_path}"

        return import_statement


    def _is_py_standard_exception(self, exception_type: str) -> bool:
        """
        Determine if the provided exception type is a standard Python exception.
        
        Args:
        exception_type (type): The exception class to check.

        Returns:
        bool: True if it's a standard Python exception, False if it's likely a custom exception.
        """
        return exception_type in [
            exc.__name__ for exc 
            in builtins.__dict__.values() 
            if isinstance(exc, type) and issubclass(exc, BaseException)
        ]

    def _generate_fuzzed_inputs(self, parameters: list) -> List:
        """
        Generate multiple fuzzed inputs for each parameter using various strategies.
        """
        fuzzed_inputs_sets = []

        for param in parameters:
            # Get the list of possible fuzzed values for this parameter
            fuzzed_values = self.fuzz_parameter(param.param_type)

            self.logger.log(
                "debug",
                f"[+] Testing parameter: {param.name} with {len(fuzzed_values)} permutations.",
            )
            for fuzzed_value in fuzzed_values:
                input_set = {
                    p.name: None for p in parameters
                }  # Initialize with None for all params
                input_set[param.name] = (
                    fuzzed_value  # Set the fuzzed value for the current param
                )

                # Save this set of fuzzed inputs
                fuzzed_inputs_sets.append(input_set)

        return fuzzed_inputs_sets

    def fuzz_parameter(self, param_type: str) -> List:
        """
        Apply a gauntlet of fuzzing strategies based on the parameter's expected type.
        """
        fuzzed_values = []

        if param_type == "int":
            fuzzed_values.extend(self.fuzz_integers())
        elif param_type == "str":
            fuzzed_values.extend(self.fuzz_strings())
        elif param_type == "bool":
            fuzzed_values.extend(self.fuzz_booleans())
        elif param_type == "list":
            fuzzed_values.extend(self.fuzz_lists())
        elif param_type == "dict":
            fuzzed_values.extend(self.fuzz_dicts())
        elif param_type == "float":
            fuzzed_values.extend(self.fuzz_floats())
        else:
            fuzzed_values.append(None)  # Default case for unknown types

        return fuzzed_values

    def fuzz_integers(self) -> List:
        return [
            "not_an_int",  # Type mismatch
            sys.maxsize,  # Boundary value
            -sys.maxsize - 1,  # Boundary value
            0,  # Edge case
            -1,
            1,  # Small integers
            sys.maxsize + 1,  # Overflow
            -sys.maxsize - 2,  # Underflow
        ]

    def fuzz_strings(self) -> List:
        return [
            12345,  # Type mismatch
            "",  # Empty string
            "\n",
            "\t",
            "\0",  # Special characters
            "A" * 10000,  # Long string
            "!@#$%^&*()",  # Special symbols
            None,  # Null case
        ]

    def fuzz_booleans(self) -> List:
        return [
            "not_a_bool",  # Type mismatch
            True,
            False,  # Normal values
            0,
            1,  # Integer equivalents
            None,  # Null case
        ]

    def fuzz_lists(self) -> List:
        return [
            [],  # Empty list
            [1, 2, 3],  # Normal list
            ["a", "b", "c"],  # Mixed type list
            None,  # Null case
        ]

    def fuzz_dicts(self) -> List:
        return [
            {},  # Empty dictionary
            {"key": "value"},  # Normal dictionary
            {"key": None},  # Dictionary with None value
            {1: "one", 2: "two"},  # Dictionary with integer keys
            None,  # Null case
        ]

    def fuzz_floats(self) -> List:
        return [
            "not_a_float",  # Type mismatch
            sys.float_info.max,  # Boundary value
            -sys.float_info.max,  # Boundary value
            0.0,  # Edge case
            -1.0,
            1.0,  # Small floats
            sys.float_info.max * 2,  # Overflow
            -sys.float_info.max * 2,  # Underflow
        ]

    def fuzz_method(self, method_path: str) -> None:
        import_statement = self.generate_import_statement(method_path)

        # Dynamically import the class or method
        exec(import_statement, globals())

        # Split the method_path to identify class and method names
        components = method_path.split(".")
        method_name = components[-1]
        class_name = components[-2] if len(components) > 2 else None
        module_name = ".".join(components[:-2])

        # Import the module containing the class or function
        module = importlib.import_module(module_name)

        if class_name:
            cls = getattr(module, class_name)
            # Check if the class is abstract
            if inspect.isabstract(cls):
                self.logger.log(
                    "debug",
                    f"[!] Skipping abstract class {cls.__name__}. We can do better.",
                )
                return

            # Handle required constructor arguments
            init_signature = inspect.signature(cls.__init__)
            init_params = init_signature.parameters
            required_args = [
                p
                for p in init_params
                if init_params[p].default == inspect.Parameter.empty and p != "self"
            ]

            if required_args:
                self.logger.log(
                    "debug",
                    f"[!] Skipping class {cls.__name__} due to required constructor arguments: {required_args}. We can do better.",
                )
                return

            # If no required arguments, create an instance
            instance = cls()
            method = getattr(instance, method_name)
        else:
            method = getattr(module, method_name)

        self.logger.log(
            "info", f"[+] Fuzzing: '{import_statement} as x; x.{method_name}()'"
        )

        method_result = MethodResult(method_name=method_name)
        parameters = self.test_map[method_path].parameters
        fuzzed_inputs_sets = self._generate_fuzzed_inputs(parameters)

        source_code = inspect.getsource(method)
        encoded_source = base64.b64encode(source_code.encode()).decode()

        # Suggest improvement via AI and encode result
        improved_source = self.ai.suggest_improvement(
                source_code=encoded_source, 
                code_path=f"{module_name}::{class_name}::{method_name}").encode('utf-8')

        for fuzzed_inputs in fuzzed_inputs_sets:
            test_case = FuzzCase(inputs=fuzzed_inputs, encoded_source=encoded_source)
            try:
                test_case.return_value = method(**fuzzed_inputs)
                
            except Exception as e:
                self.exception_count[type(e).__name__] += 1
                test_case.exception = str(e)
                test_case.exception_type = type(e).__name__
                test_case.exception_traceback = base64.b64encode(
                    traceback.format_exc().encode('utf-8')
                ).decode('utf-8')
                test_case.is_python_exception = self._is_py_standard_exception(exception_type=type(e).__name__)

            test_case.improved_source = base64.b64encode(improved_source).decode("utf-8")

            method_result.test_cases.append(test_case)
            
        self.fuzz_results.method_results.append(method_result)

    def summarize_exceptions(self) -> None:
        """
        Print a summary of all unhandled exceptions encountered during fuzzing.
        """
        for exception_type, count in self.exception_count.items():
            self.logger.log(
                "info",
                f"[-->] Found New Unhandled Exception: {exception_type}: {count} occurrence(s)",
            )

    def run(self) -> bool:
        """
        Run the fuzzer on all methods/functions in the test map.
        """
        if not self.has_specific_types:
            self.logger.log(
                "error",
                "[-] No defined type annotations found in codebase. Fuzzing skipped.",
            )
            return False

        self.logger.log("info", "[+] Begin method/function fuzzing.")
        for method_path in self.test_map:
            self.fuzz_method(method_path)
        self.logger.log("info", "[+] Completed method/function fuzzing.")

        self.summarize_exceptions()

        return True
