#!/bin/bash
set -e

RULES_FILE="99-ajazz-ak820.rules"
RULES_DIR="/etc/udev/rules.d"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"

echo "Installing AJAZZ AK820 udev rules..."
echo "Project path: $PROJECT_DIR"

# Copy rules file
sudo cp "$SCRIPT_DIR/$RULES_FILE" "$RULES_DIR/$RULES_FILE"

# Replace placeholder path with actual project path
sudo sed -i "s|/opt/ajazz-deck|$PROJECT_DIR|g" "$RULES_DIR/$RULES_FILE"

# Reload udev
sudo udevadm control --reload-rules
sudo udevadm trigger

echo "✓ udev rules installed at $RULES_DIR/$RULES_FILE"
echo "✓ Unplug and replug your AK820 to test autostart"
