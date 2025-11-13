#!/bin/bash
# Setup script for Creative Flow Upload System

echo "=========================================="
echo "Creative Flow Upload System Setup"
echo "=========================================="
echo ""

cd "/Users/joshb/Desktop/Dev/Creative Flow"

# Activate virtual environment
echo "1. Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "2. Upgrading pip..."
python -m pip install --upgrade pip

# Install dependencies
echo "3. Installing dependencies..."
python -m pip install playwright==1.48.0 python-dotenv==1.0.1 colorama==0.4.6

# Install Playwright browsers
echo "4. Installing Playwright browsers..."
playwright install chromium

echo ""
echo "=========================================="
echo "Setup Complete!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. Create config/.env file with your TJ credentials"
echo "2. Run: python3 scripts/upload_manager.py --help"
echo ""

