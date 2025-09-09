import os


class OpenAIWrapper:
    """Wrapper for OpenAI API to match BaseLLM interface."""

    def __init__(
        self, model="gpt-4o", api_key=None, base_url=None, model_config=None, **kwargs
    ):
        from openai import OpenAI

        # If model_config is provided, use it for configuration
        if model_config is not None:
            # Extract client-specific parameters
            client_api_key = (
                model_config.get("api_key") or api_key or os.getenv("OPENAI_API_KEY")
            )
            client_base_url = model_config.get("base_url") or base_url

            # Use model from config if provided
            self.model = model_config.get("model", model)

            # Store only the chat completion parameters from config
            self.chat_params = {
                k: v
                for k, v in model_config.items()
                if k not in ["api_key", "base_url", "model"]
            }
        else:
            # Fallback to individual parameters
            client_api_key = api_key or os.getenv("OPENAI_API_KEY")
            client_base_url = base_url
            self.model = model
            self.chat_params = {}

        # Filter out None values from kwargs to avoid passing them to OpenAI client
        client_kwargs = {k: v for k, v in kwargs.items() if v is not None}
        if client_base_url is not None:
            client_kwargs["base_url"] = client_base_url

        self.client = OpenAI(api_key=client_api_key, **client_kwargs)

    def chat_completion(self, messages, tools=None, **kwargs):
        """Create a chat completion with OpenAI API."""
        # Merge stored chat parameters with any kwargs passed to this method
        # kwargs take precedence over stored config
        chat_kwargs = {**self.chat_params, **kwargs}

        # Temporary model-specific parameter normalization
        # Some newer models (e.g., GPT-5 family) expect 'max_completion_tokens'
        # instead of 'max_tokens'. Normalize when needed to avoid API errors.
        if "max_tokens" in chat_kwargs and isinstance(self.model, str):
            normalized_model = self.model.lower()
            if normalized_model.startswith("gpt-5"):
                # Map and remove the legacy key
                chat_kwargs["max_completion_tokens"] = chat_kwargs.pop("max_tokens")

        response = self.client.chat.completions.create(
            model=self.model, messages=messages, tools=tools, **chat_kwargs
        )

        # Convert to dict format expected by evaluator
        return {
            "choices": [
                {
                    "message": {
                        "role": response.choices[0].message.role,
                        "content": response.choices[0].message.content,
                        "tool_calls": [
                            {
                                "id": tc.id,
                                "type": tc.type,
                                "function": {
                                    "name": tc.function.name,
                                    "arguments": tc.function.arguments,
                                },
                            }
                            for tc in (response.choices[0].message.tool_calls or [])
                        ],
                    }
                }
            ]
        }
