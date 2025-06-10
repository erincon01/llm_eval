import os
import time
import uuid

import pandas as pd
import yaml
from database_schema_tables import Database_schema_tables
from dotenv import load_dotenv
from langfuse import get_client, observe
from module_data import get_dynamic_sql
from module_llm import get_chat_completion_from_platform
from module_utils import align_columns_by_first_row, normalize_numeric_columns, remove_quotations
from questions import Questions

# sys.path.append(os.path.abspath('./python_modules'))


class LLMsEvaluator:

    def __init__(
        self,
        questions_file_name=None,
        db_schema_file_name=None,
        semantic_rules_file_name=None,
        system_message_file_name=None,
        models_file_name=None,
    ):

        load_dotenv()

        self.questions_file_name = questions_file_name
        self.db_schema_file_name = db_schema_file_name
        self.semantic_rules_file_name = semantic_rules_file_name
        self.system_message_file_name = system_message_file_name

        if not os.path.exists(questions_file_name):
            raise FileNotFoundError(f"File {questions_file_name} not found. Please check the path.")

        self.questions_file_name = questions_file_name
        self.questions_obj = Questions(yaml_file=self.questions_file_name)
        self.questions_obj.load_questions()
        self.all_questions = self.questions_obj.get_all_questions()

        # # filter to only the first  2 question
        # self.all_questions = self.all_questions[:2]

        if not os.path.exists(db_schema_file_name):
            raise FileNotFoundError(f"File {db_schema_file_name} not found. Please check the path.")

        self.db_schema = Database_schema_tables(db_schema_file_name)

        if not os.path.exists(semantic_rules_file_name):
            raise FileNotFoundError(
                f"File {semantic_rules_file_name} not found.",
                "Please check the path.",
            )

        self.semantic_rules = self.__load_file(semantic_rules_file_name)

        if not os.path.exists(system_message_file_name):
            raise FileNotFoundError(f"File {system_message_file_name} not found.")

        self.system_message = self.__load_file(system_message_file_name)

        if not os.path.exists(models_file_name):
            raise FileNotFoundError(f"File {models_file_name} not found. Please check the path.")

        self.models_configs, self.models = self.__load_models_from_yaml(models_file_name)

    def __load_file(self, filename):
        """
        Load the content of a file as a string.

        Args:
            filename (str): Path to the file to be loaded.

        Returns:
            str: Content of the file as a string.
        """
        with open(filename, "r", encoding="utf-8") as file:
            content = file.read()
        return content

    def __load_questions(self):
        """
        Loads questions from the YAML file specified in
        self.questions_file_name.
        Returns:
            - List of all questions loaded from the YAML file.
        Raises:
            - FileNotFoundError: If the YAML file cannot be found or loaded.
            - Exception: If there is an error loading the questions from
            the YAML file.
        """

        try:
            questions = Questions(yaml_file=self.questions_file_name)
            questions.load_questions()
            return questions.get_all_questions()

        except Exception as e:
            raise FileNotFoundError(f"Error loading questions from {self.questions_file_name}: {e}")

    def __load_models_from_yaml(self, yaml_path: str):
        """
        Loads enabled model configurations and models from a YAML file.

        Returns:
            - models_configs: list of enabled providers with full
            config and filtered models
            - models: flat list of enabled models with id, name,
            and token costs
        Raises:
            Exception: If the YAML file cannot be loaded or is
            missing required fields.
        """
        try:
            with open(yaml_path, "r", encoding="utf-8") as f:
                raw = yaml.safe_load(f)
        except Exception as e:
            raise Exception(f"Error loading YAML file '{yaml_path}': {e}")

        if not isinstance(raw, dict):
            raise Exception(f"YAML file '{yaml_path}' is not a valid dictionary.")

        raw_configs = raw.get("models_configs", [])
        if not isinstance(raw_configs, list):
            raise Exception(f"'models_configs' must be a list in '{yaml_path}'.")

        models_configs = []
        models = []

        for provider in raw_configs:
            if not provider.get("enabled", True):
                continue

            if not all(k in provider for k in ("id", "endpoint", "api_key", "models")):
                raise Exception(f"Provider config missing required fields: {provider}")

            enabled_models = []
            for model in provider.get("models", []):
                if model.get("enabled", True):
                    if "name" not in model:
                        raise Exception(f"Model config missing 'name': {model}")
                    # Add token costs to the model
                    model["cost_input_tokens_EUR_1K"] = model.get("cost_input_tokens_EUR_1K", 0.0)
                    model["cost_output_tokens_EUR_1K"] = model.get("cost_output_tokens_EUR_1K", 0.0)
                    enabled_models.append(model)
                    models.append(
                        {
                            "id": provider["id"],
                            "name": model["name"],
                            "cost_input_tokens_EUR_1K": model["cost_input_tokens_EUR_1K"],
                            "cost_output_tokens_EUR_1K": model["cost_output_tokens_EUR_1K"],
                        }
                    )

            if enabled_models:
                config = {
                    "id": provider["id"],
                    "endpoint": provider["endpoint"],
                    "api_key": provider["api_key"],
                    "models": enabled_models,
                }
                models_configs.append(config)

        if not models_configs or not models:
            raise Exception(f"No enabled models found in '{yaml_path}'.")

        return models_configs, models

    @observe(capture_input=False, capture_output=True)
    def __get_sql_query_from_LLM(
        self,
        platform: str,
        model: str,
        question_number: str,
        user_prompt: str,
        temperature: float,
        max_tokens: int,
        database_tables_context: str,
        **model_config,
    ):
        """
        Get the SQL query to execute from the LLM based on the user prompt.

        :param platform: Platform to use for generating chat completions.
        :param model: Model to use for generating chat completions.
        :param question_number: Question number.
        :param user_prompt: User prompt.
        :param temperature: Temperature for the LLM.
        :param max_tokens: Maximum tokens for the LLM.
        :param database_tables_context: Database tables context.
        :param model_config: Model configuration [id, endpoint, api_key].
        :return: SQL query to execute, and metadata in json that includes
            tokens used and LLM call duration.

        """

        # copy the self.system_message to a new variable that is local
        # to the execution of this function
        system_message = self.system_message

        system_message = system_message.replace("{{database_tables_context}}", database_tables_context)
        system_message = system_message.replace("{{semantic_rules}}", self.semantic_rules)

        user_prompt = f"""
            {user_prompt}
        """

        sql_query = ""
        metadata_json = {}
        duration = 0

        try:

            params = {"question_number": question_number, **model_config}

            # Call the LLM to get the SQL query
            sql_query, metadata_json = get_chat_completion_from_platform(
                platform,
                model["name"],
                system_message,
                user_prompt,
                temperature,
                max_tokens,
                True,
                **params,
            )

        except Exception as e:
            print(f"Error: {e}")
            sql_query = ""
            duration = 0
            print(f"Error: {e}")
            print(f"Duration: {duration} seconds")
            print(f"SQL to execute: {sql_query}")

        langfuse = get_client()

        langfuse.update_current_trace(tags=["qa"])

        langfuse.update_current_span(
            metadata={
                "question_number": question_number,
            }
        )

        return sql_query, metadata_json

    def __remove_baseline_datasets(self, results_to_path: str):
        """
        Remove the baseline datasets from the results path.
        :param results_to_path: Path to the results directory.
        """

        # remove the baseline datasets if they exist
        if not os.path.exists(results_to_path):
            print(
                f"Results path {results_to_path} does not exist.",
                "No baseline datasets to remove.",
            )
            return 0
        for file in os.listdir(results_to_path):
            file_path = os.path.join(results_to_path, file)
            if os.path.isfile(file_path) and file.startswith("question_") and file.endswith(".csv"):
                print(f"Removing baseline dataset {file_path}")
                os.remove(file_path)

        # remove the summary file if it exists
        summary_file_path = os.path.join(results_to_path, "questions_baseline_summary.csv")
        summary_file_path = summary_file_path.replace("//", "/")
        if os.path.exists(summary_file_path):
            print(f"Removing baseline summary file {summary_file_path}")
            os.remove(summary_file_path)

    def compare_baseline_resultset_with_LLM_resultset(self, baseline_df, llm_df, question_number):
        """
        Compares the baseline resultset with the one generated by the LLM,
        ignoring column names and order, but considering the internal
        order of values in each row.

        :param baseline_df: Baseline DataFrame.
        :param llm_df: DataFrame generated by the LLM.
        :param question_number: Question number.
        :return:
            - percent_rows_equality: ratio of number of rows (size-based)
            - percent_columns_equality: ratio of number of columns (size-based)
            - percent_baseline_covered: how much of baseline data is covered
                in LLM result
            - percent_llm_covered: how much of LLM data exists in baseline
        """
        if baseline_df is None or llm_df is None or baseline_df.empty:
            return 0.00, 0.00, 0.00, 0.00

        try:
            # Normalize numeric columns to avoid float/decimal mismatches
            baseline_df, llm_df = normalize_numeric_columns(baseline_df, llm_df)

            # Align columns based on values in the first row (not column names)
            baseline_df, llm_df = align_columns_by_first_row(baseline_df, llm_df)

            # Convert rows to sets of tuples for set comparison
            baseline_set = set(map(tuple, baseline_df.to_numpy()))
            llm_set = set(map(tuple, llm_df.to_numpy()))

            # Calculate intersection
            intersection = baseline_set.intersection(llm_set)

            # Coverage percentages
            percent_baseline_covered = round(len(intersection) / len(baseline_set), 2) if baseline_set else 0.0
            percent_llm_covered = round(len(intersection) / len(llm_set), 2) if llm_set else 0.0

            # Pure size comparison (not content-aware)
            percent_rows_equality = round(len(llm_df) / len(baseline_df), 2) if len(llm_df) <= len(baseline_df) else 0.0
            percent_columns_equality = (
                round(len(llm_df.columns) / len(baseline_df.columns), 2)
                if len(llm_df.columns) <= len(baseline_df.columns)
                else 0.0
            )

            return (
                percent_rows_equality,
                percent_columns_equality,
                percent_baseline_covered,
                percent_llm_covered,
            )

        except Exception as e:
            print(f"[ERROR] Question #{question_number}: comparison failed: {e}")
            return 0.0, 0.0, 0.0, 0.0

    @observe(capture_input=False, capture_output=True)
    def process_questions_with_model(
        self,
        model: str,
        model_config: dict,
        temperature: float,
        max_tokens: int,
    ) -> str:
        """
        Process each question, generate SQL queries using the LLM,
        run the SQL Query, compare the results with the baseline,
        and log the results.

        :param model: Model to use for generating chat completions.
        :param model_config: Model configuration [id, endpoint, api_key].
        :param temperature: Temperature for the LLM.
        :param max_tokens: Maximum tokens for the LLM.
        :return: summary of the processing with the model.
        """

        total_time = time.time()
        total_rows = 0
        total_time_sql = 0
        total_time_llm = 0
        total_queries = 0

        summary_text = []

        for question in self.all_questions:

            question_number = question["question_number"]
            user_question = question["user_question"]
            tables_used = question["tables_used"]
            sql_query = ""

            table_scripts = []

            for table in tables_used:
                table_script = self.db_schema.get_table_script(table)
                if table_script:
                    table_scripts.append(table_script)
            database_tables_context = "\n".join(table_scripts)

            # Call the process_query function with the loaded question
            sql_query, metadata = self.__get_sql_query_from_LLM(
                platform="azure_openai",
                model=model,
                question_number=question_number,
                user_prompt=user_question,
                database_tables_context=database_tables_context,
                temperature=temperature,
                max_tokens=max_tokens,
                model_config=model_config,
            )

            sql_query, changed = remove_quotations(sql_query)

            # execute the SQL query
            executed = True
            df = None
            rows = 0
            columns = 0
            duration_sql = 0
            if sql_query:
                try:
                    t = time.time()
                    df = get_dynamic_sql("azure-sql", sql_query, True)
                    duration_sql = time.time() - t
                    if df is not None:
                        rows = len(df)
                        columns = len(df.columns)
                except Exception as e:
                    df = None
                    executed = False
                    print(f"[ERROR] SQL execution failed: {e}")
            else:
                executed = False
                duration_sql = 0
                rows = 0

            # compare the result with the baseline
            baseline_dataframes = self.baseline_datasets
            baseline_entry = next(
                (item for item in baseline_dataframes if item["question_number"] == question_number),
                None,
            )
            baseline_df = baseline_entry["df"] if baseline_entry else None

            (
                percent_rows_equality,
                percent_columns_equality,
                percent_source_rows_equality,
                percent_llm_rows_equality,
            ) = self.compare_baseline_resultset_with_LLM_resultset(baseline_df, df, question_number)

            duration_sql = round(duration_sql, 2)
            duration_llm = round(metadata.get("duration", 0), 2)

            question["llm_sql_query"] = sql_query
            question["tables_used"] = tables_used
            question["executed"] = executed
            question["rows"] = rows
            question["columns"] = columns
            question["percent_rows_equality"] = percent_rows_equality
            question["percent_columns_equality"] = percent_columns_equality
            question["percent_source_rows_equality"] = percent_source_rows_equality
            question["percent_llm_rows_equality"] = percent_llm_rows_equality

            question["duration_sql"] = duration_sql
            question["duration_llm"] = duration_llm
            question["llm_sql_query_changed"] = changed

            question["total_tokens"] = metadata.get("total_tokens", 0)
            question["prompt_tokens"] = metadata.get("prompt_tokens", 0)
            question["completion_tokens"] = metadata.get("completion_tokens", 0)

            selected_model = next(
                (m for m in model_config.get("models", []) if m.get("name") == model),
                {},
            )

            # Calculate costs
            cost_input_EUR = question["prompt_tokens"] * (selected_model.get("cost_input_tokens_EUR_1K", 0.0) / 1000)
            cost_output_EUR = question["completion_tokens"] * (
                selected_model.get("cost_output_tokens_EUR_1K", 0.0) / 1000
            )
            question["cost_input_EUR"] = round(cost_input_EUR, 6)
            question["cost_output_EUR"] = round(cost_output_EUR, 6)
            question["cost_total_EUR"] = round(cost_input_EUR + cost_output_EUR, 6)

            total_rows += rows
            total_time_sql += duration_sql
            total_time_llm += duration_llm
            total_queries += 1

            print(
                f"Question #{question_number}: LLM: {duration_llm:.1f} sec(s),"
                f"SQL: {duration_sql:.1f} sec(s), {rows} row(s) affected,\n"
                f"    {percent_rows_equality} rows equality, "
                f"{percent_columns_equality} columns equality,\n"
                f"    {percent_source_rows_equality} source rows equality, "
                f"{percent_llm_rows_equality} LLM rows equality..."
            )

            row_log = (
                f"{time.strftime('%Y-%m-%d %H:%M:%S')}\t{question_number}\t{model}\t"
                f"{duration_llm:.1f}\t{duration_sql:.1f}\t{rows}\t{columns}\t"
                f"{percent_rows_equality}\t{percent_columns_equality}\t"
                f"{percent_source_rows_equality}\t{percent_llm_rows_equality}\t"
                f"{question['total_tokens']}\t{question['prompt_tokens']}\t"
                f"{question['completion_tokens']}\t{question['cost_total_EUR']}\t"
                f"{question['cost_input_EUR']}\t{question['cost_output_EUR']}"
            )

            summary_text.append(row_log)

        batch_id = "batch_id-" + str(uuid.uuid4())

        total_time_sql = round(total_time_sql, 2)
        total_time_llm = round(total_time_llm, 2)

        langfuse = get_client()
        langfuse.update_current_trace(
            user_id="demo_user",
            session_id=batch_id,
            tags=["qa"],
            metadata={
                "total_rows": total_rows,
                "total_time_sql": total_time_sql,
                "total_time_llm": total_time_llm,
                "total_queries": total_queries,
            },
        )

        total_time = time.time() - total_time
        total_time = round(total_time, 2)

        print(
            f"  Batch summary: processed {total_queries} queries, {total_rows} rows, "
            f"{total_time_sql} sec SQL, {total_time_llm} sec LLM"
        )
        print(f"  Batch ID     : {batch_id} processed in {total_time} second(s)\n")

        return summary_text

    def evaluate_models(
        self,
        temperature: float,
        results_to_path: str,
        file_name_prefix: str,
        log_results: bool = True,
        log_summary: bool = True,
    ) -> str:
        """
        Iterate each model and execute each sql question in self.all_questions.
        Compares the resultsets and log results.

        :param temperature: Temperature for the LLM.
        :param results_to_path: Path where the results will be saved.
        :param file_name_prefix: Prefix for the generated files.
        :param log_results: If True, the results will be saved to YAML files.
        :param log_summary: If True, a summary file will be created with the results.
        :raises Exception: If any of the required configuration variables are None.
        :return: files_generated: List of generated files,
                summary_text: Summary of the processing with the model.
        """

        # Check for None values and raise exception if any are missing
        if any(
            v is None
            for v in [
                self.all_questions,
                self.db_schema,
                self.semantic_rules,
                self.system_message,
                self.models_configs,
                self.models,
                self.baseline_datasets,
            ]
        ):
            raise Exception("One or more required configuration variables are None.")

        files_generated = []
        summary_text = []

        # now
        d = time.strftime("%Y%m%d_%H%M")

        if log_summary:

            summary_file_path = os.path.join(
                results_to_path,
                "questions_summary_" + file_name_prefix + "_" + d + ".csv",
            )
            summary_file_path = summary_file_path.replace("//", "/")

            row_header = (
                "Timestamp\tQuestion\tModel\tLLM_time\tSQL_time\tRows\tColumns\t"
                "Percent_rows_equality\tPercent_columns_equality\t"
                "Percent_source_rows_equality\tPercent_llm_rows_equality\t"
                "Total_tokens\tPrompt_tokens\tCompletion_tokens\t"
                "Cost_total_EUR\tCost_input_tokens_EUR\tCost_output_tokens_EUR\n"
            )

            summary_text.append(row_header)

            # remove the file if it exists
            if os.path.exists(summary_file_path):
                os.remove(summary_file_path)

            # create the file and write the header
            with open(summary_file_path, "w", encoding="utf-8") as file:
                file.write("\n".join(summary_text))

        for model in self.models:

            print(f"\nProcessing questions with model {model}, temperature {temperature}")

            model_id = model["id"]
            if model_id is None or model_id == "":
                raise ValueError(f"Model {model_id} not found in the variable model.")

            model_name = model["name"]
            if model_name is None or model_name == "":
                raise ValueError(f"Model {model_name} not found in the variable model.")

            model_config = next(
                (cfg for cfg in self.models_configs if cfg["id"] == model_id),
                None,
            )

            if model_config is None:
                raise ValueError(f"Model {model_id} not found in the variable model_config.")

            model_summary_text = self.process_questions_with_model(
                model=model,
                model_config=model_config,
                temperature=temperature,
                max_tokens=10000,
            )

            if log_results:
                # save the results to a YAML file
                file_name = f"{results_to_path}/{file_name_prefix}_{model}.yaml"
                file_name = file_name.replace("//", "/")
                if os.path.exists(file_name):
                    os.remove(file_name)
                self.questions_obj.save_questions(yaml_file=file_name)
                files_generated.append(file_name)

            print(f"Processed questions with model {model}")
            print("---")

            if log_summary:
                # add to the summary file the model_summary_text
                with open(summary_file_path, "a", encoding="utf-8") as file:
                    for line in model_summary_text:
                        file.write(f"{line}\n")
                        summary_text.append(line)

        print("All batches processed.")

        return files_generated, summary_text

    def execute_queries(
        self,
        sql_query_column: str,
        summary_file_name: str,
        results_to_path: str,
        persist_results: bool = True,
        drop_results_if_exists: bool = False,
    ):
        """
        Run the SQL queries from the questions file and export the results to CSV files.
        :param sql_query_column: Column name in the questions file that contains the SQL queries.
        :param summary_file_name: Name of the summary file to be created.
        :param results_to_path: Path where the results will be saved.
        :param persist_results: If True, the results will be saved to CSV files.
        :param drop_results_if_exists: If True, the existing results will be removed before running the queries.
        :return: None
        """

        if self.all_questions is None:
            self.questions_obj = Questions(yaml_file=self.questions_file_name)
            self.questions_obj.load_questions()
            self.all_questions = self.questions_obj.get_all_questions()

        if drop_results_if_exists:
            self.__remove_baseline_datasets(results_to_path)

        summary_text = []
        summary_text.append("question_number\tduration_sql\tcolumns\trows")

        for question in self.all_questions:

            question_number = question["question_number"]
            sql_query = question.get(sql_query_column, "")

            df = None
            rows = 0
            columns = 0
            duration_sql = 0
            if sql_query:
                try:
                    t = time.time()
                    df = get_dynamic_sql("azure-sql", sql_query, True)
                    duration_sql = time.time() - t
                    if df is not None:
                        rows = len(df)
                        columns = len(df.columns)

                except Exception as e:
                    df = None
                    print(f"[ERROR] SQL execution failed for question #{question_number}: {e}")
            else:
                duration_sql = 0
                rows = 0
                columns = 0

            duration_sql = round(duration_sql, 2)

            summary_text.append(f"{question_number}\t{duration_sql:.1f}\t{columns}\t{rows}")

            if df is not None and not df.empty and persist_results:
                file_name = f"{results_to_path}/question_{int(question_number):02d}.csv"
                file_name = file_name.replace("//", "/")
                df.to_csv(
                    file_name,
                    index=False,
                    header=True,
                    encoding="utf-8",
                    sep="\t",
                )

        print(f"  Question #{question_number}: SQL: {duration_sql:.1f} sec(s), " f"{rows} row(s) affected...")

        # save the summary file
        summary_file_path = os.path.join(results_to_path, summary_file_name)
        summary_file_path = summary_file_path.replace("//", "/")

        with open(summary_file_path, "w", encoding="utf-8") as file:
            file.write("\n".join(summary_text))
        print(f"Summary file {summary_file_path} generated.")
        print("All baseline queries processed.")

    def load_baseline_datasets(self, baseline_path: str):
        """
        Loads baseline datasets from the specified directory path.

        This method searches for CSV files in the given directory whose
        filenames start with "question_" and end with ".csv".
        Each matching file is read into a pandas DataFrame, and the question number is
        extracted from the filename.
        The loaded datasets are stored as a list of dictionaries in the `self.baseline_datasets` attribute,
        where each dictionary contains the question number and its corresponding DataFrame.

        Args:
            baseline_path (str): The path to the directory containing baseline dataset CSV files.

        Raises:
            FileNotFoundError: If the specified baseline_path does not exist.
            NotADirectoryError: If the specified baseline_path is not a directory.

        Returns:
            None
        """

        try:
            if not os.path.exists(baseline_path):
                raise FileNotFoundError(f"Baseline path {baseline_path} does not exist.")
            if not os.path.isdir(baseline_path):
                raise NotADirectoryError(f"Baseline path {baseline_path} is not a directory.")
        except Exception as e:
            print(f"Error loading baseline datasets: {e}")
            return

        baseline_datasets = []

        for file in os.listdir(baseline_path):
            file_path = os.path.join(baseline_path, file)
            if os.path.isfile(file_path) and file.startswith("question_") and file.endswith(".csv"):
                df = pd.read_csv(file_path, sep="\t", encoding="utf-8")
                question_number = int(file.split("_")[1].split(".")[0])
                baseline_datasets.append({"question_number": question_number, "df": df})

        self.baseline_datasets = baseline_datasets
