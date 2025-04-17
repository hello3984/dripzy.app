#!/usr/bin/env python
"""
Simple script to check environment variables and API keys
"""

import os
import sys
from dotenv import load_dotenv
import json
import ssl

# First load environment variables
print("Loading environment variables...")
load_dotenv()

# Check for API keys
api_keys = {
    "SERPAPI_API_KEY": os.environ.get("SERPAPI_API_KEY"),
    "ANTHROPIC_API_KEY": os.environ.get("ANTHROPIC_API_KEY"),
}

print("\n=== API Keys Status ===")
for key_name, key_value in api_keys.items():
    status = "✅ Present" if key_value else "❌ Missing"
    if key_value:
        masked_key = f"{key_value[:4]}...{key_value[-4:]}" if len(key_value) > 8 else "***"
        print(f"{key_name}: {status} ({masked_key})")
    else:
        print(f"{key_name}: {status}")

# Check .env file existence
env_file_path = os.path.join(os.getcwd(), ".env")
env_exists = os.path.exists(env_file_path)
print(f"\n.env file exists: {'✅ Yes' if env_exists else '❌ No'} ({env_file_path})")

# Check paths
print("\n=== File Structure ===")
backend_path = os.path.join(os.getcwd(), "backend")
backend_exists = os.path.exists(backend_path)
print(f"Backend directory exists: {'✅ Yes' if backend_exists else '❌ No'} ({backend_path})")

server_script = os.path.join(backend_path, "run_server.py")
server_script_exists = os.path.exists(server_script)
print(f"run_server.py exists: {'✅ Yes' if server_script_exists else '❌ No'} ({server_script})")

# Check SSL context
print("\n=== SSL Context ===")
try:
    ssl_context = ssl.create_default_context()
    print("✅ Default SSL context can be created")
except Exception as e:
    print(f"❌ SSL context error: {e}")

print("\nTo run the server correctly, use:")
print(f"cd {backend_path} && python run_server.py") 