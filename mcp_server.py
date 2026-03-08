#!/usr/bin/env python3
"""FastMCP server for AJAZZ AK820 macro pad control."""

import os
import subprocess
from pathlib import Path

import yaml
from fastmcp import FastMCP

from config_models import ButtonConfig
from image_engine import process_image

# Paths
PROJECT_DIR = Path(__file__).parent.resolve()
CONFIG_FILE = PROJECT_DIR / "buttons.yaml"
PID_FILE = PROJECT_DIR / "deck.pid"
LOG_FILE = PROJECT_DIR / "deck.log"

mcp = FastMCP(
    "ajazz-deck",
    instructions="""
    Controls the AJAZZ AK820 macro pad daemon.
    Use set_button to configure physical buttons with shell commands.
    Always check daemon_status before starting.
    After set_button, daemon auto-restarts if it was running.
    """,
)


# ── Helpers ────────────────────────────────────────────────────


def _read_config() -> dict:
    """Read buttons.yaml configuration."""
    if not CONFIG_FILE.exists():
        return {"buttons": {}}
    return yaml.safe_load(CONFIG_FILE.read_text()) or {"buttons": {}}


def _write_config(config: dict) -> None:
    """Write buttons.yaml configuration."""
    CONFIG_FILE.write_text(
        yaml.dump(config, default_flow_style=False, allow_unicode=True)
    )


def _daemon_running() -> tuple[bool, int | None]:
    """Check if daemon is running via PID file."""
    if not PID_FILE.exists():
        return False, None
    try:
        pid = int(PID_FILE.read_text().strip())
        os.kill(pid, 0)  # Check if process exists
        return True, pid
    except (ProcessLookupError, ValueError):
        return False, None


def _run_cli(*args) -> str:
    """Run cli.py command and return output."""
    result = subprocess.run(
        ["python3", str(PROJECT_DIR / "cli.py")] + list(args),
        capture_output=True,
        text=True,
        cwd=PROJECT_DIR,
    )
    return result.stdout.strip() or result.stderr.strip()


# ── Tools ──────────────────────────────────────────────────────


@mcp.tool()
def list_buttons() -> dict:
    """List all configured buttons on the AK820 macro pad."""
    config = _read_config()
    buttons = config.get("buttons", {})
    if not buttons:
        return {
            "count": 0,
            "buttons": {},
            "hint": "No buttons configured. Use set_button to add some.",
        }
    return {"count": len(buttons), "buttons": buttons}


@mcp.tool()
def set_button(
    button_id: int,
    label: str,
    command: str,
    type: str = "shell",
    icon: str | None = None,
) -> str:
    """Configure a physical button on the AK820.

    Args:
        button_id: Button number (1-15)
        label: Display name (e.g. 'Terminal')
        command: Shell command to run on press (e.g. 'xterm')
        type: 'shell' (default), 'clipboard', or 'script'
        icon: Optional path to .png icon file
    """
    if not 1 <= button_id <= 15:
        return f"Error: button_id must be 1–15, got {button_id}"

    config = _read_config()
    config.setdefault("buttons", {})

    # Use 'script' field for script/clipboard types (matches deck.py's lookup order)
    if type in ("script", "clipboard"):
        entry = {"label": label, "script": command, "type": type}
    else:
        entry = {"label": label, "command": command, "type": type}

    if icon:
        entry["image"] = icon

    try:
        ButtonConfig(**entry)
    except Exception as e:
        return f"Error: Invalid button configuration: {e}"

    config["buttons"][button_id] = entry
    _write_config(config)

    was_running, _ = _daemon_running()
    if was_running:
        _run_cli("daemon", "restart")
        return (
            f"Button {button_id} configured: '{label}' → {command}\n"
            f"Daemon restarted to apply changes."
        )
    return (
        f"Button {button_id} configured: '{label}' → {command}\n"
        f"Daemon not running. Start with: ajazz daemon start"
    )


@mcp.tool()
def remove_button(button_id: int) -> str:
    """Remove a button configuration from the AK820."""
    config = _read_config()
    buttons = config.get("buttons", {})
    if button_id not in buttons:
        return f"Button {button_id} is not configured."
    del buttons[button_id]
    _write_config(config)
    was_running, _ = _daemon_running()
    if was_running:
        _run_cli("daemon", "restart")
        return f"Button {button_id} removed. Daemon restarted."
    return f"Button {button_id} removed."


@mcp.tool()
def daemon_status() -> dict:
    """Check if the AK820 daemon is running."""
    running, pid = _daemon_running()
    return {
        "running": running,
        "pid": pid,
        "config_exists": CONFIG_FILE.exists(),
        "device_vid_pid": "0300:3010",
    }


@mcp.tool()
def daemon_start() -> str:
    """Start the AK820 daemon."""
    running, pid = _daemon_running()
    if running:
        return f"Daemon already running (PID {pid})."
    if not CONFIG_FILE.exists():
        return (
            "Error: buttons.yaml not found. Use set_button to configure buttons first."
        )
    return _run_cli("daemon", "start")


@mcp.tool()
def daemon_stop() -> str:
    """Stop the AK820 daemon."""
    running, _ = _daemon_running()
    if not running:
        return "Daemon is not running."
    return _run_cli("daemon", "stop")


@mcp.tool()
def set_button_image_from_url(button_id: int, url: str) -> dict:
    """Download image from URL and set as button icon.

    Args:
        button_id: Button number (1-15)
        url: URL to image file

    Returns:
        Status dict with result and image path
    """
    if not 1 <= button_id <= 15:
        return {"error": f"button_id must be 1–15, got {button_id}"}

    try:
        image_path = process_image(url, button_id)

        config = _read_config()
        config.setdefault("buttons", {})
        if button_id not in config["buttons"]:
            config["buttons"][button_id] = {"image": image_path}
        else:
            config["buttons"][button_id]["image"] = image_path
        _write_config(config)

        was_running, _ = _daemon_running()
        if was_running:
            _run_cli("daemon", "restart")

        return {
            "status": "success",
            "button_id": button_id,
            "image_path": image_path,
            "daemon_restarted": was_running,
        }
    except Exception as e:
        return {"error": str(e)}


@mcp.tool()
def set_button_image_from_prompt(button_id: int, prompt: str) -> dict:
    """Generate button icon with Gemini AI from text description.

    Args:
        button_id: Button number (1-15)
        prompt: Text description of desired image

    Returns:
        Status dict with result and image path
    """
    if not 1 <= button_id <= 15:
        return {"error": f"button_id must be 1–15, got {button_id}"}

    try:
        source = f"generate:{prompt}"
        image_path = process_image(source, button_id)

        config = _read_config()
        config.setdefault("buttons", {})
        if button_id not in config["buttons"]:
            config["buttons"][button_id] = {"image": image_path}
        else:
            config["buttons"][button_id]["image"] = image_path
        _write_config(config)

        was_running, _ = _daemon_running()
        if was_running:
            _run_cli("daemon", "restart")

        return {
            "status": "success",
            "button_id": button_id,
            "image_path": image_path,
            "daemon_restarted": was_running,
        }
    except Exception as e:
        return {"error": str(e)}


@mcp.tool()
def clear_button_image(button_id: int) -> dict:
    """Remove image from button.

    Args:
        button_id: Button number (1-15)

    Returns:
        Status dict with result
    """
    if not 1 <= button_id <= 15:
        return {"error": f"button_id must be 1–15, got {button_id}"}

    config = _read_config()
    buttons = config.get("buttons", {})

    if button_id not in buttons:
        return {"status": "button_not_found", "button_id": button_id}

    if "image" not in buttons[button_id]:
        return {"status": "no_image", "button_id": button_id}

    del buttons[button_id]["image"]
    _write_config(config)

    was_running, _ = _daemon_running()
    if was_running:
        _run_cli("daemon", "restart")

    return {
        "status": "success",
        "button_id": button_id,
        "daemon_restarted": was_running,
    }


@mcp.tool()
def get_logs(lines: int = 20) -> str:
    """Get the last N lines from the daemon log file."""
    if not LOG_FILE.exists():
        return "No log file found. Start the daemon first."
    log_lines = LOG_FILE.read_text().splitlines()
    return "\n".join(log_lines[-lines:])


def main():
    """Entry point for the MCP server."""
    mcp.run()


if __name__ == "__main__":
    main()
