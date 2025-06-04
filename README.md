# llm_eval

# Project Overview

This project is designed to evaluate the performance of various Large Language Models (LLMs) in generating SQL queries based on predefined questions and database schemas. It provides tools for orchestrating evaluations, comparing results, and generating performance reports.

# Dependencies

The project relies on the following Python packages:
- `python-dotenv`
- `requests`
- `pandas`
- `streamlit`
- `matplotlib`
- `seaborn`
- `beautifulsoup4`
- `pillow`
- `openai`
- `pyodbc`
- `sqlalchemy`
- `pyyaml`
- `azure-core`
- `azure.ai.inference`
- `tiktoken`
- `polars`
- `python-docx`
- `anthropic`
- `vertexai`
- `langfuse`
- `tabulate`

# Modules and Functionalities

### `llms_evaluator`
This module contains the `LLMsEvaluator` class, which is central to the evaluation process. It:
- Loads questions from YAML files.
- Parses database schemas.
- Applies semantic rules.
- Interacts with LLMs to generate SQL queries.
- Compares generated queries with baseline datasets.

### `module_utils`
Provides utility functions for:
- Consolidating files by iteration or model.
- Normalizing numeric columns.
- Aligning columns by the first row.
- Generating performance reports.

### Other Modules
- `module_data`: Handles dynamic SQL generation.
- `module_azure_openai`: Facilitates interaction with Azure OpenAI services.

# Key Classes and Methods

### `LLMsEvaluator`
The `LLMsEvaluator` class is initialized with paths to configuration files, including:
- Questions (`01-questions.yaml`)
- Database schema (`02-database_schema.yaml`)
- Semantic rules (`03-semantic-rules.md`)
- System messages (`04-system_message.md`)
- Models (`05-models.yaml`)

Key methods:
- `load_baseline_datasets`: Loads baseline datasets for comparison.
- `execute_queries`: Executes SQL queries to establish a baseline.

# Role of `main_evaluation.py`

The `main_evaluation.py` script orchestrates the evaluation process. It:
1. Initializes the `LLMsEvaluator` class with configuration files.
2. Loads baseline datasets.
3. Iterates through LLMs to generate SQL queries.
4. Compares results and generates performance reports.

# Contribution Guidelines

Developers interested in contributing can follow these steps:
1. Clone the repository.
2. Install dependencies using `pip install -r requirements.txt`.
3. Explore the `main_evaluation.py` script and `llms_evaluator` module.
4. Add new models or improve evaluation methods.
5. Submit pull requests with detailed descriptions of changes.

For any questions, refer to the documentation in the `docs/` directory.

