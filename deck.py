#!/usr/bin/env python3
import sys
import os
from pathlib import Path

# Add SDK to path
SDK_PATH = Path(__file__).parent / "sdk" / "Python-SDK" / "src"
sys.path.insert(0, str(SDK_PATH))

import yaml
import subprocess
import time
import logging
from logging.handlers import RotatingFileHandler
import shlex
import atexit
from typing import Dict, Optional

from StreamDock.DeviceManager import DeviceManager
from StreamDock.Devices.StreamDock import StreamDock
from StreamDock.InputTypes import EventType

# Paths
PROJECT_DIR = Path(__file__).parent
LOG_FILE = PROJECT_DIR / "deck.log"
PID_FILE = PROJECT_DIR / "deck.pid"
CONFIG_FILE = Path(os.getenv("AJAZZ_CONFIG", str(PROJECT_DIR / "buttons.yaml")))

# Ensure directories exist
LOG_FILE.parent.mkdir(exist_ok=True)

def setup_logging() -> logging.Logger:
    """Configure rotating file logger."""
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    handler = RotatingFileHandler(
        str(LOG_FILE),
        maxBytes=1_000_000,  # 1 MB
        backupCount=3
    )
    formatter = logging.Formatter(
        '%(asctime)s [%(levelname)s] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    return logger


def check_single_instance() -> None:
    """Ensure only one instance runs. Exit if another is already running."""
    if PID_FILE.exists():
        try:
            old_pid = int(PID_FILE.read_text().strip())
            # Check if process is still running
            os.kill(old_pid, 0)
            logger.error(f"Another instance (PID {old_pid}) is already running")
            sys.exit(1)
        except (ProcessLookupError, ValueError):
            # Process doesn't exist or PID file corrupted, continue
            pass

    # Write our PID and register cleanup
    PID_FILE.write_text(str(os.getpid()))
    atexit.register(lambda: PID_FILE.unlink(missing_ok=True))


logger = setup_logging()
check_single_instance()

def load_config(config_file: str | Path = CONFIG_FILE) -> Dict[int, dict]:
    """Load button mappings from YAML config.

    Supports both simple command strings and complex button objects:
    - Simple: button_id: "command string"
    - Complex: button_id: {label, image, type, script/command}
    """
    config_path = Path(config_file)
    try:
        with open(config_path, "r") as f:
            config = yaml.safe_load(f)
        buttons = config.get("buttons", {})

        # Normalize button format: convert string commands to dict format
        normalized = {}
        for button_id, button_data in buttons.items():
            if isinstance(button_data, str):
                # Legacy format: convert string to dict
                normalized[button_id] = {"command": button_data, "type": "shell"}
            elif isinstance(button_data, dict):
                # New format: already a dict
                normalized[button_id] = button_data
            else:
                logger.warning(f"Button {button_id} has invalid format: {button_data}")

        return normalized
    except FileNotFoundError:
        logger.error(f"Config file not found: {config_path}")
        sys.exit(1)
    except yaml.YAMLError as e:
        logger.error(f"Error parsing {config_path}: {e}")
        sys.exit(1)

def find_device() -> StreamDock:
    """Find and open the AJAZZ via the Mirabox StreamDock SDK."""
    manager = DeviceManager()
    devices = manager.enumerate()

    if not devices:
        logger.error("No StreamDock device found (VID=0x0300, PID=0x3010)")
        sys.exit(1)

    device = devices[0]
    device.open()
    device.init()
    logger.info(f"Connected to {device.path} (firmware: {device.firmware_version})")
    return device

def execute_command(command: str, use_shell: bool = False) -> None:
    """Execute a command with optional shell support.

    Args:
        command: Command or script to execute
        use_shell: If True, execute with shell=True (for scripts with pipes).
                  If False, parse safely with shlex.split() to prevent injection.
    """
    try:
        if use_shell:
            # For complex scripts with pipes (e.g., clipboard commands)
            logger.info(f"Executing script (shell): {command[:80]}...")
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=10
            )
        else:
            # For safety: parse command without shell interpretation
            cmd_parts = shlex.split(command)
            logger.info(f"Executing command (safe): {command}")
            result = subprocess.run(
                cmd_parts,
                capture_output=True,
                text=True,
                timeout=5
            )

        if result.returncode != 0:
            logger.error(f"Command failed: {command}")
            if result.stderr:
                logger.error(f"Error: {result.stderr}")
        else:
            if result.stdout:
                logger.info(f"Output: {result.stdout.strip()}")
    except subprocess.TimeoutExpired:
        logger.error(f"Command timeout: {command}")
    except ValueError as e:
        logger.error(f"Invalid command syntax: {command} - {e}")
    except FileNotFoundError:
        logger.error(f"Command not found: {command}")
    except Exception as e:
        logger.error(f"Error executing command: {e}")

def make_button_callback(buttons: Dict) -> callable:
    """Return a callback for the SDK's set_key_callback."""
    def on_key(device: StreamDock, event) -> None:
        if event.event_type != EventType.BUTTON or event.state != 1:
            return  # only trigger on press, ignore release

        button_id = event.key.value  # integer 1-15
        if button_id not in buttons:
            logger.debug(f"Unmapped button {button_id}")
            return

        button_config = buttons[button_id]
        button_label = button_config.get("label", f"Button {button_id}")
        command = button_config.get("script") or button_config.get("command")
        button_type = button_config.get("type", "shell")

        if not command:
            logger.warning(f"Button {button_id} has no script or command defined")
            return

        logger.info(f"Button {button_id} pressed ({button_label})")
        use_shell = button_type in ("clipboard", "script")
        execute_command(command, use_shell=use_shell)

    return on_key


def main() -> None:
    """Main loop: open device via SDK, listen for button presses via callback."""
    buttons = load_config()
    logger.info("Loading config...")
    logger.info(f"Configured buttons: {list(buttons.keys())}")

    device = find_device()
    device.set_key_callback(make_button_callback(buttons))
    logger.info("Listening for button presses...")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
    finally:
        try:
            device.set_key_callback(None)
            time.sleep(0.1)
            device.close()
            logger.info("Device closed successfully")
        except Exception as e:
            logger.debug(f"Error closing device: {e}")

if __name__ == "__main__":
    main()
