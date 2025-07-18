"""
Dataset module for loading and processing data for LLM evaluation.
"""

from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Union, Any, Iterator

import json


class DatasetFormat(Enum):
    """Supported dataset formats."""

    JSON = "json"
    JSONL = "jsonl"


class Dataset:
    """
    Simple dataset class for loading and accessing data.

    This class provides functionality to load datasets from JSON formats
    and access their contents.
    """

    def __init__(
        self,
        data_path: Optional[Union[str, Path]] = None,
        data_format: Optional[Union[str, DatasetFormat]] = None,
        data: Optional[Union[List[Dict[str, Any]], Dict[str, Any]]] = None,
    ):
        """
        Initialize a dataset.

        Args:
            data_path: Path to the dataset file. Not needed if data is provided directly.
            data_format: Format of the dataset file (JSON or JSONL).
            data: Data to use directly instead of loading from a file.
        """
        self._data = []

        # Convert string format to enum if needed
        if isinstance(data_format, str):
            try:
                data_format = DatasetFormat(data_format.lower())
            except ValueError:
                raise ValueError(f"Unsupported data format: {data_format}")

        # Load data from appropriate source
        if data is not None:
            # Data provided directly
            if isinstance(data, list):
                self._data = data
            elif isinstance(data, dict):
                self._data = [data]
            else:
                raise ValueError("Data must be a list of dictionaries or a dictionary")
        elif data_path is not None:
            # Load from file
            if data_format is None:
                # Try to infer format from file extension
                ext = Path(data_path).suffix.lower()[1:]  # Remove the dot
                try:
                    data_format = DatasetFormat(ext)
                except ValueError:
                    raise ValueError(
                        f"Could not infer data format from extension: {ext}"
                    )

            self._load_from_file(data_path, data_format)
        else:
            raise ValueError(
                "No data source specified. Provide either data or data_path"
            )

    def _load_from_file(
        self, data_path: Union[str, Path], data_format: DatasetFormat
    ) -> None:
        """Load data from a file with the specified format."""
        path = Path(data_path)
        if not path.exists():
            raise FileNotFoundError(f"Data file not found: {path}")

        if data_format == DatasetFormat.JSON:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, list):
                    self._data = data
                else:
                    self._data = [data]

        elif data_format == DatasetFormat.JSONL:
            self._data = []
            with open(path, "r", encoding="utf-8") as f:
                for line in f:
                    if line.strip():
                        self._data.append(json.loads(line))

        else:
            raise ValueError(f"Unsupported data format: {data_format}")

    def __len__(self) -> int:
        """Return the number of samples in the dataset."""
        return len(self._data)

    def __getitem__(
        self, idx: Union[int, slice]
    ) -> Union[Dict[str, Any], List[Dict[str, Any]]]:
        """Get a sample or samples from the dataset."""
        return self._data[idx]

    def __iter__(self) -> Iterator[Dict[str, Any]]:
        """Iterate through the dataset."""
        return iter(self._data)

    @property
    def data(self) -> List[Dict[str, Any]]:
        """Return the dataset as a list of dictionaries."""
        return self._data

    def save(
        self,
        output_path: Union[str, Path],
        format: Union[str, DatasetFormat] = DatasetFormat.JSON,
    ) -> None:
        """
        Save the dataset to a file.

        Args:
            output_path: Path to save the dataset to.
            format: Format to save the dataset in.
        """
        if isinstance(format, str):
            try:
                format = DatasetFormat(format.lower())
            except ValueError:
                raise ValueError(f"Unsupported data format: {format}")

        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)

        if format == DatasetFormat.JSON:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(self._data, f, ensure_ascii=False, indent=2)

        elif format == DatasetFormat.JSONL:
            with open(path, "w", encoding="utf-8") as f:
                for item in self._data:
                    f.write(json.dumps(item, ensure_ascii=False) + "\n")

        else:
            raise ValueError(f"Unsupported data format for saving: {format}")
