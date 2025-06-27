import os
import time


class ModelEvaluator:
    """
    Core business logic for evaluating multiple LLM models.
    Extracted from LLMsEvaluator.evaluate_models()
    """

    def __init__(self, question_processor, questions_obj):
        self.question_processor = question_processor
        self.questions_obj = questions_obj

    def evaluate_models(
        self,
        models,
        models_configs,
        all_questions,
        baseline_datasets,
        semantic_rules,
        system_message,
        temperature,
        results_to_path,
        file_name_prefix,
        log_results=True,
        log_summary=True,
    ):
        """
        Iterate each model and execute each sql question.
        Compares the resultsets and log results.

        :param models: List of models to evaluate.
        :param models_configs: Model configurations.
        :param all_questions: List of all questions to process.
        :param baseline_datasets: Baseline datasets for comparison.
        :param semantic_rules: Semantic rules content.
        :param system_message: System message template.
        :param temperature: Temperature for the LLM.
        :param results_to_path: Path where the results will be saved.
        :param file_name_prefix: Prefix for the generated files.
        :param log_results: If True, the results will be saved to YAML files.
        :param log_summary: If True, a summary file will be created with the results.
        :return: files_generated: List of generated files,
                summary_text: Summary of the processing with the model.
        """

        # Check for None values and raise exception if any are missing
        if any(
            v is None
            for v in [
                all_questions,
                semantic_rules,
                system_message,
                models_configs,
                models,
                baseline_datasets,
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

        for model in models:

            print(f"\nProcessing questions with model {model}, temperature {temperature}")

            model_id = model["id"]
            if model_id is None or model_id == "":
                raise ValueError(f"Model {model_id} not found in the variable model.")

            model_name = model["name"]
            if model_name is None or model_name == "":
                raise ValueError(f"Model {model_name} not found in the variable model.")

            model_config = next(
                (cfg for cfg in models_configs if cfg["id"] == model_id),
                None,
            )

            if model_config is None:
                raise ValueError(f"Model {model_id} not found in the variable model_config.")

            model_summary_text = self.question_processor.process_questions_with_model(
                questions=all_questions,
                baseline_datasets=baseline_datasets,
                model=model,
                model_config=model_config,
                system_message=system_message,
                semantic_rules=semantic_rules,
                temperature=temperature,
                max_tokens=10000,
            )

            if log_results:
                # save the results to a YAML file
                file_name = f"{results_to_path}/{file_name_prefix}_{model['name']}.yaml"
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
