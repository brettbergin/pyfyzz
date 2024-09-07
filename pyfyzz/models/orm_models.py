#!/usr/bin/env python3

import uuid

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
    Boolean,
)


Base = declarative_base()


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
    package_record = relationship("PackageRecords", back_populates="batch_job")


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
    return_value = Column(Text, nullable=True)

    batch_job = relationship("BatchJob", back_populates="fuzz_results")


# Object for the topologies table in db.
class PackageTopology(Base):
    __tablename__ = "topologies"

    record_id = Column(CHAR(36), primary_key=True, unique=True)
    batch_job_id = Column(CHAR(36), ForeignKey("batches.batch_job_id"))
    package_name = Column(String(255), nullable=True)
    package_filepath = Column(Text, nullable=True)
    module_name = Column(String(255), nullable=True)
    class_name = Column(String(255), nullable=True)
    method_name = Column(String(255), nullable=True)
    method_filepath = Column(Text, nullable=True)
    param_name = Column(String(255), nullable=True)
    param_kind = Column(String(255), nullable=True)
    param_default = Column(String(255), nullable=True)
    param_type = Column(String(255), nullable=True)
    return_type = Column(String(255), nullable=True)

    batch_job = relationship("BatchJob", back_populates="topologies")


# Object for the package_info table in db.
class PackageRecords(Base):
    __tablename__ = "package_records"

    id = Column(
        CHAR(36), primary_key=True, default=lambda: str(uuid.uuid4()), unique=True
    )
    batch_job_id = Column(CHAR(36), ForeignKey("batches.batch_job_id"))

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
    project_urls = Column(Text, nullable=True)

    release_files = relationship("ReleaseFile", back_populates="package_record")
    vulnerabilities = relationship("Vulnerabilities", back_populates="package_record")
    batch_job = relationship("BatchJob", back_populates="package_record")


# Object for the release_files table in db.
class ReleaseFile(Base):
    __tablename__ = "release_files"

    id = Column(
        CHAR(36), primary_key=True, default=lambda: str(uuid.uuid4()), unique=True
    )
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
    package_record_id = Column(CHAR(36), ForeignKey("package_records.id"))

    package_record = relationship("PackageRecords", back_populates="release_files")
    digests = relationship("Digests", uselist=False, back_populates="release_files")


# Object for the digests table in db.
class Digests(Base):
    __tablename__ = "digests"

    id = Column(
        CHAR(36), primary_key=True, default=lambda: str(uuid.uuid4()), unique=True
    )
    blake2b_256 = Column(String(255), nullable=True)
    md5 = Column(String(255), nullable=True)
    sha256 = Column(String(255), nullable=True)
    release_file_id = Column(CHAR(36), ForeignKey("release_files.id"))

    release_files = relationship("ReleaseFile", back_populates="digests")


# Object for the vulnerabilities table in db.
class Vulnerabilities(Base):
    __tablename__ = "vulnerabilities"

    id = Column(
        CHAR(36), primary_key=True, default=lambda: str(uuid.uuid4()), unique=True
    )

    vulnerability_type = Column(String(255), nullable=True)
    severity = Column(String(50), nullable=True)
    package_record_id = Column(CHAR(36), ForeignKey("package_records.id"))

    package_record = relationship("PackageRecords", back_populates="vulnerabilities")
