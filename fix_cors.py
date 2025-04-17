#!/usr/bin/env python
"""
Script to check and fix CORS configuration in the backend
"""
import os
import re
import sys

# Path to main.py
MAIN_PY_PATH = 'backend/app/main.py'

def check_cors_config():
    """Check if CORS is properly configured and fix it if needed"""
    if not os.path.exists(MAIN_PY_PATH):
        print(f"Error: {MAIN_PY_PATH} not found")
        return False
    
    with open(MAIN_PY_PATH, 'r') as f:
        content = f.read()
    
    # Check if localhost:3006 is in allow_origins
    cors_pattern = r"allow_origins=\[(.*?)\]"
    cors_match = re.search(cors_pattern, content, re.DOTALL)
    
    if not cors_match:
        print("Error: Could not find CORS configuration in main.py")
        return False
    
    cors_origins = cors_match.group(1)
    
    if '"http://localhost:3006"' not in cors_origins and "'http://localhost:3006'" not in cors_origins:
        print("CORS configuration needs to be updated to include localhost:3006")
        
        # Add localhost:3006 to origins
        updated_origins = cors_origins
        if updated_origins.strip().endswith(','):
            updated_origins += " 'http://localhost:3006'"
        else:
            updated_origins += ", 'http://localhost:3006'"
        
        updated_content = content.replace(cors_match.group(1), updated_origins)
        
        # Write updated content back to the file
        with open(MAIN_PY_PATH, 'w') as f:
            f.write(updated_content)
        
        print("CORS configuration updated successfully")
        return True
    else:
        print("CORS configuration already includes localhost:3006")
        return True

def check_preflight_handler():
    """Check if there's a preflight handler for OPTIONS requests"""
    if not os.path.exists(MAIN_PY_PATH):
        return False
    
    with open(MAIN_PY_PATH, 'r') as f:
        content = f.read()
    
    # Check if there's a handler for OPTIONS requests
    if "@app.options" not in content:
        print("Adding OPTIONS handler to support preflight requests")
        
        # Find the location after the routes are registered
        routes_pattern = r"app\.include_router\(outfits_router\)"
        match = re.search(routes_pattern, content)
        
        if not match:
            print("Could not find the right place to add OPTIONS handler")
            return False
        
        # Add OPTIONS handler after routes are registered
        options_handler = """

# Handle OPTIONS requests for CORS preflight
@app.options("/{rest_of_path:path}")
async def options_handler(rest_of_path: str):
    return {}
"""
        
        position = match.end()
        updated_content = content[:position] + options_handler + content[position:]
        
        # Write updated content back to the file
        with open(MAIN_PY_PATH, 'w') as f:
            f.write(updated_content)
        
        print("OPTIONS handler added successfully")
        return True
    else:
        print("OPTIONS handler already exists")
        return True

if __name__ == "__main__":
    print("Checking and fixing CORS configuration...")
    cors_ok = check_cors_config()
    preflight_ok = check_preflight_handler()
    
    if cors_ok and preflight_ok:
        print("CORS configuration should now be correct")
        print("Restart the backend server for changes to take effect")
    else:
        print("Some issues could not be fixed automatically") 