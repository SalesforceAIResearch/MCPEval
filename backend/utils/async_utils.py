import asyncio
import threading
from typing import Optional


class EventLoopManager:
    """Manages a persistent event loop for MCP operations"""
    
    def __init__(self):
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._thread: Optional[threading.Thread] = None
        self._loop_ready = threading.Event()
    
    def start_loop(self):
        """Start the persistent event loop in a background thread"""
        if self._loop is not None and not self._loop.is_closed():
            return  # Loop already running
        
        self._loop_ready.clear()
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()
        self._loop_ready.wait()  # Wait for loop to be ready
    
    def _run_loop(self):
        """Run the event loop in the background thread"""
        self._loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._loop)
        self._loop_ready.set()  # Signal that loop is ready
        try:
            self._loop.run_forever()
        finally:
            self._loop.close()
    
    def run_async(self, coro):
        """Run an async function in the persistent event loop"""
        if self._loop is None or self._loop.is_closed():
            self.start_loop()
        
        # Schedule the coroutine in the background loop
        future = asyncio.run_coroutine_threadsafe(coro, self._loop)
        return future.result()  # Block until complete
    
    def stop_loop(self):
        """Stop the persistent event loop"""
        if self._loop and not self._loop.is_closed():
            self._loop.call_soon_threadsafe(self._loop.stop)
            if self._thread:
                self._thread.join(timeout=5)
        self._loop = None
        self._thread = None


# Global event loop manager for MCP operations
_mcp_loop_manager = EventLoopManager()


def run_async_function(async_func):
    """
    Helper function to run async functions consistently in the same event loop
    This ensures MCP connections remain valid across multiple operations
    """
    try:
        return _mcp_loop_manager.run_async(async_func())
    except Exception as e:
        print(f"Error in run_async_function: {e}")
        import traceback
        traceback.print_exc()
        raise e


def cleanup_event_loop():
    """Cleanup the persistent event loop"""
    global _mcp_loop_manager
    _mcp_loop_manager.stop_loop() 