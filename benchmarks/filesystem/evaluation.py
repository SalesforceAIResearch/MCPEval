#!/usr/bin/env python3
"""
Simplified Filesystem Model Evaluation Script

This script evaluates gpt-4o model performance on filesystem tasks,
clearing the working directory before each task to ensure independence.
"""

import asyncio
import os
import sys
import json
import shutil
import time
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from mcpeval.eval.task_executor import LLMTaskExecutor
from mcpeval.models.llms import OpenAIWrapper
from mcpeval.client.openai_client import OpenAIMCPClient
from mcpeval.synthesis.utils import load_tasks_from_jsonl
from mcpeval.utils.cli import load_prompt_from_file
from dotenv import load_dotenv

# Import shared utilities
from utils import clear_working_directory

# Load environment variables
load_dotenv()

class FilesystemEvaluator:
    """Simplified evaluator for filesystem tasks."""
    
    def __init__(self, model_name="gpt-4o", working_dir="benchmarks/filesystem/working"):
        self.model_name = model_name
        self.working_dir = working_dir
        self.server_path = "@modelcontextprotocol/server-filesystem"
        self.server_args = [working_dir]
        
    async def evaluate_task(self, task, system_message=None, max_turns=10):
        """Evaluate a single task."""
        print(f"\n🔍 Evaluating task: {task.name}")
        
        # Clear working directory before each task
        print(f"🔄 Clearing working directory for task: {task.name}")
        success = clear_working_directory(self.working_dir)
        if not success:
            print(f"⚠️ Warning: Working directory clearing may have failed, proceeding anyway...")
        
        # Create OpenAI client
        client = OpenAIMCPClient(
            model=self.model_name,
            system_prompt=system_message or "You are a helpful assistant completing filesystem tasks using tools.",
            api_key=os.getenv("OPENAI_API_KEY")
        )
        
        try:
            # Connect to MCP server using connect_to_multiple_servers
            # Convert single server to list format for connect_to_multiple_servers
            server_paths = [self.server_path]
            server_args_list = [self.server_args] if self.server_args else [None]
            server_envs = None
            await client.connect_to_multiple_servers(server_paths, server_args_list, server_envs)
            print(f"🔗 Connected to filesystem server")
            
            # Create executor
            llm = OpenAIWrapper(model=self.model_name)
            executor = LLMTaskExecutor(llm)
            
            # Create tool mapping
            tool_name_to_session = {}
            try:
                available_tools = await client.get_all_tools()
                for tool in available_tools:
                    tool_name_to_session[tool.name] = client.tool_name_to_session[tool.name]
            except Exception as e:
                print(f"⚠️  Warning: Could not get available tools: {e}")
                tool_name_to_session = client.tool_name_to_session if client.tool_name_to_session else {}
            
            # Execute task
            start_time = time.time()
            success, result = await executor.execute_task(
                task=task,
                tool_name_to_session=tool_name_to_session,
                max_turns=max_turns,
                system_message=system_message
            )
            execution_time = time.time() - start_time
            
            # Process results
            tool_calls = []
            for tc in result.get("tool_calls", []):
                if hasattr(tc, "model_dump"):
                    tool_calls.append(tc.model_dump())
                elif hasattr(tc, "__dict__"):
                    tool_calls.append({
                        "tool_name": getattr(tc, "tool_name", "unknown"),
                        "tool_parameters": getattr(tc, "tool_parameters", {})
                    })
                else:
                    tool_calls.append({"str_representation": str(tc)})
            
            conversation = []
            for msg in result.get("conversation", []):
                if isinstance(msg, dict):
                    conversation.append(dict(msg))
                elif hasattr(msg, "model_dump"):
                    conversation.append(msg.model_dump())
                else:
                    conversation.append({"str_representation": str(msg)})
            
            # Create evaluation result
            evaluation_result = {
                "task_id": task.id,
                "task_name": task.name,
                "success": success,
                "execution_time": execution_time,
                "tool_calls_count": len(tool_calls),
                "tool_calls": tool_calls,
                "final_response": result.get("final_response", ""),
                "conversation": conversation,
                "model": self.model_name,
                "timestamp": time.time()
            }
            
            print(f"{'✅' if success else '❌'} Task completed in {execution_time:.2f}s - {len(tool_calls)} tool calls")
            return evaluation_result
            
        except Exception as e:
            print(f"❌ Error executing task: {e}")
            return {
                "task_id": task.id,
                "task_name": task.name,
                "success": False,
                "error": str(e),
                "execution_time": 0,
                "tool_calls_count": 0,
                "tool_calls": [],
                "final_response": f"Error: {e}",
                "conversation": [],
                "model": self.model_name,
                "timestamp": time.time()
            }
        finally:
            # Cleanup
            await client.cleanup()

    async def evaluate_all_tasks(self, tasks_file, output_file, system_prompt_file=None, max_turns=10):
        """Evaluate all tasks and save results."""
        print(f"🚀 Starting filesystem evaluation with {self.model_name}")
        print(f"📋 Tasks file: {tasks_file}")
        print(f"💾 Output file: {output_file}")
        print(f"🏠 Working directory: {self.working_dir}")
        print("-" * 60)
        
        # Load system message
        system_message = None
        if system_prompt_file:
            system_message = load_prompt_from_file(system_prompt_file)
            if system_message:
                print(f"📝 Loaded system message from: {system_prompt_file}")
        
        # Load tasks
        tasks = load_tasks_from_jsonl(tasks_file)
        print(f"📚 Loaded {len(tasks)} tasks")
        
        if not tasks:
            print("❌ No tasks found!")
            return
        
        # Load existing results to avoid re-running
        existing_results = []
        completed_task_ids = set()
        if os.path.exists(output_file):
            try:
                with open(output_file, 'r') as f:
                    existing_results = json.load(f)
                # Filter out results without task_id to be more robust
                completed_task_ids = {result.get('task_id') for result in existing_results if result.get('task_id')}
                print(f"📄 Found {len(completed_task_ids)} already completed tasks")
            except Exception as e:
                print(f"⚠️  Warning: Could not load existing results: {e}")
        
        # Clear working directory at the start of evaluation
        print(f"🔄 Ensuring working directory is clean before starting evaluation...")
        clear_working_directory(self.working_dir)
        
        # Evaluate tasks
        results = existing_results.copy()
        success_count = 0
        total_time = 0
        
        for i, task in enumerate(tasks):
            # Skip tasks that have already been tested
            if task.id in completed_task_ids:
                print(f"⏭️  Skipping task {i+1}/{len(tasks)}: {task.id} (already completed)")
                # Count existing successful tasks
                existing_result = next((r for r in existing_results if r.get('task_id') == task.id), None)
                if existing_result and existing_result.get('success'):
                    success_count += 1
                continue
            
            print(f"\n📋 Task {i+1}/{len(tasks)}")
            
            try:
                result = await self.evaluate_task(task, system_message, max_turns)
                results.append(result)
                
                if result['success']:
                    success_count += 1
                
                total_time += result.get('execution_time', 0)
                
                # Save incremental results after each task
                try:
                    os.makedirs(os.path.dirname(output_file), exist_ok=True)
                    with open(output_file, 'w') as f:
                        json.dump(results, f, indent=2)
                    print(f"💾 Saved incremental results")
                except Exception as save_error:
                    print(f"⚠️  Warning: Error saving incremental results: {save_error}")
                
                print(f"✅ Completed task {i+1}/{len(tasks)}")
                
            except Exception as task_error:
                print(f"❌ Error executing task {task.id}: {task_error}")
                
                # Create error result to preserve progress
                error_result = {
                    "task_id": task.id,
                    "task_name": task.name,
                    "success": False,
                    "error": str(task_error),
                    "execution_time": 0,
                    "tool_calls_count": 0,
                    "tool_calls": [],
                    "final_response": f"Error occurred during task execution: {task_error}",
                    "conversation": [],
                    "model": self.model_name,
                    "timestamp": time.time()
                }
                results.append(error_result)
                
                # Save results after error to preserve progress
                try:
                    os.makedirs(os.path.dirname(output_file), exist_ok=True)
                    with open(output_file, 'w') as f:
                        json.dump(results, f, indent=2)
                    print(f"💾 Saved results after error")
                except Exception as save_error:
                    print(f"⚠️  Warning: Error saving results after error: {save_error}")
            
            # Brief pause to avoid overwhelming
            await asyncio.sleep(1)
        
        # Final summary
        total_tasks = len(results)
        success_rate = (success_count / total_tasks * 100) if total_tasks > 0 else 0
        avg_time = total_time / len([r for r in results if r.get('execution_time', 0) > 0]) if results else 0
        
        print(f"\n{'='*60}")
        print(f"🎯 EVALUATION SUMMARY")
        print(f"{'='*60}")
        print(f"🤖 Model: {self.model_name}")
        print(f"📊 Total tasks: {total_tasks}")
        print(f"✅ Successful: {success_count}")
        print(f"❌ Failed: {total_tasks - success_count}")
        print(f"📈 Success rate: {success_rate:.1f}%")
        print(f"⏱️  Average time per task: {avg_time:.2f}s")
        print(f"💾 Results saved to: {output_file}")
        print(f"{'='*60}")
        
        return results

async def main():
    """Main evaluation function."""
    # Configuration
    tasks_file = "data/filesystem/tasks_verified.jsonl"
    output_file = "data/filesystem/evaluation_results.json"
    system_prompt_file = "benchmarks/filesystem/filesystem_eval_prompt.json"
    working_dir = "benchmarks/filesystem/working"
    model_name = "gpt-4o"
    max_turns = 30
    
    # Check if required files exist
    required_files = [tasks_file, system_prompt_file]
    for file_path in required_files:
        if not os.path.exists(file_path):
            print(f"❌ Required file not found: {file_path}")
            return
    
    # Check API key
    if not os.getenv('OPENAI_API_KEY'):
        print("❌ OPENAI_API_KEY environment variable is not set")
        print("Please set your OpenAI API key:")
        print("export OPENAI_API_KEY='your-api-key-here'")
        return
    
    # Create evaluator and run evaluation
    evaluator = FilesystemEvaluator(model_name=model_name, working_dir=working_dir)
    
    try:
        await evaluator.evaluate_all_tasks(
            tasks_file=tasks_file,
            output_file=output_file,
            system_prompt_file=system_prompt_file,
            max_turns=max_turns
        )
        print("🎉 Evaluation completed successfully!")
        
    except Exception as e:
        print(f"💥 Evaluation failed: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(main())
