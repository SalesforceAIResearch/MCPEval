import os
import json
import logging
import uuid
import requests
from dotenv import load_dotenv
from typing import Dict, Any, List
from .base_llm import BaseLLM
from .utils import prepare_chat_prompt
from .parser import get_fixed_tool_calls_or_text_output


# Load environment variables from .env file
load_dotenv()

logger = logging.getLogger(__name__)


class APIBasedLLM(BaseLLM):
    """
    Implementation of an API-based model that can work with any API endpoint.
    Originally designed for XLAM model but can be used for any API-based inference.
    """

    def __init__(self, name: str = None, config: Dict[str, Any] = None):
        """
        Initialize the API-based model.

        Args:
            name: Name of the model
            config: Configuration dictionary
        """
        super().__init__(name=name, config=config)

        # Get API key from environment - check both formats
        self.api_key = os.getenv("X_API_KEY") or os.getenv("X-Api-Key")

        # Validate API key is provided
        if not self.api_key:
            raise ValueError(
                "API key environment variable is required but not set. "
                "Please set your API key using one of these formats:\n"
                "  export X_API_KEY='your-api-key-here'  (recommended for shell)\n"
                "  or add X-Api-Key=your-api-key-here to your .env file"
            )

        # Get API endpoint
        self.api_endpoint = self.model_config.get("api_endpoint", None)
        if not self.api_endpoint:
            raise ValueError(
                "API endpoint is required but not set. Please set the api_endpoint in the model config."
            )

        # Model parameters
        self.temperature = self.model_config.get("temperature", 0.1)
        self.max_tokens = self.model_config.get("max_tokens", 1000)
        self.parallel_tool_calls = self.model_config.get("parallel_tool_calls", False)

    def _generate(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Private method to generate a response using the API-based model.

        Args:
            input_data: Input data containing messages and optional tools

        Returns:
            Model response
        """
        prepared_prompt = prepare_chat_prompt(input_data)
        messages = prepared_prompt["messages"]

        # Prepare request data
        request_data = {
            "prompts": messages,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
            "parallel_tool_calls": self.parallel_tool_calls,
        }

        # Add tools if available
        if "tools" in prepared_prompt:
            request_data["tools"] = prepared_prompt["tools"]
        try:
            logger.debug(f"Sending request to API endpoint: {json.dumps(request_data)}")

            # Make the API request
            response = requests.post(
                self.api_endpoint,
                headers={"Content-Type": "application/json", "X-Api-Key": self.api_key},
                json=request_data,
            )

            response.raise_for_status()
            output = response.json()
            logger.debug(f"Received response from API endpoint: {json.dumps(output)}")

            # Extract the model's response
            model_output = output["result"][0]
            try:
                model_output, label = get_fixed_tool_calls_or_text_output(model_output)
            except Exception as e:
                logger.error(f"Error parsing model output: {str(e)}")
                label = "api_text_output"
                model_output = model_output
            logger.debug(f"Formatted model output: {model_output}, label: {label}")
            # Format response in OpenAI-like structure for compatibility
            formatted_response = {
                "id": f"api-{self.name}-{uuid.uuid4()}",  # Unique ID for the response
                "object": "chat.completion",
                "created": int(response.elapsed.total_seconds()),
                "model": self.name,
                "choices": [{"index": 0, "message": {}, "finish_reason": "stop"}],
                "usage": {
                    "prompt_tokens": -1,  # Not provided by API
                    "completion_tokens": -1,  # Not provided by API
                    "total_tokens": -1,  # Not provided by API
                },
            }

            # Process output based on type (text or tool calls)
            if label == "api_text_output":
                formatted_response["choices"][0]["message"] = {
                    "role": "assistant",
                    "content": model_output,
                }
            elif label == "api_tool_calls":
                # Handle tool calls in OpenAI-like format
                if isinstance(model_output, list):
                    # Convert API tool call format to OpenAI format
                    openai_tool_calls = []
                    for idx, tool_call in enumerate(model_output):
                        # Create an OpenAI-style tool call with required fields
                        openai_tool_call = {
                            "id": f"call_{uuid.uuid4()}",
                            "type": "function",
                            "function": {
                                "name": tool_call.get("name", ""),
                                "arguments": json.dumps(tool_call.get("arguments", {})),
                            },
                        }
                        openai_tool_calls.append(openai_tool_call)

                    formatted_response["choices"][0]["message"] = {
                        "role": "assistant",
                        "content": None,
                        "tool_calls": openai_tool_calls,
                    }
                else:
                    # Fallback if structure is unexpected
                    logger.warning(f"Unexpected tool calls format: {model_output}")
                    formatted_response["choices"][0]["message"] = {
                        "role": "assistant",
                        "content": str(model_output),
                    }

            return formatted_response

        except Exception as e:
            logger.error(f"Error generating response with API-based model: {str(e)}")
            return {"error": str(e)}

    def chat_completion(
        self,
        messages: List[Dict[str, Any]],
        tools: List[Dict[str, Any]] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Create a chat completion with OpenAI-like interface.
        This is the primary interface for interacting with the model.

        Args:
            messages: List of messages
            tools: List of tools
            **kwargs: Additional parameters

        Returns:
            Chat completion response in a standardized format
        """
        # Prepare the prompt
        prompt = {"messages": messages}

        if tools:
            prompt["tools"] = tools

        # Add any additional parameters
        for key, value in kwargs.items():
            if value is not None:
                prompt[key] = value

        # Generate the response
        return self._generate(prompt)
