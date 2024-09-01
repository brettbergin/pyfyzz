#!/usr/bin/env python3

import os
import json
import pandas as pd
from sqlalchemy import (
    create_engine,
    inspect,
    text,
    MetaData,
    Table,
    Column,
    String,
    Integer,
    Float,
    Boolean,
    DateTime,
    JSON,
    Text,
)
from sqlalchemy.dialects.mysql import VARCHAR
import pandas as pd
import uuid
import yaml

from .logger import PyFyzzLogger


class FileExporter:
    def __init__(self, logger) -> None:
        if not logger:
            self.logger = PyFyzzLogger()
        else:
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

        if "id" not in df.columns:
            df["id"] = [str(uuid.uuid4()) for _ in range(len(df))]

        for col in df.columns:
            if col == "id":
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

        try:
            df.to_sql(table_name, con=self.engine, if_exists="append", index=False)
            self.logger.log(
                "info",
                f"[+] Data successfully exported to table '{table_name}' in the database.",
            )

        except Exception as e:
            self.logger.log(
                "error",
                f"[-] Failed to export data to table '{table_name}'. Error: {str(e)}",
            )
