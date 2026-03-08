# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code
in this repository.

## Project Overview

**AJAZZ Deck** is a Linux daemon + CLI for the AJAZZ AKP153 macro pad.
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

## Security Rules

**Critical — must follow these rules when working with this repository:**

- **Never access credential files directly** — Do not read, extract, or display:
  - `~/.config/gh/hosts.yml` (GitHub CLI tokens)
  - `~/.netrc` (authentication credentials)
  - `~/.ssh/` (private keys)
  - `.env` files with API keys or secrets
  - `~/.git-credentials`

- **Never extract or use OAuth tokens, API keys, or passwords** — Even if found in environment variables or config files, do not use them directly in git commands. Always ask the user to authenticate manually.

- **If push/auth fails** — Stop immediately and tell the user:
  ```bash
  gh auth login
  # or
  git push origin main
  ```
  Do NOT attempt to work around auth failures by embedding credentials in URLs.

- **Never embed credentials in URLs** — Do not construct URLs like:
  ```bash
  # ❌ WRONG
  git push https://user:token@github.com/repo.git
  ```

- **Always ask for permission** before:
  - Accessing files outside the project directory
  - Reading configuration or credential files
  - Making changes that affect git history or branches
  - Pushing to remote repositories

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

- **deck.py**: Main daemon (config, device management, execution, logging)
- **cli.py**: CLI interface (daemon control, button config, image management, logs)
- **mcp_server.py**: FastMCP server for Claude Code/Windsurf/Zed integration
- **config_models.py**: Pydantic models for button and app configuration validation
- **image_engine.py**: Image processing (URL download, local file, Gemini AI generation)
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

**Daemon Management:**
```bash
ajazz daemon start|stop|restart|status
ajazz logs [--lines N]                  # Show last N lines from deck.log (default: 20)
```

**Button Configuration:**
```bash
ajazz button list                       # Show all configured buttons
ajazz button show <id>                  # Show button details
ajazz button set <id> --label TEXT --command TEXT [--type shell|clipboard|script] [--icon PATH]
ajazz button remove <id>                # Remove button from configuration
ajazz button test <id>                  # Test button execution
```

**Button Images:**
```bash
ajazz image set <id> --url URL          # Set image from URL (auto-resizes to 96×96)
ajazz image set <id> --file PATH        # Set image from local file
ajazz image set <id> --generate PROMPT  # Generate image with Gemini (requires GOOGLE_API_KEY)
ajazz image show <id>                   # Show button's current image path
ajazz image clear <id>                  # Remove image from button
```

**Configuration & Status:**
```bash
ajazz config show                       # Display button configuration
ajazz config validate                   # Validate buttons.yaml syntax
ajazz device-status                     # Show device connection status
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

## Image Generation

**image_engine.py** handles three image sources:

1. **URL Download** (`download_from_url`):
   - Downloads image from HTTP/HTTPS URL
   - Auto-resizes to 96×96 px (AKP153 native format)
   - Converts to RGB and saves as PNG

2. **Local File** (`process_image`):
   - Loads image from local file path
   - Same resize and format conversion

3. **AI Generation** (`generate_from_prompt`):
   - Uses Google Gemini 3.1 Flash Image Preview model
   - Requires `GOOGLE_API_KEY` environment variable
   - Generates 96×96 px image directly from text prompt

All processed images saved to `icons/{button_id}.png`.

## Configuration & Environment

### Environment Variables

- `AJAZZ_CONFIG`: Path to button config (default: `./buttons.yaml`)
- `LOG_LEVEL`: Logging verbosity (default: `INFO`)
- `GOOGLE_API_KEY`: Google Gemini API key for AI image generation (optional)
  - Get free key at https://aistudio.google.com/apikey
  - Store in `.env` file (see `.env.example`)

### Important Paths

- `deck.log`: Rotating file log (1MB max, 7-day retention)
- `deck.pid`: Runtime PID file (auto-cleaned on shutdown)
- `sdk/Python-SDK`: Mirabox SDK submodule
- `install/udev/`: Linux autostart files
- `install/wsl/`: WSL setup guide

## Dependencies

### Core (`pyproject.toml`)

- `click>=8.3.1`: CLI framework
- `hid>=1.0.9`: HID protocol
- `loguru>=0.7.3`: Logging
- `pillow>=12.1.1`: Image processing
- `pyudev>=0.24.4`: Device enumeration
- `pyyaml>=6.0.3`: Config parsing
- `rich>=14.3.3`: Terminal formatting
- `pydantic>=2.0.0`: Configuration validation
- `fastmcp>=2.3.0`: MCP server for Claude/Windsurf/Zed
- `google-genai>=1.0`: Gemini API for AI image generation
- `httpx>=0.27`: HTTP client for image downloads
- `python-dotenv>=1.0`: Environment variable loading

### Dev (`tool.uv.optional-dependencies.dev`)

- `ruff>=0.1.0`: Linting and code formatting

## SDK Integration

Mirabox StreamDock SDK (git submodule in `sdk/`):

- `StreamDock.DeviceManager`: Enumerate devices
- `StreamDock.Devices.StreamDock`: Device instance, `set_key_callback()`
- `StreamDock.InputTypes.EventType`: Button/encoder events

SDK path injected at startup: `deck.py:8`

Clone with: `git clone --recursive`

## MCP Server Integration

**mcp_server.py** provides FastMCP server for Claude Code, Windsurf, and Zed integration.

Available MCP tools (exposed as Claude tools):
- `list_buttons()` — List all configured buttons
- `set_button(id, label, command, type, icon)` — Configure button
- `remove_button(id)` — Delete button
- `daemon_status()` — Check daemon running status
- `daemon_start()` / `daemon_stop()` — Control daemon
- `set_button_image_from_url(id, url)` — Set button icon from URL
- `set_button_image_from_prompt(id, prompt)` — Generate button icon with AI
- `clear_button_image(id)` — Remove button icon

Run server: `uv run ajazz-mcp` (or `uv run mcp_server.py` directly)

## Command Execution Safety

- **shell type**: Uses `shlex.split()` → safe, no injection risk
- **clipboard/script types**: Use `shell=True` → enables pipes, injection possible
- **Timeouts**: 5s (safe), 10s (shell) prevent hung processes
- **Config validation**: Always validate `buttons.yaml` — malicious YAML can execute
arbitrary code

## Git Workflow

- **main**: Primary development branch (default)
- No secondary branch — all work happens on `main`

All commits go to `main`. Tag releases with version numbers (e.g., `v0.2.0`).

## Code Quality & Linting

**Ruff** handles linting and formatting:

```bash
# Check for style issues
uv run ruff check .

# Auto-fix issues
uv run ruff check --fix .

# Format code
uv run ruff format .

# CI runs both: ruff check . && ruff format --check .
```

Configuration in `pyproject.toml`:
- Line length: 88 characters
- Target: Python 3.12+
- Rules: E, W, F, I, N, UP, B, C4, TCH (see `[tool.ruff.lint]`)
- Per-file: `deck.py` allows E402 (late imports after sys.path modification)

## Build System & Package Installation

Uses Hatchling with flat project structure configuration:

```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.uv]
package = true

[tool.hatch.build.targets.wheel]
only-packages = false
include = ["/cli.py", "/deck.py", "/mcp_server.py", "/config_models.py", "/image_engine.py", "/raw_hid.py"]
```

Result: `uv sync` builds the package and installs `ajazz` and `ajazz-mcp` entry points.

## Development Notes

- **No test framework yet** — consider pytest when adding tests
- **Single-instance enforcement**: Check `deck.pid` before starting; remove manually if crash without cleanup
- **Device auto-reconnect**: Device hotplug reloads config (see `_reconnect_event` in deck.py)
- **WSL networking**: udev not available; use usbipd + Task Scheduler for autostart
- **Platform-specific**: Clipboard uses `/mnt/c/Windows/System32/clip.exe` on WSL
- **Config validation**: `config_models.py` uses Pydantic with custom validators
  - `ButtonConfig`: Single button validation
  - `AjazzConfig`: Full configuration with button dict
