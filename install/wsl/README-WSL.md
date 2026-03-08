# WSL Setup — AJAZZ AKP153

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

Create a Windows Task Scheduler entry to auto-attach device on login:

1. Open **Task Scheduler** (taskschd.msc)
2. Create **Basic Task** → Name: "Attach AJAZZ AKP153 to WSL"
3. Trigger: **When I log on** (any user)
4. Action: **Start a program**
   - Program: `powershell.exe`
   - Arguments: `-ExecutionPolicy Bypass -File "C:\path\to\ajazz-deck\install\wsl\attach.ps1"`
5. Conditions: Uncheck "Start the task only if the computer is on AC power"
6. Settings: Check "Allow task to be run on demand"

**Alternative:** Run `attach.ps1` manually from PowerShell when needed.

## Troubleshooting

### Device not found
```powershell
# List available devices
usbipd list

# Check if AKP153 is listed:
# BUSID  DEVICE                        STATE
# 1-2    AJAZZ AKP153 (0300:3010)       Shared
```

### Attachment fails
```powershell
# Ensure device is not attached elsewhere
usbipd detach --hardware-id 0300:3010

# Try attaching again
usbipd attach --wsl --hardware-id 0300:3010
```

### WSL can't see device
```bash
# Check device visibility in WSL
lsusb | grep 0300:3010

# Should show: Bus XXX Device XXX: ID 0300:3010 HOTSPOTEKUSB HID DEMO
```
