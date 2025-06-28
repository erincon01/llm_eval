from data.questions import Questions


class QuestionsLoader:
    """
    Utility class for loading questions from YAML files.
    Extracted from LLMsEvaluator.__load_questions()
    """

    @staticmethod
    def load_questions_from_file(questions_file_name: str):
        """
        Loads questions from the YAML file specified.

        Args:
            questions_file_name (str): Path to the YAML file containing questions.

        Returns:
            list: List of all questions loaded from the YAML file.

        Raises:
            FileNotFoundError: If the YAML file cannot be found or loaded.
            Exception: If there is an error loading the questions from the YAML file.
        """
        try:
            questions = Questions(yaml_file=questions_file_name)
            questions.load_questions()
            return questions.get_all_questions()

        except Exception as e:
            raise FileNotFoundError(f"Error loading questions from {questions_file_name}: {e}")
