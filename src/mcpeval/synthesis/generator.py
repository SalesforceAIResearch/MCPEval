from openai import OpenAI
import os
from typing import Dict, List, Any, Optional
import logging

# from mcpeval.synthesis.scenarios import Scenario, ScenarioLibrary, ScenarioNameDescFormat  # TODO: scenarios module not implemented yet

logger = logging.getLogger(__name__)


class LLMGenerator:
    """Base class for all generators."""

    def __init__(
        self,
        model_provider: str = "openai",
        model_name: str = "gpt-4o",
        model_temperature: float = 0.1,
        max_tokens: int = 1000,
        top_p: float = 0.95,
        api_key: Optional[str] = None,
    ):
        """Initialize the LLM generator.

        Args:
            model_provider: Provider of the LLM ("openai", etc.)
            model_name: Name of the model to use
            model_temperature: Temperature for model generation
            max_tokens: Maximum number of tokens to generate
            top_p: Top-p sampling parameter
            api_key: API key for the model provider (or None to use env vars)
        """
        self.model_provider = model_provider
        self.model_name = model_name
        self.model_temperature = model_temperature
        self.max_tokens = max_tokens
        self.top_p = top_p
        self.api_key = api_key
        self.llm = self._get_llm()

    def _get_llm(self):
        if self.model_provider == "openai":
            return OpenAI(api_key=self.api_key or os.getenv("OPENAI_API_KEY"))
        else:
            raise ValueError(f"Unsupported model provider: {self.model_provider}")

    def generate_unstructured_response(self, messages: List[Dict[str, Any]]) -> str:
        """Generate an unstructured response using the configured LLM."""
        if self.model_provider == "openai":
            completion = self.llm.chat.completions.create(
                model=self.model_name,
                messages=messages,
                max_tokens=self.max_tokens,
                temperature=self.model_temperature,
                top_p=self.top_p,
            )
            return completion.choices[0].message.content
        else:
            raise ValueError(f"Unsupported model provider: {self.model_provider}")


