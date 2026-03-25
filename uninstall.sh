#!/bin/bash
#
# Morning Briefing Uninstall Script
# Removes the launchd job
#

set -e

echo "================================================"
echo "Morning Briefing - Uninstall Script"
echo "================================================"
echo ""

PLIST_DEST="$HOME/Library/LaunchAgents/com.exxede.morning-briefing.plist"

if [ -f "$PLIST_DEST" ]; then
    echo "Unloading launchd job..."
    launchctl unload "$PLIST_DEST" 2>/dev/null || true

    echo "Removing plist file..."
    rm "$PLIST_DEST"

    echo ""
    echo "✓ Morning briefing automation uninstalled"
    echo ""
    echo "Note: Project files and logs have been preserved."
    echo "To completely remove, delete: $( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
else
    echo "No launchd job found to uninstall."
fi

echo ""
