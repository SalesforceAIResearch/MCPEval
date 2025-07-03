from pydantic import BaseModel, Field, ConfigDict
import logging
import random
import json
from typing import Dict, List, Any, Optional, Union

from ..commons.types import Task, ToolCall
from .tools import ToolDefinition, ToolLibrary, format_tools_for_prompt
from .generator import LLMGenerator
from ..commons.prompts import (task_generation_system_prompt, task_generation_with_tools_user_prompt,
                       task_revision_system_prompt, task_revision_user_prompt)
from .utils import append_task_to_jsonl, load_tasks_from_jsonl
logger = logging.getLogger(__name__)


class TaskFormat(BaseModel):
    """Format for generating task descriptions."""
    name: str = Field(..., description="Name of the task")
    description: str = Field(..., description="Description of the task")
    tool_calls: List[ToolCall] = Field(
        default_factory=list,
        description="Expected tool calls for this task"
    )
    goal: str = Field(..., description="Goal of the task")

class TaskGenerator:
    """Generator for creating tool use tasks."""
    
    def __init__(
        self, 
        tool_library: ToolLibrary,
        model_provider: str = "openai",
        model_name: str = "gpt-4.1-2025-04-14",
        model_temperature: float = 0.1,
        max_tokens: int = 1000,
        top_p: float = 0.95,
        api_key: Optional[str] = None,
        system_message: Optional[str] = None,
        existing_tasks: Optional[List[Task]] = None,
        *args,
        **kwargs
    ):
        """Initialize the task generator.

        Args:
            tool_library: Library of tool definitions
            scenario_library: Optional library of scenarios
            model_provider: Provider of the LLM
            model_name: Name of the model to use
            model_temperature: Temperature for model generation
            max_tokens: Maximum number of tokens to generate
            top_p: Top-p sampling parameter
            api_key: API key for the model provider
            system_message: Optional system message for the LLM
            existing_tasks: Optional list of existing tasks
        """
        self.tool_library = tool_library
        self.llm_generator = LLMGenerator(
            model_provider=model_provider,
            model_name=model_name,
            model_temperature=model_temperature,
            max_tokens=max_tokens,
            top_p=top_p,
            api_key=api_key,
            *args,
            **kwargs
        )
        
        self.system_message = system_message or task_generation_system_prompt
        self.existing_tasks = existing_tasks or []
    
    def _parse_json_with_retry(self, raw_response: str, messages: Optional[List[Dict[str, Any]]] = None, max_retries: int = 5):
        """Parse JSON from a string with retries and cleanup for malformed responses.
        
        Args:
            raw_response: The string containing JSON to parse
            messages: Optional list of message objects to use for retrying with the LLM
            max_retries: Maximum number of retries before giving up
            
        Returns:
            Parsed JSON data or None if parsing failed
        """
        task_data = None
        retry_count = 0
        current_response = raw_response
        
        while task_data is None and retry_count < max_retries:
            try:
                # First attempt: direct JSON parsing
                task_data = json.loads(current_response)
            except json.JSONDecodeError:
                # Second attempt: try to extract JSON from markdown code blocks
                try:
                    import re
                    json_match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', current_response)
                    if json_match:
                        json_str = json_match.group(1).strip()
                        # Try to parse the extracted JSON
                        try:
                            task_data = json.loads(json_str)
                        except json.JSONDecodeError:
                            # Third attempt: try to clean up common JSON issues
                            # Remove comments
                            cleaned_json = re.sub(r'//.*?$', '', json_str, flags=re.MULTILINE)
                            # Remove trailing commas
                            cleaned_json = re.sub(r',\s*([}\]])', r'\1', cleaned_json)
                            try:
                                task_data = json.loads(cleaned_json)
                            except json.JSONDecodeError:
                                # If still failing, continue with retry logic
                                pass
                    
                    # If we can't extract or parse JSON and messages are provided, retry with the LLM
                    if task_data is None and messages and retry_count < max_retries - 1:
                        logger.info(f"Retrying JSON generation (attempt {retry_count+1}/{max_retries})")
                        
                        # Append error information to the messages for the retry
                        retry_messages = messages.copy()
                        retry_messages.append({"role": "assistant", "content": current_response})
                        retry_messages.append({
                            "role": "user", 
                            "content": "The previous response couldn't be parsed as JSON. Please provide a valid JSON response with 'name', 'description', and 'tool_calls' fields. Make sure your response is properly formatted JSON without any comments or trailing commas."
                        })
                        
                        current_response = self.llm_generator.generate_unstructured_response(messages=retry_messages)
                        logger.info(f"Retry generated: {current_response}")
                    
                    retry_count += 1
                except Exception as e:
                    logger.error(f"Error extracting JSON: {e}")
                    retry_count += 1
        
        return task_data
        
    def generate_task_from_tools(
        self,
        tools: List[ToolDefinition],
        system_message: Optional[str] = None,
        user_message: Optional[str] = None
    ) -> Task:
        """Generate tasks directly from specific tools.
        
        Args:
            tools: List of tool definitions to use in the task
            system_message: Optional custom system message
            user_message: Optional custom user message
            auto_format_json: Optional flag to auto-format the JSON response
        Returns:
            A task or list of tasks using the specified tools
        """
        # Handle case where tool_names might actually contain ToolDefinition objects
        if tools and all(hasattr(t, 'name') for t in tools) and not all(isinstance(t, str) for t in tools):
            # We were passed tool objects directly
            selected_tools = tools
            logger.debug(f"Using directly provided tool objects: {[t.name for t in selected_tools]}")
        else:
            # Filter tools to include only the requested ones by name
            selected_tools = [tool for tool in self.tool_library.tools if tool.name in [tool.name for tool in tools]]
            if not selected_tools:
                raise ValueError(f"None of the specified tools {tools} were found in the tool library")
            logger.debug(f"Selected tools by name: {[t.name for t in selected_tools]}")
        
        if user_message is None:
            user_message = task_generation_with_tools_user_prompt.format(
                formatted_tools=format_tools_for_prompt(selected_tools),
                existing_tasks=self.existing_tasks
            )
        else:
            # ensure user message is formatable with the tools and existing tasks
            user_message = user_message.format(
                formatted_tools=format_tools_for_prompt(selected_tools),
                existing_tasks=self.existing_tasks
            )
        
        
        system_message = system_message or self.system_message
        messages = [
            {"role": "system", "content": system_message},
            {"role": "user", "content": user_message}
        ]
        
        raw_response = self.llm_generator.generate_unstructured_response(messages=messages)
        logger.info(f"Generated task: {raw_response}")
        
        # Parse the JSON with retries
        task_data = self._parse_json_with_retry(raw_response, messages=messages)
        
        if task_data is None:
            raise ValueError("Failed to generate valid JSON after retries")

        # Create tool calls
        tool_calls = []
        for tc in task_data.get("tool_calls", []):
            tool_calls.append(ToolCall(
                tool_name=tc.get("tool_name", ""),
                tool_parameters=tc.get("tool_parameters", {})
            ))
    
        # Create the task
        try:
            task = Task(
                name=task_data.get("name", ""),
                description=task_data.get("description", ""),
                tools=selected_tools,
                tool_calls=tool_calls,
                goal=task_data.get("goal", "")
            )
            self.existing_tasks.append(task.name)
        except Exception as e:
            logger.error(f"Error creating task: {e}")
            raise e
    
        return task

    def generate_random_tasks(
        self,
        number_of_tasks: int = 1, 
        min_tools: int = 1,
        max_tools: int = 3
    ) -> List[Task]:
        """Generate random tasks with a random selection of tools.
        
        Args:
            number_of_tasks: Number of tasks to generate
            min_tools: Minimum number of tools per task
            max_tools: Maximum number of tools per task
            
        Returns:
            List of randomly generated tasks
        """
        tasks = []
        
        for _ in range(number_of_tasks):
            # Randomly select tools
            num_tools = random.randint(min_tools, min(max_tools, len(self.tool_library.tools)))
            selected_tools = random.sample(self.tool_library.tools, num_tools)
            
            # Get the tool names
            tool_names = [tool.name for tool in selected_tools]
            
            # Generate the task
            task = self.generate_task_from_tools(tool_names)
            tasks.append(task)
            
        return tasks
    
    def _format_tools_for_prompt(self, tools: List[ToolDefinition]) -> str:
        """Format tools for inclusion in a prompt."""
        tool_descriptions = []
        
        for tool in tools:
            params = tool.inputSchema.get("properties", {})
            required = tool.inputSchema.get("required", [])
            
            param_desc = []
            for name, schema in params.items():
                req_text = " (required)" if name in required else " (optional)"
                param_desc.append(f"- {name}: {schema.get('description', '')}{req_text}")
            
            tool_descriptions.append(
                f"Tool: {tool.name}\n"
                f"Description: {tool.description}\n"
                f"Parameters:\n" + "\n".join(param_desc)
            )
        
        return "\n\n".join(tool_descriptions)
    
    def save_task_to_jsonl(self, task: Task, file_path: str, create_if_not_exists: bool = True) -> None:
        """Save a task to a JSONL file."""
        append_task_to_jsonl(task, file_path, create_if_not_exists)

    def load_tasks_from_jsonl(self, file_path: str) -> List[Task]:
        """Load tasks from a JSONL file."""
        tasks = load_tasks_from_jsonl(file_path)
        self.existing_tasks.extend([task.name for task in tasks])
        return tasks

    def updating_task_from_feedback(self, task: Task, feedback: str, messages: List[Dict[str, Any]] = None) -> Task:
        """Update a task based on feedback from a verifier.
        
        Args:
            task: The task to update
            feedback: Feedback from the verifier
            messages: Optional custom messages to use
            
        Returns:
            Updated task
        """
        # Format the task for the prompt - only include name, description, and goal
        task_for_prompt = {
            "name": task.name,
            "description": task.description,
            "goal": task.goal
        }
        
        # Setup messages for LLM
        if not messages:
            system_message = task_revision_system_prompt
            user_message = task_revision_user_prompt.format(
                task=json.dumps(task_for_prompt),
                formatted_tools=format_tools_for_prompt(task.tools),
                feedback=feedback
            )
            messages = [
                {"role": "system", "content": system_message},
                {"role": "user", "content": user_message}
            ]
        
        # Generate the updated task content
        raw_response = self.llm_generator.generate_unstructured_response(messages=messages)
        logger.info(f"Generated updated task: {raw_response}")
        
        # Parse the response
        task_data = self._parse_json_with_retry(raw_response, messages=messages)
        
        if task_data is None:
            raise ValueError("Failed to generate valid JSON for task update after retries")
        
        # Update only the description and goal, keep the original name, tools, and tool_calls
        updated_task = Task(
            name=task_data.get("name", task.name),
            description=task_data.get("description", task.description),
            goal=task_data.get("goal", task.goal),
            tools=task.tools,
            tool_calls=task.tool_calls
        )
        
        # Log the differences
        if updated_task.description != task.description:
            logger.info(f"Updated description:\nOld: {task.description}\nNew: {updated_task.description}")
        
        if updated_task.goal != task.goal:
            logger.info(f"Updated goal:\nOld: {task.goal}\nNew: {updated_task.goal}")
        
        return updated_task