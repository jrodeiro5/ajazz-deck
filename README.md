# AJAZZ Deck

Linux daemon for the AJAZZ AK820 (AKP153E) macro pad / stream deck, with button-to-command mappings and CLI control.

## Requirements

- **Python:** 3.12+
- **OS:** Linux (tested on WSL2)
- **Hardware:** AJAZZ AK820 / Mirabox StreamDock (VID=0x0300, PID=0x3010)

## Installation

```bash
git clone https://github.com/yourusername/ajazz-deck.git
cd ajazz-deck
uv sync
```

## Usage

### Start the daemon
```bash
python3 cli.py daemon start
```

### Check daemon status
```bash
python3 cli.py daemon status
```

### List configured buttons
```bash
python3 cli.py button-list
```

### Validate configuration
```bash
python3 cli.py config-validate
```

## Configuration

Edit `buttons.yaml` to define button actions:

```yaml
buttons:
  1:
    label: "Git Status"
    type: "shell"
    command: "git status"
  2:
    label: "Docker PS"
    type: "shell"
    command: "docker ps"
  3:
    label: "Project Context"
    type: "clipboard"
    script: |
      PROJECT=$(pwd)
      echo "Project: $PROJECT" | /mnt/c/Windows/System32/clip.exe
```

### Button Types
- **shell** (default): Safe command execution via `shlex.split()`
- **clipboard**: Shell execution with pipe support (WSL-compatible)
- **script**: Multi-line bash scripts

## Architecture

- **deck.py** — Main daemon (logs to `deck.log`, PID at `deck.pid`)
- **cli.py** — Command-line interface (start/stop/restart/status, config management)
- **buttons.yaml** — Button configuration mappings
- **vendor/StreamDock** — Vendored Mirabox SDK (MIT licensed)

## Logging

Real-time logs:
```bash
tail -f deck.log
```

Debug mode:
```bash
LOG_LEVEL=DEBUG python3 deck.py
```

## License

MIT — See `vendor/LICENSE` for vendored SDK license (Mirabox StreamDock)
