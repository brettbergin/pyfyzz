#!/usr/bin/env python3

import os
import json
import uuid
import datetime

import yaml
import pandas as pd
from sqlalchemy import create_engine, ForeignKey
from sqlalchemy import String, DateTime, Column, CHAR, Text, Integer
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.ext.declarative import declarative_base

from .logger import PyFyzzLogger

Base = declarative_base()


class FileExporter:
    def __init__(self, logger) -> None:
        self.logger = logger

    def _check_file_exists(self, f):
        if os.path.exists(f):
            os.remove(f)

    def export_to_json(self, payload: dict, file_path: str) -> None:
        """
        Export the analyzed package information to a JSON file.
        """
        self._check_file_exists(file_path)

        def custom_default(o):
            if isinstance(o, (set, list, tuple)):
                return list(o)
            elif callable(o):
                try:
                    return f"<callable {o.__name__}>"
                except AttributeError:
                    return "<callable object>"
            return str(o)

        with open(file_path, "w") as json_file:
            json.dump(payload, json_file, indent=4, default=custom_default)

        self.logger.log(
            "info", f"[+] Package information exported to JSON file: {file_path}"
        )

    def export_to_yaml(self, payload: dict, file_path: str) -> None:
        """
        Export the analyzed package information to a YAML file.
        """
        self._check_file_exists(file_path)

        with open(file_path, "w") as yaml_file:
            yaml.dump(payload, yaml_file, default_flow_style=False)

        self.logger.log(
            "info", f"[+] Package information exported to YAML file: {file_path}"
        )


class BatchJob(Base):
    __tablename__ = "batches"

    batch_job_id = Column(CHAR(36), primary_key=True, unique=True)
    package_name = Column(String(255), nullable=False)
    start_time = Column(DateTime, nullable=False)
    stop_time = Column(DateTime, nullable=True)
    batch_status = Column(String(255), nullable=False)
    at_risk_methods = Column(Integer, nullable=True)
    at_risk_methods_date = Column(DateTime, nullable=True)

    fuzz_results = relationship("FuzzResults", back_populates="batch_job")
    topologies = relationship("PackageTopology", back_populates="batch_job")
    batch_summaries = relationship(
        "BatchSummaries", back_populates="batch_job"
    )  # Added relationship to BatchSummaries


class BatchSummaries(Base):
    __tablename__ = "batch_summaries"

    batch_summary_id = Column(CHAR(36), primary_key=True, unique=True)
    batch_job_id = Column(CHAR(36), ForeignKey("batches.batch_job_id"))
    package_name = Column(String(255), nullable=False)
    exception_type = Column(String(255), nullable=False)
    exception_occurences = Column(Integer, nullable=True)
    exception_occurences_date = Column(DateTime, nullable=True)

    batch_job = relationship(
        "BatchJob", back_populates="batch_summaries"
    )  # Corrected back_populates to match BatchJob


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


class DatabaseExporter:
    def __init__(self, db_uri: str, logger: PyFyzzLogger = None) -> None:
        """
        Initialize the DatabaseExporter with a database URI and optional logger.
        """
        self.logger = logger if logger else PyFyzzLogger()

        self._engine = create_engine(db_uri)
        self._db_session = sessionmaker(bind=self._engine)
        self.session = self._db_session()

        self.setup_database()

    def setup_database(self):
        Base.metadata.create_all(self._engine)

    def start_new_batch(
        self,
        batch_job_id,
        package_name,
        start_time,
        at_risk_count,
        stop_time=None,
        batch_status="running",
    ) -> None:
        """ """
        new_batch_job = BatchJob(
            batch_job_id=batch_job_id,
            package_name=package_name,
            start_time=start_time,
            stop_time=stop_time,
            at_risk_methods=at_risk_count,
            at_risk_methods_date=datetime.datetime.now(),
            batch_status=batch_status,
        )
        self.session.add(new_batch_job)
        self.session.commit()

    def update_job_complete(self, batch_job_id, stop_time, batch_status):
        """
        Update the batch job with the given ID to mark its completion.

        :param batch_job_id: The unique identifier of the batch job to update.
        :param stop_time: The time the batch job was completed.
        :param status: The status to set for the batch job.
        """

        batch_job = self.session.query(BatchJob).get(batch_job_id)
        if batch_job:
            batch_job.batch_status = batch_status
            batch_job.stop_time = stop_time
            self.session.commit()

    def insert_batch_summary(self, counts, batch_job_id, pkg_name):
        """ """
        for exception_type, exception_occurences in counts.items():
            new_batch_summary = BatchSummaries(
                batch_summary_id=str(uuid.uuid4()),
                batch_job_id=batch_job_id,
                package_name=pkg_name,
                exception_type=exception_type,
                exception_occurences=exception_occurences,
                exception_occurences_date=datetime.datetime.now(),
            )
            self.session.add(new_batch_summary)
        self.session.commit()
        return

    def export_to_database(self, df: pd.DataFrame, table_name: str) -> None:
        """
        Export the given DataFrame to a SQL database.

        :param df: The DataFrame to be exported.
        :param table_name: The name of the table to which the data will be exported.
        """
        if df.empty:
            self.logger.log(
                "error",
                f"[-] DataFrame is empty. No data to export to table '{table_name}'.",
            )
            return

        if "batch_job_id" not in df.columns:
            self.logger.log("error", "[-] batch_job_id column is missing. Quitting.")
            return

        table_row_identifier = "record_id"

        if table_row_identifier not in df.columns:
            df[table_row_identifier] = [str(uuid.uuid4()) for _ in range(len(df))]

        for col in df.columns:
            if col == table_row_identifier:
                continue

            if df[col].apply(lambda x: isinstance(x, (dict, list, object))).any():
                df[col] = df[col].apply(
                    lambda x: json.dumps(x) if isinstance(x, (dict, list)) else str(x)
                )

        try:
            df.to_sql(table_name, con=self._engine, if_exists="append", index=False)
            self.logger.log(
                "info",
                f"[+] Data successfully exported to table '{table_name}' in the database.",
            )

        except Exception as e:
            self.logger.log(
                "error",
                f"[-] Failed to export data to table '{table_name}'. Error: {str(e)}",
            )
