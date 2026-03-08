# AGENTS.md

A guide for AI coding agents working with the AJAZZ Deck project.

## Quick Setup Commands

```bash
# Install dependencies
uv sync --dev

# Run linting and formatting
uv run ruff check . --fix
uv run ruff format .

# Validate configuration
uv run python3 cli.py config validate

# Start daemon for testing
uv run python3 cli.py daemon start

# Run tests (when implemented)
uv run pytest -v
```

## Project Knowledge

### Tech Stack

- **Python 3.12+** with `uv` package manager
- **CLI Framework**: Click 8.3.1+ with Rich terminal output
- **Device SDK**: Mirabox StreamDock SDK (vendored in `vendor/`)
- **Configuration**: YAML with Pydantic validation
- **Image Processing**: Pillow 12.1.1+ with AI generation support
- **MCP Server**: FastMCP 3.1.0+ for Claude Code integration
- **Code Quality**: Ruff 0.15.5+ for linting and formatting

### File Structure

```text
ajazz-deck/
├── cli.py                 # Main CLI interface (ajazz command)
├── deck.py                # Core daemon and device management
├── mcp_server.py          # MCP server for Claude Code integration
├── config_models.py       # Pydantic configuration validation
├── image_engine.py        # Image processing and AI generation
├── buttons.yaml           # Button configuration (user creates)
├── buttons.example.yaml   # Example configuration template
├── vendor/                # StreamDock SDK (do not modify)
├── pyproject.toml         # Project configuration and dependencies
└── CHANGELOG*.md          # Version history and release notes
```

### Key Components

- **Daemon (`deck.py`)**: Manages device connection, button events, command execution
- **CLI (`cli.py`)**: User interface with grouped commands (`ajazz daemon`,
  `ajazz button`, etc.)
- **MCP Server (`mcp_server.py`)**: Provides programmatic control for AI agents
- **Config Validation (`config_models.py`)**: Ensures `buttons.yaml` structure
and constraints

## Code Style & Standards

### Python Style (Ruff Configuration)

- Line length: 88 characters
- Use type hints (Python 3.12+ syntax: `str | None` not `Optional[str]`)
- Import organization: Ruff handles automatically
- Modern Python: Use f-strings, dataclasses, context managers

### Code Examples

#### ✅ Good CLI Command Implementation

```python
@cli.command()
@click.argument("button_id", type=int)
def show(button_id: int) -> None:
    """Show specific button configuration."""
    if not 1 <= button_id <= 15:
        console.print(f"[red]Error: button_id must be 1–15, got {button_id}[/red]")
        sys.exit(1)
    
    buttons = read_config()
    if button_id not in buttons:
        console.print(f"[yellow]Button {button_id} not configured[/yellow]")
        return
    
    # Display button info...
```

#### ✅ Good Configuration Validation

```python
class ButtonConfig(BaseModel):
    """Configuration for a single button."""
    label: str = Field(..., description="Display label for the button")
    command: Optional[str] = Field(None, description="Shell command to execute")
    script: Optional[str] = Field(None, description="Legacy script field")
    icon: Optional[Path] = Field(None, description="Optional path to icon file")

    @model_validator(mode='before')
    @classmethod
    def resolve_command_and_validate(cls, values):
        """Resolve command from either command or script field."""
        if isinstance(values, dict):
            command = values.get('command')
            script = values.get('script')
            
            if command is None and script is not None:
                values['command'] = script
            
            if values.get('command') is None:
                raise ValueError("Either 'command' or 'script' field is required")
                
        return values
```

#### ❌ Bad Practices to Avoid

```python
# Don't: Ignore type hints
def show(button_id):
    pass

# Don't: Use bare except
try:
    config = load_config()
except:
    print("Error")

# Don't: Ignore error handling
subprocess.run(command)  # Should check return code
```

## Testing Strategy

### Current State

- No test framework implemented yet (planned: pytest)
- Manual testing via CLI commands
- Configuration validation via Pydantic

### Test Commands (When Implemented)

```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=.

# Run specific test file
uv run pytest tests/test_cli.py
```

## MCP Integration

### Available Tools for AI Agents

- `list_buttons()` - Show all configured buttons
- `set_button(button_id, label, command, type="shell", icon=None)` - Configure button
- `remove_button(button_id)` - Delete button
- `daemon_status()` - Check daemon status
- `daemon_start()` / `daemon_stop()` - Control daemon
- `set_button_image_from_url(button_id, url)` - Set image from URL
- `set_button_image_from_prompt(button_id, prompt)` - Generate with AI
- `clear_button_image(button_id)` - Remove image

### Example MCP Usage

```python
# Configure a new button
set_button(
    button_id=1,
    label="Terminal",
    command="xterm",
    type="shell"
)

# Set an AI-generated icon
set_button_image_from_prompt(
    button_id=1,
    prompt="Terminal command line icon, minimalist, black and white"
)

# Start daemon if needed
if not daemon_status()["running"]:
    daemon_start()
```

## Development Workflow

### Git Workflow

- **main**: Primary branch (for releases)
- **master**: Development branch (current)
- Always align branches before release: `git checkout main && git merge master`

### Before Committing

1. Run linting: `uv run ruff check . --fix`
2. Run formatting: `uv run ruff format .`
3. Validate config: `uv run python3 cli.py config validate`
4. Test CLI: `uv run python3 cli.py --help`

### Release Process

1. Update version in `pyproject.toml`
2. Update CHANGELOG.md and CHANGELOG-INTERNAL.md
3. Tag release: `git tag v0.1.0`
4. Push to main branch

## Boundaries

### ✅ Always Do

- Run `uv run ruff check . --fix` before commits
- Use type hints and follow Python 3.12+ conventions
- Validate configuration changes with `config validate`
- Update CHANGELOG.md for user-facing changes
- Test CLI commands before submitting

### ⚠️ Ask First

- Modifying `vendor/` directory (third-party SDK)
- Breaking changes to CLI command structure
- Adding new dependencies to `pyproject.toml`
- Changes to MCP server protocol

### 🚫 Never Do

- Commit secrets or API keys
- Modify `.venv/` directory
- Hardcode absolute paths (use `PROJECT_DIR` constant)
- Ignore error handling in subprocess calls
- Modify `CHANGELOG-INTERNAL.md` without understanding its purpose

## Device-Specific Considerations

### AJAZZ AK820 Device

- 15 programmable buttons (IDs: 1-15)
- 96×96 pixel display per button
- USB HID interface with vendor-specific protocol
- Supports hotplug and auto-reconnection

### Platform Support

- **Linux Native**: Full udev integration for autostart
- **WSL**: Requires usbipd for device access
- **Clipboard**: Platform-specific implementations

## Common Agent Tasks

### Adding New Button Configuration

1. Validate button ID is 1-15
2. Use `set_button()` MCP tool or edit `buttons.yaml`
3. Run `config validate` to check syntax
4. Test with `daemon restart` if running

### Debugging Device Issues

1. Check device status: `ajazz device status`
2. Review logs: `tail -f deck.log`
3. Verify daemon: `ajazz daemon status`
4. Test with simple button first

### Adding New CLI Commands

1. Follow existing Click patterns in `cli.py`
2. Use Rich for output formatting
3. Add help text and examples
4. Test with `--help` flag

This AGENTS.md file helps AI agents understand the project structure, coding standards,
and workflows specific to the AJAZZ Deck macro pad controller project.
