"""
Specialized dataset for LLM evaluation tasks.
"""

from typing import Dict, List, Optional, Union, Any
from pathlib import Path
import json
import copy

from .dataset import Dataset
from ..commons import OneStepChatBasedSample, OneStepToolBasedSample



class LLMEvalDataset(Dataset):
    """
    Unified dataset for evaluating LLMs on both message-based and tool-based tasks.
    
    This class can handle both simple message-based evaluations and more complex
    tool-based evaluations where the LLM needs to use tools to complete tasks.
    """
    
    def __init__(
        self,
        task_type: str = "tool",
        messages_key: str = "messages",
        tools_key: Optional[str] = "tools",
        reference_key: Optional[str] = "reference",
        reference_tool_calls_key: Optional[str] = "reference_tool_calls",
        **kwargs
    ):
        """
        Initialize an LLM evaluation dataset.
        
        Args:
            task_type: The type of task ("tool" or "chat").
            messages_key: Key in the data samples that contains the message array.
            tools_key: Key for the tools array in each sample (for tool-based tasks).
            reference_key: Key for optional reference/expected outputs.
            reference_tool_calls_key: Key for the expected tool calls (for tool-based tasks).
            **kwargs: Additional arguments to pass to the parent Dataset class.
        """
        super().__init__(**kwargs)
        self.task_type = task_type
        self.messages_key = messages_key
        self.tools_key = tools_key
        self.reference_key = reference_key
        self.reference_tool_calls_key = reference_tool_calls_key
        
        # Convert raw dict data to Pydantic models
        self._samples = []
        for i, sample_dict in enumerate(self._data):
            try:
                # Extract fields common to both sample types
                messages = sample_dict.get(self.messages_key, [])
                reference = sample_dict.get(self.reference_key)
                
                # Get criteria if present or use empty dict
                criteria = sample_dict.get("criteria", {})
                if not isinstance(criteria, dict):
                    criteria = {}
                
                # Add any additional metadata to criteria
                common_keys = [self.messages_key, self.reference_key, "criteria"]
                if self.task_type == "tool":
                    common_keys.extend([self.tools_key, self.reference_tool_calls_key])
                
                for key, value in sample_dict.items():
                    if key not in common_keys:
                        criteria[key] = value
                
                # Create validated Pydantic model based on task type
                if self.task_type == "chat":
                    validated_sample = OneStepChatBasedSample(
                        messages=messages,
                        reference=reference,
                        criteria=criteria if criteria else None
                    )
                else:  # Tool-based task
                    tools = sample_dict.get(self.tools_key, [])
                    reference_tool_calls = sample_dict.get(self.reference_tool_calls_key)
                    
                    validated_sample = OneStepToolBasedSample(
                        messages=messages,
                        tools=tools,
                        reference=reference,
                        reference_tool_calls=reference_tool_calls,
                        criteria=criteria if criteria else None
                    )
                
                self._samples.append(validated_sample)
            except Exception as e:
                raise ValueError(f"Failed to validate sample {i}: {str(e)}") from e
    
    def __len__(self) -> int:
        """Return the number of samples in the dataset."""
        return len(self._samples)
    
    def __getitem__(self, idx: Union[int, slice]) -> Union[Union[OneStepChatBasedSample, OneStepToolBasedSample], 
                                                        List[Union[OneStepChatBasedSample, OneStepToolBasedSample]]]:
        """Get a sample or samples from the dataset."""
        return self._samples[idx]
    
    def get_formatted_messages(self, idx: int) -> List[Dict[str, str]]:
        """Get the messages for a specific sample, formatted for API calls."""
        return [msg.model_dump() for msg in self._samples[idx].messages]
    
    def get_all_formatted_messages(self) -> List[List[Dict[str, str]]]:
        """Get all messages from the dataset, formatted for API calls."""
        return [[msg.model_dump() for msg in sample.messages] for sample in self._samples]
    
    def get_tools(self, idx: int) -> List[Dict[str, Any]]:
        """Get the tools for a specific sample (for tool-based tasks)."""
        if self.task_type != "tool":
            raise ValueError("Tools are only available for tool-based tasks")
        return [tool.model_dump() for tool in self._samples[idx].tools]
    
    def get_all_tools(self) -> List[List[Dict[str, Any]]]:
        """Get all tools from the dataset (for tool-based tasks)."""
        if self.task_type != "tool":
            raise ValueError("Tools are only available for tool-based tasks")
        return [[tool.model_dump() for tool in sample.tools] for sample in self._samples]
    
    def get_references(self) -> List[Optional[str]]:
        """Get all reference outputs from the dataset if available."""
        return [sample.reference for sample in self._samples]
    
    def get_reference_tool_calls(self) -> List[Optional[List[Dict[str, Any]]]]:
        """Get the reference tool calls if available (for tool-based tasks)."""
        if self.task_type != "tool":
            raise ValueError("Reference tool calls are only available for tool-based tasks")
        return [
            [call.model_dump() for call in sample.reference_tool_calls] if sample.reference_tool_calls else None 
            for sample in self._samples
        ]
        
    def get_metadata_value(self, key: str) -> List[Optional[Any]]:
        """Get values for a specific metadata key from all samples."""
        return [
            sample.criteria.get(key) if sample.criteria else None
            for sample in self._samples
        ]
    
    def prepare_inputs_for_api(self, idx: int) -> Dict[str, Any]:
        """
        Prepare inputs for API calls with messages and tools if applicable.
        
        Args:
            idx: Index of the sample to prepare.
            
        Returns:
            Dictionary with messages and tools (if tool-based) formatted for API calls.
        """
        if self.task_type == "chat":
            return {
                "messages": self.get_formatted_messages(idx)
            }
        else:
            return {
                "messages": self.get_formatted_messages(idx),
                "tools": self.get_tools(idx)
            }
        
    def filter(self, condition_fn) -> 'LLMEvalDataset':
        """Filter samples based on a condition function."""
        new_dataset = copy.deepcopy(self)
        new_dataset._samples = [s for s in self._samples if condition_fn(s)]
        return new_dataset
    
    def map(self, transform_fn) -> 'LLMEvalDataset':
        """Apply a transformation to each sample."""
        new_dataset = copy.deepcopy(self)
        new_dataset._samples = [transform_fn(s) for s in self._samples]
        return new_dataset
        
    def filter_by_metadata(self, key: str, value: Any) -> 'LLMEvalDataset':
        """Filter samples by a metadata key-value pair."""
        return self.filter(lambda s: s.criteria and s.criteria.get(key) == value)
        
    def to_dict(self):
        """Convert the dataset to a dictionary."""
        return {
            'task_type': self.task_type,
            'samples': [sample.model_dump() for sample in self._samples]
        }
        
    def save(self, path: Union[str, Path], format: str = 'json'):
        """Save the dataset to a file."""
        data = [sample.model_dump() for sample in self._samples]
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        
        if format.lower() == 'json':
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
        elif format.lower() == 'jsonl':
            with open(path, 'w', encoding='utf-8') as f:
                for sample in data:
                    f.write(json.dumps(sample) + '\n')
        else:
            raise ValueError(f"Unsupported format: {format}")

