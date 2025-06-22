import os

from data.questions_loader import QuestionsLoader
from utils.file_utils import FileUtils


class BaselineExecutor:
    """
    Core business logic for executing baseline queries.
    Extracted from LLMsEvaluator.execute_queries()
    """

    def __init__(self, db_service):
        self.db_service = db_service

    def execute_queries(
        self,
        questions,
        sql_query_column: str,
        summary_file_name: str,
        results_to_path: str,
        persist_results: bool = True,
        drop_results_if_exists: bool = False,
        questions_file_name: str = None,
    ):
        """
        Run the SQL queries from the questions file and export the results to CSV files.

        :param questions: List of questions to process.
        :param sql_query_column: Column name in the questions file that contains the SQL queries.
        :param summary_file_name: Name of the summary file to be created.
        :param results_to_path: Path where the results will be saved.
        :param persist_results: If True, the results will be saved to CSV files.
        :param drop_results_if_exists: If True, the existing results will be removed before running the queries.
        :param questions_file_name: Fallback file name if questions is None.
        :return: None
        """

        if questions is None and questions_file_name:
            questions = QuestionsLoader.load_questions_from_file(questions_file_name)

        if drop_results_if_exists:
            FileUtils.remove_baseline_datasets(results_to_path)

        summary_text = []
        summary_text.append("question_number\tduration_sql\tcolumns\trows")

        for question in questions:

            question_number = question["question_number"]
            sql_query = question.get(sql_query_column, "")
            df, executed, rows, columns, duration_sql = self.db_service.execute_sql_query(sql_query)

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
