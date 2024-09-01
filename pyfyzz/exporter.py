#!/usr/bin/env python3

import os
import json
import uuid

import yaml
import pandas as pd
from sqlalchemy import create_engine, inspect, text

from .logger import PyFyzzLogger


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


class DatabaseExporter:
    def __init__(self, db_uri: str, logger: PyFyzzLogger = None) -> None:
        """
        Initialize the DatabaseExporter with a database URI and optional logger.
        """
        self.db_uri = db_uri
        self.engine = create_engine(db_uri)
        self.logger = logger if logger else PyFyzzLogger()

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
        
        if 'batch_job_id' not in df.columns:
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

        inspector = inspect(self.engine)  # Use Inspector to check for table existence
        if not inspector.has_table(table_name):
            self.logger.log(
                "info", f"[+] Creating table '{table_name}' in the database."
            )
            # If table does not exist, create it with appropriate data types
            df.head(0).to_sql(table_name, con=self.engine, if_exists='fail', index=False)

        try:
            df.to_sql(table_name, con=self.engine, if_exists="append", index=False)
            primary_key_columns = inspector.get_pk_constraint(table_name).get('constrained_columns', [])

            if not len(primary_key_columns) > 0:
                self.logger.log("debug", f"[!] No primary keys found on table {table_name}. Adding: {primary_key_columns} as primary key.")
                with self.engine.connect() as connection:
                    connection.execute(text(f"ALTER TABLE {table_name} MODIFY {table_row_identifier} CHAR(36);"))
                    connection.execute(text(f"ALTER TABLE {table_name} ADD PRIMARY KEY ({table_row_identifier});"))

            else:
                self.logger.log("info", f"[+] Primary Key: {primary_key_columns} exists on table: {table_name}")

            self.logger.log(
                "info",
                f"[+] Data successfully exported to table '{table_name}' in the database.",
            )

        except Exception as e:
            self.logger.log(
                "error",
                f"[-] Failed to export data to table '{table_name}'. Error: {str(e)}",
            )
