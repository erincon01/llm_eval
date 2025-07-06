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
3. **DuckDB File** (`duckdb`)

#### DuckDB Setup

To use DuckDB with TPCH sample data:

```bash
# Set up TPCH sample data
python scripts/setup_duckdb.py

# Set environment variable
DUCKDB_PATH="./docs/tpch-sf10.db"
```

To download preloaded TPCH databases for duckdb:
https://duckdb.org/docs/stable/core_extensions/tpch.html


```bash

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
   - Download and install [ODBC Driver 18 for SQL Server](https://learn.microsoft.com/en-us/sql/connect/odbc/download-odbc-driver-for-sql-server).

4. **Set Up Environment Variables:**
   Create a `.env` following the `.env.sample`
   

## Project Structure

```
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

**Supported Platforms:** `azure_openai`, `anthropic`, `deepseek`

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

### Templates

#### `query_templates.py`
Predefined SQL query templates for common operations.

**Constants:**
- `GET_ORDERS_BY_WEEK` - Weekly orders aggregation
- `GET_CUSTOMERS_ORDERS` - Customer orders by week
- `GET_PARTSUPP_ORDERS` - Part supplier orders by month
- `GET_YEARS_WITH_ORDERS` - Years with order data
- `GET_CUSTOMERS_WITH_ORDERS` - Customers with orders
- `GET_TABLES_INFO_DATA` - Database table information
- `GET_SCHEMA_OVERVIEW` - Database schema overview

## Legacy Modules (python_modules)

The `python_modules` directory contains legacy implementations being refactored:

#### `module_data.py`
Legacy database utility functions (use `database_utils.py` instead).

#### `module_llm.py`
Legacy LLM interaction functions (use `llm_utils.py` instead).

#### `module_utils.py`
Legacy utility functions (use specific utility modules instead).

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

## Usage Examples

### Using SQL Server Database (Default)
```bash
python ./src/main_evaluation.py \
    --questions_file_name ./docs/01-questions.yaml \
    --database_source sql-server \
    --get_baseline_from_data_source \
    --iterations 1
```

### Using DuckDB with TPCH Data
```bash
# First, set up DuckDB with sample data
python scripts/setup_duckdb.py

# Then run evaluation
python ./src/main_evaluation.py \
    --questions_file_name ./docs/01-questions.yaml \
    --database_source duckdb \
    --get_baseline_from_data_source \
    --iterations 1
```

## Configuration Files

### Questions Format (`01-questions.yaml`)
```yaml
questions:
  - question_number: 1
    user_question: "Show me weekly sales for 2024"
    sql_query: "SELECT DATEPART(week, order_date)..."
    tables_used: ["orders", "customer"]
```

### Database Schema (`02-database_schema.yaml`)
```yaml
tables:
  - name: "orders"
    script: "CREATE TABLE orders (id INT, ...)"
  - name: "customer" 
    script: "CREATE TABLE customer (id INT, ...)"
```

### Models Configuration (`05-models.yaml`)
```yaml
models_configs:
  - id: "azure_openai"
    enabled: true
    models:
      - name: "gpt-4o"
        enabled: true
        cost_input_tokens_EUR_1K: 0.005
        cost_output_tokens_EUR_1K: 0.015
```

## Environment Variables

### Database Configuration
- `SQL_SERVER`, `SQL_SERVER_DATABASE`, `SQL_SERVER_USERNAME`, `SQL_SERVER_PASSWORD`

### LLM API Configuration
- `OPENAI_ENDPOINT`, `OPENAI_KEY`, `OPENAI_MODEL`
- `DEEKSEEK_ENDPOINT`, `DEEKSEEK_KEY`, `DEEKSEEK_MODEL`
- `ENDPOINT_{SUBSCRIPTION}`
- `API_KEY_{SUBSCRIPTION}`

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

- `pandas` - Data manipulation and analysis
- `sqlalchemy` - Database connections and ORM
- `langfuse` - LLM observability and tracing
- `anthropic` - Anthropic Claude API
- `azure-ai-inference` - Azure AI services
- `yaml` - Configuration file parsing
- `tabulate` - Report formatting
- `python-dotenv` - Environment variable management

## Output Files

- **Baseline:** Tab-separated CSV files per question (`question_01.csv`, etc.)
- **Results:** YAML files with detailed evaluation results per model
- **Summary:** CSV files with aggregated metrics across all evaluations
- **Reports:** Formatted performance and ranking reports