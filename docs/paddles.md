# Independent back paddles and M button

## What it does

With the stock firmware, the four back paddles can only copy another button (you map them in the
Legion app, or with M + paddle + button), and the M button is not reported at all. The patch makes the
four paddles and M buttons of their own:

| button | report bit | HID button | Linux key code | Steam Deck (InputPlumber) |
|---|---|---|---|---|
| left top paddle | byte 6, bit 5 | 6 | `BTN_Z` | L4 |
| right top paddle | byte 6, bit 2 | 3 | `BTN_C` | R4 |
| left bottom paddle | byte 5, bit 4 | 17 | `BTN_TRIGGER_HAPPY1` | L5 |
| right bottom paddle | byte 5, bit 5 | 18 | `BTN_TRIGGER_HAPPY2` | R5 |
| M | byte 5, bit 6 | 19 | `BTN_TRIGGER_HAPPY3` | Quick Access menu (…) |

Leave the paddles **unmapped** in the Legion app: a mapped paddle also sends the button it is mapped
to. M still works for the controller's own remapping (M + paddle + button), but while you do that the
system sees M pressed too.

**M does not register every press yet.** It is also the controller's own key for remapping (and maybe
for other combinations), and the firmware still handles that, so now and then a press of M does not
open the Quick Access menu. Press it again.

This is for the controller's HID mode (report ID 1, 10 bytes), the one it uses with Linux and PCs.

## Report descriptor

Only two bits of the 16 HID buttons were free (buttons 3 and 6). The 4 bits after the hat were
constant padding; the patch rewrites that part of the report descriptor so they become HID buttons
17–20, with the same descriptor length (22 bytes replaced by 22 bytes) and the same report size:

```
was: 75 04 95 01 81 01                     4-bit padding
     05 09 19 01 29 10 15 00 25 01 75 01 95 10 81 02    buttons 1-16
now: 05 09 19 11 29 14 25 01 75 01 95 04 81 02          buttons 17-20
     19 01 29 10 95 10 81 02                            buttons 1-16
```

The logical minimum 0 is still set by the hat item before. On Linux, buttons above 16 of a gamepad
become `BTN_TRIGGER_HAPPY1` and up, so no udev rule is needed. Firmware updates go through the vendor
interface (the second HID interface), which the patch does not touch.

## Linux side

`BTN_C` and `BTN_Z` were already mapped to `RightPaddle1` and `LeftPaddle1` by the InputPlumber
capability map of the G9, so L4 and R4 work on the current Armada image. L5, R5 and M need three map
entries, which come with the next update of my Armada port (OTA).

### Until the next Armada update

On the tablet, as root:

```sh
cp /usr/share/inputplumber/capability_maps/lenovo_legion_g9.yaml \
   /etc/inputplumber/capability_maps.d/zz-lenovo_legion_g9.yaml
```

Then add these entries under `mapping:` in `/etc/inputplumber/capability_maps.d/zz-lenovo_legion_g9.yaml`
(same `id`, loaded after the stock file, so it replaces it) and unplug and replug the G9:

```yaml
  - name: Left Paddle 2
    source_events:
      - evdev:
          event_type: KEY
          event_code: BTN_TRIGGER_HAPPY1
          value_type: button
    target_event:
      gamepad:
        button: LeftPaddle2
  - name: Right Paddle 2
    source_events:
      - evdev:
          event_type: KEY
          event_code: BTN_TRIGGER_HAPPY2
          value_type: button
    target_event:
      gamepad:
        button: RightPaddle2
  - name: M button
    source_events:
      - evdev:
          event_type: KEY
          event_code: BTN_TRIGGER_HAPPY3
          value_type: button
    target_event:
      gamepad:
        button: QuickAccess
```

Remove the file once the update is installed.

### Other distributions with InputPlumber

The firmware side is the same on any system; what turns the new buttons into L4, R4, L5, R5 and the
Quick Access button is the G9 profile for InputPlumber, which ships with my Armada port. On another
distribution that uses InputPlumber, take the two files from Armada and adapt the device profile:

- copy [`05-lenovo-legion-g9.yaml`](https://github.com/enij90/armada-tb321fu/blob/main/system_files/usr/share/inputplumber/devices/05-lenovo-legion-g9.yaml)
  to `/etc/inputplumber/devices.d/` and
  [`lenovo_legion_g9.yaml`](https://github.com/enij90/armada-tb321fu/blob/main/system_files/usr/share/inputplumber/capability_maps/lenovo_legion_g9.yaml)
  to `/etc/inputplumber/capability_maps.d/`;
- in the device profile, change the devicetree `model` under `matches` to yours
  (`cat /sys/firmware/devicetree/base/model`), remove the `TB321FU IMU` source (Armada's IMU bridge),
  and fix or remove the two `aw86937-haptics` sources if your kernel names the vibration motors
  differently;
- add the three map entries shown above.

I have not tested this outside Armada.

## How it works

Addresses are in the decrypted image (`file offset = address - 0x1dfc000`).

- The button scan writes a 32-bit raw button word at RAM `0x6430`; the paddles are bits 23 (left
  top), 24 (right top), 25 (left bottom) and 26 (right bottom), M is bit 30.
- `FUN_01e1d292` copies it, runs the button mapper `FUN_01e1bb9a` and then the report builder
  `FUN_01e1d064`. The mapper drops unmapped paddles and M, and the HID report (mode 7, `0x1e1d148`)
  takes only the low 16 bits of the mapped word (`0x1e1d158 r0 = [r4+0]`, `0x1e1d15a h[sp+6] = r0`)
  and the hat, stored in byte 5 at `0x1e1d21a` (`b[sp+5] = r0`, the only store of that byte).
- The patch replaces both stores with jumps to new code that reads the raw word again: bits 23 and 24
  go into bits 5 and 2 of the button word, bits 25, 26 and 30 into bits 4, 5 and 6 of the hat byte.
  Then it does the original store and jumps back. The hat value (low 4 bits) is untouched.
- The new code lives in the right strip's static repaint block of the lighting task (`0x1e23960`),
  which is redundant with the steady repaint that runs in the same tick; its first instruction now
  skips to the end of the block. The per-LED patch uses the left one the same way, so both patches can
  be built together.
- The report descriptor is at `0x1e32423`; the patched part starts at `0x1e32458`.

I found the bits with two diagnostic builds that put bits 16–31 of the mapped word and of the raw word
into the report, read on the tablet while pressing each paddle.
