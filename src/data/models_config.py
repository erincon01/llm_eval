from typing import Any, Dict, List, Tuple

import yaml


class ModelsConfig:
    """
    Handles loading and management of model configurations from YAML files.
    Extracted from LLMsEvaluator.__load_models_from_yaml()
    """

    def __init__(self, yaml_path: str):
        self.yaml_path = yaml_path
        self.models_configs = []
        self.models = []

    def load_models_from_yaml(self) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
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
            with open(self.yaml_path, "r", encoding="utf-8") as f:
                raw = yaml.safe_load(f)
        except Exception as e:
            raise Exception(f"Error loading YAML file '{self.yaml_path}': {e}")

        if not isinstance(raw, dict):
            raise Exception(f"YAML file '{self.yaml_path}' is not a valid dictionary.")

        raw_configs = raw.get("models_configs", [])
        if not isinstance(raw_configs, list):
            raise Exception(f"'models_configs' must be a list in '{self.yaml_path}'.")

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
            raise Exception(f"No enabled models found in '{self.yaml_path}'.")

        # Store in instance variables
        self.models_configs = models_configs
        self.models = models

        return models_configs, models

    def get_models_configs(self) -> List[Dict[str, Any]]:
        """Return the loaded models configurations"""
        return self.models_configs

    def get_models(self) -> List[Dict[str, Any]]:
        """Return the loaded models list"""
        return self.models

    def get_model_config_by_id(self, model_id: str) -> Dict[str, Any]:
        """Get model configuration by provider ID"""
        return next(
            (cfg for cfg in self.models_configs if cfg["id"] == model_id),
            None,
        )
