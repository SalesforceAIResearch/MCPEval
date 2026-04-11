"""
User Simulation module for multi-turn evaluation data generation.

This module provides:
- UserSimulator: LLM-powered user simulation for generating realistic user messages
- ConversationOrchestrator: Drives multi-turn conversation loops between user simulator and agent
- MultiTurnScenarioGenerator: Generates or converts tasks into multi-turn scenarios
- Persona management: Built-in and custom user personas
"""

from mcpeval.simulation.conversation_orchestrator import ConversationOrchestrator
from mcpeval.simulation.personas import (
    DEFAULT_PERSONAS,
    get_random_persona,
    load_personas_from_file,
)
from mcpeval.simulation.scenario_generator import MultiTurnScenarioGenerator
from mcpeval.simulation.user_simulator import UserSimulator

__all__ = [
    "UserSimulator",
    "ConversationOrchestrator",
    "MultiTurnScenarioGenerator",
    "DEFAULT_PERSONAS",
    "load_personas_from_file",
    "get_random_persona",
]
