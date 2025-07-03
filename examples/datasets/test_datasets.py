#!/usr/bin/env python
"""
Test examples for using the LLMEvalDataset class with both message-based and tool-based data.
"""

import os
import json
import sys
from pathlib import Path

# Add the project root to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from mcp_eval_llm.commons import TaskType
from mcp_eval_llm.dataset import LLMEvalDataset

def main():
    """Run test examples with the unified LLMEvalDataset class."""
    # Path to example data
    data_path = Path("data")
    
    # Example 1: Create a message-based dataset using the unified class
    print("\n=== Example 1: Message-based Dataset using LLMEvalDataset ===")
    message_data_path = data_path / "message_samples" / "message_data.json"
    print(f"Message data path: {message_data_path}")
    message_dataset = LLMEvalDataset(
        task_type=TaskType.CHAT_BASED,
        data_path=message_data_path
    )
    
    print(f"Number of samples: {len(message_dataset)}")
    # Print example message
    sample_idx = 0
    print(f"\nExample message at index {sample_idx}:")
    messages = message_dataset.get_formatted_messages(sample_idx)
    for msg in messages:
        print(f"  {msg['role']}: {msg['content'][:50]}..." if len(msg['content']) > 50 else f"  {msg['role']}: {msg['content']}")
    
    # Example 2: Create a tool-based dataset using the unified class
    print("\n=== Example 2: Tool-based Dataset using LLMEvalDataset ===")
    tool_data_path = data_path / "tool_samples" / "tool_data.json"
    
    tool_dataset = LLMEvalDataset(
        task_type=TaskType.TOOL_BASED,
        data_path=tool_data_path
    )
    
    print(f"Number of samples: {len(tool_dataset)}")
    # Print example tool data
    sample_idx = 0
    print(f"\nExample at index {sample_idx}:")
    messages = tool_dataset.get_formatted_messages(sample_idx)
    for msg in messages:
        print(f"  {msg['role']}: {msg['content'][:50]}..." if msg['content'] and len(msg['content']) > 50 else f"  {msg['role']}: {msg['content']}")
    
    # Print tools
    tools = tool_dataset.get_tools(sample_idx)
    print("\nAvailable tools:")
    for tool in tools:
        print(f"  Tool: {tool['function']['name']} - {tool['function']['description']}")
    
    # Example 5: Create a new message-based dataset and save it
    print("\n=== Example 3: Creating and saving a new dataset ===")
    simple_messages = [
        {
            "messages": [
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "What is the capital of Japan?"}
            ],
            "reference": "The capital of Japan is Tokyo.",
            "criteria": {
                "accuracy": "high",
                "category": "geography"
            }
        },
        {
            "messages": [
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "Who wrote 'The Great Gatsby'?"}
            ],
            "reference": "The Great Gatsby was written by F. Scott Fitzgerald.",
            "criteria": {
                "accuracy": "high",
                "category": "literature"
            }
        }
    ]
    
    custom_dataset = LLMEvalDataset(
        task_type=TaskType.CHAT_BASED,
        data=simple_messages
    )
    
    # Filter by metadata
    literature_dataset = custom_dataset.filter_by_metadata("category", "literature")
    print(f"Filtered dataset has {len(literature_dataset)} samples")
    
    # Save to file
    output_path = data_path / "custom_test_dataset.json"
    custom_dataset.save(output_path)
    print(f"Dataset saved to {output_path}")
    
    # Example 6: Create a new tool-based dataset and save it
    print("\n=== Example 4: Creating and saving a new tool-based dataset ===")
    simple_tool_data = [
        {
            "messages": [
                {"role": "system", "content": "You are a helpful assistant with tools."},
                {"role": "user", "content": "Convert 100 USD to EUR"}
            ],
            "tools": [
                {
                    "type": "function",
                    "function": {
                        "name": "convert_currency",
                        "description": "Convert an amount from one currency to another",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "amount": {"type": "number"},
                                "from_currency": {"type": "string"},
                                "to_currency": {"type": "string"}
                            },
                            "required": ["amount", "from_currency", "to_currency"]
                        }
                    }
                }
            ],
            "reference_tool_calls": [
                {
                    "tool_name": "convert_currency",
                    "tool_parameters": {
                        "amount": 100,
                        "from_currency": "USD",
                        "to_currency": "EUR"
                    }
                }
            ],
            "criteria": {
                "category": "finance"
            }
        }
    ]
    
    custom_tool_dataset = LLMEvalDataset(
        task_type=TaskType.TOOL_BASED,
        data=simple_tool_data
    )
    
    # Save to file
    output_tool_path = data_path / "custom_test_tool_dataset.json"
    custom_tool_dataset.save(output_tool_path)
    print(f"Tool-based dataset saved to {output_tool_path}")
    
    # Cleanup test files
    cleanup_test_files(output_path, output_tool_path)

def cleanup_test_files(*paths):
    """Clean up test files created during the examples."""
    for path in paths:
        try:
            if path.exists():
                os.remove(path)
                print(f"Cleaned up test file: {path}")
        except Exception as e:
            print(f"Error cleaning up {path}: {e}")

if __name__ == "__main__":
    main() 