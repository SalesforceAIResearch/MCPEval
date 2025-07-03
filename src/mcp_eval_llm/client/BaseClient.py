import asyncio
from typing import Optional, List, Dict, Any
from contextlib import AsyncExitStack
import json
import sys
from abc import ABC, abstractmethod

from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()  # load environment variables from .env

class BaseClient(ABC):
    session: Optional[Any] = None
    stdio: Optional[Any] = None
    write: Optional[Any] = None
        
    @abstractmethod
    async def connect_to_server(self, server_script_path: str):
        """Connect to an MCP server

        Args:
            server_script_path: Path to the server script (.py or .js)
        """
        pass

    @abstractmethod
    async def cleanup(self):
        """Clean up resources"""
        pass
