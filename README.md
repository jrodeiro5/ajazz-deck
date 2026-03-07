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

## CLI Reference

```bash
python3 cli.py daemon start|stop|restart|status
python3 cli.py button list
python3 cli.py button show <id>
python3 cli.py config validate
python3 cli.py device status
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
