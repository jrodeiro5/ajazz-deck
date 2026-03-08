# AKP153E Raw HID Protocol — Research Notes

Reverse-engineering progress for direct HID communication with the AJAZZ AKP153E macro pad,
bypassing the vendor StreamDock SDK.

**Firmware tested:** V3.AKP153E.01.002
**Protocol source:** https://gist.github.com/ZCube/430fab6039899eaa0e18367f60d36b3c
**Research environment:** ~/ajazz-test (personal sandbox, not this repo)

---

## Hardware

- **VID/PID:** 0x0300 / 0x3010
- **Device path:** `/dev/hidraw1` (may vary — check `ls /dev/hidraw*`)
- **Packet size:** 512 bytes (all packets, zero-padded)
- **Report ID:** prepend `0x00` before every `hid.write()` call (hidapi requirement)
- **Image size:** 85×85 px (device native), JPEG format

---

## What Works (confirmed with hardware)

### Open device

```python
import hid
device = hid.Device(path=b'/dev/hidraw1')
```

No SDK needed. Direct hidapi access.

### Packet format

All packets are exactly 512 bytes. Pad with zeros, then prepend `0x00` (report ID):

```python
packet = data + [0] * (512 - len(data))
device.write(bytes([0x00] + packet))
```

### Set Brightness

Turns the screen on. Send once to wake, then every ~1s as heartbeat.

```
[0x43, 0x52, 0x54, 0x00, 0x00, 0x4C, 0x49, 0x47, 0x00, 0x00, PCT]
```

`PCT` = brightness percentage, 0–100. **Device goes to sleep ~2s without a heartbeat.**

### Clear all (black screen)

```
[0x43, 0x52, 0x54, 0x00, 0x00, 0x43, 0x4C, 0x45, 0x00, 0x00, 0x00, 0xFF, 0x00, 0x00, 0x00, 0x00]
```

### Clear + show AJAZZ logo

```
[0x43, 0x52, 0x54, 0x00, 0x00, 0x43, 0x4C, 0x45, 0x00, 0x00, 0x44, 0x43, 0x00, 0x00, 0x00, 0x00]
```

### ACK response

Device replies after each command. ACK starts with:

```
[0x41, 0x43, 0x4B, 0x00, 0x00, 0x4F, 0x4B, ...]
```

`ACK` = `0x41 0x43 0x4B`, `OK` = `0x4F 0x4B` in ASCII.

### Key events

Button press/release arrives in the read buffer. Hardware key index is at byte 9,
state byte at byte 10 (`0x01` = press, other = release).

### Logical → hardware key mapping

The physical button layout maps to hardware key indices as follows:

```
Logical:  1   2   3   4   5   6   7   8   9  10  11  12  13  14  15
Hardware: 13  10   7   4   1  14  11   8   5   2  15  12   9   6   3
```

(Derived from SDK source reverse-engineering.)

---

## What Is NOT Working

### set_image — image does not appear on display

The protocol sends without error and receives ACK, but **the image never appears**.

**Sequence attempted:**

1. **Header packet** — announces image size and target hardware key:

   ```
   [0x43, 0x52, 0x54, 0x00, 0x00, 0x42, 0x41, 0x54, 0x00, 0x00, SIZE_HI, SIZE_LO, HW_KEY, 0x00, 0x00, 0x00]
   ```

   `SIZE_HI`/`SIZE_LO` = big-endian JPEG byte count.
   `HW_KEY` = hardware key index from the mapping above.

2. **Data chunks** — raw JPEG bytes in 512-byte packets (no framing, just raw data).

3. **Stop/flush packet:**

   ```
   [0x43, 0x52, 0x54, 0x00, 0x00, 0x53, 0x54, 0x50]
   ```

**Image encoding used:**
- Resize to 85×85 px
- Rotate 90° (observed in SDK; reason unknown)
- Convert to RGB
- Encode as JPEG (quality=95 → ~775 bytes → `SIZE_HI=0x03, SIZE_LO=0x07`)

**Tested with:** `hw_key=1` (logical button 5 per the mapping above).

**ACK received:** Yes — the device acknowledges the packets but ignores the image.

**Possible root causes (unresolved):**
- Wrong `HW_KEY` value (mapping may differ for image commands vs. key events)
- Image format issue — wrong dimensions, rotation, or JPEG quality
- Missing framing or sequencing detail not present in the gist
- Command byte `0x42 0x41 0x54` (`BAT`) may not be the correct image command
- Timing issue — header and chunks sent too fast without waiting for ACK between packets

---

## SDK Findings

The vendor StreamDock SDK (`vendor/StreamDock/`) wraps a compiled C library
(`libtransport*.so`). Key observations:

- `transport_wakeup_screen()` **never turns on the screen** on this firmware.
- SDK heartbeat (`_heartbeat_worker`) sends `transport_heartbeat()` every **10 seconds** —
  the device sleeps after ~2s, so this is insufficient.
- The C library likely sends commands tailored for a different firmware version.
- **Conclusion:** Direct HID is more reliable than the SDK for this firmware.

---

## Next Steps / Open Questions

- Try `hw_key=0` or other values — maybe image commands use a different key numbering
- Try JPEG quality=80 or uncompressed BMP to rule out format issues
- Sniff USB traffic with Wireshark + usbmon while the Windows StreamDock app sends an image
- Try waiting for ACK between header and data chunks
- Examine `0x42 0x41 0x54` (`BAT`) more carefully — may be a battery query, not image set
- Cross-reference with similar Elgato/StreamDeck protocol implementations
