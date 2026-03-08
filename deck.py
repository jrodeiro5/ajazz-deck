#!/usr/bin/env python3
import os
import sys
import threading
from pathlib import Path

# Add vendored SDK to path
VENDOR_PATH = Path(__file__).parent / "vendor"
sys.path.insert(0, str(VENDOR_PATH))

import atexit
import shlex
import subprocess
import time

import pyudev
import yaml
from loguru import logger
from StreamDock.DeviceManager import DeviceManager
from StreamDock.Devices.StreamDock import StreamDock
from StreamDock.InputTypes import EventType

from config_models import ButtonConfig

# Paths
PROJECT_DIR = Path(__file__).parent
LOG_FILE = PROJECT_DIR / "deck.log"
PID_FILE = PROJECT_DIR / "deck.pid"
CONFIG_FILE = Path(os.getenv("AJAZZ_CONFIG", str(PROJECT_DIR / "buttons.yaml")))

# Ensure directories exist
LOG_FILE.parent.mkdir(exist_ok=True)

# Configure loguru
logger.remove()
logger.add(
    sys.stderr,
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="{time:YYYY-MM-DD HH:mm:ss} [{level}] {message}",
)
logger.add(
    str(LOG_FILE),
    rotation="10 MB",
    retention="7 days",
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="{time:YYYY-MM-DD HH:mm:ss} [{level}] {message}",
)

# Global reconnect event for udev hotplug
_reconnect_event = threading.Event()


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


check_single_instance()


def load_config(config_file: str | Path = CONFIG_FILE) -> dict[int, dict]:
    """Load button mappings from YAML config.

    Supports both simple command strings and complex button objects:
    - Simple: button_id: "command string"
    - Complex: button_id: {label, image, type, script/command}
    """
    config_path = Path(config_file)
    try:
        with open(config_path) as f:
            config = yaml.safe_load(f)
        buttons = config.get("buttons", {})

        # Normalize button format: convert string commands to dict format
        normalized = {}
        for button_id, button_data in buttons.items():
            if isinstance(button_data, str):
                # Legacy format: convert string to dict
                normalized[button_id] = {"command": button_data, "type": "shell"}
            elif isinstance(button_data, dict):
                normalized[button_id] = button_data
            else:
                logger.warning(f"Button {button_id} has invalid format: {button_data}")

        # Validate each button with Pydantic
        for button_id, button_data in normalized.items():
            try:
                ButtonConfig(**button_data)
            except Exception as e:
                logger.error(f"Invalid config for button {button_id}: {e}")
                sys.exit(1)

        return normalized
    except FileNotFoundError:
        logger.error(
            "buttons.yaml not found. Run: cp buttons.example.yaml buttons.yaml"
        )
        sys.exit(1)
    except yaml.YAMLError as e:
        logger.error(f"Error parsing {config_path}: {e}")
        sys.exit(1)


def find_device() -> StreamDock:
    """Find and open AJAZZ via the Mirabox StreamDock SDK."""
    manager = DeviceManager()
    devices = manager.enumerate()

    if not devices:
        raise RuntimeError("No StreamDock device found (VID=0x0300, PID=0x3010)")

    device = devices[0]
    device.open()
    device.init()
    logger.info(f"Connected to {device.path} (firmware: {device.firmware_version})")
    return device


def connect_with_retry() -> StreamDock:
    """Connect to device with exponential backoff retry."""
    attempt = 0
    while True:
        try:
            return find_device()
        except Exception as e:
            wait = min(2**attempt, 60)
            logger.warning(
                "Device not found (attempt {a}): {e}. Retry in {w}s",
                a=attempt + 1,
                e=e,
                w=wait,
            )
            time.sleep(wait)
            attempt += 1


def usbipd_status() -> str:
    """Check usbipd attachment status for AJAZZ device."""
    try:
        result = subprocess.run(
            ["usbipd.exe", "list"], capture_output=True, text=True, timeout=5
        )
        for line in result.stdout.splitlines():
            if "0300:3010" in line.lower():
                return (
                    "attached"
                    if "attached" in line.lower()
                    else f"NOT attached — {line.strip()}"
                )
        return "VID:PID 0300:3010 not found in usbipd list"
    except FileNotFoundError:
        return "usbipd.exe not found (non-WSL or not installed)"
    except Exception as e:
        return f"check failed: {e}"


def start_udev_monitor() -> None:
    """Start udev monitor for hotplug device detection."""

    def _watch():
        context = pyudev.Context()
        monitor = pyudev.Monitor.from_netlink(context)
        monitor.filter_by(subsystem="usb")
        for action, device in monitor:
            if action == "add":
                vid = device.get("ID_VENDOR_ID", "")
                pid = device.get("ID_MODEL_ID", "")
                if vid == "0300" and pid == "3010":
                    logger.info("udev: AJAZZ device attached — signaling reconnect")
                    _reconnect_event.set()

    t = threading.Thread(target=_watch, daemon=True)
    t.start()


def apply_button_images(device: StreamDock, buttons: dict) -> None:
    """Apply configured button images to device.

    Iterates over all buttons with an 'image' path and sends them to the device.
    Calls device.refresh() once after setting all images.

    Args:
        device: Connected StreamDock device
        buttons: Button configuration dict from load_config()
    """
    images_applied = 0
    for button_id, btn_conf in buttons.items():
        if isinstance(btn_conf, dict) and btn_conf.get("image"):
            image_path = btn_conf["image"]
            image_file = Path(image_path)
            if image_file.exists():
                try:
                    device.set_key_image(int(button_id), image_path)
                    images_applied += 1
                    logger.debug(f"Set image for button {button_id}: {image_path}")
                except Exception as e:
                    logger.warning(f"Failed to set image for button {button_id}: {e}")
            else:
                logger.warning(
                    f"Image file not found for button {button_id}: {image_path}"
                )

    if images_applied > 0:
        try:
            device.refresh()
            logger.info(f"Applied {images_applied} button images and refreshed display")
        except Exception as e:
            logger.warning(f"Failed to refresh display after setting images: {e}")


def execute_command(command: str, use_shell: bool = False) -> None:
    """Execute a command with optional shell support.

    Args:
        command: Command or script to execute
        use_shell: If True, execute with shell=True (for scripts with pipes).
                  If False, parse safely with shlex.split() to prevent injection.
    """
    try:
        start = time.monotonic()

        if use_shell:
            # For complex scripts with pipes (e.g., clipboard commands)
            logger.info(f"Executing script (shell): {command[:80]}...")
            result = subprocess.run(
                ["bash", "-c", command], capture_output=True, text=True, timeout=10
            )
        else:
            # For safety: parse command without shell interpretation
            cmd_parts = shlex.split(command)
            logger.info(f"Executing command (safe): {command}")
            result = subprocess.run(
                cmd_parts, capture_output=True, text=True, timeout=5
            )

        elapsed_ms = int((time.monotonic() - start) * 1000)
        logger.info("exit={rc} duration={ms}ms", rc=result.returncode, ms=elapsed_ms)

        if result.returncode != 0:
            logger.error(f"Command failed: {command}")
            if result.stderr:
                logger.error(f"stderr: {result.stderr.strip()[:200]}")
        else:
            out = result.stdout.strip()
            snippet = (out[:200] + "…") if len(out) > 200 else out
            if snippet:
                logger.debug(f"stdout: {snippet}")

    except subprocess.TimeoutExpired:
        logger.error(f"Command timeout: {command}")
    except ValueError as e:
        logger.error(f"Invalid command syntax: {command} - {e}")
    except FileNotFoundError:
        logger.error(f"Command not found: {command}")
    except Exception as e:
        logger.error(f"Error executing command: {e}")


def make_button_callback(buttons: dict) -> callable:
    """Return a callback for the SDK's set_key_callback."""

    def on_key(device, event) -> None:
        # Debug HID event logging
        logger.debug(
            "HID event: type={t} key={k} state={s}",
            t=event.event_type,
            k=getattr(event.key, "value", None),
            s=event.state,
        )

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


@logger.catch
def main() -> None:
    """Main loop: open device via SDK, listen for button presses via callback."""
    # Start udev monitor for hotplug detection
    start_udev_monitor()

    logger.info("Loading config...")
    buttons = load_config()
    logger.info(f"Configured buttons: {list(buttons.keys())}")

    device = connect_with_retry()
    apply_button_images(device, buttons)
    device.set_key_callback(make_button_callback(buttons))

    # Startup banner
    logger.info(
        "ajazz-deck v{ver} | device={fw} | buttons={n}",
        ver="0.1.0",
        fw=device.firmware_version,
        n=len(buttons),
    )
    usb = usbipd_status()
    if "attached" not in usb:
        logger.warning("usbipd: {s}", s=usb)
    else:
        logger.info("usbipd: {s}", s=usb)

    logger.info("Listening for button presses...")

    try:
        while True:
            # Check for udev hotplug reconnect signal
            if _reconnect_event.is_set():
                _reconnect_event.clear()
                logger.info("Reconnecting due to udev hotplug...")
                try:
                    device.close()
                except Exception:
                    pass
                device = connect_with_retry()
                apply_button_images(device, buttons)
                device.set_key_callback(make_button_callback(buttons))
                logger.info("Reconnected successfully")

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
