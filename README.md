# LLM Evaluation Library

A comprehensive Python library for evaluating LLM models' SQL query generation capabilities against baseline datasets.

## Requirements

To run this project, ensure the following dependencies are installed:

### Python Dependencies

- `pandas` - Data manipulation and analysis
- `sqlalchemy` - Database connections and ORM
- `anthropic` - Anthropic Claude API
- `azure-core` - Azure SDK core library
- `tabulate` - Report formatting
- `python-dotenv` - Environment variable management
- `pyodbc` - ODBC driver for SQL Server
- `openai` - OpenAI API client
- `duckdb` - DuckDB database engine

### System Requirements

- **Python Version:** Ensure Python 3.10 or higher is installed.
- **ODBC Driver:** Install ODBC Driver 18 for SQL Server (recommended).
- **SQL Database** used as example tpch database, build your own test!

### Database Sources

The application supports multiple database sources:

1. **SQL Azure Database or SQL Server OnPrem** (`sql-server`)
2. **DuckDB File** (`duckdb`)

#### DuckDB Setup

To use DuckDB with TPCH sample data:

1. Download the TPCH database files from the DuckDB documentation.
https://duckdb.org/docs/stable/core_extensions/tpch.html

1. Run the setup_duckdb.py script to create the baseline results:

```bash
# Run the TPCH queries to populate the baseline files:
python scripts/setup_duckdb.py
```

1. Adjust the relevant parameters in the `.env` file to point to the DuckDB database file:

```bash
# Set environment variable
DUCKDB_PATH="./docs/tpch-sf10.db"
```

### Installation

1. **Clone the Repository:**

   ```bash
   git clone https://github.com/erincon01/llm_eval.git
   cd llm_eval
   ```

2. **Install Python Dependencies:**
   Use Poetry to install dependencies:

   ```bash
   poetry lock
   poetry install
   ```

   Check poetry envirormnent for debugging in vs.code:

   ```bash
   poetry env list
   poetry env info --path
   ```

3. **Install System Dependencies:**
   - Download and install [ODBC Driver 18 for SQL Server](https://learn.microsoft.com/en-us/sql/connect/odbc/download-odbc-driver-for-sql-server) if sql-server is used as data-source [both for SQL Azure and SQL Server].

4. **Set Up Environment Variables:**
   Create a `.env` following the `.env.sample`

## Project Structure

```bash
├── core/                    # Core business logic components
├── data/                    # Data management classes
├── services/                # Service layer for external integrations
├── utils/                   # Utility functions and helpers
└── docs/                    # Configuration and results
```

## Main Entry Point

### `llms_evaluator.py`

Primary orchestrator class that coordinates all evaluation components.

**Constructor Parameters:**

- `questions_file_name` - Path to YAML file with evaluation questions
- `db_schema_file_name` - Path to YAML file with database schema
- `semantic_rules_file_name` - Path to Markdown file with semantic rules
- `system_message_file_name` - Path to Markdown file with system message template
- `models_file_name` - Path to YAML file with model configurations

**Key Methods:**

- `evaluate_models(temperature, results_to_path, file_name_prefix, log_results, log_summary)` - Run full evaluation across all models
- `execute_queries(sql_query_column, summary_file_name, results_to_path, ...)` - Generate baseline datasets
- `load_baseline_datasets(baseline_path)` - Load reference datasets for comparison
- `process_questions_with_model(model, model_config, temperature, max_tokens)` - Process questions with specific model

**Attributes:**

- `all_questions` - Loaded evaluation questions
- `baseline_datasets` - Reference datasets for comparison
- `models`, `models_configs` - Available models and their configurations
- `db_schema` - Database schema information
- `semantic_rules` - Business rules content
- `system_message` - LLM system prompt template

## Core Components

### Services

#### `database_service.py`

Handles database connections and SQL execution.

**Methods:**

- `get_dynamic_sql(source, sql_query, as_data_frame)` - Execute SQL queries on specified database
- `execute_sql_query(sql_query)` - Execute SQL and return results with metadata
- `get_connection(source)` - Get database connection engine
- `decode_source(source)` - Normalize database source names

**Supported Sources:** `sql-server`, `duckdb`

#### `llm_service.py`

Manages LLM interactions for SQL generation.

**Methods:**

- `generate_sql_query(platform, model, question_number, user_prompt, ...)` - Generate SQL from natural language

**Supported Platforms:** `azure_openai`, `anthropic`

### Core Executors

#### `baseline_executor.py`

Executes baseline SQL queries and generates reference datasets.

**Methods:**

- `execute_queries(questions, sql_query_column, summary_file_name, results_to_path, ...)` - Run baseline queries and export results

#### `model_evaluator.py`

Orchestrates evaluation of multiple LLM models.

**Methods:**

- `evaluate_models(models, models_configs, all_questions, baseline_datasets, ...)` - Evaluate multiple models against baseline

#### `question_processor.py`

Processes individual questions with LLM models and compares results.

**Methods:**

- `process_questions_with_model(questions, baseline_datasets, model, ...)` - Process questions with specific model and compare results

### Data Management

#### `questions.py`

Manages question datasets and YAML serialization.

**Methods:**

- `load_questions()` - Load questions from YAML file
- `add_question(question)` - Add new question to dataset
- `get_all_questions()` - Retrieve all questions
- `save_questions(yaml_file)` - Save questions to YAML
- `find_question(keyword)` - Search questions by keyword

**Attributes:**

- `yaml_file` - Path to YAML file
- `questions` - List of question dictionaries

#### `questions_loader.py`

Utility for loading questions from files.

**Methods:**

- `load_questions_from_file(questions_file_name)` - Static method to load questions

#### `models_config.py`

Handles model configuration loading from YAML.

**Methods:**

- `load_models_from_yaml()` - Load enabled models and configurations
- `get_models_configs()` - Return loaded model configurations
- `get_models()` - Return flat list of enabled models
- `get_model_config_by_id(model_id)` - Get configuration by provider ID

**Attributes:**

- `yaml_path` - Path to models configuration YAML
- `models_configs` - List of provider configurations
- `models` - Flat list of enabled models

### Schema Management

#### `schema.py` (python_modules)

Database schema management from YAML configuration.

**Methods:**

- `load_schema()` - Load database schema from YAML file
- `get_table_names()` - Return list of all table names
- `get_table_script(table_name)` - Return script for specific table
- `get_all_tables_scripts()` - Return all table scripts
- `add_table(table_name, script)` - Add new table to schema
- `save_schema()` - Save schema back to YAML file

**Attributes:**

- `yaml_file` - Path to schema YAML file
- `tables` - List of table definitions

### Utilities

#### `data_utils.py`

Data comparison and baseline loading utilities.

**Methods:**

- `compare_dataframes(baseline_df, llm_df, question_number)` - Compare baseline vs LLM results
- `load_baseline_datasets(baseline_path)` - Load baseline CSV files from directory

**Returns:** Equality percentages for rows, columns, and coverage metrics

#### `dataframe_utils.py`

DataFrame normalization and alignment utilities.

**Methods:**

- `normalize_numeric_columns(df1, df2)` - Normalize numeric precision across DataFrames
- `align_columns_by_first_row(df1, df2)` - Align column order based on first row values

#### `file_utils.py`

File operations utilities.

**Methods:**

- `load_file(filename)` - Load file content as string
- `remove_baseline_datasets(results_to_path)` - Remove baseline CSV files

#### `llm_utils.py`

Low-level LLM API interactions.

**Methods:**

- `get_chat_completion_from_platform(platform, model, system_message, user_prompt, ...)` - Get chat completion from various platforms

#### `sql_utils.py`

SQL query processing utilities.

**Methods:**

- `remove_quotations(sql_query)` - Extract SQL from markdown code blocks

#### `reporting_utils.py`

Performance reporting and analysis.

**Methods:**

- `performance_report(results_path, file_name_prefix)` - Generate comprehensive performance reports
- `_generate_model_performance_report(all_data)` - Model-specific performance metrics
- `_generate_query_performance_report(all_data)` - Query-specific performance metrics
- `_generate_ranking_reports(all_data)` - Ranking reports by different metrics
- `_generate_combined_ranking(agg)` - Combined ranking by quality, time, and price

## Usage Example

### `main_evaluation.py`

Complete evaluation workflow example:

```python

from llms_evaluator import LLMsEvaluator
from utils.reporting_utils import performance_report

# Initialize evaluator
evaluator = LLMsEvaluator(
    questions_file_name="./docs/01-questions-sql-server.yaml",
    db_schema_file_name="./docs/02-database_schema.yaml", 
    semantic_rules_file_name="./docs/03-semantic_rules-sql-server.md",
    system_message_file_name="./docs/04-system_message-sql-server.md",
    models_file_name="./docs/05-models.yaml",
    data_source="sql-server"  # or "duckdb"
)

# Step 1: Generate baseline datasets
evaluator.execute_queries(
    sql_query_column="sql_query",
    summary_file_name="questions_baseline_summary.csv",
    results_to_path="./docs/results/baseline_dataset-sql-server",
    persist_results=True,
    drop_results_if_exists=True
)

# Step 2: Load baseline for comparison
evaluator.load_baseline_datasets("./docs/results/baseline_dataset-sql-server")

# Step 3: Run evaluation iterations
for i in range(number_of_iterations):
    i_str = str(i + 1).zfill(2)
    evaluator.evaluate_models(
        temperature=0.9,
        results_to_path="./docs/results",
        file_name_prefix=f"results_llm_{i:02d}",
        log_results=True,
        log_summary=True,
        iteration=i_str,
    )

# Step 4: Generate performance reports
performance_report(
    results_path="./docs/results",
    file_name_prefix="questions_summary_results_llm"
)
```

## Configuration Files

### Questions Format (`01-questions.yaml`)

```yaml
questions:
  - question_number: 1
    user_question: |
      Which customers from the 'BUILDING' market segment placed more than 10 orders in 1996? Order by total order value descending.
    sql_query: |
      SELECT ...
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
      xxxx
    sql_query: |
      xxxx
    tables_used:
      - xxxx
      - yyyy
  - question_number: n
```

### Database Schema (`02-database_schema.yaml`)

```yaml
tables:
  - name: "region"
    script: |
      create table region (
          r_regionkey integer not null,
          r_name char(25) not null,
          r_comment varchar(152),
          primary key (r_regionkey)
      );
  - name: xxxx
    script: |
      xxxx
  - name: yyyyy
    script: |
      xxxxxxx
```

### Semantic Rules (`03-semantic_rules.md`)

```markdown
# Semantic Rules for SQL Queries
## Semantic Rules
- Ensure all SQL queries are syntactically correct and executable.
- Use appropriate JOINs to connect tables based on foreign key relationships.
- Filter results using WHERE clauses to match user questions.
```

### System Message Template (`04-system_message.md`)

```markdown
# System Message Template for LLMs
You are an expert SQL query generator. Given a user question, generate a valid SQL query that
retrieves the requested data from the specified database schema. Ensure the query is optimized for performance and adheres to the semantic rules provided.
```

### Models Configuration (`05-models.yaml`)

```yaml
models_configs:
  - id: "azure_openai"
    enabled: true | false
    models:
      - name: "gpt-4o"
        enabled: true | false
        cost_input_tokens_EUR_1K: 0.005
        cost_output_tokens_EUR_1K: 0.015
```

## Environment Variables

See the `.env.sample` file for a complete list of environment variables.

## Evaluation Workflow

1. **Initialize:** Create `LLMsEvaluator` instance with configuration files
2. **Generate Baseline:** Execute ground truth SQL queries to create reference datasets
3. **Load Baseline:** Load reference datasets for comparison
4. **Evaluate Models:** Run evaluation iterations across configured LLM models
5. **Analyze Results:** Generate performance reports and rankings
6. **Consolidate:** Merge results across experiments (optional)

## Metrics Generated

- **Accuracy Metrics:** Row/column equality percentages, coverage ratios
- **Performance Metrics:** SQL execution time, LLM response time
- **Cost Metrics:** Token usage and EUR costs per model
- **Quality Metrics:** Data completeness and correctness ratios

## Dependencies

See the files: `requirements.txt` and `pyproject.toml`

## Output Files

- **Baseline:** Tab-separated CSV files per question (`question_01.csv`, etc.)
- **Results:** YAML files with detailed evaluation results per model
- **Summary:** CSV files with aggregated metrics across all evaluations
- **Reports:** Formatted performance and ranking reports
  