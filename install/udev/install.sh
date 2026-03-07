#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"
RULES_DIR="/etc/udev/rules.d"
SERVICE_DIR="$HOME/.config/systemd/user"

echo "Installing AJAZZ AK820 autostart..."
echo "Project path: $PROJECT_DIR"

# Install udev rules
sudo cp "$SCRIPT_DIR/99-ajazz-ak820.rules" "$RULES_DIR/"
sudo udevadm control --reload-rules
sudo udevadm trigger

# Install systemd user services
mkdir -p "$SERVICE_DIR"
cp "$SCRIPT_DIR/ajazz-deck.service" "$SERVICE_DIR/"
cp "$SCRIPT_DIR/ajazz-deck-stop.service" "$SERVICE_DIR/"

# Replace %h placeholder with actual home in service files
sed -i "s|%h/ajazz-deck|$PROJECT_DIR|g" "$SERVICE_DIR/ajazz-deck.service"
sed -i "s|%h/ajazz-deck|$PROJECT_DIR|g" "$SERVICE_DIR/ajazz-deck-stop.service"

# Reload systemd user daemon
systemctl --user daemon-reload

echo "✓ udev rules installed"
echo "✓ systemd user services installed"
echo "✓ Unplug and replug AK820 to test autostart"
