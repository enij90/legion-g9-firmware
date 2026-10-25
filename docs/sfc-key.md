# The SFC key of the G9 image

`ota.bin` (256 KiB) holds a loader zone (below `0x4000`) and the application zone, which the flash
controller decrypts on the fly. The application zone is encrypted in 32-byte blocks: each block is
XORed with a 16-bit LFSR stream (polynomial `0x1021`) seeded with `0x2496 ^ index`.

The index is **not** simply `offset >> 2` everywhere:

| file offset | index |
|---|---|
| `0x4000`–`0x7FFF`, `0xC000`–`0xFFFF`, `0x14000`–`0x17FFF`, … (odd 16 KiB segments) | `offset >> 2` |
| `0x8000`–`0xBFFF`, `0x10000`–`0x13FFF`, … (even 16 KiB segments from `0x8000`) | `(offset >> 2) - 0x2000` |

With the plain `offset >> 2` rule half the image decrypts to noise, which looks like compressed data
or "bad instruction data" in a disassembler. I found the shifted rule by brute force: for each
candidate key, count the bytes that mark pi32v2 code (`0xEA` as the second byte of a call/goto, `0xFF`
as the second byte of a 32-bit immediate load). On known code the real key wins about 26 to 10; on the
"unreadable" segments the shifted key wins 24 to 3. Over the whole image the marker count goes from
5283 to 10454.

The flash holds `ota.bin` byte for byte (checked on a full flash dump at `0x1000`): nothing is
decompressed when flashing, the difference is only the key.

`tools/g9fw.py` implements the rule (`key_index`), both to decrypt and to re-encrypt patched blocks.
