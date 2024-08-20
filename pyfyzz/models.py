#!/usr/bin/env python3

from dataclasses import dataclass, field
from typing import List, Dict, Optional


@dataclass
class ParameterInfo:
    name: str
    kind: str
    default: Optional[str] = None
    param_type: Optional[str] = None


@dataclass
class MethodInfo:
    name: str
    parameters: List[ParameterInfo] = field(default_factory=list)
    return_type: Optional[str] = None


@dataclass
class ClassInfo:
    name: str
    methods: Dict[str, List[ParameterInfo]] = field(default_factory=dict)


@dataclass
class ModuleInfo:
    name: str
    classes: Dict[str, Dict[str, List[ParameterInfo]]] = field(default_factory=dict)
    functions: List[str] = field(default_factory=list)


@dataclass
class PackageInfo:
    name: str
    modules: Dict[str, Dict[str, Dict[str, List[ParameterInfo]]]] = field(
        default_factory=dict
    )


@dataclass
class FuzzCase:
    inputs: Dict[str, any]
    return_value: Optional[any] = None
    exception: Optional[str] = None
    encoded_source: Optional[str] = None  


@dataclass
class MethodResult:
    method_name: str
    test_cases: List[FuzzCase] = field(default_factory=list)


@dataclass
class FuzzResult:
    name: str
    method_results: List[MethodResult] = field(default_factory=list)
