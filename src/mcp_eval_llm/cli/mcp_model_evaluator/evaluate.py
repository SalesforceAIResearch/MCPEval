#!/usr/bin/env python3
"""
Model Evaluator Module

This module provides functionality for evaluating LLM models on MCP tasks.
It enables connecting to an MCP server, executing tasks, and reporting results.
"""
import os
import sys
import json
import asyncio
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
import time

from mcp_eval_llm.eval.task_executor import LLMTaskExecutor
from mcp_eval_llm.commons.types import Task
from mcp_eval_llm.synthesis.utils import load_tasks_from_jsonl
from mcp_eval_llm.client.openai_client import OpenAIMCPClient
from mcp_eval_llm.utils.cli import load_prompt_from_file, load_json
from mcp_eval_llm.models.llms import OpenAIWrapper

# Set up logging
logger = logging.getLogger(__name__)

async def evaluate_performance(tasks: List[Task], model_name: str, model_config: Dict[str, Any], 
                              server_script_path: str = None, server_args: List[str] = None,
                              server_paths: List[str] = None, server_args_list: List[List[str]] = None,
                              output_file: str = None, max_turns: int = 30,
                              prompt_file: str = None):
    """
    Evaluate model performance on tasks using OpenAI client with single or multiple servers.
    
    Args:
        tasks: List of Task objects
        model_name: Name of the model being evaluated
        model_config: Model configuration
        server_script_path: Path to the MCP server script (single server mode)
        server_args: Arguments to pass to the MCP server (single server mode)
        server_paths: List of server paths (multi-server mode)
        server_args_list: List of server arguments (multi-server mode)
        output_file: Path to output file
        max_turns: Maximum number of turns for task execution
        prompt_file: Optional path to JSON file containing system message
    """
    try:
        # Load system message from prompt file if provided
        loaded_system_message = load_prompt_from_file(prompt_file)
        
        if loaded_system_message:
            final_system_message = loaded_system_message
            logger.info(f"Using system message from prompt file: {prompt_file}")
        else:
            final_system_message = "You are a helpful assistant completing tasks using tools."
            logger.info("Using default system message")
            
        # First, check if output file exists and load already tested task IDs
        already_tested_task_ids = set()
        existing_results = []
        if os.path.exists(output_file):
            try:
                existing_results = load_json(output_file)
                already_tested_task_ids = {result.get('task_id') for result in existing_results if result.get('task_id')}
                logger.info(f"Found {len(already_tested_task_ids)} already tested tasks in {output_file}")
            except Exception as e:
                logger.warning(f"Could not load existing results from {output_file}: {e}")
        
        # Create OpenAI client
        logger.info(f"Initializing OpenAI client for model: {model_name} with config: {model_config}")
        
        api_key = model_config.get("api_key") or os.getenv("OPENAI_API_KEY")
        client = OpenAIMCPClient(
            model=model_config.get("model") or model_name,
            system_prompt=final_system_message,
            api_key=api_key,
            base_url=model_config.get("base_url")
        )
        logger.info("OpenAI MCP client created")
        
        # Connect to server(s)
        if server_paths and server_args_list:
            # Multi-server mode
            logger.info(f"Connecting to {len(server_paths)} MCP servers for evaluation")
            await client.connect_to_multiple_servers(server_paths, server_args_list)
            logger.info(f"Connected to {len(server_paths)} MCP servers")
        else:
            # Single server mode (backward compatibility)
            await client.connect_to_server(server_script_path, server_args)
            logger.info(f"Connected to MCP server {server_script_path} with args: {server_args}")
        
        results = existing_results.copy() if existing_results else []
        
        for i, task in enumerate(tasks):
            # Skip tasks that have already been tested
            if task.id in already_tested_task_ids:
                logger.info(f"Skipping task {i+1}/{len(tasks)}: {task.id} (already tested)")
                continue
                
            logger.info(f"Executing task {i+1}/{len(tasks)}: {task.id}")
            
            try:
                # Use the existing OpenAIWrapper from llms.py with same config as client
                wrapped_llm = OpenAIWrapper(
                    model=model_name,
                    model_config=model_config
                )
                executor = LLMTaskExecutor(wrapped_llm)
                
                # Create tool_name_to_session mapping
                if server_paths and server_args_list:
                    # Multi-server mode - use client's tool mapping
                    tool_name_to_session = client.tool_name_to_session
                    logger.debug(f"Using multi-server tool mapping with {len(tool_name_to_session)} tools")
                else:
                    # Single server mode - create mapping for single session
                    tool_name_to_session = {}
                    if hasattr(client, 'session') and client.session:
                        # Get available tools and map them to the session
                        try:
                            available_tools_response = await client.session.list_tools()
                            for tool in available_tools_response.tools:
                                tool_name_to_session[tool.name] = client.session
                        except Exception as e:
                            logger.warning(f"Could not get available tools for OpenAI client: {e}")
                            tool_name_to_session = {tool.name: client.session for tool in task.tools} if task.tools else {}
                
                success, result = await executor.execute_task(
                    task=task,
                    tool_name_to_session=tool_name_to_session,
                    max_turns=max_turns,
                    system_message=final_system_message
                )
                
                # Convert ToolCall objects to dictionaries for JSON serialization
                tool_calls = []
                for tc in result.get("tool_calls", []):
                    if hasattr(tc, "model_dump"):
                        tool_calls.append(tc.model_dump())
                    elif hasattr(tc, "to_dict"):
                        tool_calls.append(tc.to_dict())
                    elif hasattr(tc, "__dict__"):
                        tool_calls.append(tc.__dict__)
                    else:
                        try:
                            tool_call_dict = {}
                            if hasattr(tc, "tool_name"):
                                tool_call_dict["tool_name"] = tc.tool_name
                            if hasattr(tc, "tool_parameters"):
                                tool_call_dict["tool_parameters"] = tc.tool_parameters
                            tool_calls.append(tool_call_dict)
                        except Exception as e:
                            logger.warning(f"Could not convert tool call to dict: {e}")
                            tool_calls.append({"str_representation": str(tc)})
                
                conversation = []
                for msg in result.get("conversation", []):
                    if isinstance(msg, dict):
                        conversation.append(dict(msg))
                    elif hasattr(msg, "model_dump"):
                        conversation.append(msg.model_dump())
                    elif hasattr(msg, "to_dict"):
                        conversation.append(msg.to_dict())
                    elif hasattr(msg, "__dict__"):
                        conversation.append(msg.__dict__)
                    else:
                        conversation.append({"str_representation": str(msg)})
                
                # Create result object
                evaluation_result = {
                    "task_id": task.id,
                    "success": success,
                    "tool_calls": tool_calls,
                    "final_response": result.get("final_response", ""),
                    "conversation": conversation,
                    "task": {
                        "id": task.id,
                        "name": task.name,
                        "description": task.description,
                        "goal": task.goal
                    },
                    "model": model_name,
                    "client_type": "openai"
                }
                
                results.append(evaluation_result)
                
                # Save incremental results after each task
                try:
                    with open(output_file, 'w') as f:
                        json.dump(results, f, indent=2)
                    logger.info(f"Saved incremental results to {output_file}")
                except Exception as save_error:
                    logger.error(f"Error saving incremental results: {save_error}")
                
                logger.info(f"Completed task {i+1}/{len(tasks)}")
            except Exception as task_error:
                logger.error(f"Error executing task {task.id}: {task_error}")
                
                # Check if this is an API key related error
                error_message = str(task_error)
                if "OPENAI_API_KEY" in error_message or "api" in error_message.lower():
                    logger.error("This appears to be an API key related error. Please ensure your OpenAI API key is properly set (OPENAI_API_KEY).")
                
                # Try to capture any partial execution data if the executor was created
                partial_tool_calls = []
                partial_conversation = []
                try:
                    if 'executor' in locals():
                        # Try to get any partial results from the executor
                        # This is best effort - if it fails, we'll just use empty lists
                        pass
                except:
                    pass
                
                error_result = {
                    "task_id": task.id,
                    "success": False,
                    "error": str(task_error),
                    "tool_calls": partial_tool_calls,  # Include any partial tool calls
                    "final_response": f"Error occurred during task execution: {task_error}",
                    "conversation": partial_conversation,  # Include any partial conversation
                    "task": {
                        "id": task.id,
                        "name": task.name,
                        "description": task.description,
                        "goal": task.goal
                    },
                    "model": model_name,
                    "client_type": "openai"
                }
                results.append(error_result)
                
                # Save results after error to preserve progress
                try:
                    with open(output_file, 'w') as f:
                        json.dump(results, f, indent=2)
                    logger.info(f"Saved results after error to {output_file}")
                except Exception as save_error:
                    logger.error(f"Error saving results after error: {save_error}")
                
        # Compute overall statistics
        successful_tasks = sum(1 for r in results if r.get("success", False))
        logger.info(f"Overall success rate: {successful_tasks}/{len(results)} ({successful_tasks/len(results)*100:.2f}%)")
        
        # Cleanup
        await client.cleanup()
        logger.info("Client resources cleaned up")
        
        return results
    except Exception as e:
        logger.exception(f"Error in evaluate_performance: {e}")
        raise

async def run_evaluation(args):
    """
    Run the evaluation process.
    
    Args:
        args: Command line arguments
    """
    try:
        # Create output directory if it doesn't exist
        output_dir = os.path.dirname(args.output)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        # Model configuration
        model_config = {}
        
        # Load model configuration from file if provided
        if hasattr(args, 'model_config') and args.model_config:
            try:
                config_path = Path(args.model_config)
                if not config_path.exists():
                    logger.error(f"Model config file not found: {args.model_config}")
                    return False
                
                with open(config_path, 'r') as f:
                    model_config = json.load(f)
                
                logger.info(f"Loaded model configuration from {args.model_config}")
            except Exception as e:
                logger.error(f"Error loading model config file {args.model_config}: {e}")
                return False
            
        logger.info(f"Model config: {model_config}")
        
        # Determine final model name - prioritize model_config, then fall back to CLI arg
        final_model_name = model_config.get("model") or args.model
        logger.info(f"Using model: {final_model_name} (from {'config file' if model_config.get('model') else 'CLI argument'})")
        

        
        # Load tasks
        tasks = load_tasks_from_jsonl(args.tasks_file)
        logger.info(f"Loaded {len(tasks)} tasks from {args.tasks_file}")
        
        if not tasks:
            logger.error(f"No tasks loaded from {args.tasks_file}")
            return False
        
        # Limit number of tasks if specified
        if args.num_tasks > 0:
            tasks = tasks[:args.num_tasks]
            logger.info(f"Limiting evaluation to first {args.num_tasks} tasks")
        
        # If force_rerun is specified, rename the existing output file as a backup
        if hasattr(args, 'force_rerun') and args.force_rerun and os.path.exists(args.output):
            backup_file = f"{args.output}.bak.{int(time.time())}"
            os.rename(args.output, backup_file)
            logger.info(f"Renamed existing output file to {backup_file} for force rerun")
        
        # Evaluate performance
        if hasattr(args, 'server_paths') and args.server_paths:
            # Multi-server mode
            results = await evaluate_performance(
                tasks=tasks, 
                model_name=final_model_name, 
                model_config=model_config, 
                server_paths=args.server_paths,
                server_args_list=args.server_args_list,
                output_file=args.output,
                max_turns=args.max_turns if hasattr(args, 'max_turns') else 3,
                prompt_file=args.prompt_file if hasattr(args, 'prompt_file') else None
            )
        else:
            # Single server mode (backward compatibility)
            results = await evaluate_performance(
                tasks=tasks, 
                model_name=final_model_name, 
                model_config=model_config, 
                server_script_path=args.server, 
                server_args=args.server_args if hasattr(args, 'server_args') else [],
                output_file=args.output,
                max_turns=args.max_turns if hasattr(args, 'max_turns') else 3,
                prompt_file=args.prompt_file if hasattr(args, 'prompt_file') else None
            )
        
        logger.info(f"Evaluation complete. Results saved to {args.output}")
        
        # Print summary statistics
        successful_tasks = sum(1 for r in results if r.get("success", False))
        total_tasks = len(results)
        success_rate = successful_tasks/total_tasks*100 if total_tasks > 0 else 0
        
        # Color utilities (simple inline version)
        GREEN = '\033[92m'
        BLUE = '\033[94m'
        YELLOW = '\033[93m'
        CYAN = '\033[96m'
        BOLD = '\033[1m'
        RESET = '\033[0m'
        
        if sys.stdout.isatty():
            print(f"\n{CYAN}{BOLD}📊 Evaluation Summary:{RESET}")
            print(f"{CYAN}{'─' * 50}{RESET}")
            print(f"{BLUE}Model:{RESET} {BOLD}{final_model_name}{RESET}")
            print(f"{BLUE}Client Type:{RESET} {BOLD}openai{RESET}")
            print(f"{BLUE}Tasks evaluated:{RESET} {BOLD}{total_tasks}{RESET}")
            print(f"{GREEN}Tasks completed successfully:{RESET} {BOLD}{successful_tasks}{RESET}")
            
            # Color-code success rate
            if success_rate >= 80:
                rate_color = GREEN
            elif success_rate >= 60:
                rate_color = YELLOW
            else:
                rate_color = '\033[91m'  # Red
                
            print(f"{BLUE}Success rate:{RESET} {rate_color}{BOLD}{success_rate:.2f}%{RESET}")
            print(f"{BLUE}Results saved to:{RESET} {BOLD}{args.output}{RESET}")
        else:
            print(f"\nEvaluation Summary:")
            print(f"-------------------")
            print(f"Model: {final_model_name}")
            print(f"Client Type: openai")
            print(f"Tasks evaluated: {total_tasks}")
            print(f"Tasks completed successfully: {successful_tasks}")
            print(f"Success rate: {success_rate:.2f}%")
            print(f"Results saved to: {args.output}")
        
        return True
        
    except Exception as e:
        logger.exception(f"Error in run_evaluation: {e}")
        if sys.stdout.isatty():
            RED = '\033[91m'
            BOLD = '\033[1m'
            RESET = '\033[0m'
            print(f"{RED}{BOLD}❌ Evaluation failed: {e}{RESET}")
        else:
            print(f"Evaluation failed: {e}")
        return False

def main(args):
    """
    Main entry point for the model evaluator.
    
    Args:
        args: Command line arguments
    """
    try:
        # Run the evaluation asynchronously
        success = asyncio.run(run_evaluation(args))
        
        # Only show success message if evaluation actually completed
        if not success:
            # run_evaluation already printed the appropriate error message
            sys.exit(1)
            
    except KeyboardInterrupt:
        logger.info("Evaluation interrupted by user")
        if sys.stdout.isatty():
            YELLOW = '\033[93m'
            BOLD = '\033[1m'
            RESET = '\033[0m'
            print(f"\n{YELLOW}{BOLD}⚠️  Evaluation interrupted by user{RESET}")
        else:
            print("Evaluation interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.exception(f"Error in model evaluator main: {e}")
        if sys.stdout.isatty():
            RED = '\033[91m'
            BOLD = '\033[1m'
            RESET = '\033[0m'
            print(f"{RED}{BOLD}❌ Evaluation failed: {e}{RESET}")
        else:
            print(f"Evaluation failed: {e}")
        sys.exit(1) 