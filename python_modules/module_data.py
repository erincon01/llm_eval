import os
import traceback

import pandas as pd
from data.query_templates import (
    GET_CUSTOMERS_ORDERS,
    GET_CUSTOMERS_WITH_ORDERS,
    GET_ORDERS_BY_WEEK,
    GET_PARTSUPP_ORDERS,
    GET_SCHEMA_OVERVIEW,
    GET_TABLES_INFO_DATA,
    GET_YEARS_WITH_ORDERS,
)
from services.database_service import DatabaseService


def get_orders(source, year):
    try:
        db_service = DatabaseService()
        conn = db_service.get_connection(source)

        query = GET_ORDERS_BY_WEEK.format(start_date=f"{year}-01-01", end_date=f"{year}-12-31")

        df = pd.read_sql(query, conn)
        return df, query

    except Exception as e:
        tb = traceback.extract_tb(e.__traceback__)
        frame = tb[0]
        raise RuntimeError(
            f"[{os.path.basename(frame.filename)}].[{frame.name}] Error executing query in the database."
        ) from e


def get_customers_orders(source, year):
    try:
        db_service = DatabaseService()
        conn = db_service.get_connection(source)

        query = GET_CUSTOMERS_ORDERS.format(start_date=f"{year}-01-01", end_date=f"{year}-12-31")

        df = pd.read_sql(query, conn)
        return df, query

    except Exception as e:
        tb = traceback.extract_tb(e.__traceback__)
        frame = tb[0]
        raise RuntimeError(
            f"[{os.path.basename(frame.filename)}].[{frame.name}] Error executing query in the database."
        ) from e


def get_partsupp_orders(source, year):
    try:
        db_service = DatabaseService()
        conn = db_service.get_connection(source)

        query = GET_PARTSUPP_ORDERS.format(start_date=f"{year}-01-01", end_date=f"{year}-12-31")

        df = pd.read_sql(query, conn)
        return df, query

    except Exception as e:
        tb = traceback.extract_tb(e.__traceback__)
        frame = tb[0]
        raise RuntimeError(
            f"[{os.path.basename(frame.filename)}].[{frame.name}] Error executing query in the database."
        ) from e


def get_years_with_orders(source, as_data_frame=False):
    try:
        db_service = DatabaseService()
        conn = db_service.get_connection(source)

        query = GET_YEARS_WITH_ORDERS
        df = pd.read_sql(query, conn)

        return df if as_data_frame else df.to_string(index=False)

    except Exception as e:
        tb = traceback.extract_tb(e.__traceback__)
        frame = tb[0]
        raise RuntimeError(
            f"[{os.path.basename(frame.filename)}].[{frame.name}] Error executing query in the database."
        ) from e


def get_customers_with_orders(source, as_data_frame=False):
    try:
        db_service = DatabaseService()
        conn = db_service.get_connection(source)

        query = GET_CUSTOMERS_WITH_ORDERS
        df = pd.read_sql(query, conn)

        return df if as_data_frame else df.to_string(index=False)

    except Exception as e:
        tb = traceback.extract_tb(e.__traceback__)
        frame = tb[0]
        raise RuntimeError(
            f"[{os.path.basename(frame.filename)}].[{frame.name}] Error executing query in the database."
        ) from e


def get_tables_info_data(source, as_data_frame=False):
    try:
        db_service = DatabaseService()
        conn = db_service.get_connection(source)

        query = GET_TABLES_INFO_DATA
        df = pd.read_sql(query, conn)

        return df if as_data_frame else df.to_string(index=False)

    except Exception as e:
        tb = traceback.extract_tb(e.__traceback__)
        frame = tb[0]
        raise RuntimeError(
            f"[{os.path.basename(frame.filename)}].[{frame.name}] Error executing query in the database."
        ) from e


def get_database_schema(source, as_data_frame=False):
    try:
        db_service = DatabaseService()
        conn = db_service.get_connection(source)

        query = GET_SCHEMA_OVERVIEW
        df = pd.read_sql(query, conn)

        return df if as_data_frame else df.to_string(index=False)

    except Exception as e:
        tb = traceback.extract_tb(e.__traceback__)
        frame = tb[0]
        raise RuntimeError(
            f"[{os.path.basename(frame.filename)}].[{frame.name}] Error executing query in the database."
        ) from e
