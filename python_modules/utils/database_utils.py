import os
import traceback

import pandas as pd
from services.database_service import DatabaseService
from sqlalchemy import text


def get_database_schema(source: str, as_data_frame: bool = False):
    """
    Retrieves the database schema.

    Args:
        source (str): The source of the database. Either "azure-sql", or "onprem-sql".
        as_data_frame (bool): If True, the result is returned as a pandas DataFrame.
    Returns:
        str or pd.DataFrame: The schema as a string or DataFrame.
    Raises:
        RuntimeError: If there is an error connecting to or executing the query in the database.
    """
    try:
        db_service = DatabaseService()
        conn = db_service.get_connection(source)

        if source in ["azure-sql", "onprem-sql"]:
            query = """
                SELECT
                    t.TABLE_NAME AS table_name,
                    STRING_AGG('| ' + c.COLUMN_NAME + ' ' + c.DATA_TYPE + ' |', ', ') AS columns_with_types
                FROM
                    INFORMATION_SCHEMA.TABLES t
                JOIN
                    INFORMATION_SCHEMA.COLUMNS c
                ON
                    t.TABLE_NAME = c.TABLE_NAME
                GROUP BY
                    t.TABLE_NAME
                ORDER BY
                    t.TABLE_NAME;
            """

        df = pd.read_sql(query, conn)

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


def execute_stored_procedure(source: str, procedure_sql: str, as_data_frame: bool = False):
    """
    Executes a stored procedure on the specified database source.

    Args:
        source (str): The source of the database. Either "azure-sql", or "onprem-sql".
        procedure_sql (str): The complete SQL command to execute, including EXEC and parameters.
        as_data_frame (bool): If True, the result is returned as a pandas DataFrame.

    Returns:
        str or pd.DataFrame: The result of the stored procedure execution as a string or DataFrame.

    Raises:
        RuntimeError: If there is an error connecting to or executing the procedure in the database.
    """
    try:
        db_service = DatabaseService()
        conn = db_service.get_connection(source)

        with conn.connect() as connection:
            result = connection.execute(text(procedure_sql))
            rows = result.fetchall()
            columns = result.keys()

        # Return results as DataFrame or formatted string
        if as_data_frame:
            return pd.DataFrame(rows, columns=columns)
        else:
            return pd.DataFrame(rows, columns=columns).to_string(index=False)

    except Exception as e:
        tb = traceback.extract_tb(e.__traceback__)
        frame = tb[0]
        method_name = frame.name
        line_number = frame.lineno
        file_name = os.path.basename(frame.filename)
        raise RuntimeError(
            f"[{file_name}].[{method_name}].[line-{line_number}] Error executing stored procedure. {e}"
        ) from e


def get_table_data(source: str, table_name: str, top_rows: str = "", as_data_frame: bool = False):
    """
    Retrieves tables data from the database.

    Args:
        source (str): The source of the database. Either "azure-sql", or "onprem-sql".
        table_name (str): Name of the table to query.
        top_rows (str): TOP clause for limiting rows.
        as_data_frame (bool): If True, the result is returned as a pandas DataFrame.
    Returns:
        tuple: (columns_info, table_data) as strings or DataFrames.
    Raises:
        RuntimeError: If there is an error connecting to or executing the query in the database.
    """
    try:
        db_service = DatabaseService()
        conn = db_service.get_connection(source)

        if source in ["azure-sql", "onprem-sql"]:
            # Get table data
            query = f"""
                SELECT {top_rows} *
                FROM {table_name} order by 1;
            """
            df = pd.read_sql(query, conn)

            # Get column names
            query = f"""
                select sc.name name from sys.columns sc
                join sys.tables t on sc.object_id = t.object_id
                where t.name = '{table_name}';
            """
            dfc = pd.read_sql(query, conn)

        if as_data_frame:
            return dfc, df
        else:
            result1 = df.to_string(index=False)
            resultc = dfc.to_string(index=False)
            return resultc, result1

    except Exception as e:
        tb = traceback.extract_tb(e.__traceback__)
        frame = tb[0]
        method_name = frame.name
        file_name = os.path.basename(frame.filename)
        raise RuntimeError(
            f"[{file_name}].[{method_name}] Error connecting or executing the query in the database."
        ) from e


def get_orders(source: str, year: str):
    """Get orders data grouped by week for a specific year."""
    try:
        db_service = DatabaseService()
        conn = db_service.get_connection(source)

        query = f"""
            SELECT
                DATEPART(week, o_orderdate) AS week_number,
                COUNT(*) AS order_count,
                SUM(o_totalprice) AS o_totalprice
            FROM orders
            WHERE o_orderdate between '{year}-01-01' and '{year}-12-31'
            GROUP BY DATEPART(week, o_orderdate)
            ORDER BY week_number;
        """

        df = pd.read_sql(query, conn)
        return df, query

    except Exception as e:
        tb = traceback.extract_tb(e.__traceback__)
        frame = tb[0]
        method_name = frame.name
        file_name = os.path.basename(frame.filename)
        raise RuntimeError(
            f"[{file_name}].[{method_name}] Error connecting or executing the query in the database."
        ) from e


def get_customers_orders(source: str, year: str):
    """Get customer orders data grouped by week for a specific year."""
    try:
        db_service = DatabaseService()
        conn = db_service.get_connection(source)

        query = f"""
            SELECT
                o_custkey, c_name, n_name,
                DATEPART(week, o_orderdate) AS week_number,
                COUNT(*) AS order_count,
                SUM(o_totalprice) AS o_totalprice
            FROM orders
            JOIN customer ON o_custkey = c_custkey
            JOIN nation ON c_nationkey = n_nationkey
            WHERE o_orderdate between '{year}-01-01' and '{year}-12-31'
            GROUP BY o_custkey, c_name, n_name, DATEPART(week, o_orderdate);
        """

        df = pd.read_sql(query, conn)
        return df, query

    except Exception as e:
        tb = traceback.extract_tb(e.__traceback__)
        frame = tb[0]
        method_name = frame.name
        file_name = os.path.basename(frame.filename)
        raise RuntimeError(
            f"[{file_name}].[{method_name}] Error connecting or executing the query in the database."
        ) from e


def get_partsupp_orders(source: str, year: str):
    """Get part supplier orders data for a specific year."""
    try:
        db_service = DatabaseService()
        conn = db_service.get_connection(source)

        query = f"""
            SELECT
                l_partkey, l_suppkey, o.o_custkey, SUM(l_quantity) l_quantity, SUM(l_extendedprice) l_extendedprice,
                COUNT(*) AS items_count, DATEPART(month, o_orderdate) AS month
            FROM lineitem join orders o on l_orderkey = o.o_orderkey
            WHERE o.o_orderdate between '{year}-01-01' and '{year}-12-31'
            GROUP BY l_partkey, l_suppkey, o.o_custkey, DATEPART(month, o_orderdate);
        """

        df = pd.read_sql(query, conn)
        return df, query

    except Exception as e:
        tb = traceback.extract_tb(e.__traceback__)
        frame = tb[0]
        method_name = frame.name
        file_name = os.path.basename(frame.filename)
        raise RuntimeError(
            f"[{file_name}].[{method_name}] Error connecting or executing the query in the database."
        ) from e


def get_nations_orders(source: str):
    """Get nations orders data grouped by year."""
    try:
        db_service = DatabaseService()
        conn = db_service.get_connection(source)

        query = """
            SELECT
                n_name,
                DATEPART(year, o_orderdate) AS year,
                COUNT(*) AS order_count,
                SUM(o_totalprice) AS o_totalprice
            FROM orders
            JOIN customer ON o_custkey = c_custkey
            JOIN nation ON c_nationkey = n_nationkey
            GROUP BY n_name, DATEPART(year, o_orderdate);
        """

        df = pd.read_sql(query, conn)
        return df, query

    except Exception as e:
        tb = traceback.extract_tb(e.__traceback__)
        frame = tb[0]
        method_name = frame.name
        file_name = os.path.basename(frame.filename)
        raise RuntimeError(
            f"[{file_name}].[{method_name}] Error connecting or executing the query in the database."
        ) from e


def get_years_with_orders(source: str, as_data_frame: bool = False):
    """Get distinct years from orders_feedback table."""
    try:
        db_service = DatabaseService()
        conn = db_service.get_connection(source)

        query = """
            SELECT
                DISTINCT
                DATEPART(year, o_orderdate) AS year
            FROM orders_feedback (nolock)
            WHERE conversation is not null;
        """

        df = pd.read_sql(query, conn)

        if as_data_frame:
            return df
        else:
            return df.to_string(index=False)

    except Exception as e:
        tb = traceback.extract_tb(e.__traceback__)
        frame = tb[0]
        method_name = frame.name
        file_name = os.path.basename(frame.filename)
        raise RuntimeError(
            f"[{file_name}].[{method_name}] Error connecting or executing the query in the database."
        ) from e


def get_customers_with_orders(source: str, as_data_frame: bool = False):
    """Get customers with orders from orders_feedback table."""
    try:
        db_service = DatabaseService()
        conn = db_service.get_connection(source)

        query = """
            SELECT
                DISTINCT
                cast(o_custkey as varchar(10)) + ' - ' + c_name AS customer_name
            FROM orders_feedback (nolock)
            JOIN customer on o_custkey = c_custkey
            WHERE conversation is not null;
        """

        df = pd.read_sql(query, conn)

        if as_data_frame:
            return df
        else:
            return df.to_string(index=False)

    except Exception as e:
        tb = traceback.extract_tb(e.__traceback__)
        frame = tb[0]
        method_name = frame.name
        file_name = os.path.basename(frame.filename)
        raise RuntimeError(
            f"[{file_name}].[{method_name}] Error connecting or executing the query in the database."
        ) from e


def get_partsupp_orders_agg(
    source: str, selected_year: str, selected_customer: int, having: int, as_data_frame: bool = False
):
    """Get aggregated part supplier orders data."""
    try:
        db_service = DatabaseService()
        conn = db_service.get_connection(source)

        query = f"""
            SELECT
                p_name,
                sum(o_totalprice) as total_price,
                COUNT(distinct o_orderkey) as order_count, p_type, l_partkey, l_suppkey
            FROM orders_feedback (NOLOCK)
            JOIN lineitem l ON l_orderkey = o_orderkey
            JOIN part p ON p_partkey = l_partkey
            WHERE o_orderdate between '{selected_year}-01-01' and '{selected_year}-12-31'
            AND o_custkey = {selected_customer}
            AND conversation is not null
            GROUP BY l_partkey, l_suppkey, p_name, p_type
            HAVING COUNT(distinct o_orderkey) >= {having}
            ORDER BY order_count DESC;
        """

        df = pd.read_sql(query, conn)

        if as_data_frame:
            return df, query
        else:
            result = df.to_string(index=False)
            return result, query

    except Exception as e:
        tb = traceback.extract_tb(e.__traceback__)
        frame = tb[0]
        method_name = frame.name
        file_name = os.path.basename(frame.filename)
        raise RuntimeError(
            f"[{file_name}].[{method_name}] Error connecting or executing the query in the database."
        ) from e


def get_feedback_from_partsupp(
    source: str,
    selected_year: str,
    selected_customer: int,
    part_key: str,
    top_n: str,
    satisfaction_type: str,
    as_data_frame: bool = False,
):
    """Get feedback data from part supplier orders."""
    try:
        db_service = DatabaseService()
        conn = db_service.get_connection(source)

        partkey_filter = ""
        if part_key != "[ALL]":
            partkey_filter = f"WHERE l_partkey = {part_key}"

        query = f"""
            WITH cte AS (
                SELECT
                    o.product_details_json, o.o_totalprice, ofp.*, o.conversation
                FROM orders_feedback o
                JOIN orders_feedback_precomputed ofp
                ON o.o_orderkey = ofp.o_orderkey
                WHERE o.o_orderdate between '{selected_year}-01-01' and '{selected_year}-12-31'
                AND o.o_custkey = {selected_customer}
            )
            SELECT {top_n}
                cte.o_orderkey, cte.o_orderdate, cte.{satisfaction_type} as satisfaction, cte.conversation, j.*
            FROM cte
            CROSS APPLY OPENJSON(product_details_json)
            WITH (
                l_partkey INT '$.l_partkey',
                l_suppkey INT '$.l_suppkey',
                p_name varchar(100) '$.p_name',
                p_type varchar(100) '$.p_type'
            ) AS j
            {partkey_filter}
            order by satisfaction ASC;
        """

        df = pd.read_sql(query, conn)

        if as_data_frame:
            return df, query
        else:
            result = df.to_string(index=False)
            return result, query

    except Exception as e:
        tb = traceback.extract_tb(e.__traceback__)
        frame = tb[0]
        method_name = frame.name
        file_name = os.path.basename(frame.filename)
        raise RuntimeError(
            f"[{file_name}].[{method_name}] Error connecting or executing the query in the database."
        ) from e


def get_tables_info_data(source: str, as_data_frame: bool = False):
    """
    Retrieves tables information from the database.

    Args:
        source (str): The source of the database. Either "azure-sql", or "onprem-sql".
        as_data_frame (bool): If True, the result is returned as a pandas DataFrame.
    Returns:
        str or pd.DataFrame: The table info as a string or DataFrame.
    Raises:
        RuntimeError: If there is an error connecting to or executing the query in the database.
    """
    try:
        db_service = DatabaseService()
        conn = db_service.get_connection(source)

        if source in ["azure-sql", "onprem-sql"]:
            query = """
                SELECT
                    t.name AS table_name,
                    CAST(CAST(SUM(a.total_pages) * 8 / 1024.0 AS DECIMAL(10,2)) AS DECIMAL(10,0)) AS total_size_MB,
                    i.rows as rows_count
                FROM sys.tables t
                JOIN sys.schemas s ON t.schema_id = s.schema_id
                JOIN sys.sysindexes i ON t.object_id = i.id
                JOIN sys.partitions p ON i.id = p.object_id AND i.indid = p.index_id
                JOIN sys.allocation_units a ON p.partition_id = a.container_id
                WHERE i.rows > 100
                GROUP BY
                    t.name, i.rows
                ORDER BY
                    total_size_MB DESC;
            """

        df = pd.read_sql(query, conn)

        if as_data_frame:
            return df
        else:
            return df.to_string(index=False)

    except Exception as e:
        tb = traceback.extract_tb(e.__traceback__)
        frame = tb[0]
        method_name = frame.name
        file_name = os.path.basename(frame.filename)
        raise RuntimeError(
            f"[{file_name}].[{method_name}] Error connecting or executing the query in the database."
        ) from e
