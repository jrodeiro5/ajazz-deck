#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"
RULES_DIR="/etc/udev/rules.d"
SERVICE_DIR="$HOME/.config/systemd/user"

echo "Installing AJAZZ AKP153 autostart..."
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

# Install ajazz CLI to system PATH
echo "Installing ajazz CLI to /usr/local/bin..."
sudo ln -sf "$PROJECT_DIR/.venv/bin/ajazz" /usr/local/bin/ajazz
sudo ln -sf "$PROJECT_DIR/.venv/bin/ajazz-mcp" /usr/local/bin/ajazz-mcp
echo "✓ ajazz command available globally"

echo "✓ udev rules installed"
echo "✓ systemd user services installed"
echo "✓ Unplug and replug AKP153 to test autostart"
