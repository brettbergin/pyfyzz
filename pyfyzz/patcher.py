#!/usr/bin/env python3

import os
import re
import ast
import textwrap
from pathlib import Path

import black


class PyFyzzCodePatcher:

    def __init__(self, logger) -> None:
        self.logger = logger

    def _ensure_indentation_replacement(self, original_code, new_code):
        """
        Ensures the new method code has the correct indentation level based on the original method.
        """
        self.logger.log("debug", "[!] Ensuring proper indentation for the new code.")

        original_indent = re.match(r"(\s*)", original_code).group(0)
        indented_new_code = "\n".join(
            [
                original_indent + line if line.strip() else line
                for line in new_code.splitlines()
            ]
        )

        self.logger.log("debug", "[!] Indentation ensured for new code.")
        return indented_new_code

    def _write_ast_to_file(self, tree, file_path):
        """
        Write the modified AST back to the file.
        """
        self.logger.log("info", f"[+] Writing updated AST to file: {file_path}")

        try:
            new_code = ast.unparse(tree)
            with open(file_path, "w") as f:
                f.write(new_code)

            self.logger.log(
                "info",
                f"[+] Successfully wrote the updated patch back to file!",
            )

        except Exception as e:
            self.logger.log(
                "error", f"[-] Error writing updated patch to {file_path}: {str(e)}"
            )

    def _format_raw_code(self, raw_code):
        """
        Formats a raw string of code into valid Python format.
        """
        self.logger.log(
            "info", "[+] Formatting python source code in prep for AST parsing."
        )

        formatted_code = textwrap.dedent(raw_code).strip()
        formatted_code_lines = [
            line for line in formatted_code.splitlines() if line.strip()
        ]
        formatted_code = "\n".join(formatted_code_lines)

        try:
            ast.parse(formatted_code)
            self.logger.log("info", "[+] python source code formatted successfully.")
            return formatted_code

        except SyntaxError as e:
            self.logger.log(
                "error", f"[-] Syntax error when formatting source code: {e}"
            )
            return None

    def _compare_function_signature(self, node, original_node):
        """
        Compares two function signatures based on name and arguments.
        """
        self.logger.log(
            "info",
            f"[+] Comparing function signatures: {node.name} vs {original_node.name}",
        )

        if node.name != original_node.name:
            self.logger.log(
                "error", "[-] Function signatures do not match. Name mismatch."
            )
            return False

        if len(node.args.args) != len(original_node.args.args):
            self.logger.log(
                "error", "[-] Function signatures do not match. Size mismatch."
            )
            return False

        self.logger.log("info", "[+] Function signatures match.")
        return True

    def _find_file_with_code(self, folder_path, original_code):
        """
        Finds the file in the folder that contains the given original code.
        """
        self.logger.log(
            "info", "[+] Searching for a file containing the original source code."
        )
        formatted_code = self._format_raw_code(original_code)

        if not formatted_code:
            self.logger.log("error", "[-] Original code cannot be formatted.")
            raise ValueError(f"Error: Original code can't be formatted.")

        try:
            original_ast = ast.parse(formatted_code).body
        except SyntaxError as e:
            self.logger.log("error", f"[-] Error parsing original code: {e}")
            return None

        for root, _, files in os.walk(folder_path):
            for file in files:
                if file.endswith(".py"):
                    file_path = os.path.join(root, file)
                    with open(file_path, "r", encoding="utf-8") as f:
                        source_code = f.read()
                        try:
                            tree = ast.parse(source_code)

                        except SyntaxError as e:
                            self.logger.log(
                                "error",
                                f"[-] Error attempting AST parsing on file: {file_path}: {e}",
                            )
                            continue

                        for node in ast.walk(tree):

                            if (
                                isinstance(node, ast.FunctionDef)
                                and node.name == original_ast[0].name
                            ):
                                if self._compare_function_signature(
                                    node, original_ast[0]
                                ):
                                    self.logger.log(
                                        "info",
                                        f"[+] Found matching function in file: {file_path}",
                                    )
                                    return file_path

                            if isinstance(node, ast.ClassDef):
                                for class_node in node.body:
                                    if (
                                        isinstance(class_node, ast.FunctionDef)
                                        and class_node.name == original_ast[0].name
                                    ):
                                        if self._compare_function_signature(
                                            class_node, original_ast[0]
                                        ):
                                            self.logger.log(
                                                "info",
                                                f"[+] Found matching method in class in file: {file_path}",
                                            )
                                            return file_path

        self.logger.log("error", "[-] File not found.")
        return None

    def _format_with_black(self, dir_path):
        """ """
        if not isinstance(dir_path, str):
            return False

        path = Path(dir_path)
        self.logger.log("info", f"[+] Attempting formatting w/ Black.")

        black.format_file_in_place(
            src=path, fast=False, mode=black.FileMode(), write_back=black.WriteBack.YES
        )

        self.logger.log("info", f"[+] Successfully formatted updated code.")
        return True
