#!/bin/bash
# Launcher for Desktop Application

echo "Starting Live Stream Phone Extractor..."

# Check if in correct directory
if [ ! -f "app.py" ]; then
    echo "Error: Please run this from the desktop_app directory"
    exit 1
fi

# Run the application
python3 app.py
