# Per-LED lighting

## Using it

The G9 takes lighting commands on its vendor HID interface (usage page `0xFF7A`), as output reports
without a report ID:

```
05 0C 0C 01 <strip> <H> <S> <B> <effect> <speed> <brightness> <sum>
```

`H` is the hue scaled to a byte, `S` and `B` are 0–100, `effect` 1 solid, 2 breathing, 4 rainbow,
`0xFF` off, `sum` the byte sum of the payload. Strips are `1` (left grip) and `2` (right grip).

With the patch, a **solid** command on strip **0** whose **speed** byte is `0xE0 + channel` sets one LED:

```
05 0C 0C 01 00 <H> <S> <B> 01 <0xE0 + channel> FF <sum>
```

- `H`/`S` as usual, `B` is the brightness of that LED alone.
- `B = 0` is ignored by the firmware (the LED keeps its color): send `B = 1` for a dark LED. From 0.75
  `B = 1` turns the LED off; earlier versions show a faint white.
- Channels, top-down: left grip `7 8 9 10 11`, right grip `4 3 2 1 0`. `5` and `6` are the two
  halves of the Legion button: from the 0.80 test build (now zip 0.50) they follow channel `3` (4th
  from the bottom of the right grip, next to the button). Up to 0.75 the button was off while per-LED
  was active.
- One command per LED. The controller handles about 100 commands a second without dropping off USB.
- Any normal command (speed `0x80`, an effect, off) on strip 0 or 1 leaves per-LED mode.

`tools/tablet/perledtest.py` (`static`, `wave SECONDS`, `stock`) and `tools/tablet/px.py` show it from a
Linux host; they need write access to the G9 hidraw node.

## How the patch works

Addresses are in the decrypted image (`file offset = address - 0x1dfc000`).

- **Color command** (`0x1e21b90`, strip-0 color branch, right after the HSB→RGB conversion): if the
  packet speed is `0xE0`–`0xEB`, the converted color and the LED brightness (`B * 5 / 2`) go into spare
  bytes of that channel's state (`+5..+7` color, `+9` brightness, channel state at
  `0x7128 + ch * 0x1c`; channel 3 also goes into channels 5 and 6), then the handler jumps to the
  reply (`0x1e21bc4`). This skips the stock code
  that repaints the whole strip after every command (`0x1e1cbec`, the per-channel brightness refresh
  and `0x1e1f4ee`), which otherwise shows as flicker.
- **Render task, steady path** (`0x1e23b62`): in static mode with a per-LED speed stored, every tick
  clears each channel's animation mode and redraws it from its spare bytes (`FUN_01e1a946`), instead
  of painting the strip color.
- **Render task, dirty path** (`0x1e2374e`, code in the free bytes at `0x1e000f8`): skips the whole-strip
  repaint blocks in per-LED mode.
- The left static repaint block (`0x1e23804`, redundant with the steady path) holds the new code.

Everything else is stock: USB, input, update and the normal lighting modes. The patch changes 231 bytes,
all in odd 16 KiB segments of the image.
