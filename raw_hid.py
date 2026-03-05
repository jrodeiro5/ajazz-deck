#!/usr/bin/env python3
"""
AJAZZ AKP153 protocol test.
1. Opens hidraw0 (vendor interface)
2. Sends a Set Brightness command (should trigger ACK OK from device)
3. Reads ALL packets for 10s — including zero-only — to see if anything comes back
4. Then reads for 15s more while user presses buttons
"""
import hid
import time

PATH = b'/dev/hidraw0'

# Set Brightness to 80% — per AKP153 protocol spec
BRIGHTNESS_CMD = bytes([
    0x43, 0x52, 0x54, 0x00, 0x00,
    0x4c, 0x49, 0x47, 0x00, 0x00,
    80,   # percentage
]) + bytes(512 - 12)  # zero-pad to 512 bytes

def main():
    dev = hid.Device(path=PATH)
    dev.nonblocking = False  # blocking read

    print(f"Opened {PATH}")
    print(f"Sending Set Brightness (80%) command ({len(BRIGHTNESS_CMD)} bytes)...")

    # hidapi write() prepends a 0x00 report ID byte — send raw via os.write instead
    import os
    fd = os.open(PATH, os.O_RDWR)
    written = os.write(fd, BRIGHTNESS_CMD)
    print(f"Wrote {written} bytes")

    print("\nReading for 10s — watching for ACK OK from device...\n")
    deadline = time.monotonic() + 10
    while time.monotonic() < deadline:
        try:
            data = dev.read(512)
        except Exception as e:
            print(f"read error: {e}")
            break
        if data:
            hex_prefix = ' '.join(f'{b:02x}' for b in data[:16])
            is_zero = not any(data)
            tag = " [ALL ZEROS]" if is_zero else ""
            print(f"  RECV: {hex_prefix}...{tag}")

    print("\nNow press buttons for 15s...\n")
    deadline = time.monotonic() + 15
    count = 0
    while time.monotonic() < deadline:
        try:
            data = dev.read(512)
        except Exception as e:
            print(f"read error: {e}")
            break
        if data:
            count += 1
            hex_prefix = ' '.join(f'{b:02x}' for b in data[:16])
            is_zero = not any(data)
            tag = " [ALL ZEROS]" if is_zero else f"  <-- byte[9]={hex(data[9])}"
            print(f"  [{count}] {hex_prefix}...{tag}")

    print("\nDone. If nothing printed above, the device isn't sending any USB data.")
    dev.close()
    os.close(fd)

if __name__ == "__main__":
    main()
