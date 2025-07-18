from typing import Dict, Any, List
from abc import ABC, abstractmethod


class BaseLLM(ABC):
    """
    Abstract base class for all language models.
    """

    def __init__(self, name: str = None, config: Dict[str, Any] = None):
        """
        Initialize the language model.

        Args:
            name: Name of the model
            config: Configuration dictionary
        """
        self.name = name
        self.config = config or {}

        # Find model config in the configuration
        if "models" in self.config:
            self.model_config = next(
                (m for m in self.config["models"] if m["name"] == name), {}
            )
        else:
            # If no models in config, use the entire config as the model config
            self.model_config = self.config

    @abstractmethod
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
        pass
