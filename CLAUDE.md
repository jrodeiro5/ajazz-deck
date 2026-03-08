# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code
in this repository.

## Project Overview

**AJAZZ Deck** is a Linux daemon + CLI for the AJAZZ AK820 macro pad.
It loads button configurations from YAML and executes shell commands or scripts
when buttons are pressed.

### Key Characteristics

- Uses **Mirabox StreamDock SDK** (Python-SDK submodule in `sdk/`)
- Runs as daemon with single-instance enforcement via PID file
- Supports clipboard integration via WSL Windows integration
- Includes HID protocol debugging utilities
- Python 3.12+, using `uv` package manager
- CLI entry point: `ajazz` command (defined in `pyproject.toml`)
- Auto-starts on device connect via udev (Linux) or Task Scheduler (WSL)

## Architecture

### Core Application Flow

**deck.py** (daemon):

1. Logging setup, PID file check (single-instance enforcement)
2. Load config from `buttons.yaml` (path via `AJAZZ_CONFIG` env var)
3. Detect AJAZZ device via Mirabox SDK (`StreamDock` class)
4. Register callback, listen indefinitely for button presses
5. On press: execute configured command/script with timeout

**cli.py** (CLI interface):

- Manages daemon lifecycle (start/stop/restart/status)
- Displays button configuration
- Validates config syntax
- Shows device status

### Button Configuration (`buttons.yaml`)

Format supports simple and complex button definitions:

```yaml
buttons:
  1:
    label: "Button Name"
    type: "shell"                        # shell|clipboard|script (default: shell)
    command: "command"                   # For type: shell
    script: "multi\nline script"         # For type: clipboard/script
    image: "icons/icon.png"              # Optional display icon
```

**Execution modes:**

- `shell` (default): Safe via `shlex.split()` — prevents injection
- `clipboard`: Shell with pipes enabled — for clipboard operations
- `script`: Full shell — for complex multi-line scripts

Timeouts: 5s (safe mode), 10s (shell mode)

### Key Modules

- **deck.py**: Main daemon (config, device management, execution)
- **cli.py**: CLI interface (daemon control, info display)
- **raw_hid.py**: HID debugging tool (direct `/dev/hidraw` communication)

## Development & Deployment

### Setup

```bash
uv sync              # Install dependencies (uses uv.lock)
uv update            # Update dependencies
```

### Running Daemon

```bash
# Preferred: use CLI
python3 cli.py daemon start|stop|restart|status

# Direct (also works)
python deck.py
AJAZZ_CONFIG=/path/to/buttons.yaml python deck.py
```

### CLI Commands

```bash
ajazz daemon start|stop|restart|status  # Daemon control
ajazz button list                       # Show all buttons
ajazz button show <id>                  # Show button details
ajazz button test <id>                  # Test button execution
ajazz config show|validate              # Config management
ajazz device status                     # Show device info
```

### Debugging

```bash
# Check running instances
ps aux | grep deck.py
cat deck.pid

# Validate config syntax
python -c "import yaml; yaml.safe_load(open('buttons.yaml'))"

# Test HID communication (requires device)
python raw_hid.py

# View logs (rotating handler, max 1MB per file)
tail -f deck.log
LOG_LEVEL=DEBUG python3 cli.py daemon start  # Verbose logging
```

## Autostart Setup

### Linux (native)

Uses udev rules + systemd user services:

```bash
sudo ./install/udev/install.sh
```

Creates `/etc/udev/rules.d/99-ajazz-ak820.rules` which:

- Triggers `ajazz-deck.service` on device plug-in (daemon start)
- Triggers `ajazz-deck-stop.service` on device unplug (daemon stop)

Services run as user systemd (not root) — required for GUI apps like `xterm`, `xdg-open`.

**Debugging udev:**

```bash
sudo udevadm control --reload-rules
sudo udevadm trigger  # Test rules without replug
```

### WSL (Windows)

Uses usbipd instead of udev (WSL doesn't support udev):

```bash
# One-time: Install usbipd-win, bind device
# Daily: Attach device, start daemon
usbipd attach --wsl --hardware-id 0300:3010
python3 cli.py daemon start
```

See `install/wsl/README-WSL.md` for full setup.

## Configuration & Environment

### Environment Variables

- `AJAZZ_CONFIG`: Path to button config (default: `./buttons.yaml`)
- `LOG_LEVEL`: Logging verbosity (default: `INFO`)

### Important Paths

- `deck.log`: Rotating file log (1MB max, 7-day retention)
- `deck.pid`: Runtime PID file (auto-cleaned on shutdown)
- `sdk/Python-SDK`: Mirabox SDK submodule
- `install/udev/`: Linux autostart files
- `install/wsl/`: WSL setup guide

## Dependencies

From `pyproject.toml`:

- `click>=8.3.1`: CLI framework
- `hid>=1.0.9`: HID protocol
- `loguru>=0.7.3`: Logging
- `pillow>=12.1.1`: Image processing
- `pyudev>=0.24.4`: Device enumeration
- `pyyaml>=6.0.3`: Config parsing
- `rich>=14.4.0`: Terminal formatting

## SDK Integration

Mirabox StreamDock SDK (git submodule in `sdk/`):

- `StreamDock.DeviceManager`: Enumerate devices
- `StreamDock.Devices.StreamDock`: Device instance, `set_key_callback()`
- `StreamDock.InputTypes.EventType`: Button/encoder events

SDK path injected at startup: `deck.py:8`

Clone with: `git clone --recursive`

## Command Execution Safety

- **shell type**: Uses `shlex.split()` → safe, no injection risk
- **clipboard/script types**: Use `shell=True` → enables pipes, injection possible
- **Timeouts**: 5s (safe), 10s (shell) prevent hung processes
- **Config validation**: Always validate `buttons.yaml` — malicious YAML can execute
arbitrary code

## Git Workflow

- **master**: Development branch (current)
- **main**: Primary branch (for PRs)

Align branches before release: merge master → main or switch default.

## Development Notes

- **No test framework** yet — consider pytest when adding tests
- **Single-instance enforcement**: Check `deck.pid` before starting; remove manually
  if crash without cleanup
- **Device auto-reconnect**: Device hotplug
reloads config (see `_reconnect_event` in deck.py)
- **WSL networking**: udev not available; use usbipd + Task Scheduler
for autostart
- **Platform-specific**: Clipboard uses `/mnt/c/Windows/System32/clip.exe` on WSL
