import os


class FileUtils:
    """
    Utility class for file operations.
    Extracted from LLMsEvaluator.__load_file()
    """

    @staticmethod
    def load_file(filename: str) -> str:
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

    @staticmethod
    def remove_baseline_datasets(results_to_path: str):
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
