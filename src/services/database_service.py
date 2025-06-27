import os
import time
import traceback
import urllib.parse

import pandas as pd
from langfuse import observe
from sqlalchemy import create_engine


class DatabaseService:
    """
    Service class for database interactions.
    Extracted SQL execution logic from LLMsEvaluator.process_questions_with_model()
    and decode_source from module_data.
    """

    @observe
    def get_dynamic_sql(self, source: str, sql_query: str, as_data_frame: bool = False):
        """
        Execute dynamic SQL query on specified database source.

        Args:
            source (str): The source of the database. Either "azure-sql", or "onprem-sql".
            sql_query (str): The SQL query to execute.
            as_data_frame (bool): If True, the result is returned as a pandas DataFrame.
        Returns:
            str or pd.DataFrame: The result as a string or DataFrame.
        Raises:
            RuntimeError: If there is an error connecting to or executing the query in the database.
        """
        try:
            conn = self.get_connection(source)
            df = pd.read_sql(sql_query, conn)

            if as_data_frame:
                return df
            else:
                return df.to_string(index=False)

        except Exception as e:
            tb = traceback.extract_tb(e.__traceback__)
            frame = tb[0]
            method_name = frame.name
            line_number = frame.lineno
            file_name = os.path.basename(frame.filename)
            raise RuntimeError(
                f"[{file_name}].[{method_name}].[line-{line_number}] "
                "Error connecting or executing the query in the database."
            ) from e

    @staticmethod
    def decode_source(source):
        """
        Decode and normalize database source names.
        Extracted from module_data.decode_source()

        Args:
            source (str): Source identifier to decode

        Returns:
            str: Normalized source name
        """
        if source.lower() == "azuresql" or source.lower() == "azure-sql":
            return "azure-sql"
        if source.lower() == "onpremsql" or source.lower() == "onprem-sql":
            return "onprem-sql"
        return source.lower()

    def execute_sql_query(self, sql_query: str):
        """
        Execute SQL query and return results with metadata.

        Args:
            sql_query (str): SQL query to execute

        Returns:
            tuple: (df, executed, rows, columns, duration_sql)
                - df: DataFrame with results or None
                - executed: bool indicating if execution was successful
                - rows: number of rows returned
                - columns: number of columns returned
                - duration_sql: execution time in seconds
        """
        executed = True
        df = None
        rows = 0
        columns = 0
        duration_sql = 0

        if sql_query:
            try:
                t = time.time()
                df = self.get_dynamic_sql("azure-sql", sql_query, True)
                duration_sql = time.time() - t
                if df is not None:
                    rows = len(df)
                    columns = len(df.columns)
            except Exception as e:
                df = None
                executed = False
                print(f"[ERROR] SQL execution failed: {e}")
        else:
            executed = False
            duration_sql = 0
            rows = 0

        duration_sql = round(duration_sql, 2)

        return df, executed, rows, columns, duration_sql

    def get_connection(self, source):
        """
        Get database connection engine.
        Extracted from module_data.get_connection()

        Args:
            source (str): Database source identifier

        Returns:
            sqlalchemy.engine.Engine: Database connection engine

        Raises:
            RuntimeError: If connection fails
        """
        source = self.decode_source(source)
        engine = None

        if source == "azure-sql":
            server = os.getenv("DB_SERVER_AZURE")
            database = os.getenv("DB_NAME_AZURE")
            username = os.getenv("DB_USER_AZURE")
            password = os.getenv("DB_PASSWORD_AZURE")
            password = urllib.parse.quote_plus(password)

        elif source == "onprem-sql":
            server = os.getenv("DB_SERVER_ONPREM")
            database = os.getenv("DB_NAME_ONPREM")
            username = os.getenv("DB_USER_ONPREM")
            password = os.getenv("DB_PASSWORD_ONPREM")
            password = urllib.parse.quote_plus(password)

        # Usando pyodbc para generar la cadena de conexión adecuada
        connection_string = (
            f"mssql+pyodbc://{username}:{password}@{server}/{database}"
            "?driver=ODBC+Driver+18+for+SQL+Server&TrustServerCertificate=yes"
        )
        engine = create_engine(connection_string)

        # tries to conect to the server to warm up [for sql azure serverless]
        try:
            _ = pd.read_sql("SELECT @@servername", engine)
        except Exception:
            try:
                _ = pd.read_sql("SELECT @@servername", engine)
            except Exception as e:
                raise RuntimeError("Error connecting to the Azure SQL database.") from e

        return engine
