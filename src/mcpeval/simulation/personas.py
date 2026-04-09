"""
Persona definitions for user simulation.

Provides built-in default personas and utilities for loading custom personas from JSON files.
"""

import json
import random
import logging
from typing import List, Optional

from mcpeval.commons.types import Persona

logger = logging.getLogger(__name__)

DEFAULT_PERSONAS = [
    Persona(
        name="Casual User",
        description=(
            "A regular user with limited technical knowledge. They describe what they want "
            "in everyday language, may be vague about specifics, and sometimes need guidance "
            "on what information to provide."
        ),
        communication_style="casual and conversational",
        expertise_level="novice",
    ),
    Persona(
        name="Technical Expert",
        description=(
            "A software engineer who knows exactly what they want. They use precise terminology, "
            "provide structured requests, and expect detailed, accurate responses. They may "
            "challenge the assistant if results seem wrong."
        ),
        communication_style="precise and technical",
        expertise_level="expert",
    ),
    Persona(
        name="Busy Executive",
        description=(
            "A time-pressed executive who communicates in short, direct messages. They want "
            "quick results without lengthy explanations. They may provide minimal context and "
            "expect the assistant to fill in reasonable defaults."
        ),
        communication_style="terse and direct",
        expertise_level="intermediate",
    ),
    Persona(
        name="Detail-Oriented Analyst",
        description=(
            "A data analyst who is thorough and methodical. They ask many follow-up questions, "
            "want to understand the data behind results, and often request modifications or "
            "additional analyses based on initial findings."
        ),
        communication_style="verbose and analytical",
        expertise_level="expert",
    ),
    Persona(
        name="Non-Native Speaker",
        description=(
            "A user who communicates in simple, straightforward English. They may occasionally "
            "use unusual phrasing or be less precise in their requests, but their intent is clear. "
            "They appreciate clear, simple responses."
        ),
        communication_style="simple and straightforward",
        expertise_level="intermediate",
    ),
]


def load_personas_from_file(file_path: str) -> List[Persona]:
    """Load personas from a JSON file.

    Expected format: a JSON array of persona objects, each with at least
    'name' and 'description' fields.

    Args:
        file_path: Path to the JSON file containing persona definitions.

    Returns:
        List of Persona objects.
    """
    with open(file_path, "r") as f:
        data = json.load(f)

    personas = []
    items = data if isinstance(data, list) else [data]
    for item in items:
        personas.append(Persona(**item))

    logger.info(f"Loaded {len(personas)} personas from {file_path}")
    return personas


def get_random_persona(pool: Optional[List[Persona]] = None) -> Persona:
    """Get a random persona from the pool or defaults.

    Args:
        pool: Optional list of personas to choose from. Uses DEFAULT_PERSONAS if None.

    Returns:
        A randomly selected Persona.
    """
    source = pool if pool else DEFAULT_PERSONAS
    return random.choice(source)
