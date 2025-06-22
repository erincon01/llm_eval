import os

from core.baseline_executor import BaselineExecutor
from core.model_evaluator import ModelEvaluator
from core.question_processor import QuestionProcessor
from data.models_config import ModelsConfig
from data.questions import Questions
from dotenv import load_dotenv
from services.database_service import DatabaseService
from services.llm_service import LLMService
from utils.data_utils import DataUtils
from utils.file_utils import FileUtils

from python_modules.schema import Database_schema_tables

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

        self.semantic_rules = FileUtils.load_file(semantic_rules_file_name)
        if not os.path.exists(system_message_file_name):
            raise FileNotFoundError(f"File {system_message_file_name} not found.")

        self.system_message = FileUtils.load_file(system_message_file_name)
        if not os.path.exists(models_file_name):
            raise FileNotFoundError(f"File {models_file_name} not found. Please check the path.")

        models_config = ModelsConfig(models_file_name)
        self.models_configs, self.models = models_config.load_models_from_yaml()
        self.llm_service = LLMService()
        self.db_service = DatabaseService()
        self.question_processor = QuestionProcessor(self.llm_service, self.db_service, self.db_schema)
        self.model_evaluator = ModelEvaluator(self.question_processor, self.questions_obj)
        self.baseline_executor = BaselineExecutor(self.db_service)

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
        """
        return self.question_processor.process_questions_with_model(
            questions=self.all_questions,
            baseline_datasets=self.baseline_datasets,
            model=model,
            model_config=model_config,
            system_message=self.system_message,
            semantic_rules=self.semantic_rules,
            temperature=temperature,
            max_tokens=max_tokens,
        )

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
        """
        return self.model_evaluator.evaluate_models(
            models=self.models,
            models_configs=self.models_configs,
            all_questions=self.all_questions,
            baseline_datasets=self.baseline_datasets,
            semantic_rules=self.semantic_rules,
            system_message=self.system_message,
            temperature=temperature,
            results_to_path=results_to_path,
            file_name_prefix=file_name_prefix,
            log_results=log_results,
            log_summary=log_summary,
        )

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
        """
        return self.baseline_executor.execute_queries(
            questions=self.all_questions,
            sql_query_column=sql_query_column,
            summary_file_name=summary_file_name,
            results_to_path=results_to_path,
            persist_results=persist_results,
            drop_results_if_exists=drop_results_if_exists,
            questions_file_name=self.questions_file_name,
        )

    def load_baseline_datasets(self, baseline_path: str):
        """
        Loads baseline datasets from the specified directory path.
        """
        self.baseline_datasets = DataUtils.load_baseline_datasets(baseline_path)
