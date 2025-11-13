#!/bin/bash
# Test script for duplicate Creative ID detection
# 
# This script tests the following:
# 1. Upload a creative to TJ (should succeed)
# 2. Upload the same creative again (should detect as duplicate)
# 
# SETUP: Delete the creative from TJ first, then run this script

set -e  # Exit on error

echo "=========================================="
echo "Duplicate Detection Test"
echo "=========================================="
echo ""
echo "Prerequisites:"
echo "1. Ensure the test creative is DELETED from TJ Media Library"
echo "2. Test will upload the same file TWICE"
echo "3. First upload should succeed (new Creative ID)"
echo "4. Second upload should be marked as 'duplicate'"
echo ""
read -p "Press Enter to start test (or Ctrl+C to cancel)..."
echo ""

# Navigate to project directory
cd "/Users/joshb/Desktop/Dev/Creative Flow"

# Activate virtual environment
source venv/bin/activate

# Limit to 1 file (native pair = 2 files actually)
LIMIT=1

echo "=========================================="
echo "TEST 1: First Upload (should succeed)"
echo "=========================================="
python3 scripts/upload_manager.py \
    --session \
    --live \
    --limit $LIMIT \
    --force \
    --verbose

echo ""
echo "=========================================="
echo "First upload complete!"
echo "Check the logs above for Creative IDs."
echo "=========================================="
echo ""
read -p "Press Enter to run SECOND upload (duplicate test)..."
echo ""

echo "=========================================="
echo "TEST 2: Second Upload (should detect duplicate)"
echo "=========================================="
python3 scripts/upload_manager.py \
    --session \
    --live \
    --limit $LIMIT \
    --force \
    --verbose

echo ""
echo "=========================================="
echo "Test Complete!"
echo "=========================================="
echo ""
echo "Expected Results:"
echo "  TEST 1: ✓ Successfully uploaded X NEW creatives"
echo "  TEST 2: ⚠ No new Creative IDs - files may already exist on TJ"
echo ""
echo "Check the upload logs in tracking/upload_logs/"
echo ""

