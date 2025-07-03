#!/usr/bin/env python3
"""
Response Processing Utilities

This module provides helper functions for processing different types of responses,
conversations, and tool call results from LLM interactions.
"""
import logging
from typing import List, Any, Optional, Union, Tuple

from mcp_eval_llm.commons.types import Message, ToolCall, ToolCallResult

logger = logging.getLogger(__name__)


def process_conversation(conversation: List[Any]) -> List[Union[Message, dict]]:
    """Process conversation to ensure content is a string and create proper Message objects.
    
    Args:
        conversation: List of conversation messages
        
    Returns:
        List of processed Message objects or dicts
    """
    processed_conversation = []
    for msg in conversation:
        # Extract fields from the message
        msg_dict = {}
        msg_dict["role"] = msg.get("role", "")
        
        # Handle TextContent objects in the content field
        content = msg.get("content")
        if isinstance(content, list):
            # For list type content (TextContent objects), convert to string
            try:
                # Try to extract text from TextContent objects
                text_contents = []
                for item in content:
                    if hasattr(item, "text"):
                        text_contents.append(item.text)
                
                msg_dict["content"] = "\n".join(text_contents) if text_contents else None
            except Exception as e:
                logger.warning(f"Error processing conversation content: {e}")
                msg_dict["content"] = str(content)
        else:
            msg_dict["content"] = content
        
        # Add other message fields if they exist
        if "tool_call_id" in msg:
            msg_dict["tool_call_id"] = msg["tool_call_id"]
        if "tool_calls" in msg:
            msg_dict["tool_calls"] = msg["tool_calls"]
            
        # Create a proper Message object
        try:
            message = Message(**msg_dict)
            processed_conversation.append(message)
        except Exception as e:
            logger.warning(f"Error creating Message object: {e}. Using dict instead.")
            processed_conversation.append(msg_dict)
    
    return processed_conversation


def process_final_response(final_response: Any) -> str:
    """Process final_response to ensure it's a string.
    
    Args:
        final_response: The final response from LLMTaskVerifier (can be string or list)
        
    Returns:
        String representation of the final response
    """
    if isinstance(final_response, list):
        # For list type content (TextContent objects), convert to string
        try:
            # Try to extract text from TextContent objects
            text_contents = []
            for item in final_response:
                if hasattr(item, "text"):
                    text_contents.append(item.text)
                elif isinstance(item, dict) and "text" in item:
                    text_contents.append(item["text"])
                else:
                    text_contents.append(str(item))
            
            return "\n".join(text_contents) if text_contents else ""
        except Exception as e:
            logger.warning(f"Error processing final_response content: {e}")
            return str(final_response)
    elif final_response is None:
        return ""
    else:
        return str(final_response)


def process_tool_call_results(tool_call_results: Any) -> Optional[List[Tuple[ToolCall, ToolCallResult]]]:
    """Process tool_call_results to ensure proper format.
    
    Args:
        tool_call_results: Tool call results from LLMTaskVerifier
        
    Returns:
        Properly formatted tool call results or None
    """
    if tool_call_results is None:
        return None
    
    # If it's already in the expected format, return as is
    if isinstance(tool_call_results, list):
        processed_results = []
        for item in tool_call_results:
            if isinstance(item, tuple) and len(item) == 2:
                # Already in correct format (ToolCall, ToolCallResult)
                processed_results.append(item)
            else:
                # Try to process into correct format, but if not possible, skip
                logger.warning(f"Unexpected tool_call_results format: {type(item)}")
        
        return processed_results if processed_results else None
    else:
        logger.warning(f"Unexpected tool_call_results type: {type(tool_call_results)}")
        return None 