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
    async def connect_to_server(
        self,
        server_script_path: str,
        server_args: List[str] = None,
        env: Optional[Dict[str, str]] = None,
    ):
        """Connect to an MCP server

        Args:
            server_script_path: Path to the server script (.py or .js)
            server_args: List of arguments to pass to the server script
            env: Optional environment variables dictionary
        """
        pass

    @abstractmethod
    async def connect_to_multiple_servers(
        self,
        server_script_paths: List[str],
        server_args: List[List[str]] = None,
        server_envs: List[Optional[Dict[str, str]]] = None,
    ) -> Dict[str, Dict[str, Any]]:
        """Connect to multiple MCP servers and return a mapping of sessions and tools

        Args:
            server_script_paths: List of paths to the server scripts
            server_args: List of lists of arguments to pass to the server scripts
            server_envs: List of environment variables dictionaries for each server

        Returns:
            Dict: A dictionary mapping server paths to their respective sessions, stdios, writes and tools
        """
        pass

    @abstractmethod
    async def cleanup(self):
        """Clean up resources"""
        pass
