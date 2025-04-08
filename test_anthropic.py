import os
from dotenv import load_dotenv
import anthropic

# Load environment variables
load_dotenv()

# Get API key
api_key = os.getenv("ANTHROPIC_API_KEY")

if not api_key:
    print("ERROR: ANTHROPIC_API_KEY not found in .env file")
    exit(1)

print(f"API key found: {api_key[:5]}...{api_key[-4:]}")

# Initialize Anthropic client
try:
    client = anthropic.Anthropic(api_key=api_key)
    print("Successfully initialized Anthropic client")
except Exception as e:
    print(f"ERROR initializing client: {e}")
    exit(1)

# Test API with a simple request
try:
    response = client.messages.create(
        model="claude-3-haiku-20240307",
        max_tokens=100,
        system="You are a helpful assistant.",
        messages=[
            {"role": "user", "content": "Say 'API test successful' if you can read this message."}
        ]
    )
    print("\nAPI RESPONSE:")
    print(response.content[0].text)
    print("\nAPI TEST SUCCESSFUL!")
except Exception as e:
    print(f"\nAPI TEST FAILED: {e}") 