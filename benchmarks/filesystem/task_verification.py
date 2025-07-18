#!/usr/bin/env python3
"""
Standalone task verification script for filesystem benchmarks.

This script replicates the functionality of:
mcp-eval verify-tasks --server @modelcontextprotocol/server-filesystem 
--server-args "benchmarks/filesystem/working" --model gpt-4.1-2025-04-14 
--prompt-file benchmarks/filesystem/task_verification_prompt.json 
--tasks-file data/filesystem/tasks_test.jsonl 
--output data/filesystem/tasks_test_verified.jsonl
"""

import asyncio
import os
import sys
import shutil
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from mcpeval.cli.mcp_task_verifier.verify import verify_task
from mcpeval.synthesis.utils import load_tasks_from_jsonl
from mcpeval.utils.cli import save_tasks_to_jsonl, generate_output_filename, handle_existing_file, load_prompt_from_file
from dotenv import load_dotenv

# Import shared utilities
from .utils import clear_working_directory

# Load environment variables
load_dotenv()

async def verify_tasks_with_clean_workspace(args):
    """Verify tasks from a JSONL file and save results, clearing workspace before each task."""
    # Load tasks from file
    all_tasks = load_tasks_from_jsonl(args.tasks_file)
    
    # Setup output files
    output_file = generate_output_filename(args.tasks_file, args.output, prefix="verified")
    output_file, _ = handle_existing_file(output_file, non_interactive=True)
    
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
    unverified_file, _ = handle_existing_file(unverified_file, non_interactive=True)
    
    # Get server args and system message
    server_args = getattr(args, 'server_args', [])
    system_message = load_prompt_from_file(getattr(args, 'prompt_file', None))
    
    # Extract working directory from server args
    working_directory = server_args[0] if server_args else None
    
    print(f"Verifying {len(tasks)} tasks...")
    
    # Process tasks
    for i, task in enumerate(tasks):
        print(f"\nProcessing task {i+1}/{len(tasks)}: {task.name}")
        
        # Clear working directory before each task if enabled and directory is specified
        if getattr(args, 'clear_working_dir', False) and working_directory:
            print(f"🔄 Clearing working directory for task: {task.name}")
            success = clear_working_directory(working_directory)
            if not success:
                print(f"⚠️ Warning: Working directory clearing may have failed, proceeding anyway...")
        
        try:
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

class Args:
    """Simple args container to mimic argparse namespace."""
    def __init__(self):
        self.server = "@modelcontextprotocol/server-filesystem"
        self.server_args = ["benchmarks/filesystem/working"]
        self.model = "gpt-4.1-2025-04-14"
        self.prompt_file = "benchmarks/filesystem/task_verification_prompt.json"
        self.tasks_file = "data/filesystem/tasks.jsonl"
        self.output = "data/filesystem/tasks_verified.jsonl"
        self.num_tasks = -1  # Process all tasks
        self.max_turns = 10
        self.api_key = None  # Will use environment variable
        self.clear_working_dir = True  # Enable working directory clearing

async def main():
    """Run the task verification."""
    print("Starting filesystem task verification...")
    print(f"Server: @modelcontextprotocol/server-filesystem")
    print(f"Working directory: benchmarks/filesystem/working")
    print(f"Model: gpt-4.1-2025-04-14")
    print(f"Tasks file: data/filesystem/tasks.jsonl")
    print(f"Output file: data/filesystem/tasks_verified.jsonl")
    print(f"Clear working directory before each task: True")
    print("-" * 50)
    
    # Check if required files exist
    required_files = [
        "benchmarks/filesystem/task_verification_prompt.json",
        "data/filesystem/tasks.jsonl"
    ]
    
    for file_path in required_files:
        if not os.path.exists(file_path):
            print(f"Error: Required file not found: {file_path}")
            return
    
    # Create args object
    args = Args()
    
    # Verify OPENAI_API_KEY is set
    if not os.getenv('OPENAI_API_KEY'):
        print("Error: OPENAI_API_KEY environment variable is not set")
        return
    
    try:
        # Run verification with clean workspace
        await verify_tasks_with_clean_workspace(args)
        print("\nTask verification completed!")
        
    except Exception as e:
        print(f"Error during verification: {e}")
        return

if __name__ == "__main__":
    asyncio.run(main())
