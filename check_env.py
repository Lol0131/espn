#!/usr/bin/env python3
"""
Quick script to check if .env file is set up correctly
"""
import os
from dotenv import load_dotenv

load_dotenv()

print("=" * 50)
print("Checking .env Configuration")
print("=" * 50)

# Check if .env file exists
env_file = os.path.join(os.path.dirname(__file__), ".env")
if os.path.exists(env_file):
    print("✓ .env file exists")
    with open(env_file, 'r') as f:
        content = f.read()
        if "OPENAI_API_KEY" in content:
            print("✓ OPENAI_API_KEY found in .env file")
        else:
            print("✗ OPENAI_API_KEY not found in .env file")
else:
    print("✗ .env file not found")
    print("  Create a .env file with: OPENAI_API_KEY=your_key_here")

# Check API key
api_key = os.getenv("OPENAI_API_KEY", "")
if api_key:
    api_key = api_key.strip().strip('"').strip("'")
    print(f"\nAPI Key Status:")
    print(f"  Length: {len(api_key)} characters")
    print(f"  Starts with: {api_key[:7] if len(api_key) >= 7 else api_key}...")
    
    if api_key == "your_openai_api_key_here" or api_key == "":
        print("  ✗ Using placeholder value - please set your actual API key")
    elif not api_key.startswith("sk-"):
        print("  ✗ Invalid format - API key should start with 'sk-'")
    elif len(api_key) < 20:
        print("  ✗ Key seems too short - OpenAI API keys are typically ~51 characters")
    else:
        print("  ✓ API key format looks valid")
        
    # Check for common issues
    if "\n" in api_key or "\r" in api_key:
        print("  ⚠ Warning: API key contains newlines - this may cause issues")
    if " " in api_key and not api_key.startswith("sk-"):
        print("  ⚠ Warning: API key contains spaces")
else:
    print("\n✗ OPENAI_API_KEY not set in environment")

print("\n" + "=" * 50)
print("To fix issues:")
print("1. Make sure your .env file contains: OPENAI_API_KEY=sk-...")
print("2. No spaces around the = sign")
print("3. No quotes around the key value")
print("4. No newlines in the key")
print("=" * 50)

