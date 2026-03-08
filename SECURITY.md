# Security Policy

## Reporting a Vulnerability

**Please do NOT open a public issue for security vulnerabilities.**

Instead, please report security issues using GitHub's private security advisory feature:
1. Go to **Security** tab → **Advisories** → **Report a vulnerability**
2. Fill in the details and submit

Alternatively, you can reach out directly to the maintainers.

## Security Best Practices for Users

### Protect Your API Keys

Never commit sensitive files to git:

```bash
# ✓ CORRECT — API keys in .env (not tracked)
echo "GOOGLE_API_KEY=your-key-here" >> .env

# ✗ WRONG — Never add to buttons.yaml
buttons:
  1:
    api_key: "sk-abc123"  # DO NOT DO THIS
```

**Protected by `.gitignore`:**
- `.env` — Environment variables with API keys
- `.mcp.json` — MCP configuration with local paths
- `mcp.json` — MCP server registry
- `buttons.yaml` — User's personal button config
- `deck.log` — Log files (may contain paths/info)

### Safe Command Execution

All button commands are executed safely:

```python
# ✓ Safe: shlex.split() prevents injection
execute_command("echo hello", use_shell=False)

# ✓ Safe: Pydantic validation on config load
from config_models import ButtonConfig
ButtonConfig(**user_config)
```

### Device Security

- Access is limited to device VID:PID `0300:3010` (AJAZZ AK820 only)
- No network communication with external services (except image downloads and Gemini API)
- All button commands run with user's own privileges (no privilege escalation)

## Vulnerability Disclosure Timeline

If you report a vulnerability:
1. **Day 0**: Initial report acknowledged
2. **Day 3**: Analysis and scope confirmation
3. **Day 7**: Fix release (if applicable)
4. **Day 14**: Public disclosure in security advisory

## Dependencies

This project uses the following security-relevant dependencies:

- **pydantic** — Configuration validation (protects against injection)
- **click** — CLI framework (input handling)
- **httpx** — HTTP client (for image downloads)
- **google-genai** — Gemini API client (uses official Google SDK)

All dependencies are pinned in `uv.lock` for reproducible installs.

## Pre-commit Security

Check before committing:

```bash
# Verify no secrets in diff
git diff | grep -iE "(GOOGLE_API_KEY|token|secret|password)" && echo "⚠️ STOP — Found potential secret!"

# Run security linters
uv run ruff check .
```

## Responsible Disclosure

We take security seriously. Thank you for helping keep ajazz-deck safe!
