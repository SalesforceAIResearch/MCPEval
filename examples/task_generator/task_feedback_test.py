import asyncio
import sys
import os
from dotenv import load_dotenv
import logging
import json
from typing import List, Dict, Any

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
    client = OpenAIMCPClient()
    logger.info("OpenAI MCP client created")
    server_script_path = '@openbnb/mcp-server-airbnb'
    
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
            
        # Set up task generator
        task_generator = TaskGenerator(
            tool_library=ToolLibrary(tools=tools_data),
            model_provider="openai",
            model_name="gpt-4o",
            max_tokens=4000,
            model_temperature=0.2,
            top_p=0.95
        )
        
        # Create a manually defined task with deliberately vague description and goal
        logger.info("Creating a deliberately vague task for testing...")
        
        # Create tool calls for the task
        tool_calls = [
            ToolCall(
                tool_name="airbnb_search",
                tool_parameters={
                    "location": "New York",
                    "checkin": "2023-12-01",
                    "checkout": "2023-12-08",
                    "adults": 2
                }
            ),
            ToolCall(
                tool_name="airbnb_listing_details",
                tool_parameters={
                    "id": "123456"
                }
            )
        ]
        
        # Create a vague task
        initial_task = Task(
            name="Find Accommodation in New York",
            description="Find a good place to stay in New York for a week in December. Look up some options and get details about one of them.",
            goal="Find a suitable Airbnb in New York",
            tools=tools_data,
            tool_calls=tool_calls
        )
        
        print_task(initial_task, "Initial Vague Task")
        
        # Simulate feedback for the task
        feedback = """
        The task is not specific enough about what information the user needs to find. 
        It doesn't clearly state what criteria are important for selecting accommodations.
        Please add specific requirements for the accommodation, such as:
        - Minimum number of bedrooms/bathrooms needed (at least 2 bedrooms, 2 bathrooms)
        - Specific amenities required (WiFi, kitchen, air conditioning, parking, pet-friendly)
        - Proximity to specific locations (within 2 miles of Times Square)
        - Price range ($150-300 per night)
        Also, the goal should be more measurable and specific about what constitutes success.
        """
        
        # Update the task based on feedback
        logger.info("Updating task based on feedback...")
        updated_task = task_generator.updating_task_from_feedback(initial_task, feedback)
        print_task(updated_task, "Updated Task")
        
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