import os
import time
import traceback

# anthropic
import anthropic
import tiktoken

# gemini
from azure.ai.inference import ChatCompletionsClient
from azure.core.credentials import AzureKeyCredential

# from openai import AzureOpenAI -- previous import statement without langfuse
from langfuse import get_client, observe
from langfuse.openai import AzureOpenAI

# pip install langfuse anthropic google-cloud-aiplatform


@observe(capture_input=False, capture_output=True)
def get_chat_completion_from_platform(
    platform,
    model,
    system_message,
    user_prompt,
    temperature,
    tokens,
    langfuse_enabled=True,
    **model_config,
):
    """
    Retrieves a chat completion from Azure OpenAI API.
    Args:
        platform (str): The platform to use for generating chat completions.
            Either "azure_openai" or "deepseek". deepseek is deprecated.
        If the model starts with "claude-", it will use the Anthropic API.
        model (str): The model to use for generating chat completions.
        system_message (str): The system message.
        user_prompt (str): The user prompt.
        temperature (float): The temperature value for generating chat completions.
        tokens (int): The maximum number of tokens for generating chat completions.
        langfuse_enabled (bool): Whether to enable Langfuse integration.
        model_config (dict): Additional model configuration parameters (id, endpoint, api_key).
    Returns:
        str: The generated chat completion.
        metadata_json (dict): A dictionary containing tokens usage and duration of the call.
            the json object should have endpoint and api_key
    Raises:
        ValueError: If the platform is not supported or if required environment variables are not set.
        RuntimeError: If there is an error retrieving chat completion from the API.
    """

    if model.startswith("claude-") or model.startswith("claude2-") or model.startswith("claude3-"):
        platform = "anthropic"

    endpoint = None
    api_key = None
    api_version = "2023-05-15"
    metadata_json = {}

    # Desanidar si es necesario
    if "model_config" in model_config and isinstance(model_config["model_config"], dict):
        model_config = {**model_config, **model_config["model_config"]}

    metadata = {k: v for k, v in model_config.items() if k not in {"id", "endpoint", "api_key"}}

    if platform == "azure_openai":

        if model_config is None:
            model_config = {}

        # Extraer valores con fallback a variables de entorno
        endpoint = model_config.get("endpoint") or os.getenv("OPENAI_ENDPOINT")
        api_key = model_config.get("api_key") or os.getenv("OPENAI_KEY")

        if model is None:
            model = os.getenv("OPENAI_MODEL")

        # from azure openai documentation
        if model.startswith("gpt-4.1") or model.startswith("gpt-4o") or model == "o3-mini" or model == "o4-mini":
            api_version = "2024-12-01-preview"

        if model == "DeepSeek-V3-0324" or model.startswith("Phi-") or model.startswith("grok-"):
            api_version = "2024-05-01-preview"

        if model.startswith("Codestral-") or model.startswith("Mistral-") or model.startswith("Ministral-"):
            api_version = "2024-05-01-preview"

        if model.startswith("Llama-"):
            api_version = "2024-05-01-preview"

        if "-4k-" in model and tokens > 4096:
            tokens = 4096
        elif "-8k-" in model and tokens > 8192:
            tokens = 8192

        if model == "Ministral-3B":
            tokens = 2048

        try:
            client = AzureOpenAI(
                azure_endpoint=endpoint,
                api_key=api_key,
                api_version=api_version,
            )

            start = time.time()

            # Use 'max_completion_tokens' for 'o3-mini' and 'o4-mini', otherwise use 'max_tokens'
            completion_param = (
                {"max_completion_tokens": tokens} if model in ["o3-mini", "o4-mini"] else {"max_tokens": tokens}
            )

            optional_args = {"metadata": metadata, **completion_param}
            if model not in ["o3-mini", "o4-mini"]:
                optional_args["temperature"] = temperature

            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": user_prompt},
                ],
                **optional_args,
            )

            output = response.choices[0].message.content
            output = output.replace("\n\n", "\n").replace("\n\n", "\n")

            total_tokens = response.usage.total_tokens
            prompt_tokens = response.usage.prompt_tokens
            completion_tokens = response.usage.completion_tokens

            duration = time.time() - start
            duration = round(duration, 2)

            # put the metadata in a json object
            metadata_json = {
                "total_tokens": total_tokens,
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
                "duration": duration,
            }

            if langfuse_enabled:

                langfuse = get_client()
                langfuse.update_current_trace(tags=["azure_openai_call", "qa"])
                langfuse.update_current_span(
                    metadata={
                        "platform": platform,
                        "model": model,
                        "duration": duration,
                        "total_tokens": total_tokens,
                        "prompt_tokens": prompt_tokens,
                        "completion_tokens": completion_tokens,
                    }
                )

            return output, metadata_json

        except Exception as e:
            raise RuntimeError(f"Error retrieving chat completion from Azure OpenAI API: {str(e)}") from e

    if platform == "anthropic":

        # Extraer valores con fallback a variables de entorno
        endpoint = model_config.get("endpoint")
        api_key = model_config.get("api_key")

        client = anthropic.Anthropic(api_key=api_key)

        if "claude-3-5" in model and tokens > 8192:
            tokens = 8192

        try:

            prompt = f"{system_message.strip()}\n\n{user_prompt.strip()}\n\n"

            start = time.time()
            response = client.messages.create(
                model=model,
                max_tokens=tokens,
                messages=[{"role": "user", "content": prompt}],
            )
            output = response.content[0].text

            prompt_tokens = 0
            completion_tokens = 0
            total_tokens = 0

            usage = getattr(response, "usage", None)
            if usage:
                prompt_tokens = usage.input_tokens
                completion_tokens = usage.output_tokens
                total_tokens = prompt_tokens + completion_tokens
            else:
                prompt_tokens = completion_tokens = total_tokens = None

            duration = round(time.time() - start, 2)

            metadata_json = {
                "total_tokens": total_tokens,
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
                "duration": duration,
            }

            if langfuse_enabled:
                langfuse = get_client()
                langfuse.update_current_trace(tags=["anthropic_call", "qa"])
                langfuse.update_current_span(
                    metadata={
                        "platform": platform,
                        "model": model,
                        "duration": duration,
                        "total_tokens": total_tokens,
                        "prompt_tokens": prompt_tokens,
                        "completion_tokens": completion_tokens,
                    }
                )

            return output, metadata_json

        except Exception as e:
            raise RuntimeError(f"Error retrieving chat completion from Azure OpenAI API: {str(e)}") from e

    if platform == "deepseek":

        endpoint = os.getenv("DEEKSEEK_ENDPOINT")
        api_key = os.getenv("DEEKSEEK_KEY")
        if model is None:
            model = os.getenv("DEEKSEEK_MODEL")

        try:
            client = ChatCompletionsClient(endpoint, AzureKeyCredential(api_key))

            start = time.time()

            response = client.complete(
                model=model,
                messages=[
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=temperature,
                max_tokens=tokens,
            )

            duration = time.time() - start
            duration = round(duration, 2)

            output = response.choices[0].message.content
            output = output.replace("\n\n", "\n").replace("\n\n", "\n")

            # put the metadata in a json object
            metadata_json = {
                "total_tokens": 0,
                "prompt_tokens": 0,
                "completion_tokens": 0,
                "duration": duration,
            }

            if langfuse_enabled:
                langfuse = get_client()
                langfuse.update_current_trace(
                    tags=["deepseek_call", "qa"], metadata={"platform": platform, "model": model}
                )

            return output, metadata_json

        except Exception as e:
            tb = traceback.format_exc()
            return f"Error retrieving chat completion from DeepSeek API: {str(e)}\n{tb}"

    if endpoint is None or api_key is None or model is None:
        raise ValueError("Please set the relevant platform environment variables.")


def count_tokens(prompt):
    """
    Counts the number of tokens in the given prompt.
    Parameters:
    prompt (str): The prompt to count tokens from.
    Returns:
    int: The number of tokens in the prompt.
    """

    encoder = tiktoken.get_encoding("cl100k_base")
    tokens = encoder.encode(prompt)

    return len(tokens)
