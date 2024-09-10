#!/usr/bin/env python3

from dataclasses import dataclass, field, asdict
from typing import List, Dict, Optional, Any


# Dataclass for database configuration
@dataclass
class DBOptions:
    user: str
    password: str
    host: str
    port: int
    name: str

    def as_dict(self):
        return asdict(self)


# Dataclass for package analysis
@dataclass
class ParameterInfo:
    name: str
    kind: str
    default: Optional[str] = None
    param_type: Optional[str] = None

    def as_dict(self):
        return asdict(self)


# Dataclass for package analysis
@dataclass
class MethodInfo:
    name: str
    parameters: List[ParameterInfo] = field(default_factory=list)
    return_type: Optional[str] = None

    method_filepath: Optional[str] = None

    def as_dict(self):
        return asdict(self)


# Dataclass for package analysis
@dataclass
class ClassInfo:
    name: str
    methods: Dict[str, List[ParameterInfo]] = field(default_factory=dict)

    def as_dict(self):
        return asdict(self)


# Dataclass for package analysis
@dataclass
class ModuleInfo:
    name: str
    classes: Dict[str, Dict[str, List[ParameterInfo]]] = field(default_factory=dict)
    functions: List[str] = field(default_factory=list)

    def as_dict(self):
        return asdict(self)


# Dataclass for package analysis
@dataclass
class PackageInfo:
    name: str
    modules: Dict[str, Dict[str, Dict[str, List[ParameterInfo]]]] = field(
        default_factory=dict
    )

    package_filepath: Optional[str] = None

    def as_dict(self):
        return asdict(self)


# Dataclass for fuzzing results
@dataclass
class FuzzCase:
    inputs: Dict[str, Any]
    return_value: Optional[Any] = None
    exception: Optional[str] = None
    exception_type: Optional[str] = None
    is_python_exception: Optional[bool] = None
    encoded_source: Optional[str] = None

    def as_dict(self):
        return asdict(self)


# Dataclass for fuzzing results
@dataclass
class MethodResult:
    method_name: str
    test_cases: List[FuzzCase] = field(default_factory=list)

    def as_dict(self):
        return asdict(self)


# Dataclass for fuzzing results
@dataclass
class FuzzResult:
    name: str
    method_results: List[MethodResult] = field(default_factory=list)

    def as_dict(self):
        return asdict(self)
