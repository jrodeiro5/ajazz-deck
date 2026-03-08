#!/usr/bin/env python3
"""Simple AJAZZ CLI implementation."""

import os
import subprocess
import sys
import time
from pathlib import Path

import click
import yaml
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from config_models import AjazzConfig
from image_engine import process_image

# Paths
PROJECT_DIR = Path(__file__).parent.resolve()
PID_FILE = PROJECT_DIR / "deck.pid"
CONFIG_FILE = Path(os.getenv("AJAZZ_CONFIG", PROJECT_DIR / "buttons.yaml"))
LOG_FILE = PROJECT_DIR / "deck.log"

console = Console()

AJAZZ_BANNER = r"""
    _        _    _     _______  _______
   / \      | |  / \   |___   / |___   /
  / _ \  _  | | / _ \     /  /      /  /
 / ___ \| |_| |/ ___ \   /  /_     /  /_
/_/   \_\___//_/   \_\ /_____|   /_____|
 ____  _____  ____  _  __
|  _ \| ____||  __|| |/ /
| | | |  _|  | |   |  <
| |_| | |___ | |__ | . \
|____/|_____||____||_|\_\
"""
AJAZZ_SUBTITLE = "  [ AJazz AKP153 Macro Pad Controller ]"
AJAZZ_DIVIDER = "=" * 42


def _show_welcome():
    console.print(Text(AJAZZ_BANNER, style="bold #E53935"))
    console.print(Text(AJAZZ_SUBTITLE, style="bold #BDBDBD"))
    console.print(Text(AJAZZ_DIVIDER, style="dim #757575"))
    console.print()
    tips = (
        "[bold]Tips for getting started:[/bold]\n"
        "1. [#E53935]ajazz daemon start[/#E53935]                                 → Start daemon\n"
        "2. [#E53935]ajazz button set 1 --label 'Term' --command 'xterm'         → Configure button[/#E53935]\n"
        "3. [#E53935]ajazz button list[/#E53935]                                  → Show buttons\n"
        "4. [#E53935]ajazz --help[/#E53935]                                       → Full reference"
    )
    console.print(Panel(tips, border_style="#E53935", padding=(0, 2)))
    console.print()


def read_config():
    """Read and parse buttons.yaml configuration."""
    try:
        with open(CONFIG_FILE) as f:
            config_data = yaml.safe_load(f)
            config = AjazzConfig(**config_data)
            return {k: v.model_dump() for k, v in config.buttons.items()}
    except FileNotFoundError:
        console.print(
            "[red]buttons.yaml not found.[/red] "
            "Run: [bold]cp buttons.example.yaml buttons.yaml[/bold]"
        )
        sys.exit(1)
    except yaml.YAMLError as e:
        console.print(f"[red]Error parsing YAML: {e}[/red]")
        sys.exit(1)
    except Exception as e:
        console.print(f"[red]Configuration error: {e}[/red]")
        sys.exit(1)


def get_daemon_status():
    """Check if daemon is running via PID file."""
    if not PID_FILE.exists():
        return "stopped"

    try:
        pid = int(PID_FILE.read_text().strip())
        os.kill(pid, 0)
        return f"running (PID {pid})"
    except (ProcessLookupError, ValueError, FileNotFoundError):
        return "stopped"


@click.group(invoke_without_command=True)
@click.pass_context
def cli(ctx):
    """AJAZZ AKP153 Macro Pad Controller"""
    if ctx.invoked_subcommand is None:
        _show_welcome()


@cli.command()
@click.argument("action", type=click.Choice(["start", "stop", "restart", "status"]))
def daemon(action):
    """Control AJAZZ daemon (start|stop|restart|status)."""

    if action == "status":
        status = get_daemon_status()
        console.print(f"Daemon status: [green]{status}[/green]")
        return

    if action == "start":
        try:
            proc = subprocess.Popen(
                ["python3", str(PROJECT_DIR / "deck.py")],
                cwd=PROJECT_DIR,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=True,
            )
            time.sleep(0.5)  # Let subprocess fully start and write its own PID
            PID_FILE.write_text(str(proc.pid))
            console.print(f"[green]Daemon started (PID {proc.pid})[/green]")
        except Exception as e:
            console.print(f"[red]Failed to start: {e}[/red]")
            sys.exit(1)

    elif action == "stop":
        if not PID_FILE.exists():
            console.print("[yellow]Daemon not running[/yellow]")
            return
        try:
            pid = int(PID_FILE.read_text().strip())
            os.kill(pid, 15)  # SIGTERM
            PID_FILE.unlink()
            console.print("[green]Daemon stopped[/green]")
        except (ProcessLookupError, ValueError):
            console.print("[yellow]Daemon not running[/yellow]")
            PID_FILE.unlink(missing_ok=True)

    elif action == "restart":
        # Stop if running
        if PID_FILE.exists():
            try:
                pid = int(PID_FILE.read_text().strip())
                os.kill(pid, 15)
                PID_FILE.unlink()
            except (ProcessLookupError, ValueError):
                pass

        # Start
        try:
            proc = subprocess.Popen(
                ["python3", str(PROJECT_DIR / "deck.py")],
                cwd=PROJECT_DIR,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=True,
            )
            PID_FILE.write_text(str(proc.pid))
            console.print(f"[green]Daemon restarted (PID {proc.pid})[/green]")
        except Exception as e:
            console.print(f"[red]Failed to restart: {e}[/red]")
            sys.exit(1)


@cli.group()
def button():
    """Button management commands."""
    pass


@button.command()
@click.option("--json", "json_output", is_flag=True, help="Output in JSON format")
def list(json_output):
    """List all configured buttons."""
    buttons = read_config()

    if json_output:
        import json

        console.print(json.dumps(buttons, indent=2))
        return

    if not buttons:
        console.print("[yellow]No buttons configured[/yellow]")
        return

    table = Table(title="Configured Buttons")
    table.add_column("ID", style="cyan")
    table.add_column("Label", style="green")
    table.add_column("Type", style="magenta")
    table.add_column("Command", style="blue")

    for button_id, config in buttons.items():
        label = config.get("label", f"Button {button_id}")
        button_type = config.get("type", "shell")
        command = config.get("command") or config.get("script", "")
        command_preview = command[:50] + "..." if len(command) > 50 else command

        table.add_row(str(button_id), label, button_type, command_preview)

    console.print(table)


@button.command()
@click.argument("button_id", type=int)
def show(button_id):
    """Show specific button configuration."""
    buttons = read_config()

    if button_id not in buttons:
        console.print(f"[red]Button {button_id} not found[/red]")
        sys.exit(1)

    config = buttons[button_id]
    console.print(f"[cyan]Button {button_id} Configuration:[/cyan]")
    console.print(f"  Label: [green]{config.get('label', 'N/A')}[/green]")
    console.print(f"  Type: [magenta]{config.get('type', 'shell')}[/magenta]")

    command = config.get("command") or config.get("script", "")
    if command:
        console.print(f"  Command: [blue]{command}[/blue]")


@button.command()
@click.argument("button_id", type=int)
def test(button_id):
    """Test button command execution."""
    buttons = read_config()

    if button_id not in buttons:
        console.print(f"[red]Button {button_id} not found[/red]")
        sys.exit(1)

    config = buttons[button_id]
    command = config.get("command") or config.get("script", "")

    if not command:
        console.print(f"[red]Button {button_id} has no command configured[/red]")
        sys.exit(1)

    console.print(f"[cyan]Testing button {button_id}...[/cyan]")
    console.print(f"Command: [blue]{command[:100]}[/blue]")


@button.command()
@click.argument("button_id", type=int)
@click.option("--label", required=True, help="Display label for the button")
@click.option("--command", required=True, help="Shell command to execute")
@click.option(
    "--type",
    "button_type",
    type=click.Choice(["shell", "clipboard", "script"]),
    default="shell",
    help="Execution mode (default: shell)",
)
@click.option("--icon", help="Optional path to .png icon file")
def set(button_id, label, command, button_type, icon):
    """Add or update a button in buttons.yaml."""
    if not 1 <= button_id <= 15:
        console.print(f"[red]Error: button_id must be 1–15, got {button_id}[/red]")
        sys.exit(1)

    # Read or initialize config
    config = {"buttons": {}}
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE) as f:
                config = yaml.safe_load(f) or {"buttons": {}}
        except Exception as e:
            console.print(f"[red]Error reading config: {e}[/red]")
            sys.exit(1)

    # Build button entry
    if button_type in ("script", "clipboard"):
        entry = {"label": label, "script": command, "type": button_type}
    else:
        entry = {"label": label, "command": command, "type": button_type}

    if icon:
        entry["image"] = icon

    # Validate with Pydantic
    try:
        from config_models import ButtonConfig

        ButtonConfig(**entry)
    except Exception as e:
        console.print(f"[red]Error: Invalid button configuration: {e}[/red]")
        sys.exit(1)

    # Update config
    config.setdefault("buttons", {})[button_id] = entry

    # Write config
    try:
        with open(CONFIG_FILE, "w") as f:
            yaml.dump(config, f, default_flow_style=False, allow_unicode=True)
        console.print(
            f"[green]✓ Button {button_id} configured[/green]: {label} → {command}"
        )
    except Exception as e:
        console.print(f"[red]Error writing config: {e}[/red]")
        sys.exit(1)

    # Restart daemon if running
    status = get_daemon_status()
    if "running" in status:
        console.print("[cyan]Restarting daemon to apply changes...[/cyan]")
        subprocess.run(
            ["python3", str(PROJECT_DIR / "cli.py"), "daemon", "restart"],
            cwd=PROJECT_DIR,
            capture_output=True,
        )
        console.print("[green]✓ Daemon restarted[/green]")
    else:
        console.print(
            "[yellow]Daemon not running. Start with: ajazz daemon start[/yellow]"
        )


@button.command()
@click.argument("button_id", type=int)
def remove(button_id):
    """Remove a button from buttons.yaml."""
    if not 1 <= button_id <= 15:
        console.print(f"[red]Error: button_id must be 1–15, got {button_id}[/red]")
        sys.exit(1)

    if not CONFIG_FILE.exists():
        console.print("[red]buttons.yaml not found. No button to remove.[/red]")
        sys.exit(1)

    try:
        with open(CONFIG_FILE) as f:
            config = yaml.safe_load(f) or {"buttons": {}}
    except Exception as e:
        console.print(f"[red]Error reading config: {e}[/red]")
        sys.exit(1)

    buttons = config.get("buttons", {})
    if button_id not in buttons:
        console.print(f"[red]Error: Button {button_id} is not configured[/red]")
        sys.exit(1)

    # Remove button
    del buttons[button_id]

    # Write config
    try:
        with open(CONFIG_FILE, "w") as f:
            yaml.dump(config, f, default_flow_style=False, allow_unicode=True)
        console.print(f"[green]✓ Button {button_id} removed[/green]")
    except Exception as e:
        console.print(f"[red]Error writing config: {e}[/red]")
        sys.exit(1)

    # Restart daemon if running
    status = get_daemon_status()
    if "running" in status:
        console.print("[cyan]Restarting daemon to apply changes...[/cyan]")
        subprocess.run(
            ["python3", str(PROJECT_DIR / "cli.py"), "daemon", "restart"],
            cwd=PROJECT_DIR,
            capture_output=True,
        )
        console.print("[green]✓ Daemon restarted[/green]")


@cli.group()
def config():
    """Configuration management commands."""
    pass


@config.command()
def show_all():
    """Display current button configuration."""
    buttons = read_config()

    if not buttons:
        console.print("[yellow]No buttons configured[/yellow]")
        return

    table = Table(title="Button Configuration")
    table.add_column("ID", style="cyan")
    table.add_column("Label", style="green")
    table.add_column("Type", style="magenta")
    table.add_column("Command/Script", style="blue")

    for button_id, config_item in buttons.items():
        label = config_item.get("label", f"Button {button_id}")
        button_type = config_item.get("type", "shell")
        command = config_item.get("command") or config_item.get("script", "")
        command_preview = command[:60] + "..." if len(command) > 60 else command

        table.add_row(str(button_id), label, button_type, command_preview)

    console.print(table)


@config.command()
def validate():
    """Validate buttons.yaml syntax and structure."""
    try:
        with open(CONFIG_FILE) as f:
            config_data = yaml.safe_load(f)
            AjazzConfig(**config_data)
        console.print("[green]✓ Configuration is valid[/green]")
    except FileNotFoundError:
        console.print(
            "[red]✗ buttons.yaml not found.[/red] "
            "Run: [bold]cp buttons.example.yaml buttons.yaml[/bold]"
        )
        sys.exit(1)
    except yaml.YAMLError as e:
        console.print(f"[red]✗ YAML syntax error: {e}[/red]")
        sys.exit(1)
    except Exception as e:
        console.print(f"[red]✗ Configuration error: {e}[/red]")
        sys.exit(1)


@cli.group()
def image():
    """Button image management commands."""
    pass


@image.command("set")
@click.argument("button_id", type=int)
@click.option("--url", help="Download image from URL")
@click.option("--file", "file_path", help="Use local image file")
@click.option(
    "--generate", help="Generate image from text prompt (requires GOOGLE_API_KEY)"
)
def set_image(button_id, url, file_path, generate):
    """Set button image from URL, local file, or AI-generated prompt."""
    if not 1 <= button_id <= 15:
        console.print(f"[red]Error: button_id must be 1–15, got {button_id}[/red]")
        sys.exit(1)

    # Validate that exactly one source is provided
    sources = sum([bool(url), bool(file_path), bool(generate)])
    if sources != 1:
        console.print(
            "[red]Error: Provide exactly one source: --url, --file, or --generate[/red]"
        )
        sys.exit(1)

    # Determine source and process image
    try:
        if url:
            console.print(f"[cyan]Downloading image from {url}...[/cyan]")
            source = url
        elif file_path:
            console.print(f"[cyan]Loading image from {file_path}...[/cyan]")
            source = file_path
        else:  # generate
            console.print(f"[cyan]Generating image: '{generate}'...[/cyan]")
            source = f"generate:{generate}"

        image_path = process_image(source, button_id)
        console.print(f"[green]✓ Image processed: {image_path}[/green]")

        # Update buttons.yaml with image path
        config = {"buttons": {}}
        if CONFIG_FILE.exists():
            with open(CONFIG_FILE) as f:
                config = yaml.safe_load(f) or {"buttons": {}}

        if button_id not in config.get("buttons", {}):
            console.print(
                f"[yellow]Warning: Button {button_id} not configured. "
                "Image saved but button needs to be configured first.[/yellow]"
            )
            config.setdefault("buttons", {})[button_id] = {"image": image_path}
        else:
            config["buttons"][button_id]["image"] = image_path

        with open(CONFIG_FILE, "w") as f:
            yaml.dump(config, f, default_flow_style=False, allow_unicode=True)
        console.print("[green]✓ Updated buttons.yaml[/green]")

        # Restart daemon if running
        status = get_daemon_status()
        if "running" in status:
            console.print("[cyan]Restarting daemon to apply image...[/cyan]")
            subprocess.run(
                ["python3", str(PROJECT_DIR / "cli.py"), "daemon", "restart"],
                cwd=PROJECT_DIR,
                capture_output=True,
            )
            console.print("[green]✓ Daemon restarted[/green]")
        else:
            console.print(
                "[yellow]Daemon not running. Start with: ajazz daemon start[/yellow]"
            )

    except ValueError as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)
    except Exception as e:
        console.print(f"[red]Error processing image: {e}[/red]")
        sys.exit(1)


@image.command()
@click.argument("button_id", type=int)
def clear(button_id):
    """Remove image from button."""
    if not 1 <= button_id <= 15:
        console.print(f"[red]Error: button_id must be 1–15, got {button_id}[/red]")
        sys.exit(1)

    if not CONFIG_FILE.exists():
        console.print("[yellow]buttons.yaml not found[/yellow]")
        return

    config = yaml.safe_load(CONFIG_FILE.read_text()) or {"buttons": {}}
    if button_id not in config.get("buttons", {}):
        console.print(f"[yellow]Button {button_id} not configured[/yellow]")
        return

    button_config = config["buttons"][button_id]
    if "image" not in button_config:
        console.print(f"[yellow]Button {button_id} has no image[/yellow]")
        return

    del button_config["image"]
    CONFIG_FILE.write_text(
        yaml.dump(config, default_flow_style=False, allow_unicode=True)
    )
    console.print(f"[green]✓ Image removed from button {button_id}[/green]")

    # Restart daemon if running
    status = get_daemon_status()
    if "running" in status:
        console.print("[cyan]Restarting daemon...[/cyan]")
        subprocess.run(
            ["python3", str(PROJECT_DIR / "cli.py"), "daemon", "restart"],
            cwd=PROJECT_DIR,
            capture_output=True,
        )
        console.print("[green]✓ Daemon restarted[/green]")


@image.command()
@click.argument("button_id", type=int)
def show_image(button_id):
    """Show image path for button."""
    if not 1 <= button_id <= 15:
        console.print(f"[red]Error: button_id must be 1–15, got {button_id}[/red]")
        sys.exit(1)

    buttons = read_config()
    if button_id not in buttons:
        console.print(f"[yellow]Button {button_id} not configured[/yellow]")
        return

    button_config = buttons[button_id]
    image_path = button_config.get("image")
    if image_path:
        console.print(f"[cyan]Button {button_id} image:[/cyan] {image_path}")
    else:
        console.print(f"[yellow]Button {button_id} has no image[/yellow]")


@cli.command()
@click.option(
    "--lines",
    "-n",
    type=int,
    default=20,
    help="Number of log lines to show (default: 20)",
)
def logs(lines):
    """Show last N lines from daemon log file."""
    if not LOG_FILE.exists():
        console.print(
            "[yellow]Log file not found. Start daemon with: ajazz daemon start[/yellow]"
        )
        return

    try:
        log_content = LOG_FILE.read_text()
        log_lines = log_content.strip().split("\n")

        # Get last N lines
        last_lines = log_lines[-lines:] if len(log_lines) > lines else log_lines

        if not last_lines:
            console.print("[yellow]Log file is empty[/yellow]")
            return

        console.print(
            Panel(
                "\n".join(last_lines),
                title=f"Daemon Log (last {len(last_lines)} lines)",
                border_style="cyan",
            )
        )
    except Exception as e:
        console.print(f"[red]Error reading log file: {e}[/red]")
        sys.exit(1)


if __name__ == "__main__":
    cli()
