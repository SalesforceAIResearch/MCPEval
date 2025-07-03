import json
import os
import uuid
import logging
from typing import List

from ..commons.types import Task

logger = logging.getLogger(__name__)


def extract_content_from_mcp_result(result) -> str:
    """
    Extract string content from MCP result.
    
    Args:
        result: MCP result which may have complex structure
        
    Returns:
        str: Extracted content as string
    """
    try:
        # Handle different result formats
        if hasattr(result, 'content'):
            content = result.content
            if isinstance(content, str):
                return content
            elif isinstance(content, list) and len(content) > 0:
                # Handle list of content objects
                if hasattr(content[0], 'text'):
                    return content[0].text
                elif isinstance(content[0], dict) and 'text' in content[0]:
                    return content[0]['text']
                else:
                    return str(content[0])
            else:
                return str(content)
        else:
            return str(result)
    except Exception as e:
        logger.warning(f"Error extracting content from MCP result: {e}")
        return str(result)


def append_task_to_jsonl(task: Task, file_path: str, create_if_not_exists: bool = True) -> None:
    """
    Append a Task object to a JSONL file.
    
    Args:
        task: The Task object to append
        file_path: Path to the JSONL file
        create_if_not_exists: If True, create the file if it doesn't exist
    
    Raises:
        FileNotFoundError: If the file doesn't exist and create_if_not_exists is False
        IOError: If there's an error writing to the file
    """
    # Create directory if it doesn't exist
    directory = os.path.dirname(file_path)
    if directory and not os.path.exists(directory):
        os.makedirs(directory)
    
    # Check if file exists
    file_exists = os.path.exists(file_path)
    if not file_exists and not create_if_not_exists:
        raise FileNotFoundError(f"File {file_path} does not exist and create_if_not_exists is False")
    
    # Convert task to dictionary
    task_dict = task.model_dump()
    
    # Append to file
    try:
        with open(file_path, 'a') as f:
            f.write(json.dumps(task_dict) + '\n')
    except IOError as e:
        raise IOError(f"Error writing to file {file_path}: {str(e)}")

def load_tasks_from_jsonl(file_path: str) -> List[Task]:
    """
    Load tasks from a JSONL file.
    
    If a task doesn't have an id field, one will be automatically generated.
    """
    tasks = []
    with open(file_path, 'r') as f:
        for line in f:
            task_data = json.loads(line)
            # Set a UUID for the task if it doesn't have an id
            tasks.append(Task(**task_data))  
    return tasks    