import time
import uuid

from langfuse import get_client, observe
from utils.data_utils import DataUtils, remove_quotations


class QuestionProcessor:
    """
    Core business logic for processing questions with LLM models.
    Extracted from LLMsEvaluator.process_questions_with_model()
    """

    def __init__(self, llm_service, db_service, db_schema):
        self.llm_service = llm_service
        self.db_service = db_service
        self.db_schema = db_schema

    @observe(capture_input=False, capture_output=True)
    def process_questions_with_model(
        self,
        questions,
        baseline_datasets,
        model,
        model_config,
        system_message,
        semantic_rules,
        temperature,
        max_tokens,
    ):
        """
        Process each question, generate SQL queries using the LLM,
        run the SQL Query, compare the results with the baseline,
        and log the results.

        :param questions: List of questions to process.
        :param baseline_datasets: Baseline datasets for comparison.
        :param model: Model to use for generating chat completions.
        :param model_config: Model configuration [id, endpoint, api_key].
        :param system_message: System message template.
        :param semantic_rules: Semantic rules content.
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

        for question in questions:

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
            sql_query, metadata = self.llm_service.generate_sql_query(
                platform="azure_openai",
                model=model,
                question_number=question_number,
                user_prompt=user_question,
                database_tables_context=database_tables_context,
                temperature=temperature,
                max_tokens=max_tokens,
                system_message=system_message,
                semantic_rules=semantic_rules,
                **model_config,
            )

            sql_query, changed = remove_quotations(sql_query)
            df, executed, rows, columns, duration_sql = self.db_service.execute_sql_query(sql_query)

            # compare the result with the baseline
            baseline_entry = next(
                (item for item in baseline_datasets if item["question_number"] == question_number),
                None,
            )
            baseline_df = baseline_entry["df"] if baseline_entry else None

            (
                percent_rows_equality,
                percent_columns_equality,
                percent_source_rows_equality,
                percent_llm_rows_equality,
            ) = DataUtils.compare_dataframes(baseline_df, df, question_number)

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
                (m for m in model_config.get("models", []) if m.get("name") == model["name"]),
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
