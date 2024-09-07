#!/usr/bin/env python3

import json
import uuid
import datetime

import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from .logger import PyFyzzLogger

from .models.orm_models import (
    BatchJob,
    BatchSummaries,
    PackageRecords,
    ReleaseFile,
    Digests,
    Vulnerabilities,
    Base,
)


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
        discovered_methods_count,
        stop_time=None,
        batch_status="running",
    ) -> None:
        """ """

        new_batch_job = BatchJob(
            batch_job_id=batch_job_id,
            package_name=package_name,
            start_time=start_time,
            stop_time=stop_time,
            discovered_methods=discovered_methods_count,
            discovered_methods_date=datetime.datetime.now(),
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

    def add_pip_package(self, data: dict, batch_job_id: str):
        package_record = PackageRecords(
            name=data["info"]["name"],
            batch_job_id=batch_job_id,
            version=data["info"]["version"],
            author=data["info"]["author"],
            author_email=data["info"]["author_email"],
            description=data["info"]["description"],
            description_content_type=data["info"]["description_content_type"],
            home_page=data["info"]["home_page"],
            license=data["info"]["license"],
            summary=data["info"]["summary"],
            keywords=data["info"]["keywords"],
            project_url=data['info']['project_url'],
            project_urls=json.dumps(data['info']['project_urls']),
            yanked=data["info"]["yanked"],
            yanked_reason=data["info"]["yanked_reason"],
        )
        for version, release_list in data["releases"].items():
            for release in release_list:
                release_file = ReleaseFile(
                    comment_text=release["comment_text"],
                    downloads=release["downloads"],
                    filename=release["filename"],
                    has_sig=release["has_sig"],
                    md5_digest=release["md5_digest"],
                    packagetype=release["packagetype"],
                    python_version=release["python_version"],
                    requires_python=release["requires_python"],
                    size=release["size"],
                    upload_time=release["upload_time"],
                    url=release["url"],
                    yanked=release.get("yanked", False),
                    yanked_reason=release.get("yanked_reason", None),
                    version=version,
                    package_record=package_record,  # Associate with the main PackageRecords object
                )

                digests = Digests(
                    blake2b_256=release["digests"].get("blake2b_256"),
                    md5=release["digests"].get("md5"),
                    sha256=release["digests"].get("sha256"),
                )
                release_file.digests = digests
                package_record.release_files.append(release_file)

        for vulnerability in data.get("vulnerabilities", []):
            vulnerability_obj = Vulnerabilities(
                id=vulnerability.get("id", ""),
                description=vulnerability.get("description", ""),
                package_record=package_record  # Associate with the main PackageRecords object
            )
            package_record.vulnerabilities.append(vulnerability_obj)

        self.session.add(package_record)
        self.session.commit()

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
