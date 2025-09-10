scenario_generation_system_prompt = """
You are a helpful assistant that generates scenarios to test the use of tools. 
## Principles
- Ensure your scenarios are different from the ones already generated.
- The scenarios should be related to both the tools and the input of tools.
- More details are better.
"""

scenario_generation_user_prompt = """
Generate a scenario where the assistant uses the following tools:
{tools}
You have already generated the following scenarios:
{scenarios}
Please generate a new scenario that is different from the previous ones.
"""

task_generation_system_prompt = """
You are a helpful assistant that generates tasks for testing LLM tool use capabilities.
Tasks should be specific, clear, and realistic. Ensure all the required information from the tools is explicitly mentioned in the task description.

IMPORTANT: Your response MUST be ONLY valid JSON, with NO markdown, NO comments, and NO extra text. Do NOT include any explanations or formatting outside the JSON. All property names and string values must be double-quoted. The output must be directly parsable by Python's json.loads().

The required JSON structure is:
{
  "name": "Task name",
  "description": "Detailed task description",
  "goal": "Goal of the task"
}
"""

task_generation_with_tools_user_prompt = """
Generate a task that requires using the following tools:
{formatted_tools}
Generate a task that is different from the existing tasks:
{existing_tasks}
Ensure that your task is creative, specific, and realistic.
The task description should clearly indicate how the provided tools would be used to accomplish the goal.
"""

task_revision_system_prompt = """\
You are a helpful assistant that modifies tasks for testing LLM tool use capabilities.
Tasks should be specific, clear, and ensure all the required information from the tools is explicitly mentioned in the task description.

IMPORTANT: Your response MUST be ONLY valid JSON, with NO markdown, NO comments, and NO extra text. Do NOT include any explanations or formatting outside the JSON. All property names and string values must be double-quoted. The output must be directly parsable by Python's json.loads().

The required JSON structure is:
{
  "name": "Task name",
  "description": "Detailed task description",
  "goal": "Goal of the task",
}
"""

task_revision_user_prompt = """\
You have already generated a task 
{task}
that requires using the following tools:
{formatted_tools}
Please update the task based on the feedback:
{feedback}
"""

task_verification_system_prompt = """You are an AI assistant that helps complete tasks using available tools.
Use the provided tools to interact with external systems and complete the given task.
If the task is unclear or missing any information, use the request_task_updating tool to ask for clarification.
Otherwise, attempt to use the provided tools to complete the task."""

task_executor_system_prompt = """You are an AI assistant completing tasks via using tools. Call tools until you have completed the task."""

# New: task revalidation prompts
task_revalidation_system_prompt = """You are a precise editor that updates task descriptions so they fully reflect the actual tool usage observed in a conversation.

Requirements:
- Ensure the description explicitly includes all key inputs/assumptions that were actually used in tool calls.
- If the goal needs refinement to match the achieved outcome, update it minimally for accuracy.
- Preserve the task name unless a tiny tweak improves clarity.
- Do not invent details not evidenced in the conversation or tool results.
- Do not include information that was only known after the tool calls.

IMPORTANT: Your response MUST be ONLY valid JSON, with NO markdown, NO comments, and NO extra text. All property names and string values must be double-quoted. The output must be directly parsable by Python's json.loads().

The required JSON structure is:
{
  "name": "Task name",
  "description": "Detailed task description that includes all actually used details",
  "goal": "Accurate goal aligned to the tool usage and final outcome"
}
"""

task_revalidation_user_prompt = """You are given an original task and the actual interaction where tools were called.

## Original task:
{task}

## Available tools at the time:
{formatted_tools}

## Actual conversation (ordered messages):
{conversation}

## Actual tool calls (with parameters) and results:
{tool_calls_and_results}
"""
