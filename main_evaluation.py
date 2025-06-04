import os
import sys
from dotenv import load_dotenv
import json as json
import time
import pandas as pd

sys.path.append(os.path.abspath('./python_modules'))

from llms_evaluator import LLMsEvaluator
from module_utils import consolidate_files_by_iteration, consolidate_files_by_model, consolidate_csv_files, performance_report

if __name__ == "__main__":

    # ### CAUTION: "Phi-4" have to implement function to remove ````sql and ```code
    # ### REMOVED: "Phi-4-mini-instruct", "Phi-3-small-128k-instruct", "Phi-3-medium-128k-instruct", do not build sql code. lots of comments: 
    # ### REMOVED: "o3-mini", "o4-mini" removed because are very slow in response, for example:

    evaluator = LLMsEvaluator(
        questions_file_name="./docs/01-questions.yaml", 
        db_schema_file_name="./docs/02-database_schema.yaml",
        semantic_rules_file_name="./docs/03-semantic-rules.md",
        system_message_file_name="./docs/04-system_message.md",
        models_file_name="./docs/05-models.yaml",
    )

    temperature = 0.9
    results_path = "./docs/results"

    # ############# STEP 1: run the queries in the database in order to have a baseline to compare the results

    # evaluator.execute_queries(
    #         sql_query_column ="sql_query",
    #         summary_file_name = "questions_baseline_summary.csv",
    #         results_to_path = results_path + "/baseline_dataset", 
    #         persist_results=True,
    #         drop_results_if_exists=True)

    # ############# STEP 2: load the dataframes with the resultsets to compare with the results retrieved from the queries builts with each LLM
    evaluator.load_baseline_datasets(results_path + "/baseline_dataset")

    # # ############# STEP 3: n iterations of the LLM to generate the SQL queries

    number_of_iterations = 1

    for i in range(number_of_iterations):

        i_str = str(i+1).zfill(2)
        print(f"Iteration {i+1} of {number_of_iterations} started...")

        t = time.time()

        output_files, summary_text = evaluator.evaluate_models (
            temperature, 
            results_to_path=results_path, 
            file_name_prefix=f"results_llm_{i_str}",
            log_results=True,
            log_summary=True,
        )

        t = time.time() - t
        t = round(t, 2)
        for file in output_files:
            print(f"log file generated: {file}")

        print(f"Execution {i+1} of {number_of_iterations} completed in {t} seconds.")
        print (f"---\n")

    ############# STEP 3: files consolidation [optional step]
    ### optional steps to consolidate files.

    # results_path = "./docs/results"
    # consolidate_files_by_iteration(results_path=results_path, file_name_prefix="results_llm_")

    ############# STEP 4: performance report

    # results_path = "./docs/results-pub2"
    performance_report(results_path=results_path, file_name_prefix="questions_summary_results_llm")

