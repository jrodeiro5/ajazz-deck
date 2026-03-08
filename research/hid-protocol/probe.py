"""AKP153E raw HID probe — standalone research script.

Tests direct HID communication with the AJAZZ AKP153E macro pad,
bypassing the vendor StreamDock SDK entirely.

Usage:
    uv run python3 research/hid-protocol/probe.py

Dependencies: hid, Pillow (both in pyproject.toml)
Device path: /dev/hidraw1 (change DEVICE_PATH if needed)

Status legend used throughout this file:
    # WORKS    — confirmed working on hardware
    # BROKEN   — sends without error but has no visible effect
    # UNKNOWN  — untested or ambiguous result
"""

import io
import time
import threading

import hid
from PIL import Image

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

DEVICE_PATH = b"/dev/hidraw1"
PACKET_SIZE = 512
IMAGE_SIZE = (85, 85)   # AKP153E native key image dimensions

# Logical button (1-15) → hardware key index mapping.
# Derived from SDK reverse-engineering. Used for key events;
# may differ for image commands — see send_image_attempt() notes.
KEY_MAP = {
    1: 13, 2: 10, 3: 7,  4: 4,  5: 1,
    6: 14, 7: 11, 8: 8,  9: 5,  10: 2,
    11: 15, 12: 12, 13: 9, 14: 6, 15: 3,
}


# ---------------------------------------------------------------------------
# Low-level send
# ---------------------------------------------------------------------------

def _send(device: hid.Device, data: list[int], lock: threading.Lock) -> None:
    """Send one 512-byte HID packet, zero-padded, with report ID 0x00.

    # WORKS — confirmed packet format for all commands.
    """
    packet = data + [0] * (PACKET_SIZE - len(data))
    packet = packet[:PACKET_SIZE]
    with lock:
        device.write(bytes([0x00] + packet))


# ---------------------------------------------------------------------------
# Wake — WORKS
# ---------------------------------------------------------------------------

def wake(device: hid.Device, lock: threading.Lock, brightness: int = 100) -> None:
    """Set brightness and clear all button images.

    Turns the screen on. Without periodic heartbeat calls the device
    goes dark after ~2 seconds.

    # WORKS — screen lights up immediately.
    """
    # Brightness packet: CRT..LIG..PCT
    _send(device, [0x43, 0x52, 0x54, 0x00, 0x00, 0x4C, 0x49, 0x47, 0x00, 0x00, brightness], lock)
    # Clear all (black): CRT..CLE..0x00 0xFF
    _send(device, [0x43, 0x52, 0x54, 0x00, 0x00, 0x43, 0x4C, 0x45, 0x00, 0x00, 0x00, 0xFF], lock)


def _heartbeat_worker(
    device: hid.Device,
    lock: threading.Lock,
    stop_event: threading.Event,
    brightness: int = 100,
) -> None:
    """Send brightness packet every 1s to prevent device sleep.

    # WORKS — keeps screen on indefinitely.
    """
    while not stop_event.wait(1.0):
        try:
            _send(
                device,
                [0x43, 0x52, 0x54, 0x00, 0x00, 0x4C, 0x49, 0x47, 0x00, 0x00, brightness],
                lock,
            )
        except Exception:
            pass  # device may be closing


# ---------------------------------------------------------------------------
# Image attempt — BROKEN (ACK received but image does not appear)
# ---------------------------------------------------------------------------

def send_image_attempt(device: hid.Device, lock: threading.Lock, hw_key: int = 1) -> dict:
    """Best current attempt at sending a solid red image to a button.

    Protocol sequence (from gist ZCube/430fab6039899eaa0e18367f60d36b3c):
      1. Header packet with JPEG size (big-endian) and hardware key index
      2. Raw JPEG data in 512-byte chunks
      3. Stop/flush packet

    # BROKEN — device sends ACK but image never appears on display.
    # Root cause unknown. See README.md for open hypotheses.

    Args:
        device:  Open HID device handle.
        lock:    Shared send lock (also held by heartbeat thread).
        hw_key:  Hardware key index to target. Default 1 (= logical button 5
                 per KEY_MAP, but the correct mapping for image commands is
                 unconfirmed).

    Returns:
        dict with keys:
            jpeg_size  (int)   — encoded JPEG byte count
            ack        (bool)  — whether device replied with ACK
            raw_reply  (bytes) — first reply packet, or empty bytes
    """
    # Build solid red 85x85 JPEG image
    img = Image.new("RGB", IMAGE_SIZE, color=(255, 0, 0))
    img = img.rotate(90, expand=False)  # SDK rotates 90°; reason unknown
    jpeg_buf = io.BytesIO()
    img.save(jpeg_buf, format="JPEG", quality=95)
    jpeg_bytes = jpeg_buf.getvalue()

    size = len(jpeg_bytes)
    size_hi = (size >> 8) & 0xFF
    size_lo = size & 0xFF

    # Step 1: header — command 0x42 0x41 0x54 ("BAT"?), size, hw_key
    header = [
        0x43, 0x52, 0x54, 0x00, 0x00,
        0x42, 0x41, 0x54,             # command bytes — may be wrong
        0x00, 0x00,
        size_hi, size_lo,
        hw_key,
        0x00, 0x00, 0x00,
    ]
    _send(device, header, lock)

    # Step 2: JPEG data in 512-byte chunks
    for i in range(0, len(jpeg_bytes), PACKET_SIZE):
        chunk = list(jpeg_bytes[i : i + PACKET_SIZE])
        _send(device, chunk, lock)

    # Step 3: stop/flush — command 0x53 0x54 0x50 ("STP")
    _send(device, [0x43, 0x52, 0x54, 0x00, 0x00, 0x53, 0x54, 0x50], lock)

    # Read reply (non-blocking poll)
    raw = device.read(PACKET_SIZE, timeout_ms=500)
    if not raw:
        return {"jpeg_size": size, "ack": False, "raw_reply": b""}

    # ACK starts with 0x41 0x43 0x4B ("ACK") 0x00 0x00 0x4F 0x4B ("OK")
    ack = len(raw) >= 3 and raw[0] == 0x41 and raw[1] == 0x43 and raw[2] == 0x4B
    return {"jpeg_size": size, "ack": ack, "raw_reply": bytes(raw)}


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print(f"Opening {DEVICE_PATH.decode()} ...")
    device = hid.Device(path=DEVICE_PATH)
    lock = threading.Lock()
    stop_event = threading.Event()

    hb = threading.Thread(
        target=_heartbeat_worker,
        args=(device, lock, stop_event),
        daemon=True,
    )
    hb.start()

    try:
        # Wake device (WORKS)
        print("Waking device ...")
        wake(device, lock)
        print("  Screen should be on (black).")
        time.sleep(0.5)

        # Keep screen on for 10 seconds while doing work
        print("Holding screen on for 10s via heartbeat ...")
        time.sleep(3)

        # Attempt image send (BROKEN — for research/debugging)
        print("\nAttempting image send to hw_key=1 ...")
        result = send_image_attempt(device, lock, hw_key=1)
        print(f"  JPEG size : {result['jpeg_size']} bytes")
        print(f"  ACK       : {result['ack']}")
        if result["raw_reply"]:
            print(f"  Raw reply : {list(result['raw_reply'][:16])} ...")
        else:
            print("  Raw reply : (none)")
        print("\n  NOTE: Image NOT expected to appear — protocol incomplete.")
        print("  See research/hid-protocol/README.md for open hypotheses.")

        # Finish holding screen on
        time.sleep(6)

    finally:
        stop_event.set()
        hb.join(timeout=2)
        device.close()
        print("\nDone.")
