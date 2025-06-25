#!/bin/bash

echo "🛑 Stopping all PM2 processes..."
npx pm2 stop all

echo "🧹 Cleaning up PM2 processes..."
npx pm2 delete all

echo "✅ All processes stopped and cleaned up." 