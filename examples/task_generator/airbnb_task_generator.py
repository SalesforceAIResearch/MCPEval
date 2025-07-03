import asyncio
import sys
import os
from dotenv import load_dotenv
import logging
import json
from typing import List, Dict, Any
from enum import Enum

# Load environment variables from .env
load_dotenv()

# Set up logging
logger = logging.getLogger(__name__)
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", logging.INFO),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))
from mcp_eval_llm.client.openai_client import OpenAIMCPClient
from mcp_eval_llm.commons.types import Task, ToolCall
from mcp_eval_llm.synthesis.tools import ToolLibrary, format_tools_for_prompt
from mcp_eval_llm.synthesis.task_generator import TaskGenerator
from mcp_eval_llm.commons.prompts import task_generation_with_tools_user_prompt

async def main():
    # Set up OpenAI client for direct API access
    existing_tasks = []
    # openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    
    client = OpenAIMCPClient()
    logger.info("OpenAI MCP client created")
    server_script_path = '@openbnb/mcp-server-airbnb'
    # if it is python server file, server_script_path = 'dir/to/mcp_server.py'
    try:
        await client.connect_to_server(server_script_path)
        response = await client.session.list_tools()
        
        # Extract tools from the response
        if hasattr(response, 'tools'):
            tools_data = response.tools
        else:
            logger.error("Response does not have 'tools' attribute")
            return
            
        logger.info(f"Retrieved {len(tools_data)} tools from MCP server")
        
        if not tools_data:
            logger.error("No valid tools found. Cannot generate tasks.")
            return
            
        try:
            # Generate first task
            task_generator = TaskGenerator(
                tool_library=ToolLibrary(tools=tools_data),
                model_provider="openai",
                model_name="gpt-4o",
                max_tokens=4000,
                model_temperature=0.2,
                top_p=0.95,
                existing_tasks=existing_tasks
            )
            
            # Remove problematic debugging statements that reference undefined variables
            try:
                task = task_generator.generate_task_from_tools(tools_data)
                task_generator.save_task_to_jsonl(task, "tasks.jsonl")
                print_task(task, "Task Generated Using Direct Approach")
            except json.JSONDecodeError as json_err:
                logger.error(f"JSON decoding failed: {json_err}", exc_info=True)
                return
            except Exception as e:
                logger.error(f"Error generating tasks: {e}", exc_info=True)
                return
            
            # Generate a second task with a different system message for variety
            
            logger.info("Generating a second task with a different prompt")
            
            system_message = """You are a creative task designer focusing on real-world tool applications.\
Your task is to create a challenging but realistic scenario where someone would need to use specific tools.\
Make the task engaging and include clear expected tool usage.
Your response must be in JSON format with the following structure:
{{
  "name": "Task name",
  "description": "Detailed task description",
  "tool_calls": [
    {{
      "tool_name": "name of the tool",
      "tool_parameters": {{
        "param1": "value1",
        "param2": "value2"
      }}
    }}
  ]
}}"""
            
            task2 = task_generator.generate_task_from_tools(tools_data, system_message)
            print_task(task2, "Second Task Generated")
                
        except Exception as e:
            logger.error(f"Error generating tasks: {e}", exc_info=True)
        
    except Exception as e:
        logger.error(f"Error during execution: {e}", exc_info=True)
    finally:
        logger.info("Cleaning up resources")
        await client.cleanup()

def print_task(task: Task, title: str):
    """Print task details in a readable format."""
    print(f"\n{'='*50}")
    print(f"{title}")
    print(f"{'='*50}")
    print(f"Name: {task.name}")
    print(f"Description: {task.description}")
    print(f"Goal: {task.goal}")
    print(f"Tools used ({len(task.tools)}):")
    for tool in task.tools:
        print(f"  - {tool.name}")
    
    print("\nExpected Tool Calls:")
    for call in task.tool_calls:
        print(f"  - {call.tool_name}")
        print(f"    Parameters: {call.tool_parameters}")
    print("="*50)

if __name__ == "__main__":
    asyncio.run(main())