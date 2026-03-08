# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- **Button configuration CLI commands**
  - `ajazz button set <id>` — Add/update button with label, command, type,
    icon options
  - `ajazz button remove <id>` — Remove button from configuration
  - `ajazz logs [--lines N]` — View daemon log file (default: last 20 lines)
- **Image processing engine** (`image_engine.py`)
  - Download images from URL with automatic 96×96px resizing
  - Local file image processing with validation
  - AI image generation from text prompts via Gemini API
  - Support for GOOGLE_API_KEY environment variable
- **Developer documentation** (`AGENTS.md`)
  - Comprehensive guide for AI agents working with the project
  - Code style standards and examples
  - MCP integration documentation
  - Common agent tasks and workflows
- **Project metadata** (`.env.example`)
  - Template for required environment variables
  - GOOGLE_API_KEY configuration example

### Changed

- **Gemini API model upgrade**
  - Updated from `gemini-2.0-flash-preview-image-generation` to `gemini-3.1-flash-image-preview`
  - 64% faster (381 tokens/sec vs 232 tokens/sec)
  - Future-proof (Gemini 2.0 Flash retiring June 1, 2026)
- **CLI welcome screen**
  - Updated tips panel to highlight `button set` command as primary workflow
  - Improved visual layout with better formatting
- **CI/CD workflow**
  - Fixed ruff installation: use `uv sync --dev` instead of `--all-groups`
  - Ensures dev dependencies (ruff) are installed for linting checks
- **Dependencies updated**
  - Added `httpx>=0.27` for URL image downloads
  - Added `google-genai>=1.0` for Gemini API integration
  - Added `python-dotenv>=1.0` for environment configuration
  - Added `pydantic>=2.0.0` for model validation
  - Added `ruff>=0.1.0` as dev dependency for code quality

### Fixed

- **GitHub workflow** — CI now correctly installs all dev tools via uv
- **Entry points** — Clarified that CLI works with `uv run` without custom
build system

## [0.1.0] - 2026-03-07

### v0.1.0 Added

- **Production-ready daemon** with reliable logging and automatic reconnection
- **Comprehensive CLI** with rich formatting and AJAZZ branding
- **udev autostart system** for automatic daemon startup when AKP153 is connected
- **systemd user services** for reliable daemon management
- **WSL setup guide** with usbipd integration instructions
- **Automated installation scripts** for Linux udev rules
- **Configuration template system** with `buttons.example.yaml`
- **Complete documentation** with README and setup guides
- **JSON output support** for scripting integration
- **Hotplug monitoring** for automatic device reconnection
- **PID-based daemon control** with proper process management

### v0.1.0 Fixed

- **Config path resolution** using absolute paths and environment variables
- **PID race conditions** during daemon startup
- **CLI command structure** with proper command organization
- **GUI command integration** with systemd services
- **Error handling** throughout daemon and CLI

### Installation

```bash
# Linux (native)
git clone https://github.com/jrodeiro5/ajazz-deck
cd ajazz-deck
uv sync
sudo ./install/udev/install.sh

# WSL
# Follow install/wsl/README-WSL.md for usbipd setup
```

### Migration from v0.0.x

- Replace `python3 deck.py` with `python3 cli.py daemon start`
- Use `buttons.example.yaml` as template for configuration
- Install udev rules for autostart functionality

## [0.0.3] - 2026-03-07

### v0.0.3 Added

- **AJAZZ branded welcome screen** with getting started tips
- **Rich console output** with colored formatting and tables
- **Command grouping** for better CLI organization (button, config, daemon, device)

### v0.0.3 Changed

- **CLI entry point** now shows welcome screen when no command provided
- **Error messages** improved with helpful suggestions and file paths

## [0.0.2] - 2026-03-07

### v0.0.2 Added

- **User-facing configuration template** (`buttons.example.yaml`)
- **Complete README documentation** with installation and usage instructions
- **Example button configurations** for common use cases
- **Configuration validation** with clear error messages

### v0.0.2 Changed

- **Default configuration** moved to example template
- **Documentation** significantly expanded with troubleshooting tips

## [0.0.1] - 2026-03-07

### v0.0.1 Added

- **Initial daemon implementation** with basic device communication
- **AJAZZ AKP153 support** for macro pad functionality
- **YAML-based configuration system** for button mappings
- **Basic CLI commands** for daemon control
- **Device detection** for AJAZZ AKP153 (AKP153E) macro pad
- **Logging system** with file rotation
- **Process management** with PID file handling

## Breaking Changes

### v0.1.0

- CLI command structure changed from flat to grouped (`button-list` → `button list`)
- Configuration file path resolution now uses absolute paths
- Daemon startup behavior improved with PID race condition fixes

### v0.0.2

- Default `buttons.yaml` replaced with `buttons.example.yaml` template

## Security Notes

- All button commands execute with user privileges
- Configuration files are validated before loading
- udev rules use secure path substitution
- systemd services run as user (not root)

## Platform Support

### ✅ Supported

- Linux (Ubuntu/Debian recommended)
- WSL2 with usbipd for device access
- systemd-based distributions

### ⚠️ Limitations

- udev autostart not available in WSL
- Requires manual device attachment in WSL environments
- Single device support per daemon instance

### Fixed

- **Device naming throughout project** - Renamed all references from AK820 to AKP153
  (correct device model) across documentation, code comments, and configuration
- **WSL setup reliability** - Fixed device attachment to use hardware ID instead of
  hardcoded bus ID that changes on reconnect
- **WSL automation documentation** - Added complete Task Scheduler setup
  instructions with step-by-step configuration
- **WSL troubleshooting** - Added comprehensive troubleshooting section for
  common device attachment and visibility issues
- **Image generation reliability** - Fixed Gemini API image generation with proper
  base64 decoding for AI-generated button icons
- **Daemon restart stability** - Fixed daemon restart to wait for old process
  exit, preventing "Another instance already running" errors
- **Button testing functionality** - Fixed `ajazz button test` to handle multi-word
  commands using proper shell parsing
- **Device status reliability** - Fixed `ajazz device status` to read daemon logs
  instead of importing SDK, improving compatibility
- **WSL automation documentation** - Added complete Task Scheduler setup
  instructions with step-by-step configuration
- **WSL troubleshooting** - Added comprehensive troubleshooting section for
  common device attachment and visibility issues
- **Image generation reliability** - Fixed Gemini API image generation with proper
  base64 decoding for AI-generated button icons
- **Daemon restart stability** - Fixed daemon restart to wait for old process
  exit, preventing "Another instance already running" errors
- **Button testing functionality** - Fixed `ajazz button test` to handle multi-word
  commands using proper shell parsing
- **Device status reliability** - Fixed `ajazz device status` to read daemon logs
  instead of importing SDK, improving compatibility

## [0.1.0] - 2026-03-07
