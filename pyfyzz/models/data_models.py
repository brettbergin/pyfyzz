#!/usr/bin/env python3

from dataclasses import dataclass, field # , asdict
from typing import List, Dict, Optional, Any

# import pandas as pd


# Dataclass for database configuration
@dataclass
class DBOptions:
    user: str
    password: str
    host: str
    port: int
    name: str


# Dataclass for package analysis
@dataclass
class ParameterInfo:
    name: str
    kind: str
    default: Optional[str] = None
    param_type: Optional[str] = None

    # def as_dict(self):
    #     return asdict(self)


# Dataclass for package analysis
@dataclass
class MethodInfo:
    name: str
    parameters: List[ParameterInfo] = field(default_factory=list)
    return_type: Optional[str] = None

    method_filepath: Optional[str] = None  # Added file_path for methods

    # def as_dict(self):
    #     return asdict(self)


# Dataclass for package analysis
@dataclass
class ClassInfo:
    name: str
    methods: Dict[str, List[ParameterInfo]] = field(default_factory=dict)

    # def as_dict(self):
    #     return asdict(self)


# Dataclass for package analysis
@dataclass
class ModuleInfo:
    name: str
    classes: Dict[str, Dict[str, List[ParameterInfo]]] = field(default_factory=dict)
    functions: List[str] = field(default_factory=list)

    # def as_dict(self):
    #     return asdict(self)


# Dataclass for package analysis
@dataclass
class PackageInfo:
    name: str
    modules: Dict[str, Dict[str, Dict[str, List[ParameterInfo]]]] = field(
        default_factory=dict
    )

    package_filepath: Optional[str] = None  # Added file_path for packages

    # def as_dict(self):
    #     return asdict(self)

    # def to_dataframe(self):
    #     flattened_list = []
    #     for module_name, module_info in self.modules.items():
    #         for class_name, class_info in module_info.items():
    #             for method_name, method_info in class_info.items():
    #                 for param in method_info.parameters:
    #                     flattened_list.append(
    #                         {
    #                             "module_name": module_name,
    #                             "class_name": class_name,
    #                             "method_name": method_name,
    #                             "param_name": param.name,
    #                             "param_kind": param.kind,
    #                             "param_default": param.default,
    #                             "param_type": param.param_type,
    #                             "return_type": method_info.return_type,
    #                         }
    #                     )
    #     return pd.DataFrame(flattened_list)


# Dataclass for fuzzing results
@dataclass
class FuzzCase:
    inputs: Dict[str, Any]
    return_value: Optional[Any] = None
    exception: Optional[str] = None
    encoded_source: Optional[str] = None

    # def as_dict(self):
    #     return asdict(self)


# Dataclass for fuzzing results
@dataclass
class MethodResult:
    method_name: str
    test_cases: List[FuzzCase] = field(default_factory=list)

    # def as_dict(self):
    #     return asdict(self)


# Dataclass for fuzzing results
@dataclass
class FuzzResult:
    name: str
    method_results: List[MethodResult] = field(default_factory=list)

    # def as_dict(self):
    #     return asdict(self)

    # def to_dataframe(self):
    #     flattened_list = []
    #     for method_result in self.method_results:
    #         for test_case in method_result.test_cases:
    #             flattened_list.append(
    #                 {
    #                     "method_name": method_result.method_name,
    #                     "inputs": test_case.inputs,
    #                     "return_value": test_case.return_value,
    #                     "exception": test_case.exception,
    #                     "encoded_source": test_case.encoded_source,
    #                 }
    #             )
    #     return pd.DataFrame(flattened_list)


