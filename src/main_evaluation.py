import time
import argparse
from llms_evaluator import LLMsEvaluator
from utils.reporting_utils import performance_report

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run LLM evaluation.")
    parser.add_argument(
        "--questions_file_name",
        type=str,
        default="./docs/01-questions.yaml",
        help="Path to the questions YAML file.",
    )
    parser.add_argument(
        "--db_schema_file_name",
        type=str,
        default="./docs/02-database_schema.yaml",
        help="Path to the database schema YAML file.",
    )
    parser.add_argument(
        "--semantic_rules_file_name",
        type=str,
        default="./docs/03-semantic-rules.md",
        help="Path to the semantic rules Markdown file.",
    )
    parser.add_argument(
        "--system_message_file_name",
        type=str,
        default="./docs/04-system_message.md",
        help="Path to the system message Markdown file.",
    )
    parser.add_argument(
        "--models_file_name",
        type=str,
        default="./docs/05-models.yaml",
        help="Path to the models configuration YAML file.",
    )
    parser.add_argument(
        "--iterations",
        type=int,
        default=1,
        help="Number of iterations for the LLM evaluation.",
    )
    parser.add_argument(
        "--get_baseline_from_data_source",
        action="store_true",
        help="Run step 1 to get baseline resultsets from the data source.",
    )
    args = parser.parse_args()

    evaluator = LLMsEvaluator(
        questions_file_name=args.questions_file_name,
        db_schema_file_name=args.db_schema_file_name,
        semantic_rules_file_name=args.semantic_rules_file_name,
        system_message_file_name=args.system_message_file_name,
        models_file_name=args.models_file_name,
    )

    temperature = 0.9
    results_path = "./docs/results"

    # STEP 1: run the queries in the database in order
    # to have a baseline to compare the results
    if args.get_baseline_from_data_source:
        evaluator.execute_queries(
            sql_query_column="sql_query",
            summary_file_name="questions_baseline_summary.csv",
            results_to_path=results_path + "/baseline_dataset",
            persist_results=True,
            drop_results_if_exists=True,
        )

    # STEP 2: load the dataframes with the resultsets to compare
    # with the results retrieved
    # from the queries builts with each LLM
    evaluator.load_baseline_datasets(results_path + "/baseline_dataset")

    # STEP 3: n iterations of the LLM to generate the SQL queries

    number_of_iterations = args.iterations

    for i in range(number_of_iterations):

        i_str = str(i + 1).zfill(2)
        print(f"Iteration {i+1} of {number_of_iterations} started...")

        t = time.time()

        output_files, summary_text = evaluator.evaluate_models(
            temperature,
            results_to_path=results_path,
            file_name_prefix=f"results_llm_{i_str}",
            log_results=True,
            log_summary=True,
            iteration=i_str,
        )

        t = time.time() - t
        t = round(t, 2)
        for file in output_files:
            print(f"log file generated: {file}")

        print(
            "Execution {} of {} done in {:.2f} seconds.".format(
                i + 1,
                number_of_iterations,
                t,
            )
        )

        print("---\n")

    # STEP 3: files consolidation [optional step]
    # optional steps to consolidate files.

    # results_path = "./docs/results"
    # consolidate_files_by_iteration(results_path=results_path,
    # file_name_prefix="results_llm_")

    # STEP 4: performance report

    performance_report(
        results_path=results_path,
        file_name_prefix="questions_summary_results_llm",
    )
