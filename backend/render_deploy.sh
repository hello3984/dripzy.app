#!/bin/bash

echo "===== Preparing for Render deployment ====="

# Check if we're in the backend directory
if [ ! -f "app/main.py" ]; then
    echo "ERROR: This script must be run from the backend directory"
    exit 1
fi

echo "===== Cleaning up redundant files ====="
# Remove any duplicate model files
if [ -d "app/models" ]; then
    echo "Removing redundant app/models directory..."
    rm -rf app/models
fi

echo "===== Verifying imports ====="
# Check for any import errors in outfits.py
grep -n "app.models" app/routers/outfits.py
if [ $? -eq 0 ]; then
    echo "WARNING: Found potential import issues in outfits.py - please fix!"
else
    echo "No import issues found in outfits.py"
fi

echo "===== Creating build info ====="
# Create a version file for deployment tracking
echo "Build date: $(date)" > build_info.txt
echo "Commit: $(git rev-parse HEAD 2>/dev/null || echo 'Not a git repo')" >> build_info.txt

echo "===== Deployment preparation complete ====="
echo "Your code is ready to be deployed to Render."
echo ""
echo "Make sure your Render environment has the following variables set:"
echo "- ANTHROPIC_API_KEY"
echo "- SERPAPI_KEY"
echo ""
echo "Remember that SerpAPI free tier has a limit of 100 searches per month."
echo "The app will use fallback mock data when this limit is exceeded." 