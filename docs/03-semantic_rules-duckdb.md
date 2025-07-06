# SEMANTIC RULES FOR USER QUESTIONS

## MAP COLUMNS
customer → customer_id(c_custkey), customer_name(c_name)
supplier → supplier_id(s_suppkey), supplier_name(s_name)
part     → part_id(p_partkey), part_name(p_name)
region   → region_id(r_regionkey), region_name(r_name)
nation   → nation_id(n_nationkey), nation_name(n_name)
time     → order_year, order_quarter, order_month
metrics  → num_orders, total_amount, total_quantity, total_cost,
           avg_cost, avg_price, price_stddev,
           pct_of_total, yoy_percent_change, delta_vs_prev_q

## ENTITIES ORDER
1) Entity_blocks (customer→supplier→part→region→nation), each **id then name**
2) Time (year→quarter→month)  
3) Metrics

## NATURAL LANGUAGE SEMANTIC RULES

|    Natural Language Term                   | Expected Meaning                                | Inferred SQL Formula or Field                                          |
|--------------------------------------------|-------------------------------------------------|------------------------------------------------------------------------|
| total supply cost                          | cost to provide the available quantity          | `ps.ps_supplycost * ps.ps_availqty`                                    |
| total revenue                              | income from sales (with discount)               | `SUM(l.l_extendedprice * (1 - l.l_discount))`                          |
| total amount / order value                 | total price of orders                           | `SUM(o.o_totalprice)` or `o.o_totalprice`                              |
| total quantity ordered                     | number of items ordered                         | `SUM(l.l_quantity)`                                                    |
| number of orders                           | count of orders placed                          | `COUNT(o.o_orderkey)` or `COUNT(*)`                                    |
| average supplier account balance           | financial standing of suppliers                 | `AVG(s.s_acctbal)`                                                     |
| number of suppliers                        | distinct supplier count                         | `COUNT(DISTINCT s.s_suppkey)`                                          |
| number of customers                        | distinct customer count                         | `COUNT(DISTINCT c.c_custkey)`                                          |
| total spend / customer spend               | money spent by a customer                       | `SUM(o.o_totalprice)`                                                  |
| total sales / sales per region/period      | sum of order value                              | `SUM(o.o_totalprice)`                                                  |
| YOY (year-over-year) growth                | relative increase vs previous year              | `(current - previous) / NULLIF(previous, 0)`                           |
| quarter-over-quarter delta                 | absolute difference vs previous quarter         | `current - previous` using `LAG(...) OVER (...)`                       |
| percentage of total (e.g., market share)   | share of a subgroup vs. total                   | `100.0 * sub_total / SUM(...) OVER (...)`                              |
| price variability                          | deviation in order prices                       | `STDEV(o.o_totalprice)`                                                |
| average order price                        | average order total                             | `AVG(o.o_totalprice)`                                                  |
| most ordered part / product                | highest quantity sold                           | `SUM(l.l_quantity)` with `ORDER BY total_quantity DESC`                |
| top X suppliers / customers                | ranking based on metric                         | use `ROW_NUMBER()` or `DENSE_RANK()` with `ORDER BY metric DESC`       |


## CODING RULES  
• Include **id + name** for every entity mentioned; drop whole blocks else.  
• columns order: Entity_blocks, Time, Metrics
• Preserve column order exactly.  
• Use snake_case aliases; SQL keywords UPPER.  
• `GROUP BY` every non-aggregated canonical column.  
• Map: `COUNT(*)`→num_orders, `SUM(o_totalprice)`→total_amount.  
• New metrics: alias + append after existing ones.  
• Ensure the query runs without alias/group errors.

## DUCKDB SQL RULES
• The coding language is DuckDB SQL, which follows PostgreSQL-style syntax
• Use `LIMIT` for limiting results (not TOP). Use `OFFSET` with `LIMIT` for pagination.
• Use `OVER` clauses for window functions and running totals.
• DuckDB supports advanced analytics functions like `PERCENTILE_CONT`, `MEDIAN`, `MODE`.
• Use `UNNEST` to expand arrays and lists instead of CROSS APPLY.
• Avoid using `SELECT *`; be explicit with columns.
• Use `CTEs` for recursive logic and query modularization.
• Use conditional aggregations with `CASE` for pivot-like transformations instead of PIVOT/UNPIVOT.
• Use `PARTITION BY` with `OVER` for grouped window functions.
• Prefer `NOT EXISTS` over `NOT IN` for NULL-safe anti-joins.
• Avoid unnecessary DISTINCT — verify the root cause of duplication.
• Prefer `INNER JOIN` over `WHERE` for join conditions.
• Use `EXISTS` for checking presence efficiently.
• Combine conditions with `CASE` for conditional aggregations.
• Use `LIMIT` and `OFFSET` for efficient pagination.
• Use table aliases for readability, especially in joins.
• Filter using `HAVING` only for aggregated conditions.
• DuckDB supports `EXTRACT(year FROM date)` and date functions like `date_part()`.
• Use `||` for string concatenation (not `+`).
• DuckDB has built-in support for JSON, arrays, and struct data types.
• Use `QUALIFY` clause for filtering window function results directly.
• DuckDB supports `USING` clause in joins for natural join syntax.
• Use `ILIKE` for case-insensitive pattern matching.
• DuckDB supports `GREATEST()` and `LEAST()` functions for comparisons.
• For pivot operations, use conditional aggregations: `SUM(CASE WHEN condition THEN value END)`.
• Use `STRUCT` and `LIST` for complex data types and nested operations.

## EXAMPLE

```sql
SELECT
    c.c_custkey AS customer_id,
    c.c_name    AS customer_name,
    COUNT(*)    AS num_orders,
    SUM(o.o_totalprice) AS total_amount
FROM customer c
INNER JOIN orders o ON o.o_custkey = c.c_custkey
WHERE c.c_mktsegment = 'BUILDING'
  AND o.o_orderdate BETWEEN DATE '1996-01-01' AND DATE '1996-12-31'
  AND o.o_orderstatus = 'F'
  AND o.o_orderpriority IN ('1-URGENT', '2-HIGH')
GROUP BY c.c_custkey, c.c_name
HAVING COUNT(*) > 10
ORDER BY total_amount DESC
LIMIT 10;
```
