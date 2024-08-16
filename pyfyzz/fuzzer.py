#!/usr/bin/env python3

import sys
import json
import importlib
from dataclasses import asdict
from collections import defaultdict

import yaml

from .models import FuzzResult, MethodResult, TestCase


class Fuzzer:
    def __init__(self, package_under_test):
        self.package_under_test = package_under_test
        self.test_map = self._generate_test_map()
        self.has_specific_types = self._check_for_specific_types()
        self.exception_count = defaultdict(int)
        self.fuzz_results = FuzzResult(name=package_under_test.name)

    def _check_for_specific_types(self):
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

    def _generate_test_map(self):
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

    """
    This begins the issue regarding import statement generation
    """

    def generate_import_statement(self, method_path):
        """
        Generate a valid Python import statement for a given method_path.
        """
        # TODO: Refactor this function to improve how we resolve the method path
        # - into an import statement that aligns with the package architecture.

        components = method_path.split(".")

        package, module, clazz = components[0], components[1], components[2]
        method_name = components[-1]

        # import_path = '.'.join(components[:-1])
        # import_statement = f"from {import_path} import {method_name}"

        import_statement = f"from {package}.{module} import {clazz}"
        return import_statement

    # def generate_import_statement(self, method_path):
    #     """
    #     Generate a valid Python import statement for a given method_path.
    #     Adjust the method to dynamically resolve the import path based on package structure.
    #     """

    #     components = method_path.split(".")
    #     print(f"[!] Running with components: {components}")
    #     # Assume a minimum of a package and a method (e.g., "package.method")
    #     if len(components) < 2:
    #         raise ValueError("Invalid method path. At least package and method are required.")

    #     package = components[0]
    #     method_name = components[-1]

    #     # Handle cases based on the number of components
    #     if len(components) == 2:
    #         # Case: 'package.method'
    #         import_statement = f"from {package} import {method_name}"
    #     elif len(components) == 3:
    #         # Case: 'package.module.method' or 'package.class.method'
    #         module_or_class = components[1]
    #         import_statement = f"from {package}.{module_or_class} import {method_name}"
    #     elif len(components) > 3:
    #         # Case: 'package.subpackage.module.class.method'
    #         import_path = '.'.join(components[:-1])  # All components except the last (method)
    #         import_statement = f"from {import_path} import {method_name}"
    #     else:
    #         raise ValueError(f"Cannot resolve import statement for method path: {method_path}")

    #     print(f"[!] Attempting to use import statement: {import_statement}")
    #     return import_statement

    """
    This ends the issue regarding import statement generation
    """

    """
    The initial (legacy) way we determined input fuzzing parameters.
    """
    # def _generate_fuzzed_inputs(self, parameters):
    #     """
    #     Generate random inputs for the method's parameters.
    #     This is a simple mutation based payload generator
    #     and can be extended to handle additional parameter types.
    #     """

    #     fuzzed_inputs = {}
    #     # for param in parameters:
    #     #     if param.param_type == "int":
    #     #         fuzzed_inputs[param.name] = random.randint(-100, 100)
    #     #     elif param.param_type == "str":
    #     #         fuzzed_inputs[param.name] = "".join(
    #     #             random.choices("abcdefghijklmnopqrstuvwxyz", k=10)
    #     #         )
    #     #     elif param.param_type == "bool":
    #     #         fuzzed_inputs[param.name] = random.choice([True, False])
    #     #     else:
    #     #         fuzzed_inputs[param.name] = None  # Or generate a more complex structure
    #     for param in parameters:
    #         if param.param_type == "int":
    #             # fuzzed_inputs[param.name] = random.randint(-100, 100)
    #             fuzzed_inputs[param.name] = "".join(
    #                 random.choices("abcdefghijklmnopqrstuvwxyz", k=10)
    #             )
    #         elif param.param_type == "str":
    #             # fuzzed_inputs[param.name] = "".join(
    #             #     random.choices("abcdefghijklmnopqrstuvwxyz", k=10)
    #             # )
    #             fuzzed_inputs[param.name] = random.randint(-100, 100)

    #         elif param.param_type == "bool":
    #             # fuzzed_inputs[param.name] = random.choice([True, False])
    #             fuzzed_inputs[param.name] = random.choice([0, 1])

    #         else:
    #             fuzzed_inputs[param.name] = None  # Or generate a more complex structure

    #     return fuzzed_inputs
    """
    This ends the legacy way we determined input fuzzing paramters.
    """

    def _generate_fuzzed_inputs(self, parameters):
        """
        Generate multiple fuzzed inputs for each parameter using various strategies.
        """
        fuzzed_inputs_sets = []

        for param in parameters:
            # Get the list of possible fuzzed values for this parameter
            fuzzed_values = self.fuzz_parameter(param.param_type)

            print(
                f"[+] Testing parameter: {param.name} with {len(fuzzed_values)} permutations."
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

    def fuzz_parameter(self, param_type):
        """
        Apply a gauntlet of fuzzing strategies based on the parameter's expected type.
        """
        fuzzed_values = []

        if param_type == "int":
            # Type Mismatch
            fuzzed_values.append("not_an_int")

            # Boundary Values
            fuzzed_values.extend([sys.maxsize, -sys.maxsize - 1, 0, -1, 1])

            # Overflow/Underflow (depending on how the system handles them)
            fuzzed_values.extend([sys.maxsize + 1, -sys.maxsize - 2])

        elif param_type == "str":
            # Type Mismatch
            fuzzed_values.append(12345)

            # Empty String
            fuzzed_values.append("")

            # Special Characters
            fuzzed_values.append("\n")
            fuzzed_values.append("\t")
            fuzzed_values.append("\0")
            fuzzed_values.append("!@#$%^&*()")

            # Long String
            fuzzed_values.append("A" * 10000)

        elif param_type == "bool":
            # Type Mismatch
            fuzzed_values.append("not_a_bool")

            # Boundary Values
            fuzzed_values.extend([0, 1])

        elif param_type == "float":
            # Type Mismatch
            fuzzed_values.append("not_a_float")

            # Boundary Values
            fuzzed_values.extend(
                [sys.float_info.max, -sys.float_info.max, 0.0, -1.0, 1.0]
            )

            # Overflow/Underflow
            fuzzed_values.extend([sys.float_info.max * 2, -sys.float_info.max * 2])

        else:
            # For unknown or complex types, we can add more specific fuzzing strategies
            fuzzed_values.append(None)  # None for unknown types
            fuzzed_values.append("random_noise")  # Random noise data

        return fuzzed_values

    # def fuzz_method(self, method_path):
    #     """
    #     Fuzz a specific method by generating random inputs based on the parameters.
    #     """
    #     import_statement = self.generate_import_statement(method_path)
    #     print(f"[+] Fuzzing: {import_statement}")

    #     # Dynamically import the class or method
    #     exec(import_statement, globals())

    #     # Split the method_path to identify class and method names
    #     components = method_path.split(".")
    #     method_name = components[-1]
    #     class_name = components[-2] if len(components) > 2 else None
    #     module_name = ".".join(components[:-2])

    #     # Import the module containing the class or function
    #     module = importlib.import_module(module_name)

    #     # If class_name is present, we are dealing with an instance method
    #     if class_name:
    #         # Get the class and create an instance
    #         cls = getattr(module, class_name)
    #         instance = cls()  # Creating an instance of the class

    #         # Get the method from the instance
    #         method = getattr(instance, method_name)
    #     else:
    #         # If no class, it's a standalone function
    #         method = getattr(module, method_name)

    #     method_result = MethodResult(method_name=method_name)

    #     # Generate random inputs for each parameter
    #     method_info = self.test_map[method_path]  # This is a MethodInfo object
    #     parameters = method_info.parameters  # Access the parameters attribute
    #     fuzzed_inputs_sets = self._generate_fuzzed_inputs(parameters)  # Assume this returns a list of dicts

    #     source_code = inspect.getsource(method)
    #     print("[+] Evaluating Target:\n")
    #     print(source_code)

    #     # Iterate over each set of fuzzed inputs
    #     for fuzzed_inputs in fuzzed_inputs_sets:
    #         test_case = TestCase(inputs=fuzzed_inputs)
    #         print(
    #             f"[!] (TEST) Targeting {method.__name__}({fuzzed_inputs})"
    #         )

    #         try:
    #             test_case.return_value = method(**fuzzed_inputs)
    #         except Exception as e:
    #             test_case.exception = str(e)
    #             self.exception_count[type(e).__name__] += 1
    #         method_result.test_cases.append(test_case)
    #     self.fuzz_results.method_results.append(method_result)

    def fuzz_method(self, method_path):
        import_statement = self.generate_import_statement(method_path)

        exec(import_statement, globals())
        components = method_path.split(".")
        method_name = components[-1]
        class_name = components[-2] if len(components) > 2 else None
        module_name = ".".join(components[:-2])
        module = importlib.import_module(module_name)
        if class_name:
            cls = getattr(module, class_name)
            instance = cls()
            method = getattr(instance, method_name)
        else:
            method = getattr(module, method_name)

        print(f"[+] Fuzzing: {import_statement}.{method_name}")

        method_result = MethodResult(method_name=method_name)
        parameters = self.test_map[method_path].parameters
        fuzzed_inputs_sets = self._generate_fuzzed_inputs(parameters)
        for fuzzed_inputs in fuzzed_inputs_sets:
            test_case = TestCase(inputs=fuzzed_inputs)
            try:
                test_case.return_value = method(**fuzzed_inputs)
            except Exception as e:
                test_case.exception = str(e)
                self.exception_count[type(e).__name__] += 1
            method_result.test_cases.append(test_case)
        self.fuzz_results.method_results.append(method_result)

    def export_results_to_json(self, file_path: str):
        with open(file_path, "w") as json_file:
            json.dump(asdict(self.fuzz_results), json_file, indent=4)

    def export_results_to_yaml(self, file_path: str):
        with open(file_path, "w") as yaml_file:
            yaml.dump(asdict(self.fuzz_results), yaml_file, default_flow_style=False)

    def summarize_exceptions(self):
        """
        Print a summary of all unhandled exceptions encountered during fuzzing.
        """
        print("\n[+] Exception Summary:")
        for exception_type, count in self.exception_count.items():
            print(f"[-->] Unhandled Exception: {exception_type}: {count} occurrence(s)")

    def run(self):
        """
        Run the fuzzer on all methods/functions in the test map.
        """
        if not self.has_specific_types:
            print("[-] No defined type annotations found in codebase. Fuzzing skipped.")
            return False

        print("[+] Begin method/function fuzzing.")
        for method_path in self.test_map:
            self.fuzz_method(method_path)
        print("[+] Completed method/function fuzzing.")

        self.summarize_exceptions()

        return True
