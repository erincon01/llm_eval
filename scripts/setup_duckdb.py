import duckdb
from llms_evaluator import LLMsEvaluator


def setup_duckdb_tpch():
    """
    Set up DuckDB with TPCH sample data.
    """
    # Connect to DuckDB file
    conn = duckdb.connect("./docs/tpch-sf10.db")
    
    try:

        evaluator = LLMsEvaluator(
            questions_file_name="./docs/01-questions-duckdb.yaml",
            db_schema_file_name="./docs/02-database_schema.yaml",
            semantic_rules_file_name="./docs/03-semantic-rules.md",
            system_message_file_name="./docs/04-system_message.md",
            models_file_name="./docs/05-models.yaml",
            data_source="duckdb"
        )

        # STEP 1: run the queries in the database in order
        # to have a baseline to compare the results

        results_path = "./docs/results"

        evaluator.execute_queries(
            sql_query_column="sql_query",
            summary_file_name="questions_baseline_summary_duckdb.csv",
            results_to_path=results_path + "/baseline_dataset_duckdb",
            persist_results=True,
            drop_results_if_exists=True,
        )

        print("DuckDB TPCH setup completed successfully!")
        
    except Exception as e:
        print(f"Error setting up DuckDB: {e}")
    finally:
        conn.close()


if __name__ == "__main__":
    setup_duckdb_tpch()
