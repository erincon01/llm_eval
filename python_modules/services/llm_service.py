from langfuse import get_client, observe
from utils.llm_utils import get_chat_completion_from_platform


class LLMService:
    """
    Service class for LLM interactions.
    Extracted from LLMsEvaluator.__get_sql_query_from_LLM()
    """

    @observe(capture_input=False, capture_output=True)
    def generate_sql_query(
        self,
        platform: str,
        model: dict,
        question_number: str,
        user_prompt: str,
        temperature: float,
        max_tokens: int,
        database_tables_context: str,
        system_message: str,
        semantic_rules: str,
        **model_config,
    ):
        """
        Get the SQL query to execute from the LLM based on the user prompt.

        :param platform: Platform to use for generating chat completions.
        :param model: Model dictionary with model information.
        :param question_number: Question number.
        :param user_prompt: User prompt.
        :param temperature: Temperature for the LLM.
        :param max_tokens: Maximum tokens for the LLM.
        :param database_tables_context: Database tables context.
        :param system_message: System message template.
        :param semantic_rules: Semantic rules content.
        :param model_config: Model configuration [id, endpoint, api_key].
        :return: SQL query to execute, and metadata in json that includes
            tokens used and LLM call duration.
        """

        # copy the system_message to a new variable that is local to the execution of this function
        system_message_local = system_message

        system_message_local = system_message_local.replace("{{database_tables_context}}", database_tables_context)
        system_message_local = system_message_local.replace("{{semantic_rules}}", semantic_rules)

        user_prompt_formatted = f"""
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
                system_message_local,
                user_prompt_formatted,
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
