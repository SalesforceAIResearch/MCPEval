#!/usr/bin/env python3
"""
Convenience script to run tests with .env file loaded
"""

import os
from pathlib import Path

env_file = Path(__file__).parent / ".env"
if env_file.exists():
    print(f"Loading environment from {env_file}")
    with open(env_file) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#"):
                key, value = line.split("=", 1)
                os.environ[key] = value
    print("✓ Loaded API key\n")

from test_gateway import main

if __name__ == "__main__":
    main()
