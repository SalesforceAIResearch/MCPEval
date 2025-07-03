import asyncio
import sys
import os
from dotenv import load_dotenv
import logging
import argparse

# Load environment variables from .env
load_dotenv()

# Set up logging
logger = logging.getLogger(__name__)
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", logging.INFO),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))
from mcp_eval_llm.client.openai_client import OpenAIMCPClient

def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description='OpenAI MCP Client')
    parser.add_argument('server_script', help='Path to the server script')
    parser.add_argument('server_args', nargs='*', help='Arguments to pass to the server')
    parser.add_argument('--model', '-m', default='gpt-4o', 
                       help='OpenAI model to use (default: gpt-4o)')
    return parser.parse_args()

async def main():
    args = parse_arguments()
    
    logger.info(f"Received command line arguments: {sys.argv}")
    logger.info(f"Server script path: {args.server_script}")
    logger.info(f"Server args: {args.server_args}")
    logger.info(f"Model: {args.model}")

    client = OpenAIMCPClient(model=args.model)
    logger.info(f"OpenAI MCP client created with model: {args.model}")
    try:
        await client.connect_to_server(args.server_script, args.server_args)
        await client.chat()
    finally:
        logger.info("Cleaning up resources")
        await client.cleanup()

if __name__ == "__main__":
    asyncio.run(main())