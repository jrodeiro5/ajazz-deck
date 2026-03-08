# Contributing to ajazz-deck

Thank you for your interest in contributing! This document explains how to get started.

## Development Setup

### Clone & Install

```bash
git clone https://github.com/jrodeiro5/ajazz-deck.git
cd ajazz-deck
uv sync
```

### Activate Virtual Environment

```bash
# uv handles this automatically with `uv run`, but you can also:
source .venv/bin/activate  # Linux/macOS
# or .venv\Scripts\activate  (Windows)
```

## Before Submitting a PR

### 1. Format & Lint

```bash
# Auto-fix formatting
uv run ruff format .

# Auto-fix common issues
uv run ruff check . --fix

# Verify all checks pass
uv run ruff check .
uv run ruff format --check .
```

### 2. Test Your Changes

```bash
# Test CLI commands
uv run ajazz button list
uv run ajazz config validate

# Test imports
uv run python3 -c "from image_engine import process_image; print('OK')"
uv run python3 -c "from mcp_server import mcp; print('OK')"

# Test Pydantic models
uv run python3 -c "from config_models import ButtonConfig, AjazzConfig; print('OK')"
```

### 3. Hardware Testing

Most contributions can be tested without an AJAZZ AK820:
- CLI command changes ✓ (no hardware needed)
- Config validation ✓ (no hardware needed)
- Image processing ✓ (no hardware needed)
- Daemon/HID changes ✗ (requires hardware)

If you can't test on hardware, mention it in your PR description. Maintainers can help.

## Code Style

- **Python version**: 3.12+
- **Formatter**: `ruff format` (enforced)
- **Linter**: `ruff check` with rules E, W, F, I, N, UP, B, C4, TCH (enforced)
- **Type hints**: Encouraged but not required
- **Docstrings**: Use for public APIs and complex functions

## Commit Messages

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```
type(scope): short description

Longer explanation if needed.

Closes #123
```

Types: `feat`, `fix`, `docs`, `style`, `refactor`, `perf`, `test`, `chore`

Examples:
```
feat(image): support Gemini image generation
fix(deck): validate button config on startup
docs: add security policy
```

## PR Guidelines

1. **Scope**: Keep PRs focused on a single feature/fix
2. **Description**: Explain *why*, not just *what*
3. **Tests**: Include tests or explain why not possible
4. **Docs**: Update README if adding features
5. **Changelog**: Your PR title becomes the changelog entry

## Project Structure

```
ajazz-deck/
├── deck.py              # Daemon (listens for button presses)
├── cli.py               # CLI interface (user-facing commands)
├── mcp_server.py        # MCP integration (Claude Code/Windsurf)
├── image_engine.py      # Image processing (URLs, AI generation)
├── config_models.py     # Pydantic validation models
├── buttons.yaml         # User's button config (gitignored)
├── buttons.example.yaml # Example config template
├── .github/workflows/   # GitHub Actions CI
└── vendor/              # Vendored StreamDock SDK
```

## Common Tasks

### Add a New CLI Command

```python
# In cli.py, add to appropriate group:

@button.command()
@click.argument("button_id", type=int)
def my_command(button_id):
    """Description for help text."""
    # implementation
```

### Add a New MCP Tool

```python
# In mcp_server.py:

@mcp.tool()
def my_tool(param: str) -> dict:
    """Description and args."""
    try:
        result = do_something(param)
        return {"status": "success", "result": result}
    except Exception as e:
        return {"error": str(e)}
```

### Update Pydantic Models

```python
# In config_models.py, update ButtonConfig or AjazzConfig:

class ButtonConfig(BaseModel):
    # New field with description
    new_field: str | None = Field(None, description="What this does")

    # Add validators if needed
    @field_validator("new_field")
    @classmethod
    def validate_new_field(cls, v):
        # validation logic
        return v
```

## Testing Without Hardware

All non-daemon code can be tested without an AK820:

```bash
# Test image processing
uv run python3 -c "
from image_engine import process_image
path = process_image('icons/project_context_btn.png', 1)
print(f'✓ Image saved to {path}')
"

# Test config validation
uv run python3 cli.py config validate

# Test Pydantic models
uv run python3 -c "
from config_models import AjazzConfig
import yaml
cfg = AjazzConfig(**yaml.safe_load(open('buttons.example.yaml')))
print(f'✓ Config valid: {len(cfg.buttons)} buttons')
"
```

## Getting Help

- **Documentation**: Read [README.md](README.md) and [CLAUDE.md](CLAUDE.md)
- **Issues**: Check existing issues or [create one](https://github.com/jrodeiro5/ajazz-deck/issues)
- **Discussions**: Ask questions in GitHub Discussions

## Vendored Dependencies

### Why Vendor?

The `vendor/` directory contains the **StreamDock Python SDK**, which is not published on PyPI and has no versioned releases. Vendoring ensures reproducible builds and offline operation.

### Vendor Policy

- **Never modify vendored code directly**. If you need to extend or patch it, create a wrapper layer in project code (e.g., `deck.py`), not in the vendor directory.
- Vendored code is **pinned to a specific commit** — updates are explicit and tracked in git history.
- All vendored packages include license files. **MIT compliance is required.**

### Updating a Vendor

1. Clone the upstream repository to a temporary directory
2. Note the commit SHA
3. Replace the vendor directory with fresh files
4. Update the commit SHA in `vendor/VENDOR.md` and `vendor/README.md`
5. Test on all supported platforms (Linux, Windows/WSL)
6. Commit with message: `chore(vendor): update <package> to <new-commit-sha>`

For detailed instructions, see `vendor/VENDOR.md`.

## License

By contributing, you agree that your contributions will be licensed under the same license as the project (see LICENSE).

Happy coding! 🚀
