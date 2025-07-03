#!/usr/bin/env python
import json
from typing import Dict, List, Any, Optional
import os
import hashlib
import uuid

def convert_to_xlam_format(task_data: Dict[str, Any], prefix: str = "", split: str = "train", 
                          system_message: str = "You are a helpful assistant that can use tools to complete tasks.",
                          index: Optional[int] = None) -> Dict[str, Any]:
    """
    Convert task results to XLAM required format.
    
    The format follows the required structure with only the specified fields.
    
    Args:
        task_data: Dictionary containing the task data
        prefix: Prefix to use for the unique_trajectory_id (e.g., 'airbnb')
        split: Dataset split (train, test, val)
        system_message: System message to use as system message and task_instruction if not provided
        index: Optional index to use as the final part of the unique_trajectory_id
        
    Returns:
        Dictionary formatted to XLAM requirements
    """
    # Extract key information
    description = task_data.get("description", "")
    tools = task_data.get("tools", [])
    conversation = task_data.get("conversation", [])
    
    # Generate a unique trajectory ID
    if index is not None:
        # Use the provided index
        task_id = str(index)
    else:
        # Use task_id from data or generate one
        task_id = task_data.get("task_id", "")
        if not task_id:
            # If no task_id exists, generate one based on the content hash or random
            if description:
                content_hash = hashlib.md5(description.encode()).hexdigest()[:3]
            else:
                content_hash = uuid.uuid4().hex[:3]
            task_id = content_hash
    
    # Create unique trajectory ID with the provided prefix and split
    unique_trajectory_id = f"{prefix}---{split}---{task_id}"
    
    # Use system_message as task_instruction
    task_instruction = system_message
    
    # Create formatted conversation
    formatted_conversation = []
    
    # Always add a system message with the system_message
    formatted_conversation.append({
        "role": "system",
        "content": system_message
    })

    # Make sure the first user message includes the description
    user_message_found = False
    
    for message in conversation:
        if message.get("role") == "system":
            # Skip system message from original conversation
            # as we're using the system_message as system message
            continue
            
        # Start with the original message structure
        formatted_message = {
            "role": message.get("role")
        }
        
        # Handle different message types based on role
        if message.get("role") == "user":
            # For user messages, use description for the first one, otherwise keep original content
            if not user_message_found:
                formatted_message["content"] = description
                user_message_found = True
            else:
                formatted_message["content"] = message.get("content", "")
                
        elif message.get("role") == "assistant":
            # For assistant messages, preserve content and tool_calls
            formatted_message["content"] = message.get("content", "")
            
            # Preserve tool_calls if they exist
            if message.get("tool_calls"):
                formatted_message["tool_calls"] = message.get("tool_calls")
                
        elif message.get("role") == "tool":
            # For tool messages, preserve name, content, and tool_call_id
            formatted_message["content"] = message.get("content", "")
            
            # Add tool name if present
            if message.get("name"):
                formatted_message["name"] = message.get("name")
                
            # Add tool_call_id if present
            if message.get("tool_call_id"):
                formatted_message["tool_call_id"] = message.get("tool_call_id")
        else:
            # For any other role, preserve content
            formatted_message["content"] = message.get("content", "")
        
        # Add the formatted message to conversation
        # Include messages that have content, tool_calls, or are tool messages
        if (formatted_message.get("content") or 
            formatted_message.get("tool_calls") or 
            formatted_message.get("role") == "tool"):
            formatted_conversation.append(formatted_message)
    
    # If no user message was found in the conversation, add one with the description
    if not user_message_found:
        formatted_conversation.insert(0, {
            "role": "user",
            "content": description
        })
    
    # Create the final XLAM format with only the required fields
    xlam_format = {
        "unique_trajectory_id": unique_trajectory_id,
        "task_instruction": task_instruction,
        "format_instruction": task_data.get("format_instruction", None),
        "few_shot_examples": task_data.get("few_shot_examples", None),
        "tools": tools,
        "conversation": formatted_conversation
    }
    
    return xlam_format

def extract_task_from_evaluation_results(eval_results: Dict[str, Any], task_id: str) -> Dict[str, Any]:
    """
    Extract a specific task from evaluation results based on task_id.
    
    Args:
        eval_results: Dictionary containing evaluation results
        task_id: ID of the task to extract
        
    Returns:
        Task data for the specified task ID
    """
    # Look for the task in task_results
    task_results = eval_results.get("task_results", [])
    for task_result in task_results:
        if task_result.get("task_id") == task_id:
            return task_result
    
    # If not found, return empty dict
    return {}

def process_file(input_path: str, output_path: str, task_id: Optional[str] = None, 
                prefix: str = "", split: str = "train", 
                system_message: str = "You are a helpful assistant that can use tools to complete tasks."):
    """
    Process a file containing task results and convert to XLAM format.
    
    Args:
        input_path: Path to input file containing task results
        output_path: Path to output file for XLAM format results
        task_id: Optional task ID to extract from evaluation results
        prefix: Prefix to use for the unique_trajectory_id
        split: Dataset split (train, test, val)
        system_message: System message to use as system message and task_instruction if not provided
    """
    try:
        # Load input data
        with open(input_path, 'r') as f:
            input_data = json.load(f)
        
        # Check if this is an evaluation_results.json file and a task_id is provided
        task_data = input_data
        if task_id and "task_results" in input_data:
            task_data = extract_task_from_evaluation_results(input_data, task_id)
            if not task_data:
                print(f"Task ID {task_id} not found in evaluation results")
                return
        
        # Convert to XLAM format
        xlam_data = convert_to_xlam_format(task_data, prefix, split, system_message)
        
        # Save output data
        with open(output_path, 'w') as f:
            json.dump(xlam_data, f, indent=2)
            
        print(f"Successfully converted {input_path} to XLAM format at {output_path}")
    
    except Exception as e:
        print(f"Error processing file: {e}")

def process_jsonl_file(input_path: str, output_file: str, prefix: str = "", 
                      split: str = "train",
                      system_message: str = "You are a helpful assistant that can use tools to complete tasks."):
    """
    Process a JSONL file containing multiple tasks and convert each to XLAM format.
    All tasks are output to a single JSON file.
    
    Args:
        input_path: Path to input JSONL file with tasks
        output_file: Path to output file for XLAM format data
        prefix: Prefix to use for the unique_trajectory_id
        split: Dataset split (train, test, val)
        system_message: System message to use as system message and task_instruction if not provided
    """
    try:
        # Read the JSONL file line by line
        tasks = []
        with open(input_path, 'r') as f:
            for i, line in enumerate(f):
                if not line.strip():
                    continue
                    
                try:
                    # Parse the JSON line
                    task_data = json.loads(line)
                    
                    # Convert to XLAM format with the line index
                    xlam_data = convert_to_xlam_format(task_data, prefix, split, system_message, 
                                                     index=i+1)
                    
                    # Add to list for single file output
                    tasks.append(xlam_data)
                    print(f"Converted task {i+1} with ID: {xlam_data.get('unique_trajectory_id')}")
                    
                except Exception as e:
                    print(f"Error processing line {i+1}: {e}")
        
        # If single file output, write all tasks to one file
        if tasks:
            with open(output_file, 'w') as f:
                json.dump(tasks, f, indent=2)
            print(f"Saved all {len(tasks)} tasks to {output_file}")
                    
        print(f"Finished processing {input_path}")
    
    except Exception as e:
        print(f"Error processing JSONL file: {e}") 