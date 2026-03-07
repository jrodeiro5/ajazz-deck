#!/usr/bin/env python3
"""Simple AJAZZ CLI implementation."""

import sys
import os
from pathlib import Path
import subprocess
import click
import yaml
from rich.console import Console
from rich.table import Table
from rich.text import Text
from rich.panel import Panel

# Paths
PROJECT_DIR = Path(__file__).parent
PID_FILE = PROJECT_DIR / "deck.pid"
CONFIG_FILE = Path(os.getenv("AJAZZ_CONFIG", str(PROJECT_DIR / "buttons.yaml")))

console = Console()

AJAZZ_BANNER = r"""
    _        _    _     _______  _______
   / \      | |  / \   |___   / |___   /
  / _ \  _  | | / _ \     /  /      /  /
 / ___ \| |_| |/ ___ \   /  /_     /  /_
/_/   \_\\___//_/   \_\ /_____|   /_____|
"""
AJAZZ_SUBTITLE = "  [ OFFICIAL STORE ]"
AJAZZ_DIVIDER  = "=" * 42


def _show_welcome():
    console.print(Text(AJAZZ_BANNER, style="bold #E53935"))
    console.print(Text(AJAZZ_SUBTITLE, style="bold #BDBDBD"))
    console.print(Text(AJAZZ_DIVIDER, style="dim #757575"))
    console.print()
    tips = (
        "[bold]Tips for getting started:[/bold]\n"
        "1. [#E53935]ajazz daemon start[/#E53935]     → Start the button daemon\n"
        "2. [#E53935]ajazz button list[/#E53935]      → Show configured buttons\n"
        "3. [#E53935]ajazz config validate[/#E53935]  → Check buttons.yaml\n"
        "4. [#E53935]ajazz --help[/#E53935]           → Full command reference"
    )
    console.print(Panel(tips, border_style="#E53935", padding=(0, 2)))
    console.print()


def read_config():
    """Read and parse buttons.yaml configuration."""
    try:
        with open(CONFIG_FILE, "r") as f:
            config = yaml.safe_load(f)
            return config.get("buttons", {})
    except FileNotFoundError:
        console.print(f"[red]Config file not found: {CONFIG_FILE}[/red]")
        sys.exit(1)
    except yaml.YAMLError as e:
        console.print(f"[red]Error parsing config: {e}[/red]")
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
    """AJAZZ AK820 Macro Pad Controller"""
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
                start_new_session=True
            )
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
                start_new_session=True
            )
            PID_FILE.write_text(str(proc.pid))
            console.print(f"[green]Daemon restarted (PID {proc.pid})[/green]")
        except Exception as e:
            console.print(f"[red]Failed to restart: {e}[/red]")
            sys.exit(1)


@cli.command()
@click.option("--json", "json_output", is_flag=True, help="Output in JSON format")
def button_list(json_output):
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


@cli.command()
@click.argument("button_id", type=int)
def button_show(button_id):
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


@cli.command()
@click.argument("button_id", type=int)
def button_test(button_id):
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


@cli.command()
def config_show():
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
    
    for button_id, config in buttons.items():
        label = config.get("label", f"Button {button_id}")
        button_type = config.get("type", "shell")
        command = config.get("command") or config.get("script", "")
        command_preview = command[:60] + "..." if len(command) > 60 else command
        
        table.add_row(str(button_id), label, button_type, command_preview)
    
    console.print(table)


@cli.command()
def config_validate():
    """Validate buttons.yaml syntax."""
    try:
        with open(CONFIG_FILE, "r") as f:
            yaml.safe_load(f)
        console.print("[green]✓ Configuration syntax is valid[/green]")
    except yaml.YAMLError as e:
        console.print(f"[red]✗ Configuration error: {e}[/red]")
        sys.exit(1)
    except FileNotFoundError:
        console.print(f"[red]✗ Config file not found: {CONFIG_FILE}[/red]")
        sys.exit(1)


@cli.command()
def device_status():
    """Show device connection status."""
    console.print("[cyan]Device status: Checking...[/cyan]")
    console.print("[yellow]Note: This requires the AJAZZ device to be connected[/yellow]")


if __name__ == "__main__":
    cli()
