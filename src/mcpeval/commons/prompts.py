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

# ========================================================================
# User Simulation Prompts (Multi-Turn Evaluation)
# ========================================================================

SCENARIO_TYPE_INSTRUCTIONS = {
    "standard": (
        "Provide all necessary information in your requests naturally. "
        "Ask follow-up questions or refine your request based on the assistant's responses."
    ),
    "missing_params": (
        "In your INITIAL message, deliberately leave out some required details "
        "(e.g., specific dates, names, IDs, or parameters) so the assistant must ask "
        "for clarification. Provide the missing information naturally when asked."
    ),
    "missing_functions": (
        "Include at least one request that goes beyond what the available tools can do. "
        "See how the assistant handles the limitation. Then adjust your request to "
        "something the tools can actually accomplish."
    ),
    "composite": (
        "Combine multiple challenges: leave out some required details in your initial "
        "request, include a request that tools cannot fully handle, and add follow-up "
        "requests that build on previous results. Be a realistic but demanding user."
    ),
}

user_simulator_system_prompt = """\
You are simulating a real user interacting with an AI assistant that has access to tools.

## Your Persona
{persona_description}

## Your Goal
{scenario_goal}

## Scenario Context
{scenario_description}

## Available Tools (what the assistant can do)
{tool_descriptions}

## Interaction Guidelines
- Stay in character as the persona throughout the conversation.
- Your first message should be a natural request related to the goal.
- {scenario_type_instructions}
- In follow-up messages, react naturally to the assistant's responses.
- You may ask for modifications, provide additional information, or ask follow-up questions.
- If the assistant asks for clarification, provide it naturally (don't dump all info at once).
- When you believe the goal has been fully accomplished, indicate satisfaction and wrap up.

IMPORTANT: Respond with ONLY the user's message. Do NOT include any meta-commentary, role labels, or explanations outside the user's words."""

user_simulator_followup_prompt = """\
Based on the conversation so far, generate the next message from the user's perspective.

## User's Goal: {scenario_goal}
## Current Turn: {turn_number}
## Persona: {persona_description}

Consider:
- Has the goal been achieved? If so, thank the assistant or ask a related follow-up.
- If the assistant made an error, point it out naturally.
- If partial results were returned, ask for more or refine the request.
- If the assistant asked for clarification, provide the needed information.
- Stay in character.

Respond with ONLY the next user message."""

user_simulator_end_check_prompt = """\
Given the conversation below, has the user's goal been satisfactorily accomplished?

Goal: {scenario_goal}

Conversation:
{conversation_summary}

Respond with ONLY "yes" or "no"."""

multiturn_scenario_generation_system_prompt = """\
You are generating multi-turn conversation scenarios for testing AI agent tool-use capabilities.
Given a set of available tools, create a scenario that requires multiple conversation turns to resolve.

{scenario_type_instructions}

The scenario should feel natural and realistic - something a real user would ask in multiple messages.

IMPORTANT: Your response MUST be ONLY valid JSON with NO markdown, NO comments, and NO extra text:
{{
  "name": "Scenario name",
  "description": "Detailed scenario description and context",
  "goal": "What the user wants to accomplish across multiple turns",
  "scenario_type": "{scenario_type}",
  "max_turns": 5,
  "initial_context": "Optional additional context for the user simulator"
}}"""

multiturn_scenario_generation_user_prompt = """\
Generate a multi-turn conversation scenario using the following tools:
{formatted_tools}

You have already generated the following scenarios:
{existing_scenarios}

Please generate a new scenario that is different from the previous ones.
Ensure the scenario naturally requires multiple conversation turns (not just one request)."""

multiturn_task_conversion_system_prompt = """\
You are converting a single-turn task into a multi-turn conversation scenario.
The original task gives all information at once. Your job is to restructure it so that
a simulated user would naturally reveal the information across multiple conversation turns.

{scenario_type_instructions}

IMPORTANT: Your response MUST be ONLY valid JSON with NO markdown, NO comments, and NO extra text:
{{
  "name": "Scenario name",
  "description": "Restructured scenario description",
  "goal": "The overall goal (same intent as original but framed for multi-turn)",
  "scenario_type": "{scenario_type}",
  "max_turns": {max_turns},
  "initial_context": "What the user knows but may not say upfront"
}}"""

multiturn_task_conversion_user_prompt = """\
Convert this single-turn task into a multi-turn scenario:

Original Task:
- Name: {task_name}
- Description: {task_description}
- Goal: {task_goal}

Available Tools:
{formatted_tools}"""

multiturn_evaluation_system_prompt = """\
You are evaluating a multi-turn conversation between a user and an AI agent with tool access.
Assess the agent's performance across these dimensions:

1. **Clarification Handling** (0-10): Did the agent appropriately ask for missing information? Did it handle user-provided clarifications well?
2. **Context Maintenance** (0-10): Did the agent maintain context across turns? Did it remember what was discussed earlier?
3. **Tool Usage Efficiency** (0-10): Did the agent use tools appropriately? Did it avoid unnecessary calls? Did it use the right tools?
4. **Goal Achievement** (0-10): Was the user's goal ultimately achieved?
5. **Response Quality** (0-10): Were the agent's responses clear, helpful, and natural?

IMPORTANT: Your response MUST be ONLY valid JSON:
{{
  "clarification_handling": <score>,
  "context_maintenance": <score>,
  "tool_usage_efficiency": <score>,
  "goal_achievement": <score>,
  "response_quality": <score>,
  "overall_assessment": "<brief narrative assessment>",
  "per_turn_notes": ["<note for turn 1>", "<note for turn 2>", ...]
}}"""

multiturn_evaluation_user_prompt = """\
## Scenario
- Name: {scenario_name}
- Goal: {scenario_goal}
- Type: {scenario_type}

## Persona
{persona_description}

## Conversation
{conversation}

## Tool Calls Summary
{tool_calls_summary}

Please evaluate the agent's performance."""
