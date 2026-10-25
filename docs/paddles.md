# Independent back paddles

## What it does

With the stock firmware, the four back paddles can only copy another button (you map them in the
Legion app, or with M + paddle + button). The patch makes three of them buttons of their own:

| paddle | report bit | HID button | Linux key code | Steam Deck (InputPlumber) |
|---|---|---|---|---|
| left top | 5 | 6 | `BTN_Z` | L4 |
| right top | 2 | 3 | `BTN_C` | R4 |
| left bottom | 15 | 16 | `0x13f` (no name) → `BTN_TRIGGER_HAPPY1` with the udev rule below | L5 |
| right bottom | — | — | — | map it in the Legion app |

Leave the three paddles **unmapped** in the Legion app: a mapped paddle also sends the button it is
mapped to. Only three bits of the 16-button HID report are free, so the fourth paddle keeps the stock
behaviour; giving it a bit of its own would mean changing the USB report descriptor, which I avoid.

This is for the controller's HID mode (report ID 1, 10 bytes), the one it uses with Linux and PCs.

## Linux side

HID button 16 becomes key code `0x13f`, which has no name, so InputPlumber cannot map it. A udev hwdb
rule gives it one:

```
evdev:input:b0003v3537p1134*
 KEYBOARD_KEY_90010=btn_trigger_happy1
```

and the InputPlumber capability map of the G9 maps `BTN_TRIGGER_HAPPY1` to `LeftPaddle2`. `BTN_C` and
`BTN_Z` were already mapped to `RightPaddle1` and `LeftPaddle1`. In my Armada port both are part of
the image.

## How it works

Addresses are in the decrypted image (`file offset = address - 0x1dfc000`).

- The button scan writes a 32-bit raw button word at RAM `0x6430`; the paddles are bits 23 (left
  top), 24 (right top), 25 (left bottom) and 26 (right bottom), M is bit 30.
- `FUN_01e1d292` copies it, runs the button mapper `FUN_01e1bb9a` and then the report builder
  `FUN_01e1d064`. The mapper drops unmapped paddles, and the HID report (mode 7, `0x1e1d148`) takes
  only the low 16 bits of the mapped word (`0x1e1d158 r0 = [r4+0]`, `0x1e1d15a h[sp+6] = r0`).
- The patch replaces that store with a jump to new code that reads the raw word again and inserts
  bits 23, 24 and 25 into bits 5, 2 and 15 of the mapped word, then stores it and jumps back. The hat
  (bits 20–23 of the mapped word) is untouched.
- The new code lives in the right strip's static repaint block of the lighting task (`0x1e23960`),
  which is redundant with the steady repaint that runs in the same tick; its first instruction now
  skips to the end of the block. The per-LED patch uses the left one the same way, so both patches can
  be built together.

I found the bits with two diagnostic builds that put bits 16–31 of the mapped word and of the raw word
into the report, read on the tablet while pressing each paddle.
