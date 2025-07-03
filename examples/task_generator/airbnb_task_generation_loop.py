import asyncio
import sys
import os
import logging
import time
import random
from typing import List
from dotenv import load_dotenv

# Add the parent directory to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from mcp_eval_llm.client.openai_client import OpenAIMCPClient
from mcp_eval_llm.synthesis.task_generator import TaskGenerator, Task
from mcp_eval_llm.synthesis.tools import ToolLibrary

load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Output file path
OUTPUT_FILE = "data/airbnb_tasks/airbnb_tasks.jsonl"

async def main():
    # Connect to the Airbnb MCP server to get tools
    client = OpenAIMCPClient()
    logger.info("OpenAI MCP client created")
    
    # Setup server connection
    server_script_path = '@openbnb/mcp-server-airbnb'
    try:
        # Connect to server and get tools
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
        
        # Initialize the task generator with shorter, simpler prompts
        task_generator = TaskGenerator(
            tool_library=ToolLibrary(tools=tools_data),
            model_provider="openai",
            model_name="gpt-4o",
            model_temperature=0.2,
            max_tokens=2000,  # Reduced token limit
            top_p=0.95,
            existing_tasks=[]
        )
        
        # Generate 100 tasks
        logger.info(f"Starting generation of 100 Airbnb tasks")
        
        tasks_generated = 0
        total_tasks = 100
        
        # Load existing tasks
        task_generator.load_tasks_from_jsonl(OUTPUT_FILE)

        while tasks_generated < total_tasks:
            try:
                # Log start of generation
                logger.info(f"Starting generation for task {tasks_generated + 1}/{total_tasks}")
                start_time = time.time()
                
                # Generate task - this is synchronous
                task = task_generator.generate_task_from_tools(
                    tools=tools_data,
                )
                
                # Log success
                elapsed = time.time() - start_time
                logger.info(f"Task generation completed in {elapsed:.2f} seconds")
                
                # Save task to the output file
                task_generator.save_task_to_jsonl(task, OUTPUT_FILE)
                tasks_generated += 1
                logger.info(f"Generated task {tasks_generated}/{total_tasks}: {task.name}")
                
                # Print abbreviated task details to avoid console flooding
                if tasks_generated % 10 == 0:
                    print_task(task, f"Task {tasks_generated}")
                
                # Pause before generating next task to avoid rate limits
                await asyncio.sleep(2)
                
            except Exception as e:
                logger.error(f"Error generating task: {str(e)}", exc_info=True)
                # Wait longer after an error before retrying
                await asyncio.sleep(10)
        
        logger.info(f"Task generation complete. {tasks_generated} tasks saved to {OUTPUT_FILE}")
    
    except Exception as e:
        logger.error(f"Error during execution: {e}", exc_info=True)
    finally:
        # Always clean up the client
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