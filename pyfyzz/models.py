#!/usr/bin/env python3

import uuid
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Optional, Any

import pandas as pd

from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import (
    Column, 
    String, 
    Integer, 
    DateTime, 
    Text, 
    ForeignKey, 
    CHAR, 
    Boolean
)


Base = declarative_base()


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
    modules: Dict[str, Dict[str, Dict[str, List[ParameterInfo]]]] = field(default_factory=dict)

    def as_dict(self):
        return asdict(self)

    def to_dataframe(self):
        flattened_list = []
        for module_name, module_info in self.modules.items():
            for class_name, class_info in module_info.items():
                for method_name, method_info in class_info.items():
                    for param in method_info.parameters:
                        flattened_list.append({
                            'module_name': module_name,
                            'class_name': class_name,
                            'method_name': method_name,
                            'param_name': param.name,
                            'param_kind': param.kind,
                            'param_default': param.default,
                            'param_type': param.param_type,
                            'return_type': method_info.return_type
                        })
        return pd.DataFrame(flattened_list)

# Dataclass for fuzzing results
@dataclass
class FuzzCase:
    inputs: Dict[str, Any]
    return_value: Optional[Any] = None
    exception: Optional[str] = None
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

    def to_dataframe(self):
        flattened_list = []
        for method_result in self.method_results:
            for test_case in method_result.test_cases:
                flattened_list.append({
                    'method_name': method_result.method_name,
                    'inputs': test_case.inputs,
                    'return_value': test_case.return_value,
                    'exception': test_case.exception,
                    'encoded_source': test_case.encoded_source
                })
        return pd.DataFrame(flattened_list)

# Dataclass for database configuration
@dataclass
class DBOptions:
    user: str
    password: str
    host: str
    port: int
    name: str

# SQLAlchemy ORM Models

# Object for the batches table in db.
class BatchJob(Base):
    __tablename__ = "batches"

    batch_job_id = Column(CHAR(36), primary_key=True, unique=True)
    package_name = Column(String(255), nullable=False)
    start_time = Column(DateTime, nullable=False)
    stop_time = Column(DateTime, nullable=True)
    batch_status = Column(String(255), nullable=False)
    discovered_methods = Column(Integer, nullable=True)
    discovered_methods_date = Column(DateTime, nullable=True)

    fuzz_results = relationship("FuzzResults", back_populates="batch_job")
    topologies = relationship("PackageTopology", back_populates="batch_job")
    batch_summaries = relationship("BatchSummaries", back_populates="batch_job")

# Object for the batch_summaries table in db.
class BatchSummaries(Base):
    __tablename__ = "batch_summaries"

    batch_summary_id = Column(CHAR(36), primary_key=True, unique=True)
    batch_job_id = Column(CHAR(36), ForeignKey("batches.batch_job_id"))
    package_name = Column(String(255), nullable=False)
    exception_type = Column(String(255), nullable=False)
    exception_occurences = Column(Integer, nullable=True)
    exception_occurences_date = Column(DateTime, nullable=True)

    batch_job = relationship("BatchJob", back_populates="batch_summaries")

# Object for the fuzz_results table in db.
class FuzzResults(Base):
    __tablename__ = "fuzz_results"

    record_id = Column(CHAR(36), primary_key=True, unique=True)
    batch_job_id = Column(CHAR(36), ForeignKey("batches.batch_job_id"))
    package_name = Column(String(255), nullable=False)
    method_name = Column(String(255), nullable=False)
    inputs = Column(Text, nullable=True)
    exception = Column(String(255), nullable=True)
    encoded_source = Column(Text, nullable=True)

    batch_job = relationship("BatchJob", back_populates="fuzz_results")

# Object for the topologies table in db.
class PackageTopology(Base):
    __tablename__ = "topologies"

    record_id = Column(CHAR(36), primary_key=True, unique=True)
    batch_job_id = Column(CHAR(36), ForeignKey("batches.batch_job_id"))
    package_name = Column(String(255), nullable=True)
    module_name = Column(String(255), nullable=True)
    class_name = Column(String(255), nullable=True)
    method_name = Column(String(255), nullable=True)
    param_name = Column(String(255), nullable=True)
    param_kind = Column(String(255), nullable=True)
    param_default = Column(String(255), nullable=True)
    param_type = Column(String(255), nullable=True)
    return_type = Column(String(255), nullable=True)

    batch_job = relationship("BatchJob", back_populates="topologies")

# Object for the package_info table in db.
class PackageInfoSQL(Base):
    __tablename__ = "package_info"

    id = Column(CHAR(36), primary_key=True, default=lambda: str(uuid.uuid4()), unique=True)
    name = Column(String(255), nullable=False)
    version = Column(String(50), nullable=False)
    author = Column(String(255), nullable=True)
    author_email = Column(String(255), nullable=True)
    description = Column(Text, nullable=True)
    description_content_type = Column(String(255), nullable=True)
    home_page = Column(String(255), nullable=True)
    license = Column(Text, nullable=True)
    summary = Column(Text, nullable=True)
    keywords = Column(String(255), nullable=True)
    yanked = Column(Boolean, default=False)
    yanked_reason = Column(Text, nullable=True)
    download_count_last_day = Column(Integer, nullable=True)
    download_count_last_week = Column(Integer, nullable=True)
    download_count_last_month = Column(Integer, nullable=True)
    project_url = Column(String(255), nullable=True)

    release_files = relationship("ReleaseFile", back_populates="package_info")
    vulnerabilities = relationship("Vulnerabilities", back_populates="package_info")

# Object for the release_files table in db.
class ReleaseFile(Base):
    __tablename__ = "release_files"

    id = Column(CHAR(36), primary_key=True, default=lambda: str(uuid.uuid4()), unique=True)
    comment_text = Column(Text, nullable=True)
    downloads = Column(Integer, nullable=True)
    filename = Column(String(255), nullable=False)
    has_sig = Column(Boolean, nullable=False)
    md5_digest = Column(String(255), nullable=True)
    packagetype = Column(String(255), nullable=True)
    python_version = Column(String(255), nullable=True)
    requires_python = Column(String(255), nullable=True)
    size = Column(Integer, nullable=True)
    upload_time = Column(DateTime, nullable=True)
    url = Column(Text, nullable=True)
    yanked = Column(Boolean, default=False)
    yanked_reason = Column(Text, nullable=True)
    version = Column(String(50), nullable=False)
    package_info_id = Column(CHAR(36), ForeignKey("package_info.id"))

    package_info = relationship("PackageInfoSQL", back_populates="release_files")
    digests = relationship("Digests", uselist=False, back_populates="release_file")

# Object for the digests table in db.
class Digests(Base):
    __tablename__ = "digests"

    id = Column(CHAR(36), primary_key=True, default=lambda: str(uuid.uuid4()), unique=True)
    blake2b_256 = Column(String(255), nullable=True)
    md5 = Column(String(255), nullable=True)
    sha256 = Column(String(255), nullable=True)
    release_file_id = Column(CHAR(36), ForeignKey("release_files.id"))

    release_file = relationship("ReleaseFile", back_populates="digests")

# Object for the vulnerabilities table in db.
class Vulnerabilities(Base):
    __tablename__ = "vulnerabilities"

    id = Column(CHAR(36), primary_key=True, default=lambda: str(uuid.uuid4()), unique=True)
    vulnerability_type = Column(String(255), nullable=True)  # Example field
    severity = Column(String(50), nullable=True)  # Example field
    package_info_id = Column(CHAR(36), ForeignKey("package_info.id"))

    package_info = relationship("PackageInfoSQL", back_populates="vulnerabilities")
