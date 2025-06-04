import os
import yaml

def _multiline_str_presenter(dumper: yaml.Dumper, data: str):
    """
    - If the string is multiline:
        * Remove trailing spaces from each line (does not affect the text).
        * Use literal style (|) for better YAML readability.
    - For single-line strings, use the default style.
    """
    if "\n" in data:
        # Remove only trailing spaces from each line (not internal spaces)
        cleaned = "\n".join(line.rstrip() for line in data.splitlines())
        # Preserve the final newline if the original string had it
        if data.endswith("\n"):
            cleaned += "\n"
        return dumper.represent_scalar("tag:yaml.org,2002:str", cleaned, style="|")

    # Single-line string → normal style
    return dumper.represent_scalar("tag:yaml.org,2002:str", data)

# Register the representer in all common dumpers
for _d in filter(None, [
        yaml.SafeDumper, yaml.Dumper,
        getattr(yaml, "CSafeDumper", None), getattr(yaml, "CDumper", None)
    ]):
    yaml.add_representer(str, _multiline_str_presenter, Dumper=_d)

    
class Questions:
    def __init__(self, yaml_file):
        """
        Initialize the Questions manager with a YAML file.

        :param yaml_file: Path to the YAML file containing the questions.
        """
        self.yaml_file = yaml_file
        self.questions = []
        if os.path.exists(yaml_file):
            self.load_questions()

    def load_questions(self):
        """
        Load questions from the YAML file into the questions list.
        Ensure all properties are initialized properly.

        Args:
            None

        Returns:
            None
        """
        try:
            with open(self.yaml_file, 'r', encoding='utf-8') as file:
                data = yaml.safe_load(file)
                self.questions = []
                for item in data.get('questions', []):
                    cost_input_tokens_1k = item.get('cost_input_tokens_EUR_1K', 0.0)
                    cost_output_tokens_1k = item.get('cost_output_tokens_EUR_1K', 0.0)
                    prompt_tokens = item.get('prompt_tokens', 0)
                    completion_tokens = item.get('completion_tokens', 0)

                    self.questions.append({
                        'iteration': item.get('iteration', ''),
                        'model_name': item.get('model_name', ''),
                        'question_number': item.get('question_number', ''),
                        'user_question': item.get('user_question', ''),
                        'sql_query': item.get('sql_query', ''),
                        'llm_sql_query': item.get('llm_sql_query', ''),
                        'tables_used': item.get('tables_used', []),
                        'executed': item.get('executed', False),
                        'llm_sql_query_changed': item.get('llm_sql_query_changed', False),
                        'rows': item.get('rows', 0),
                        'columns': item.get('columns', 0),
                        'percent_rows_equality': item.get('percent_rows_equality', 0),
                        'percent_columns_equality': item.get('percent_columns_equality', 0),
                        'percent_source_rows_equality': item.get('percent_source_rows_equality', 0),
                        'percent_llm_rows_equality': item.get('percent_llm_rows_equality', 0),
                        'duration_sql': item.get('duration_sql', 0),
                        'duration_llm': item.get('duration_llm', 0),
                        'prompt_tokens': item.get('prompt_tokens', 0),
                        'completion_tokens': item.get('completion_tokens', 0),
                        'total_tokens': item.get('total_tokens', 0),
                        'cost_input_EUR': prompt_tokens * (cost_input_tokens_1k / 1000),
                        'cost_output_EUR': completion_tokens * (cost_output_tokens_1k / 1000),
                        'cost_total_EUR': prompt_tokens * (cost_input_tokens_1k / 1000) + completion_tokens * (cost_output_tokens_1k / 1000)
                    })

        except FileNotFoundError:
            print(f"Error: File {self.yaml_file} not found.")
        except yaml.YAMLError as e:
            print(f"Error parsing YAML file: {e}")


    def add_question(self, question):
        """
        Add a new question to the list.

        :param question: Dictionary containing question details.
        """
        try:
            if isinstance(question, dict):
                prompt_tokens = question.get('prompt_tokens', 0)
                completion_tokens = question.get('completion_tokens', 0)
                cost_input_tokens_1k = question.get('cost_input_tokens_EUR_1K', 0.0)
                cost_output_tokens_1k = question.get('cost_output_tokens_EUR_1K', 0.0)

                self.questions.append({
                    'iteration': question.get('iteration', ''),
                    'model_name': question.get('model_name', ''),
                    'question_number': question.get('question_number', ''),
                    'user_question': question.get('user_question', ''),
                    'sql_query': question.get('sql_query', ''),
                    'llm_sql_query': question.get('llm_sql_query', ''),
                    'tables_used': question.get('tables_used', []),
                    'executed': question.get('executed', False),
                    'llm_sql_query_changed': question.get('llm_sql_query_changed', False),
                    'rows': question.get('rows', 0),
                    'columns': question.get('columns', 0),
                    'percent_rows_equality': question.get('percent_rows_equality', 0),
                    'percent_columns_equality': question.get('percent_columns_equality', 0),
                    'percent_source_rows_equality': question.get('percent_source_rows_equality', 0),
                    'percent_llm_rows_equality': question.get('percent_llm_rows_equality', 0),
                    'duration_sql': question.get('duration_sql', 0),
                    'duration_llm': question.get('duration_llm', 0),
                    'prompt_tokens': question.get('prompt_tokens', 0),
                    'completion_tokens': question.get('completion_tokens', 0),
                    'total_tokens': question.get('total_tokens', 0),
                    'cost_input_EUR': prompt_tokens * (cost_input_tokens_1k / 1000),
                    'cost_output_EUR': completion_tokens * (cost_output_tokens_1k / 1000),
                    'cost_total_EUR': (prompt_tokens * (cost_input_tokens_1k / 1000)) + (completion_tokens * (cost_output_tokens_1k / 1000))
                })
            else:
                print("Error: Question must be a dictionary.")
        except Exception as e:
            print(f"Error adding question: {e}")

    
    def get_all_questions(self):
        """
        Get all questions.

        :return: List of all questions.
        """
        return self.questions


    def save_questions(self, yaml_file):
        """
        Save the current list of questions back to the YAML file.
        """
        try:
            data_to_dump = {"questions": self.questions}

            yaml_text: str = yaml.dump(
                data_to_dump,
                allow_unicode=True,
                sort_keys=False,
                default_flow_style=False,
                Dumper=yaml.SafeDumper,   # ← same dumper where the representer was registered
            )

            with open(yaml_file, 'w', encoding='utf-8') as file:
                file.write(yaml_text)

        except Exception as e:
            print(f"Error saving questions to file: {e}")


    def find_question(self, keyword):
        """
        Find questions that contain a specific keyword.

        :param keyword: The keyword to search for.
        :return: List of questions containing the keyword.
        """
        return [q for q in self.questions if keyword.lower() in q.get('user_question', '').lower()]

