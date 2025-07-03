#!/usr/bin/env python3
"""
Task Verifier CLI Tool

This module provides functionality for verifying tasks against an MCP server.
"""
import asyncio
import os
import logging

from mcp_eval_llm.client.openai_client import OpenAIMCPClient
from mcp_eval_llm.synthesis.task_verifier import LLMTaskVerifier
from mcp_eval_llm.models.llms import OpenAIWrapper
from mcp_eval_llm.synthesis.utils import load_tasks_from_jsonl
from mcp_eval_llm.synthesis.task_generator import TaskGenerator
from mcp_eval_llm.synthesis.tools import ToolLibrary
from mcp_eval_llm.utils.cli import (
    load_prompt_from_file, 
    print_task, 
    print_tool_calls, 
    handle_existing_file, 
    generate_output_filename, 
    save_tasks_to_jsonl,
    setup_colored_logging
)
from mcp_eval_llm.utils.response_process import (
    process_conversation,
    process_final_response,
    process_tool_call_results
)
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging using centralized setup
setup_colored_logging(level=logging.INFO)
logger = logging.getLogger(__name__)





async def verify_task(task, server_path=None, server_args=None, server_paths=None, server_args_list=None, model="gpt-4o", api_key=None, system_message=None, max_turns=10):
    """Verify a task execution with LLMTaskVerifier.
    
    Args:
        task: The task to verify
        server_path: Path to the MCP server script (single server mode)
        server_args: Additional arguments for the server (single server mode)
        server_paths: List of server paths (multi-server mode)
        server_args_list: List of server arguments (multi-server mode)
        model: Model name to use
        api_key: OpenAI API key
        system_message: System message for the task
        max_turns: Maximum number of turns for task verification
        
    Returns:
        tuple: (success, task) where task is the updated Task object with verification results
    """
    logger.info(f"Starting verification for task: {task.name}")
    
    # Initialize OpenAI LLM for the evaluator
    llm = OpenAIWrapper(model=model, api_key=api_key)
    
    # Initialize evaluator
    evaluator = LLMTaskVerifier(llm)
    
    # Initialize OpenAI MCP client
    client = OpenAIMCPClient(model=model, api_key=api_key)
    logger.info("OpenAI MCP client created")
    
    try:
        # Check if we have multiple servers or single server
        if server_paths and server_args_list:
            # Multi-server mode
            logger.info(f"Connecting to {len(server_paths)} MCP servers for verification")
            
            # Connect to multiple servers
            await client.connect_to_multiple_servers(server_paths, server_args_list)
            
            # Get aggregated tools from all servers
            all_tools = await client.get_all_tools()
            tools_data = all_tools
            logger.info(f"Retrieved {len(tools_data)} tools from {len(server_paths)} MCP servers")
            
            # Build tool_name_to_session mapping for multi-server
            tool_name_to_session = client.tool_name_to_session
            
        else:
            # Single server mode (backward compatibility)
            # Set default server args if None
            if server_args is None:
                server_args = []
            
            # Connect to MCP server
            await client.connect_to_server(server_path, server_args)
            logger.info(f"Connected to MCP server with args: {server_args}")
            
            # Get tools from the server
            response = await client.session.list_tools()
            if not hasattr(response, 'tools') or not response.tools:
                logger.error("No tools available from the server")
                return False, None
            
            tools_data = response.tools
            logger.info(f"Retrieved {len(tools_data)} tools from MCP server")
            
            # Build tool_name_to_session mapping for single server
            tool_name_to_session = {tool.name: client.session for tool in tools_data}
        
        if not tools_data:
            logger.error("No valid tools found. Cannot verify task.")
            return False, None
        
        # Initialize task generator with the tools from the server
        task_generator = TaskGenerator(
            tool_library=ToolLibrary(tools=tools_data),
            model_provider="openai",
            model_name=model,
            max_tokens=4000,
            model_temperature=0.2,
            top_p=0.95,
            api_key=api_key
        )
        
        # Update the task tools with the actual tools from the server
        task.tools = tools_data
        
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
            tool_name_to_session=tool_name_to_session,
            temperature=0.2,
            max_tokens=1000,
            max_turns=max_turns,  # Configurable max turns for complex tasks
            system_message=system_message
        )
        
        # Check if the task verification was successful
        if not success:
            # Result is a reason for clarification
            logger.info(f"LLM requested clarification: {result}")
            updated_task = task_generator.updating_task_from_feedback(task, result)
            return False, updated_task
        else:
            # Result now contains tool_calls, final_response, and conversation
            try:
                # Get all the tool calls from the result
                tool_calls = result.get('tool_calls', [])
                logger.info(f"Got {len(tool_calls)} total tool calls across all turns")
                
                # Update the task's tool_calls with the actual tool calls from the result
                task.tool_calls = [tc[0] if isinstance(tc, tuple) else tc for tc in tool_calls]
                
                # Print detailed information about tool calls
                print_tool_calls(tool_calls)
                
                # Get final response directly from the result
                final_response = result.get('final_response', '')
                
                # Process final_response to ensure it's a string
                processed_final_response = process_final_response(final_response)
                
                if processed_final_response:
                    print(f"\n{'='*20} FINAL RESPONSE {'='*20}")
                    print(processed_final_response)
                    print(f"{'='*50}")
                
                # Process conversation to ensure content is a string and create proper Message objects
                conversation = process_conversation(result.get('conversation', []))
                
                # Process tool_call_results to ensure proper format
                processed_tool_call_results = process_tool_call_results(result.get('tool_call_results'))
                
                # Update the task with the results
                task.final_response = processed_final_response
                task.conversation = conversation
                task.tool_call_results = processed_tool_call_results
                
                return True, task
                
            except Exception as e:
                logger.error(f"Error processing result: {e}")
                logger.info(f"Raw result: {result}")
                return False, None
        
    except Exception as e:
        logger.error(f"Error during execution: {e}", exc_info=True)
        return False, None
    finally:
        logger.info("Cleaning up resources")
        await client.cleanup()


async def verify_tasks(args):
    """Verify tasks from a JSONL file and save results."""
    # Load tasks from file
    all_tasks = load_tasks_from_jsonl(args.tasks_file)
    
    # Setup output files
    output_file = generate_output_filename(args.tasks_file, args.output, prefix="verified")
    output_file, _ = handle_existing_file(output_file)
    
    # Load already verified task IDs to skip duplicates
    verified_task_ids = set()
    if os.path.exists(output_file):
        try:
            existing_verified_tasks = load_tasks_from_jsonl(output_file)
            verified_task_ids = {task.id for task in existing_verified_tasks if hasattr(task, 'id') and task.id}
        except Exception:
            pass
    
    # Filter out already verified tasks and limit number if requested
    tasks = [task for task in all_tasks if not (hasattr(task, 'id') and task.id and task.id in verified_task_ids)]
    
    # Log how many tasks were skipped
    skipped_count = len(all_tasks) - len(tasks)
    if skipped_count > 0:
        logger.info(f"Skipping {skipped_count} already verified tasks")
    
    num_tasks = getattr(args, 'num_tasks', -1)
    if num_tasks > 0:
        tasks = tasks[:num_tasks]
    
    if not tasks:
        print("No tasks to verify")
        return
    
    # Ensure output directory exists
    os.makedirs(os.path.dirname(os.path.abspath(output_file)), exist_ok=True)
    
    # Track results
    verified_count = 0
    unverified_count = 0
    error_count = 0
    
    # Create unverified tasks file
    base_name, ext = os.path.splitext(output_file)
    unverified_file = f"{base_name}_unverified{ext}"
    unverified_file, _ = handle_existing_file(unverified_file)
    
    # Get server parameters and system message
    system_message = load_prompt_from_file(getattr(args, 'prompt_file', None))
    
    # Check if we have multi-server or single-server configuration
    server_paths = getattr(args, 'server_paths', None)
    server_args_list = getattr(args, 'server_args_list', None)
    server_args = getattr(args, 'server_args', [])
    
    print(f"Verifying {len(tasks)} tasks...")
    
    # Process tasks
    for i, task in enumerate(tasks):
        print(f"Processing task {i+1}/{len(tasks)}: {task.name}")
        
        try:
            if server_paths and server_args_list:
                # Multi-server mode
                success, verified_task = await verify_task(
                    task=task,
                    server_paths=server_paths,
                    server_args_list=server_args_list,
                    model=args.model,
                    api_key=getattr(args, 'api_key', None),
                    system_message=system_message,
                    max_turns=getattr(args, 'max_turns', 10)
                )
            else:
                # Single server mode
                success, verified_task = await verify_task(
                    task=task,
                    server_path=args.server,
                    server_args=server_args,
                    model=args.model,
                    api_key=getattr(args, 'api_key', None),
                    system_message=system_message,
                    max_turns=getattr(args, 'max_turns', 10)
                )
            
            if success and verified_task:
                save_tasks_to_jsonl(verified_task, output_file, append=True)
                verified_count += 1
                print(f"✓ Task {i+1} verified")
            else:
                if verified_task:
                    save_tasks_to_jsonl(verified_task, unverified_file, append=True)
                    unverified_count += 1
                    print(f"✗ Task {i+1} failed verification")
                else:
                    error_count += 1
                    print(f"✗ Task {i+1} error")
            
            await asyncio.sleep(1)  # Rate limiting
            
        except Exception as e:
            error_count += 1
            print(f"Error processing task {i+1}: {e}")
            continue
    
    # Summary
    print(f"\nSUMMARY:")
    print(f"Successfully verified: {verified_count}")
    print(f"Failed verification: {unverified_count}")
    print(f"Errors: {error_count}")


def main(args):
    """Main entry point for the CLI."""
    asyncio.run(verify_tasks(args))


if __name__ == "__main__":
    # When run directly, this should not happen as the main CLI handles argument parsing
    print("Please use the main CLI: python -m mcp_eval_llm.cli.main verify-tasks --help")
    import sys
    sys.exit(1) 