#!/bin/bash

# Navigate to the frontend directory
cd frontend

# Install dependencies
npm install

# Build the app
npm run build

# Copy the build files to the main directory
cp -r build/* ..

echo "Build completed successfully!"
echo "Your app has been built with the new Refabric-inspired styling." 