# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2026-03-07

### Added

- **Production-ready daemon** with reliable logging and automatic reconnection
- **Comprehensive CLI** with rich formatting and AJAZZ branding
- **udev autostart system** for automatic daemon startup when AK820 is connected
- **systemd user services** for reliable daemon management
- **WSL setup guide** with usbipd integration instructions
- **Automated installation scripts** for Linux udev rules
- **Configuration template system** with `buttons.example.yaml`
- **Complete documentation** with README and setup guides
- **JSON output support** for scripting integration
- **Hotplug monitoring** for automatic device reconnection
- **PID-based daemon control** with proper process management

### Fixed

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
- **AJAZZ AK820 support** for macro pad functionality
- **YAML-based configuration system** for button mappings
- **Basic CLI commands** for daemon control
- **Device detection** for AJAZZ AK820 (AKP153E) macro pad
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
