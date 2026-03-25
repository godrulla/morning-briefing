#!/bin/bash
#
# Morning Briefing Setup Script
# Installs and configures the morning briefing automation
#

set -e  # Exit on error

echo "================================================"
echo "Morning Briefing Automation - Setup Script"
echo "================================================"
echo ""

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if Python 3 is installed
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Error: Python 3 is not installed${NC}"
    exit 1
fi

echo -e "${GREEN}✓${NC} Python 3 found: $(python3 --version)"

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo ""
    echo "Creating virtual environment..."
    python3 -m venv venv
    echo -e "${GREEN}✓${NC} Virtual environment created"
else
    echo -e "${GREEN}✓${NC} Virtual environment exists"
fi

# Activate virtual environment and install dependencies
echo ""
echo "Installing dependencies..."
source venv/bin/activate
pip install --upgrade pip -q
pip install -r requirements.txt -q
echo -e "${GREEN}✓${NC} Dependencies installed"

# Create log directory
echo ""
echo "Creating log directory..."
mkdir -p ~/.local/logs
echo -e "${GREEN}✓${NC} Log directory created"

# Check if config files exist
echo ""
echo "Checking configuration files..."

if [ ! -f "config.yaml" ]; then
    echo -e "${YELLOW}!${NC} config.yaml not found, creating from example..."
    cp config.example.yaml config.yaml
    echo -e "${YELLOW}→${NC} Please edit config.yaml with your settings"
    CONFIG_NEEDS_EDIT=true
else
    echo -e "${GREEN}✓${NC} config.yaml exists"
fi

if [ ! -f "secrets.yaml" ]; then
    echo -e "${YELLOW}!${NC} secrets.yaml not found, creating from example..."
    cp secrets.example.yaml secrets.yaml
    echo -e "${YELLOW}→${NC} Please edit secrets.yaml with your credentials"
    SECRETS_NEEDS_EDIT=true
else
    echo -e "${GREEN}✓${NC} secrets.yaml exists"
fi

# Check for Google credentials
if [ ! -f "credentials/credentials.json" ]; then
    echo -e "${YELLOW}!${NC} Google OAuth credentials not found"
    echo -e "${YELLOW}→${NC} Download from Google Cloud Console and save to: credentials/credentials.json"
    GOOGLE_CREDS_MISSING=true
else
    echo -e "${GREEN}✓${NC} Google credentials found"
fi

# Install launchd plist
echo ""
echo "Installing launchd scheduler..."

PLIST_SOURCE="$SCRIPT_DIR/com.exxede.morning-briefing.plist"
PLIST_DEST="$HOME/Library/LaunchAgents/com.exxede.morning-briefing.plist"

if [ -f "$PLIST_DEST" ]; then
    echo -e "${YELLOW}!${NC} Existing launchd job found, unloading..."
    launchctl unload "$PLIST_DEST" 2>/dev/null || true
fi

cp "$PLIST_SOURCE" "$PLIST_DEST"
echo -e "${GREEN}✓${NC} launchd plist installed to ~/Library/LaunchAgents/"

# Load the launchd job
echo ""
echo "Loading launchd job..."
launchctl load "$PLIST_DEST"
echo -e "${GREEN}✓${NC} launchd job loaded (will run daily at 7:00 AM)"

# Summary
echo ""
echo "================================================"
echo "Setup Complete!"
echo "================================================"
echo ""

if [ "$CONFIG_NEEDS_EDIT" = true ] || [ "$SECRETS_NEEDS_EDIT" = true ] || [ "$GOOGLE_CREDS_MISSING" = true ]; then
    echo -e "${YELLOW}⚠ Action Required:${NC}"
    echo ""

    if [ "$CONFIG_NEEDS_EDIT" = true ]; then
        echo "1. Edit config.yaml with your preferences"
        echo "   - Set your email address"
        echo "   - Configure GitHub organizations"
        echo "   - Adjust settings as needed"
        echo ""
    fi

    if [ "$SECRETS_NEEDS_EDIT" = true ]; then
        echo "2. Edit secrets.yaml with your credentials"
        echo "   - Add GitHub Personal Access Token"
        echo "   - Verify Google OAuth paths"
        echo ""
    fi

    if [ "$GOOGLE_CREDS_MISSING" = true ]; then
        echo "3. Download Google OAuth credentials"
        echo "   - Go to https://console.cloud.google.com"
        echo "   - Enable Gmail API and Calendar API"
        echo "   - Create OAuth 2.0 credentials (Desktop app)"
        echo "   - Download and save to: $SCRIPT_DIR/credentials/credentials.json"
        echo ""
    fi

    echo "4. Run a test: ./test.sh --dry-run"
    echo ""
fi

echo "Commands:"
echo "  Test run:           ./test.sh --dry-run"
echo "  Send test email:    ./test.sh"
echo "  Run immediately:    launchctl start com.exxede.morning-briefing"
echo "  Check status:       launchctl list | grep morning-briefing"
echo "  View logs:          tail -f ~/.local/logs/morning-briefing.log"
echo "  Uninstall:          ./uninstall.sh"
echo ""
echo "The briefing will run automatically every day at 7:00 AM."
echo ""
