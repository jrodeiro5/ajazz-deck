# Vendored Dependencies

## StreamDock Python SDK

| Attribute | Value |
|-----------|-------|
| **Package** | StreamDock Python SDK |
| **Source** | https://github.com/MiraboxSpace/StreamDock-Device-SDK |
| **License** | MIT (see `vendor/LICENSE`) |
| **Vendored at commit** | `9b20bdf` |
| **Original author** | MiraboxSpace |
| **Copied** | Entire `StreamDock/` directory (unmodified from upstream) |

### Why Vendored?

The StreamDock SDK is **not published on PyPI** and has **no versioned releases** on GitHub. It is required for HID device communication with the AJAZZ AKP153 macro pad (VID `0x0300` / PID `0x3010`).

Vendoring ensures:
- ✓ Reproducible builds (no dependency on GitHub API or release availability)
- ✓ Offline operation
- ✓ Stable support for the AKP153 device
- ✓ Clear attribution via `vendor/LICENSE` (MIT compliance)

### Modifications

**None** — all files in `vendor/StreamDock/` are unmodified from upstream. The directory is injected into `sys.path` at daemon startup (see `deck.py:8`).

### How to Update

When updating the SDK to a newer version:

```bash
# Clone upstream into temporary directory
git clone https://github.com/MiraboxSpace/StreamDock-Device-SDK /tmp/sdk

# Note the new commit SHA
cd /tmp/sdk
git rev-parse HEAD
# (save this commit SHA for step 4)

# Back in ajazz-deck repo, replace the vendored directory
cd /path/to/ajazz-deck
rm -rf vendor/StreamDock
cp -r /tmp/sdk/StreamDock vendor/

# Update commit SHA in this file and vendor/README.md
# Then test the daemon
python3 cli.py daemon start
uv run ajazz button list  # Verify it works

# Commit changes
git add vendor/
git commit -m "chore(vendor): update StreamDock SDK to <new-commit-sha>"
```

### Security Considerations

The vendor directory includes **platform-specific precompiled binaries** (`.so` on Linux, `.dll` on Windows) that cannot be audited by dependabot or static analysis tools.

When updating:
1. **Verify the commit on GitHub** — Review the SDK repository commit history
2. **Check for security advisories** — Watch https://github.com/MiraboxSpace/StreamDock-Device-SDK/security
3. **Test on target platforms** — Verify the new binaries work on Linux and Windows (WSL)

### Current Status

- **Vendored commit**: `9b20bdf`
- **Last checked**: 2026-03-08
- **Latest upstream commit**: Check https://github.com/MiraboxSpace/StreamDock-Device-SDK/commits/main

To check if an update is available:

```bash
# View current vendored version
grep "Vendored at commit" vendor/VENDOR.md

# Compare with upstream
git ls-remote https://github.com/MiraboxSpace/StreamDock-Device-SDK HEAD
```

### Related Documentation

- `vendor/README.md` — Quick reference (source URL + commit)
- `vendor/LICENSE` — MIT license text
- `CONTRIBUTING.md` — Vendor policy and contribution guidelines
- `SECURITY.md` — Security notes on precompiled binaries
