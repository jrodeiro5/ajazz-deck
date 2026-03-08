# ajazz-deck

Linux daemon + CLI for the AJAZZ AKP153 macro pad.
Assign shell commands to physical buttons via a simple YAML config.

## Requirements

- Linux (Ubuntu/Debian recommended) or WSL2 with usbipd
- Python 3.12+
- [uv](https://docs.astral.sh/uv/) package manager
- AJAZZ AKP153 connected via USB

## Quick Start

```bash
# 1. Clone
git clone https://github.com/jrodeiro5/ajazz-deck
cd ajazz-deck

# 2. Install dependencies
uv sync

# 3. Configure your buttons
cp buttons.example.yaml buttons.yaml
nano buttons.yaml   # edit with your commands

# 4. Start the daemon
ajazz daemon start

# 5. Press a button on your AKP153 — it runs your command
```

## Autostart on Device Connect

### Linux (native)

```bash
sudo ./install/udev/install.sh
# Unplug and replug AKP153 — daemon starts automatically
```

### WSL (Windows Subsystem for Linux)

See [install/wsl/README-WSL.md](install/wsl/README-WSL.md)

> ⚠️ udev autostart is not supported in WSL.
> Use usbipd to attach the device, then start the daemon manually
> or via Task Scheduler.

## CLI Reference

```bash
# Daemon Management
ajazz daemon start|stop|restart|status
ajazz logs [--lines N]                  # Show last N lines from deck.log 
                                         # (default: 20)

# Button Configuration
ajazz button list                       # Show all configured buttons
ajazz button show <id>                  # Show button details
ajazz button set <id> --label TEXT --command TEXT 
  [--type shell|clipboard|script] [--icon PATH]
ajazz button remove <id>                # Remove button from configuration

# Button Images
ajazz image set <id> --url URL          # Set image from URL (auto-resizes to 96×96)
ajazz image set <id> --file PATH        # Set image from local file
ajazz image set <id> --generate PROMPT  # Generate image with Gemini (requires GOOGLE_API_KEY)
ajazz image show <id>                   # Show button's current image path
ajazz image clear <id>                  # Remove image from button

# Configuration & Status
ajazz config show                       # Display button configuration
ajazz config validate                   # Validate buttons.yaml syntax
```

## Features

- **Simple YAML Configuration**: Easy button setup with labels and commands
- **Button Management**: Add, update, remove buttons via CLI with validation
- **Button Images**: Set custom icons (96×96 px) from URLs, local files, or AI-generated
- **Rich CLI Output**: Beautiful terminal interface with AJAZZ branding
- **udev Autostart**: Automatic daemon startup when device is connected
- **WSL Support**: Full support for Windows Subsystem for Linux
- **MCP Integration**: Programmatic control from Claude Code, Windsurf, or Zed
- **JSON Output**: Script-friendly output format for automation
- **Log Viewing**: Built-in log viewer with configurable line count
- **Auto-restart**: Daemon automatically restarts when configuration changes

## Image Support

Set custom button icons on the AKP153 display — from image URLs, local files,
or AI-generated with Gemini.

### Setup

```bash
# 1. Install dependencies (included in uv sync)
uv sync

# 2. Create .env for AI image generation (optional)
cp .env.example .env
# Get a free Google Gemini API key: https://aistudio.google.com/apikey
# Add it to .env: GOOGLE_API_KEY=your-api-key
```

### CLI Usage

```bash
# Set from URL
ajazz image set 1 --url https://example.com/icon.png

# Set from local file
ajazz image set 2 --file icons/my-icon.png

# Generate with AI (requires GOOGLE_API_KEY in .env)
ajazz image set 3 --generate "red button with checkmark"

# Show current image
ajazz image show 1

# Remove image from button
ajazz image clear 1
```

### MCP Tools (Claude Code)

```python
# Set image from URL
set_button_image_from_url(button_id=1, url="https://...")

# Generate image from text
set_button_image_from_prompt(button_id=2, prompt="red stop sign")

# Remove image
clear_button_image(button_id=3)
```

### Technical Details

- **Image Format**: PNG (converted internally to JPEG for device)
- **Dimensions**: 96×96 pixels (auto-resized)
- **Storage**: Icons saved to `icons/{button_id}.png`
- **Device Sync**: Images pushed to device on daemon startup or reconnect

## Changelog

See [CHANGELOG.md](CHANGELOG.md) for user-facing changes and release notes.

For developers, see [CHANGELOG-INTERNAL.md](CHANGELOG-INTERNAL.md) for technical
details, architecture changes, and development notes.

## MCP Server (Claude Code Integration)

Control the AKP153 macro pad programmatically from Claude Code, Windsurf, or Zed.

### MCP Setup

```bash
# 1. Copy the example config template
cp .mcp.json.example .mcp.json

# 2. Edit .mcp.json with your absolute paths
nano .mcp.json
# Change "/absolute/path/to/ajazz-deck" to your actual installation path

# 3. Set up environment variables (for image generation features)
export GOOGLE_API_KEY="your-google-api-key"

# 4. Register with Claude Code (from this project directory)
claude mcp add --transport stdio ajazz-deck \
  -- ajazz-mcp
```

### Available Tools

- `list_buttons` — Show all configured buttons
- `set_button` — Add/update a button configuration
- `remove_button` — Delete a button
- `daemon_status` — Check if daemon is running

- `daemon_start` — Start the daemon

- `daemon_stop` — Stop the daemon

- `get_logs` — Retrieve daemon logs

**Image Tools:**

- `set_button_image_from_url` — Download image from URL and set as button icon

- `set_button_image_from_prompt` — Generate button icon with Gemini AI

- `clear_button_image` — Remove image from button

### Example Usage

```python
from mcp_server import set_button, daemon_start

# Add a button
set_button(button_id=1, label="Terminal", command="xterm")

# Start daemon if not running
daemon_start()
```

## buttons.yaml format

```yaml
buttons:
  1:
    label: "My Button"
    command: "your-shell-command"
    type: "shell"                          # shell, clipboard, or script
    image: "icons/my-icon.png"             # optional: path to .png icon (96×96)
  2:
    label: "With Script"
    script: "echo hello | xclip"
    type: "script"
```

See `buttons.example.yaml` for a complete working example with 6 buttons.

## Logging

```bash
tail -f deck.log        # real-time logs
LOG_LEVEL=DEBUG ajazz daemon start   # verbose mode
```

## Troubleshooting

### Device not found

- Ensure AKP153 is connected via USB
- Check `ajazz device status` for device information
- On Linux, verify user is in the `input` group: `sudo usermod -a -G input $USER`

### Daemon won't start

- Validate configuration: `ajazz config validate`
- Check logs: `tail -f deck.log`
- Ensure no other daemon is running: `ajazz daemon status`

### MCP server issues

- Verify .mcp.json has correct absolute paths
- Check environment variables are set
- Ensure dependencies are installed: `uv sync`

### WSL issues

- Follow [install/wsl/README-WSL.md](install/wsl/README-WSL.md) for usbipd setup
- Manually attach device: `usbipd attach --wsl --hardware-id 0300:3010`

## License

MIT — vendored SDK from MiraboxSpace/StreamDock-Device-SDK
