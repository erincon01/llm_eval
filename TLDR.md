# TLDR: Evaluating LLMs for Custom Business Questions

Ranking of the models based on the total cost, LLM time and source rows equality.
This is a sample result with real questions and models running on a SQL Server database.
Price values are in EUR per 1K tokens, as of June 2025.

| model                                  | rank_quality   | rank_time   | rank_price   |
|:---------------------------------------|:---------------|:------------|:-------------|
| gpt-4o                                 | 1 (0.9)        | 6 (2.62)    |              |
| gpt-4.1                                | 2 (0.85)       | 1 (1.84)    |              |
| grok-3                                 | 2 (0.85)       | 7 (3.08)    |              |
| gpt-4.1-mini                           | 4 (0.8)        | 2 (2.1)     | 6 (0.00102)  |
| grok-3-mini                            | 4 (0.8)        |             | 5 (0.000662) |
| claude-3-5-sonnet-20241022             | 6 (0.78)       |             |              |
| DeepSeek-V3-0324                       | 7 (0.77)       |             |              |
| claude-sonnet-4-20250514               | 8 (0.75)       |             |              |
| Llama-4-Maverick-17B-128E-Instruct-FP8 |                | 3 (2.16)    | 2 (0.000321) |
| gpt-4o-mini                            |                | 3 (2.16)    | 3 (0.000374) |
| Llama-4-Scout-17B-16E-Instruct         |                | 5 (2.59)    | 4 (0.000517) |
| claude-3-5-haiku-20241022              |                | 8 (4.04)    | 8 (0.00278)  |
| Phi-3-medium-128k-instruct             |                |             | 1 (0.000229) |
| Mistral-Large-2411                     |                |             | 7 (0.001875) |
| Llama-3.3-70B-Instruct                 |                |             |              |
| claude-3-7-sonnet-20250219             |                |             |              |

## Introduction

This guide describes the process for evaluating the ability of various Large Language Models (LLMs) to answer custom business questions over your database using automated, reproducible workflows. By providing your own questions, database schema, and precise SQL and semantic rules, you can benchmark and compare LLMs in terms of code generation quality, compliance with standards, and operational costs.

The procedure involves defining your input files (questions, schema, rules, and model configurations), and then running an evaluation script that systematically tests each model under identical conditions. The goal is to help you identify which LLMs are best suited to your data and requirements, streamlining the selection process for real-world analytic tasks.

No prior results are necessary; simply follow the steps to execute the evaluation with your custom inputs.

## Example: Evaluating a Business Question

### Step 1 - Define your user question

```yaml
questions:
  - question_number: 1
    user_question: |
      Which customers from the 'BUILDING' market segment placed more than 10 orders in 1996? Order by total order value descending.
    sql_query: |
      SELECT
          c.c_custkey AS customer_id,
          c.c_name    AS customer_name,
          COUNT(o.o_orderkey) AS num_orders,
          SUM(o.o_totalprice) AS total_amount
      FROM customer c
      JOIN orders o ON c.c_custkey = o.o_custkey
      WHERE c.c_mktsegment = 'BUILDING'
        AND YEAR(o.o_orderdate) = 1996
      GROUP BY c.c_custkey, c.c_name
      HAVING COUNT(o.o_orderkey) > 10
      ORDER BY total_amount DESC;
    tables_used:
      - "customer"
      - "orders"
```

### Step 2 - Set your database schema

```yaml
tables:
  - name: "customer"
    script: |
      create table customer (
          c_custkey integer not null,
          c_name varchar(25) not null,
          c_mktsegment varchar(10),
          primary key (c_custkey)
      );

  - name: "orders"
    script: |
      create table orders (
          o_orderkey integer not null,
          o_custkey integer not null,
          o_orderdate date not null,
          o_totalprice decimal(15,2),
          primary key (o_orderkey),
          foreign key (o_custkey) references customer(c_custkey)
      );
```

### Step 3 - Run the evaluation script

```bash
python ./src/main_evaluation.py ^
    --questions_file_name ./docs/01-questions-sql-server.yaml ^
    --db_schema_file_name ./docs/02-database_schema.yaml ^
    --semantic_rules_file_name ./docs/03-semantic-rules-sql-server.md ^
    --system_message_file_name ./docs/04-system_message-sql-server.md ^
    --models_file_name ./docs/05-models.yaml ^
    --iterations 1 ^
    --get_baseline_from_data_source ^
    --data_source_name "sql-server"
```

### Step 4 - Review the results

Results are printed to the console and saved in a structured format, allowing you to compare the performance of different models based on criteria such as code quality, execution time, and cost efficiency.

See files:

- `./docs/results/performance_report-sql-server.txt` where summarize by:
  - performance report per model.
  - performance report per model.
  - Best models based on average LLM time.
  - Best models based on mean token cost.
  - Best models based on average datasets equality.
  - Ranking of the models based on the total cost, LLM time and source rows equality.

- `./docs/results/performance_report-sql-server.csv`
  - CSV file with metrics for each model aggregated.

- `./docs/results/results_llm_01_sql-server_claude-3-5-sonnet-20241022_20250629_1912.yaml`
- `./docs/results/results_llm_01_sql-server_gpt-4o_20250629_1912.yaml`
- `./docs/results/results_llm_01_sql-server_gpt-4.1_20250629_1912.yaml`
  - YAML file with detailed results for each model, query, and several metrics.
  