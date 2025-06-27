# Archivo: data/query_templates.py

GET_ORDERS_BY_WEEK = """
    SELECT
        DATEPART(week, o_orderdate) AS week_number,
        COUNT(*) AS order_count,
        SUM(o_totalprice) AS o_totalprice
    FROM orders
    WHERE o_orderdate BETWEEN '{start_date}' AND '{end_date}'
    GROUP BY DATEPART(week, o_orderdate)
    ORDER BY week_number;
"""

GET_CUSTOMERS_ORDERS = """
    SELECT
        o_custkey, c_name, n_name,
        DATEPART(week, o_orderdate) AS week_number,
        COUNT(*) AS order_count,
        SUM(o_totalprice) AS o_totalprice
    FROM orders
    JOIN customer ON o_custkey = c_custkey
    JOIN nation ON c_nationkey = n_nationkey
    WHERE o_orderdate BETWEEN '{start_date}' AND '{end_date}'
    GROUP BY o_custkey, c_name, n_name, DATEPART(week, o_orderdate);
"""

GET_PARTSUPP_ORDERS = """
    SELECT
        l_partkey, l_suppkey, o.o_custkey, SUM(l_quantity) l_quantity, SUM(l_extendedprice) l_extendedprice,
        COUNT(*) AS items_count, DATEPART(month, o_orderdate) AS month
    FROM lineitem JOIN orders o ON l_orderkey = o.o_orderkey
    WHERE o.o_orderdate BETWEEN '{start_date}' AND '{end_date}'
    GROUP BY l_partkey, l_suppkey, o.o_custkey, DATEPART(month, o_orderdate);
"""

GET_YEARS_WITH_ORDERS = """
    SELECT DISTINCT DATEPART(year, o_orderdate) AS year
    FROM orders_feedback (NOLOCK)
    WHERE conversation IS NOT NULL;
"""

GET_CUSTOMERS_WITH_ORDERS = """
    SELECT DISTINCT
        CAST(o_custkey AS VARCHAR(10)) + ' - ' + c_name AS customer_name
    FROM orders_feedback (NOLOCK)
    JOIN customer ON o_custkey = c_custkey
    WHERE conversation IS NOT NULL;
"""

GET_TABLES_INFO_DATA = """
    SELECT
        t.name AS table_name,
        CAST(CAST(SUM(a.total_pages) * 8 / 1024.0 AS DECIMAL(10,2)) AS DECIMAL(10,0)) AS total_size_MB,
        i.rows AS rows_count
    FROM sys.tables t
    JOIN sys.schemas s ON t.schema_id = s.schema_id
    JOIN sys.sysindexes i ON t.object_id = i.id
    JOIN sys.partitions p ON i.id = p.object_id AND i.indid = p.index_id
    JOIN sys.allocation_units a ON p.partition_id = a.container_id
    WHERE i.rows > 100
    GROUP BY t.name, i.rows
    ORDER BY total_size_MB DESC;
"""

GET_SCHEMA_OVERVIEW = """
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
