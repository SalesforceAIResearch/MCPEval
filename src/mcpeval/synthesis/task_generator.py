from pydantic import BaseModel, Field, ConfigDict
import logging
import random
import json
from typing import Dict, List, Any, Optional, Union

from ..commons.types import Task
from .tools import ToolDefinition, ToolLibrary, format_tools_for_prompt
from ..models.llms import OpenAIWrapper
from ..commons.prompts import (
    task_generation_system_prompt,
    task_generation_with_tools_user_prompt,
    task_revision_system_prompt,
    task_revision_user_prompt,
)
from .utils import append_task_to_jsonl, load_tasks_from_jsonl

logger = logging.getLogger(__name__)


class TaskFormat(BaseModel):
    """Format for generating task descriptions."""

    name: str = Field(..., description="Name of the task")
    description: str = Field(..., description="Description of the task")
    goal: str = Field(..., description="Goal of the task")


class TaskGenerator:
    """Generator for creating tool use tasks."""

    def __init__(
        self,
        tool_library: ToolLibrary,
        model_config: Optional[Dict[str, Any]] = None,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        system_message: Optional[str] = None,
        existing_tasks: Optional[List[Task]] = None,
        **kwargs,
    ):
        """Initialize the task generator.

        Args:
            tool_library: Library of tool definitions
            model_config: Model configuration dictionary (e.g., {"model": "gpt-4o", "temperature": 0.01})
            api_key: API key for the model provider
            base_url: Base URL for the API
            system_message: Optional system message for the LLM
            existing_tasks: Optional list of existing tasks
        """
        self.tool_library = tool_library
        
        # Use default model config if none provided
        if model_config is None:
            model_config = {
                "model": "gpt-4o-2024-11-20",
                "temperature": 0.01,
                "max_tokens": 16384
            }
        
        # Initialize the OpenAI wrapper with the model config
        self.llm = OpenAIWrapper(
            api_key=api_key,
            base_url=base_url,
            model_config=model_config,
            **kwargs
        )

        self.system_message = system_message or task_generation_system_prompt
        self.existing_tasks = existing_tasks or []

    def _parse_json_with_retry(
        self,
        raw_response: str,
        messages: Optional[List[Dict[str, Any]]] = None,
        max_retries: int = 3,
        required_fields: Optional[List[str]] = None,
    ):
        """Parse JSON from a string with retries and cleanup for malformed responses.

        Args:
            raw_response: The string containing JSON to parse
            messages: Optional list of message objects to use for retrying with the LLM
            max_retries: Maximum number of retries before giving up
            required_fields: List of required fields to validate in the parsed JSON

        Returns:
            Parsed JSON data or None if parsing failed
        """
        import re
        
        # Default required fields for task generation
        if required_fields is None:
            required_fields = ["name", "description", "goal"]
        
        task_data = None
        retry_count = 0
        current_response = raw_response.strip()
        last_error = None

        while task_data is None and retry_count < max_retries:
            try:
                # Strategy 1: Direct JSON parsing
                try:
                    parsed_data = json.loads(current_response)
                    # Validate required fields
                    if self._validate_task_data(parsed_data, required_fields):
                        task_data = parsed_data
                        break
                    else:
                        last_error = f"Missing required fields: {[f for f in required_fields if f not in parsed_data]}"
                except json.JSONDecodeError as e:
                    last_error = f"JSON decode error: {str(e)}"

                # Strategy 2: Extract JSON from markdown code blocks
                if task_data is None:
                    json_patterns = [
                        r"```(?:json)?\s*([\s\S]*?)\s*```",  # Standard markdown
                        r"```json\n([\s\S]*?)\n```",        # Explicit json blocks
                        r"{[\s\S]*}",                       # Any JSON-like object
                    ]
                    
                    for pattern in json_patterns:
                        matches = re.findall(pattern, current_response)
                        for match in matches:
                            json_str = match.strip()
                            try:
                                parsed_data = json.loads(json_str)
                                if self._validate_task_data(parsed_data, required_fields):
                                    task_data = parsed_data
                                    break
                            except json.JSONDecodeError:
                                continue
                        if task_data:
                            break

                # Strategy 3: Clean up common JSON issues and retry
                if task_data is None:
                    cleaned_responses = self._clean_json_response(current_response)
                    for cleaned in cleaned_responses:
                        try:
                            parsed_data = json.loads(cleaned)
                            if self._validate_task_data(parsed_data, required_fields):
                                task_data = parsed_data
                                break
                        except json.JSONDecodeError:
                            continue
                        if task_data:
                            break

                # Strategy 4: Retry with LLM if we have messages and haven't exhausted retries
                if task_data is None and messages and retry_count < max_retries - 1:
                    logger.warning(
                        f"JSON parsing failed (attempt {retry_count + 1}/{max_retries}): {last_error}"
                    )
                    logger.info(f"Problematic response: {current_response[:200]}...")

                    # Create more specific retry prompt
                    retry_prompt = self._create_retry_prompt(current_response, last_error, required_fields)
                    
                    retry_messages = messages.copy()
                    retry_messages.append({"role": "assistant", "content": current_response})
                    retry_messages.append({"role": "user", "content": retry_prompt})

                    try:
                        response = self.llm.chat_completion(messages=retry_messages)
                        current_response = response["choices"][0]["message"]["content"].strip()
                        logger.info(f"Retry {retry_count + 1} generated response length: {len(current_response)}")
                    except Exception as e:
                        logger.error(f"Error during LLM retry: {e}")
                        break

                retry_count += 1

            except Exception as e:
                logger.error(f"Unexpected error during JSON parsing: {e}")
                last_error = str(e)
                retry_count += 1

        if task_data is None:
            logger.error(f"Failed to parse JSON after {retry_count} attempts. Last error: {last_error}")

        return task_data

    def _validate_task_data(self, data: Dict[str, Any], required_fields: List[str]) -> bool:
        """Validate that the parsed JSON contains all required fields."""
        if not isinstance(data, dict):
            return False
        
        for field in required_fields:
            if field not in data or not data[field]:
                return False
        
        return True

    def _clean_json_response(self, response: str) -> List[str]:
        """Apply various cleaning strategies to fix common JSON issues."""
        import re
        
        cleaned_versions = []
        
        # Strategy 1: Remove comments and fix trailing commas
        cleaned = re.sub(r"//.*?$", "", response, flags=re.MULTILINE)  # Remove // comments
        cleaned = re.sub(r"/\*[\s\S]*?\*/", "", cleaned)  # Remove /* */ comments
        cleaned = re.sub(r",\s*([}\]])", r"\1", cleaned)  # Remove trailing commas
        cleaned_versions.append(cleaned)
        
        # Strategy 2: Extract the first complete JSON object
        json_start = response.find("{")
        if json_start != -1:
            brace_count = 0
            for i, char in enumerate(response[json_start:], json_start):
                if char == "{":
                    brace_count += 1
                elif char == "}":
                    brace_count -= 1
                    if brace_count == 0:
                        potential_json = response[json_start:i+1]
                        cleaned_versions.append(potential_json)
                        break
        
        # Strategy 3: Fix common quote issues
        quote_fixed = re.sub(r"'([^']*)':", r'"\1":', response)  # Single to double quotes for keys
        quote_fixed = re.sub(r":\s*'([^']*)'", r': "\1"', quote_fixed)  # Single to double quotes for values
        cleaned_versions.append(quote_fixed)
        
        return cleaned_versions

    def _create_retry_prompt(self, failed_response: str, error: str, required_fields: List[str]) -> str:
        """Create a specific retry prompt based on the failure."""
        return f"""The previous response couldn't be parsed as valid JSON. 

Error: {error}

Please provide a valid JSON response with exactly these required fields: {', '.join(required_fields)}

Requirements:
1. Must be valid JSON (no comments, no trailing commas)
2. Must contain all required fields: {', '.join(required_fields)}
3. Each field must have a non-empty value
4. Return ONLY the JSON object, no additional text

Example format:
{{
    "name": "Task name here",
    "description": "Detailed task description here", 
    "goal": "Clear goal statement here"
}}"""

    def generate_task_from_tools(
        self,
        tools: List[ToolDefinition],
        system_message: Optional[str] = None,
        user_message: Optional[str] = None,
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
        if (
            tools
            and all(hasattr(t, "name") for t in tools)
            and not all(isinstance(t, str) for t in tools)
        ):
            # We were passed tool objects directly
            selected_tools = tools
            logger.debug(
                f"Using directly provided tool objects: {[t.name for t in selected_tools]}"
            )
        else:
            # Filter tools to include only the requested ones by name
            selected_tools = [
                tool
                for tool in self.tool_library.tools
                if tool.name in [tool.name for tool in tools]
            ]
            if not selected_tools:
                raise ValueError(
                    f"None of the specified tools {tools} were found in the tool library"
                )
            logger.debug(f"Selected tools by name: {[t.name for t in selected_tools]}")

        if user_message is None:
            user_message = task_generation_with_tools_user_prompt.format(
                formatted_tools=format_tools_for_prompt(selected_tools),
                existing_tasks=self.existing_tasks,
            )
        else:
            # ensure user message is formatable with the tools and existing tasks
            user_message = user_message.format(
                formatted_tools=format_tools_for_prompt(selected_tools),
                existing_tasks=self.existing_tasks,
            )

        system_message = system_message or self.system_message
        messages = [
            {"role": "system", "content": system_message},
            {"role": "user", "content": user_message},
        ]

        response = self.llm.chat_completion(messages=messages)
        raw_response = response["choices"][0]["message"]["content"]
        logger.info(f"Generated task: {raw_response}")

        # Parse the JSON with retries
        task_data = self._parse_json_with_retry(raw_response, messages=messages)

        if task_data is None:
            raise ValueError("Failed to generate valid JSON after retries")

        # Create the task
        try:
            task = Task(
                name=task_data.get("name", ""),
                description=task_data.get("description", ""),
                tools=selected_tools,
                goal=task_data.get("goal", ""),
            )
            self.existing_tasks.append(task.name)
        except Exception as e:
            logger.error(f"Error creating task: {e}")
            raise e

        return task

    def generate_random_tasks(
        self, number_of_tasks: int = 1, min_tools: int = 1, max_tools: int = 3
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
            num_tools = random.randint(
                min_tools, min(max_tools, len(self.tool_library.tools))
            )
            selected_tools = random.sample(self.tool_library.tools, num_tools)

            # Generate the task
            task = self.generate_task_from_tools(selected_tools)
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
                param_desc.append(
                    f"- {name}: {schema.get('description', '')}{req_text}"
                )

            tool_descriptions.append(
                f"Tool: {tool.name}\n"
                f"Description: {tool.description}\n"
                f"Parameters:\n" + "\n".join(param_desc)
            )

        return "\n\n".join(tool_descriptions)

    def save_task_to_jsonl(
        self, task: Task, file_path: str, create_if_not_exists: bool = True
    ) -> None:
        """Save a task to a JSONL file."""
        append_task_to_jsonl(task, file_path, create_if_not_exists)

    def load_tasks_from_jsonl(self, file_path: str) -> List[Task]:
        """Load tasks from a JSONL file."""
        tasks = load_tasks_from_jsonl(file_path)
        self.existing_tasks.extend([task.name for task in tasks])
        return tasks

    def updating_task_from_feedback(
        self, task: Task, feedback: str, messages: List[Dict[str, Any]] = None
    ) -> Task:
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
            "goal": task.goal,
        }

        # Setup messages for LLM
        if not messages:
            system_message = task_revision_system_prompt
            user_message = task_revision_user_prompt.format(
                task=json.dumps(task_for_prompt),
                formatted_tools=format_tools_for_prompt(task.tools),
                feedback=feedback,
            )
            messages = [
                {"role": "system", "content": system_message},
                {"role": "user", "content": user_message},
            ]

        # Generate the updated task content
        response = self.llm.chat_completion(messages=messages)
        raw_response = response["choices"][0]["message"]["content"]
        logger.info(f"Generated updated task: {raw_response}")

        # Parse the response
        task_data = self._parse_json_with_retry(raw_response, messages=messages)

        if task_data is None:
            raise ValueError(
                "Failed to generate valid JSON for task update after retries"
            )

        # Update only the description and goal, keep the original name and tools
        updated_task = Task(
            name=task_data.get("name", task.name),
            description=task_data.get("description", task.description),
            goal=task_data.get("goal", task.goal),
            tools=task.tools,
        )

        # Log the differences
        if updated_task.description != task.description:
            logger.info(
                f"Updated description:\nOld: {task.description}\nNew: {updated_task.description}"
            )

        if updated_task.goal != task.goal:
            logger.info(f"Updated goal:\nOld: {task.goal}\nNew: {updated_task.goal}")

        return updated_task
