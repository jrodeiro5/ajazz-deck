# ajazz-deck

Linux daemon + CLI for the AJAZZ AK820 macro pad.
Assign shell commands to physical buttons via a simple YAML config.

## Requirements
- Linux (Ubuntu/Debian recommended)
- Python 3.10+
- [uv](https://docs.astral.sh/uv/) package manager
- AJAZZ AK820 connected via USB

## Quick Start

```bash
# 1. Clone
git clone https://github.com/YOUR_USERNAME/ajazz-deck
cd ajazz-deck

# 2. Install dependencies
uv sync

# 3. Configure your buttons
cp buttons.example.yaml buttons.yaml
nano buttons.yaml   # edit with your commands

# 4. Start the daemon
python3 cli.py daemon start

# 5. Press a button on your AK820 — it runs your command
```

## Autostart on Device Connect

### Linux (native)
```bash
sudo ./install/udev/install.sh
# Unplug and replug AK820 — daemon starts automatically
```

### WSL (Windows Subsystem for Linux)
See [install/wsl/README-WSL.md](install/wsl/README-WSL.md)

> ⚠️ udev autostart is not supported in WSL.
> Use usbipd to attach the device, then start the daemon manually
> or via Task Scheduler.

## CLI Reference

```bash
python3 cli.py daemon start|stop|restart|status
python3 cli.py button list
python3 cli.py button show <id>
python3 cli.py config validate
python3 cli.py device status
```

## MCP Server (Claude Code Integration)

Control the AK820 macro pad programmatically from Claude Code, Windsurf, or Zed.

### Setup

```bash
# 1. Copy the example config template
cp .mcp.json.example .mcp.json

# 2. Edit .mcp.json with your absolute paths
nano .mcp.json
# Change "/absolute/path/to/ajazz-deck" to your actual installation path

# 3. Register with Claude Code (from this project directory)
claude mcp add --transport stdio ajazz-deck \
  -- uv run python3 /home/javi/projects/ajazz-deck/mcp_server.py
```

### Available Tools

- `list_buttons` — Show all configured buttons
- `set_button` — Add/update a button configuration
- `remove_button` — Delete a button
- `daemon_status` — Check if daemon is running
- `daemon_start` — Start the daemon
- `daemon_stop` — Stop the daemon
- `get_logs` — Retrieve daemon logs

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
```

See `buttons.example.yaml` for a complete working example with 6 buttons.

## Logging

```bash
tail -f deck.log        # real-time logs
LOG_LEVEL=DEBUG python3 deck.py   # verbose mode
```

## License
MIT — vendored SDK from MiraboxSpace/StreamDock-Device-SDK
