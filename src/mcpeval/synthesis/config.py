from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional, Union, Literal
from pathlib import Path


class GeneratorConfig(BaseModel):
    """Configuration parameters for synthetic dataset generation."""

    # General configuration
    output_path: Path = Field(
        ..., description="Path where the generated dataset will be saved"
    )
    dataset_format: Literal["json", "jsonl"] = Field(
        "jsonl", description="Format of the output dataset file"
    )
    num_samples: int = Field(100, description="Number of samples to generate", ge=1)
    # Model configuration for reference generation
    model_provider: str = Field(
        "openai", description="Provider of the LLM for generation"
    )
    model_name: str = Field(
        "gpt-4o", description="Name of the model to use for generation"
    )
    model_temperature: float = Field(
        0.1, description="Temperature for the model generation", ge=0.0, le=2.0
    )
    max_tokens: int = Field(1000, description="Maximum number of tokens to generate")
    api_key: Optional[str] = Field(None, description="API key for the model provider")
    top_p: float = Field(
        0.95, description="Top-p for the model generation", ge=0.0, le=1.0
    )
