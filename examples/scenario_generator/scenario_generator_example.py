#!/usr/bin/env python
"""
Example of using the ScenarioGenerator to generate scenarios for tool use.

This script demonstrates how to:
1. Set up a ToolLibrary with tool definitions
2. Initialize and use a ScenarioGenerator

Usage:
    python examples/scenario_generator/scenario_generator_example.py

Requirements:
    - OpenAI API key set as an environment variable OPENAI_API_KEY
"""

import os
import logging
from dotenv import load_dotenv
load_dotenv()

from mcp_eval_llm.synthesis.tools import ToolDefinition, ToolLibrary, ToolParameter
from mcp_eval_llm.synthesis.generator import ScenarioGenerator

# Set up logging if LOG_LEVEL environment variable is set
log_level = os.environ.get("LOG_LEVEL", "INFO").upper()
logging.basicConfig(level=getattr(logging, log_level))


def main():
    # Check if OpenAI API key is available
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        print("Warning: OPENAI_API_KEY environment variable not found. Using a mock key for demonstration.")
        api_key = "sk-mock-key-for-demonstration"
    
    # Create a tool library with example tools
    tool_library = create_tool_library()
    print(f"Created tool library with {len(tool_library.tools)} tools")
    
    # Initialize the scenario generator with empty existing_scenario list
    generator = ScenarioGenerator(
        tool_library=tool_library,
        model_provider="openai",
        model_name="gpt-4o",  # You can change this to a different model if needed
        model_temperature=0.7,  # Higher temperature for more creative responses
        max_tokens=1000,
        api_key=api_key,
        existing_scenario=[]  # Initialize with empty list
    )
    
    # Generate a scenario using specific tools
    try:
        print("\nGenerating a scenario for the calculator tool...")
        scenario = generator.generate_scenario_specific_tools(["calculator"])
        print("\nGenerated Scenario:")
        print(f"Name: {scenario.name}")
        print(f"Description: {scenario.description}")
        print(f"Target tools: {scenario.target_tools}")
        
        # Show that scenario was added to the generator's list
        print(f"\nNumber of scenarios in generator's history: {len(generator.existing_scenario)}")
    except Exception as e:
        print(f"Error generating scenario: {e}")
    
    # Generate another scenario with both calculator and web_search tools
    try:
        print("\nGenerating a scenario using both calculator and web_search tools...")
        scenario = generator.generate_scenario_specific_tools(["calculator", "web_search"])
        print("\nGenerated Scenario:")
        print(f"Name: {scenario.name}")
        print(f"Description: {scenario.description}")
        print(f"Target tools: {scenario.target_tools}")
        
        # Show that generator's history has grown
        print(f"\nNumber of scenarios in generator's history: {len(generator.existing_scenario)}")
    except Exception as e:
        print(f"Error generating scenario: {e}")


def create_tool_library():
    """Create and return a tool library with example tools."""
    tool_library = ToolLibrary()
    
    # Add a calculator tool using the parameter list approach
    calculator_params = [
        ToolParameter(
            name="expression",
            type="string",
            description="The mathematical expression to evaluate",
            required=True
        )
    ]
    calculator_tool = tool_library.from_parameters_list(
        name="calculator",
        description="Evaluate mathematical expressions",
        parameters=calculator_params
    )
    
    # Add a web search tool
    web_search_tool = ToolDefinition(
        name="web_search",
        description="Search the web for information",
        inputSchema={
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The search query"
                }
            },
            "required": ["query"]
        }
    )
    tool_library.add_tool(web_search_tool)
    
    return tool_library


if __name__ == "__main__":
    main() 