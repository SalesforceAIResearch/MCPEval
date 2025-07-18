from typing import Dict, Any, List


def prepare_chat_prompt(sample: Dict[str, Any]) -> Dict[str, Any]:
    """
    Prepare a standard chat prompt format from a sample.
    This is useful for LLMs that follow the chat completion interface.

    Args:
        sample: Sample from the dataset

    Returns:
        Prepared prompt with messages and optional tools
    """
    prompt = {
        "messages": [
            {
                "role": "system",
                "content": sample.get("system_prompt", "You are a helpful assistant."),
            },
            {"role": "user", "content": sample.get("user_prompt", "")},
        ]
    }

    # Handle case when messages are provided directly
    if "messages" in sample:
        prompt["messages"] = sample["messages"]

    # Add any additional context or tools from the sample
    if "context" in sample:
        prompt["context"] = sample["context"]

    if "tools" in sample:
        prompt["tools"] = sample["tools"]

    return prompt
