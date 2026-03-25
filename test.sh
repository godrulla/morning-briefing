#!/bin/bash
#
# Morning Briefing Test Script
# Test the briefing automation
#

set -e

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo "================================================"
echo "Morning Briefing - Test Script"
echo "================================================"
echo ""

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Error: Virtual environment not found. Run ./setup.sh first"
    exit 1
fi

# Activate virtual environment
source venv/bin/activate

# Parse arguments
DRY_RUN=""
if [ "$1" = "--dry-run" ]; then
    DRY_RUN="--dry-run"
    echo -e "${YELLOW}Running in DRY RUN mode (no email will be sent)${NC}"
    echo ""
fi

# Run the briefing script with verbose output
echo "Running morning briefing script..."
echo ""

python3 main.py $DRY_RUN --verbose

EXIT_CODE=$?

echo ""
if [ $EXIT_CODE -eq 0 ]; then
    echo -e "${GREEN}✓ Test completed successfully${NC}"
    echo ""
    echo "Check the logs at: ~/.local/logs/morning-briefing.log"
else
    echo "✗ Test failed with exit code $EXIT_CODE"
    echo ""
    echo "Check the error log at: ~/.local/logs/morning-briefing-error.log"
fi

exit $EXIT_CODE
