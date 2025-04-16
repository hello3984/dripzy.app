import os
from pathlib import Path
from dotenv import load_dotenv
import sys

# Print Python version and path
print(f"Python version: {sys.version}")
print(f"Python executable: {sys.executable}")

# Print the current working directory
print(f"Current working directory: {os.getcwd()}")

# Check if .env exists in current directory
print(f".env file exists in current directory: {Path('.env').exists()}")

# Try to find .env in parent directories
parent_dir = Path(os.getcwd()).parent
print(f".env file exists in parent directory: {(parent_dir / '.env').exists()}")

# Try loading with dotenv explicitly
print("\nTrying to load .env with python-dotenv:")
loaded = load_dotenv()
print(f"Loaded successfully: {loaded}")

# Check specific variables
serpapi_key = os.getenv("SERPAPI_API_KEY")
print(f"SERPAPI_API_KEY found: {bool(serpapi_key)}")
if serpapi_key:
    print(f"SERPAPI_API_KEY value: {serpapi_key[:4]}...{serpapi_key[-4:]}")

# Try with different paths
print("\nTrying to load from specific paths:")
for path in ['.env', '../.env', '../../.env']:
    exists = Path(path).exists()
    print(f"Path {path} exists: {exists}")
    if exists:
        loaded = load_dotenv(path)
        print(f"Loaded {path}: {loaded}")
        serpapi_key = os.getenv("SERPAPI_API_KEY")
        print(f"SERPAPI_API_KEY after loading {path}: {bool(serpapi_key)}")

# Check if python-dotenv is installed
print("\nCheck python-dotenv installation:")
try:
    import pkg_resources
    version = pkg_resources.get_distribution("python-dotenv").version
    print(f"python-dotenv version: {version}")
except Exception as e:
    print(f"Error checking python-dotenv: {e}")

# Check environment variables
print("\nChecking environment variables:")
serpapi_key = os.environ.get("SERPAPI_API_KEY")
if serpapi_key:
    print(f"SERPAPI_API_KEY found: {serpapi_key[:4]}...{serpapi_key[-4:] if len(serpapi_key) > 8 else ''}")
else:
    print("SERPAPI_API_KEY not found")

serpapi_key_alt = os.environ.get("SERPAPI_KEY")
if serpapi_key_alt:
    print(f"SERPAPI_KEY found: {serpapi_key_alt[:4]}...{serpapi_key_alt[-4:] if len(serpapi_key_alt) > 8 else ''}")
else:
    print("SERPAPI_KEY not found")

# Print all environment variables (optional)
print("\nAll environment variables:")
for key, value in os.environ.items():
    if "API" in key or "KEY" in key or "SECRET" in key:
        masked_value = value[:4] + "..." + value[-4:] if len(value) > 8 else "[MASKED]"
        print(f"{key}: {masked_value}")

print("\nDone testing environment variables") 