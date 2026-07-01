#!/bin/bash

# Exit on error
set -e

echo "=== Internship Scraper Launcher ==="

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is not installed on this system."
    echo "Please download and install Python from https://www.python.org/downloads/"
    exit 1
fi

# Create virtual environment if it doesn't exist
if [ ! -d ".venv" ]; then
    echo "Creating Python virtual environment (.venv)..."
    python3 -m venv .venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source .venv/bin/activate

# Upgrade pip and install dependencies
echo "Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Run Desktop app wrapper with web browser fallback
echo "Launching Scraper Console..."
python desktop.py || python3 -m streamlit run app.py --browser.gatherUsageStats false
