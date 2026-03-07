# WSL Setup — AJAZZ AK820

WSL does not support udev. Use usbipd to attach the device.

## One-time setup

```powershell
# Install usbipd-win on Windows (run as Admin in PowerShell):
winget install --interactive --exact dorssel.usbipd-win

# Share the device (run once as Admin):
usbipd bind --hardware-id 0300:3010
```

## Daily usage

```bash
# From PowerShell (or automate with Task Scheduler):
usbipd attach --wsl --hardware-id 0300:3010

# Then start the daemon from WSL:
python3 cli.py daemon start
```

## Automate with Task Scheduler (optional)
See attach.ps1 — run it on Windows login to auto-attach.
