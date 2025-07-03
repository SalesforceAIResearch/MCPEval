#!/usr/bin/env python3
"""
Shared utilities for filesystem benchmarks.
"""

import os
import shutil


def clear_working_directory(working_dir):
    """Clear the working directory to ensure task independence."""
    try:
        if os.path.exists(working_dir):
            print(f"🧹 Clearing working directory: {working_dir}")
            # Remove the entire directory and recreate it for a complete clean slate
            shutil.rmtree(working_dir)
            os.makedirs(working_dir, exist_ok=True)
            print(f"✅ Working directory cleared and recreated")
        else:
            # Create the directory if it doesn't exist
            os.makedirs(working_dir, exist_ok=True)
            print(f"📁 Created working directory: {working_dir}")
            
        # Verify the directory exists and is empty
        if not os.path.exists(working_dir):
            print(f"❌ Error: Working directory does not exist after creation!")
            return False
        elif os.listdir(working_dir):
            print(f"⚠️ Warning: Working directory is not empty after clearing!")
            return False
        return True
        
    except Exception as e:
        print(f"❌ Error clearing working directory {working_dir}: {e}")
        # Try to create it anyway
        try:
            os.makedirs(working_dir, exist_ok=True)
            return True
        except Exception as create_error:
            print(f"❌ Failed to create working directory: {create_error}")
            return False 