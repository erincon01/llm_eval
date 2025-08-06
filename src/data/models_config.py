import os
from typing import Any, Dict, List, Tuple

import yaml
from dotenv import load_dotenv


class ModelsConfig:
    """
    Handles loading and management of model configurations from YAML files.
    Loads sensitive credentials (endpoints and API keys) from environment variables.
    Extracted from LLMsEvaluator.__load_models_from_yaml()
    """

    def __init__(self, yaml_path: str):
        self.yaml_path = yaml_path
        self.models_configs = []
        self.models = []
        # Load environment variables
        load_dotenv()

    def load_models_from_yaml(self) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        Loads enabled model configurations and models from a YAML file.
        Credentials (endpoint and api_key) are loaded from environment variables.

        Returns:
            - models_configs: list of enabled providers with full
            config and filtered models
            - models: flat list of enabled models with id, name,
            and token costs
        Raises:
            Exception: If the YAML file cannot be loaded or is
            missing required fields, or if credentials are missing for enabled providers.
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

            if "id" not in provider:
                raise Exception(f"Provider config missing required 'id' field: {provider}")

            # Load credentials from environment variables
            endpoint, api_key = self._load_credentials_from_env(provider["id"])
            
            # Check if credentials are available
            if not endpoint or not api_key:
                env_id = provider["id"].replace('-', '_')
                missing_vars = []
                if not endpoint:
                    missing_vars.append(f"ENDPOINT_{env_id}")
                if not api_key:
                    missing_vars.append(f"API_KEY_{env_id}")
                
                raise Exception(
                    f"Missing environment variables for enabled provider '{provider['id']}': "
                    f"{', '.join(missing_vars)}"
                )

            if "models" not in provider:
                raise Exception(f"Provider config missing 'models' field: {provider}")

            # Load credentials from environment variables
            endpoint, api_key = self._load_credentials_from_env(provider["id"])
            if endpoint and api_key:
                provider["endpoint"] = endpoint
                provider["api_key"] = api_key

            enabled_models = []
            for model in provider.get("models", []):
                if model.get("enabled", True):
                    if "name" not in model:
                        raise Exception(f"Model config missing 'name': {model}")
                    # Add token costs and platform to the model
                    model["cost_input_tokens_EUR_1K"] = model.get(
                        "cost_input_tokens_EUR_1K", 0.0
                    )
                    model["cost_output_tokens_EUR_1K"] = model.get(
                        "cost_output_tokens_EUR_1K", 0.0
                    )
                    # Default to azure_openai for backward compatibility
                    model["platform"] = model.get("platform", "azure_openai")
                    enabled_models.append(model)
                    models.append(
                        {
                            "id": provider["id"],
                            "name": model["name"],
                            "platform": model["platform"],
                            "cost_input_tokens_EUR_1K": model[
                                "cost_input_tokens_EUR_1K"
                            ],
                            "cost_output_tokens_EUR_1K": model[
                                "cost_output_tokens_EUR_1K"
                            ],
                        }
                    )

            if enabled_models:
                config = {
                    "id": provider["id"],
                    "endpoint": endpoint,
                    "api_key": api_key,
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

    def _load_credentials_from_env(self, config_id: str) -> Tuple[str, str]:
        """
        Load endpoint and API key from environment variables.

        Args:
            config_id: The provider configuration ID

        Returns:
            Tuple of (endpoint, api_key) or (None, None) if not found
        """
        # Convert hyphens to underscores for environment variable names
        env_id = config_id.replace('-', '_')

        endpoint_var = f"ENDPOINT_{env_id}"
        api_key_var = f"API_KEY_{env_id}"

        endpoint = os.getenv(endpoint_var)
        api_key = os.getenv(api_key_var)

        return endpoint, api_key

    def validate_environment_variables(self) -> List[str]:
        """
        Validate that all required environment variables are present
        for enabled configurations.
        
        Returns:
            List of missing environment variable names
        """
        try:
            with open(self.yaml_path, "r", encoding="utf-8") as f:
                raw = yaml.safe_load(f)
        except Exception:
            return ["Error reading YAML file"]

        missing_vars = []
        raw_configs = raw.get("models_configs", [])
        
        for provider in raw_configs:
            if provider.get("enabled", True) and "id" in provider:
                endpoint, api_key = self._load_credentials_from_env(
                    provider["id"]
                )
                env_id = provider["id"].replace('-', '_')
                
                if not endpoint:
                    missing_vars.append(f"ENDPOINT_{env_id}")
                if not api_key:
                    missing_vars.append(f"API_KEY_{env_id}")
        
        return missing_vars
