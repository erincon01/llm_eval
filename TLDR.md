
# TLDR: Evaluating LLMs for Custom Business Questions

Ranking of the models based on the total cost, LLM time and source rows equality:

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

## 1 - Define your user questions to measure in natural language

````yaml
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

  - question_number: 2
    user_question: |
    sql_query: |
    tables_used:

  - question_number: n

````

## 2 - Set your database schema

````yaml
tables:
  - name: "region"
    script: |
      create table region (
          r_regionkey integer not null,
          r_name char(25) not null,
          r_comment varchar(152),
          primary key (r_regionkey)
      );

  - name: "nation"
    script: |
      create table nation (
          n_nationkey integer not null,
          n_name char(25) not null,
          n_regionkey integer not null,
          n_comment varchar(152),
          primary key (n_nationkey)
      );
````

## 3 - Set your semantic rules

````markdown
## CODING RULES  
• Include **id + name** for every entity mentioned; drop whole blocks else.  
• columns order: Entity_blocks, Time, Metrics
• Preserve column order exactly.  
• Use snake_case aliases; SQL keywords UPPER.  
• `GROUP BY` every non-aggregated canonical column.  
• Map: `COUNT(*)`→num_orders, `SUM(o_totalprice)`→total_amount.  
• New metrics: alias + append after existing ones.  
• Ensure the query runs without alias/group errors.

## TRANSACT-SQL RULES
• The coding language is Transact-SQL, TSQL, from Microsoft SQL Server
• This is Transact-SQL. Do not use LIMIT. Use TOP or OFFSET-FETCH instead to limit results.
• Use `OVER` clauses for running totals instead of self-joins.
• Use `CROSS APPLY` to unpivot inline calculations.
• Avoid using `SELECT *`; be explicit with columns.
````

## 4 - Select your LLM models to evaluate

```yaml
models_configs:
  - id: MSDN_CORP
    enabled: true
    models:
      - name: DeepSeek-V3-0324
        cost_input_tokens_EUR_1K:  0.00114
        cost_output_tokens_EUR_1K: 0.00456
      - name: gpt-4o
        cost_input_tokens_EUR_1K:  0.00250
        cost_output_tokens_EUR_1K: 0.01000
      - name: gpt-4o-mini
        cost_input_tokens_EUR_1K:  0.00015
        cost_output_tokens_EUR_1K: 0.00060
      - name: grok-3
        cost_input_tokens_EUR_1K:  0.00300
        cost_output_tokens_EUR_1K: 0.01500
      - name: grok-3-mini
        cost_input_tokens_EUR_1K:  0.00025
        cost_output_tokens_EUR_1K: 0.00127
```

## 5 - Run the evaluation script

```bash
python ./src/main_evaluation.py ^
    --questions_file_name ./docs/01-questions.yaml ^
    --db_schema_file_name ./docs/02-database_schema.yaml ^
    --semantic_rules_file_name ./docs/03-semantic-rules.md ^
    --system_message_file_name ./docs/04-system_message.md ^
    --models_file_name ./docs/05-models.yaml ^
    --iterations 1 ^
    --get_baseline_from_data_source
```
