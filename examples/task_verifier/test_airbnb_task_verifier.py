import asyncio
import os
import sys
import json
import logging
from typing import Dict, Any, List
from dotenv import load_dotenv

# Add project root to path to make imports work
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

# Import from our package
from mcp_eval_llm.synthesis.task_verifier import LLMTaskVerifier
from mcp_eval_llm.commons.types import Task, ToolCall
from mcp_eval_llm.client.openai_client import OpenAIMCPClient
from mcp_eval_llm.models.llms import OpenAIWrapper

# Load environment variables (for OpenAI API key)
load_dotenv()

# Set up logging
logger = logging.getLogger(__name__)
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", logging.INFO),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def print_tool_calls(tool_calls):
    """Print tool calls in a detailed format."""
    print(f"\n{'='*20} TOOL CALLS {'='*20}")
    for i, (tool_call, session) in enumerate(tool_calls):
        print(f"Tool Call #{i+1}:")
        print(f"  Tool Name: {tool_call.tool_name}")
        print(f"  Session: {session.name if hasattr(session, 'name') else str(session)}")
        print(f"  Parameters:")
        try:
            # Pretty print the parameters as JSON
            print(json.dumps(tool_call.tool_parameters, indent=4).replace('\n', '\n    '))
        except:
            print(f"    {tool_call.tool_parameters}")
        print()
    print(f"{'='*50}")


async def test_evaluator_multi_turn():
    """Test the LLMMCPEvaluator with multi-turn capabilities."""
    logger.info("Starting test with Airbnb MCP server")
    
    # Initialize OpenAI LLM for the evaluator
    llm = OpenAIWrapper(model="gpt-4o")
    
    # Initialize evaluator
    evaluator = LLMTaskVerifier(llm)
    
    # Initialize OpenAI MCP client
    client = OpenAIMCPClient(model="gpt-4o")
    logger.info("OpenAI MCP client created")
    
    # Connect to Airbnb MCP server
    server_script_path = '@openbnb/mcp-server-airbnb'
    server_args = ['--ignore-robots-txt']  # Add this flag to bypass robots.txt restrictions
    
    try:
        await client.connect_to_server(server_script_path, server_args)
        logger.info(f"Connected to Airbnb MCP server with args: {server_args}")
        
        # Get tools from the server
        response = await client.session.list_tools()
        if not hasattr(response, 'tools') or not response.tools:
            logger.error("No tools available from the server")
            return
        
        tools_data = response.tools
        logger.info(f"Retrieved {len(tools_data)} tools from MCP server")
        
        # Create a sample task with all tools - specifically requesting multiple tool usage
        task = Task(
            name="Find and research an Airbnb in San Francisco",
            description="Help a user find and research Airbnb listings in San Francisco by first searching for listings and then getting detailed information about the most promising option.",
            goal="First, search for available 2-bedroom listings in San Francisco for a 5-day trip from June 15-20, 2025 with a budget of $1000. Then, get detailed information about the first listing from the search results.",
            tools=tools_data,
            tool_calls=[]  # We don't provide expected tool calls here
        )
        
        # Print task information
        print_task(task)
        
        # Run the evaluation (multi-turn)
        logger.info("Running multi-turn evaluation...")
        
        # Set debug logging for task_verifier if DEBUG is true
        if os.getenv("DEBUG", "false").lower() == "true":
            logging.getLogger("mcp_eval_llm.synthesis.task_verifier").setLevel(logging.DEBUG)
            
        success, result = await evaluator.task_verification(
            task=task,
            tools=tools_data,
            tool_name_to_session={tool.name: client.session for tool in tools_data},
            temperature=0.2,
            max_tokens=1000,
            max_turns=5  # Allow up to 5 turns for more complex tasks
        )
        
        # Check if the task verification was successful
        if not success:
            # Result is a reason for clarification
            logger.info(f"LLM requested clarification: {result}")
        else:
            # Result is a dictionary with tool calls
            try:
                logger.info(f"Got {len(result['tool_calls'])} total tool calls across all turns")
                
                # Print detailed information about tool calls
                print_tool_calls(result['tool_calls'])
                
                # Show last message from conversation
                last_message = next((msg for msg in reversed(result['conversation']) 
                                   if msg['role'] == 'assistant' and msg.get('content')), None)
                
                if last_message and last_message.get('content'):
                    print(f"\n{'='*20} FINAL RESPONSE {'='*20}")
                    print(last_message.get('content', ''))
                    print(f"{'='*50}")
            except Exception as e:
                logger.error(f"Error processing result: {e}")
                logger.info(f"Raw result: {result}")
        
    except Exception as e:
        logger.error(f"Error during execution: {e}", exc_info=True)
    finally:
        logger.info("Cleaning up resources")
        await client.cleanup()


async def test_evaluator_clarification():
    """Test the LLMMCPEvaluator with a task that requires clarification."""
    logger.info("Starting test with a vague task")
    
    # Initialize OpenAI LLM for the evaluator
    llm = OpenAIWrapper(model="gpt-4o")
    
    # Initialize evaluator
    task_verifier = LLMTaskVerifier(llm)
    
    # Initialize OpenAI MCP client
    client = OpenAIMCPClient(model="gpt-4o")
    logger.info("OpenAI MCP client created")
    
    # Connect to Airbnb MCP server
    server_script_path = '@openbnb/mcp-server-airbnb'
    server_args = ['--ignore-robots-txt']
    
    try:
        await client.connect_to_server(server_script_path, server_args)
        logger.info(f"Connected to Airbnb MCP server with args: {server_args}")
        
        # Get tools from the server
        response = await client.session.list_tools()
        if not hasattr(response, 'tools') or not response.tools:
            logger.error("No tools available from the server")
            return
        
        tools_data = response.tools
        logger.info(f"Retrieved {len(tools_data)} tools from MCP server")
        
        # Give the vague task more focus to see if it can complete it
        vague_task = Task(
            name="Find an Airbnb in New York",
            description="Find an Airbnb listing for a weekend trip in New York.",
            goal="Find a good Airbnb listing in New York for 2 adults for a weekend trip (any dates in the next month).",
            tools=tools_data,
            tool_calls=[]
        )
        
        # Print task information
        print_task(vague_task)
        
        # Run the evaluation
        logger.info("Running evaluation with vague task...")
        
        # Set debug logging for task_verifier if DEBUG is true
        if os.getenv("DEBUG", "false").lower() == "true":
            logging.getLogger("mcp_eval_llm.synthesis.task_verifier").setLevel(logging.DEBUG)
            
        success, result = await task_verifier.task_verification(
            task=vague_task,
            tools=tools_data,
            tool_name_to_session={tool.name: client.session for tool in tools_data},
            temperature=0.2,
            max_tokens=1000,
            max_turns=5
        )
        
        # Check if the task verification was successful
        if not success:
            # Display clarification request
            print(f"\n{'='*20} CLARIFICATION REQUEST {'='*20}")
            print(f"The LLM requested clarification:")
            print(f"Reason: {result}")
            print(f"{'='*50}")
            logger.info(f"SUCCESS: LLM requested clarification: {result}")
        else:
            logger.info("UNEXPECTED: LLM did not request clarification for the vague task.")
            # Process tool calls from result
            try:
                logger.info(f"Got {len(result['tool_calls'])} total tool calls instead.")
                
                # Print detailed information about tool calls
                print_tool_calls(result['tool_calls'])
                
                # Show last message from conversation
                last_message = next((msg for msg in reversed(result['conversation']) 
                                   if msg['role'] == 'assistant' and msg.get('content')), None)
                
                if last_message and last_message.get('content'):
                    print(f"\n{'='*20} FINAL RESPONSE {'='*20}")
                    print(last_message.get('content', ''))
                    print(f"{'='*50}")
            except Exception as e:
                logger.error(f"Error processing result: {e}")
                logger.info(f"Raw result: {result}")
        
    except Exception as e:
        logger.error(f"Error during execution: {e}", exc_info=True)
    finally:
        logger.info("Cleaning up resources")
        await client.cleanup()


def print_task(task: Task):
    """Print task details in a readable format."""
    print(f"\n{'='*50}")
    print(f"Task: {task.name}")
    print(f"{'='*50}")
    print(f"Description: {task.description}")
    print(f"Goal: {task.goal}")
    print(f"Tools available ({len(task.tools)}):")
    for tool in task.tools:
        print(f"  - {tool.name}: {tool.description if hasattr(tool, 'description') else ''}")
    print("="*50)


if __name__ == "__main__":
    # Run both tests by default, or use TEST_TYPE env var to run just one
    test_type = os.getenv("TEST_TYPE", "both")
    
    if test_type.lower() == "clarification":
        asyncio.run(test_evaluator_clarification())
    elif test_type.lower() == "multi_turn":
        asyncio.run(test_evaluator_multi_turn())
    else:
        # Run both tests
        print("\n=== Running multi-turn test ===")
        asyncio.run(test_evaluator_multi_turn())
        print("\n=== Running clarification test ===")
        asyncio.run(test_evaluator_clarification())
