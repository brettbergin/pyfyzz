# #!/usr/bin/env python3

# import os
# import json
# import yaml


# class FileExporter:
#     def __init__(self, logger) -> None:
#         self.logger = logger

#     def _check_file_exists(self, f):
#         if os.path.exists(f):
#             os.remove(f)

#     def export_to_json(self, payload: dict, file_path: str) -> None:
#         """
#         Export the analyzed package information to a JSON file.
#         """
#         self._check_file_exists(file_path)

#         def custom_default(o):
#             if isinstance(o, (set, list, tuple)):
#                 return list(o)
#             elif callable(o):
#                 try:
#                     return f"<callable {o.__name__}>"
#                 except AttributeError:
#                     return "<callable object>"
#             return str(o)

#         with open(file_path, "w") as json_file:
#             json.dump(payload, json_file, indent=4, default=custom_default)

#         self.logger.log(
#             "info", f"[+] Package information exported to JSON file: {file_path}"
#         )

#     def export_to_yaml(self, payload: dict, file_path: str) -> None:
#         """
#         Export the analyzed package information to a YAML file.
#         """
#         self._check_file_exists(file_path)

#         with open(file_path, "w") as yaml_file:
#             yaml.dump(payload, yaml_file, default_flow_style=False)

#         self.logger.log(
#             "info", f"[+] Package information exported to YAML file: {file_path}"
#         )
