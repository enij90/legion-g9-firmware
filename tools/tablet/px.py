#!/usr/bin/env python3
# px.py "CH:H:S:B ..." : set LEDs one by one on the patched firmware (strip 0, speed 0xE0 + channel).
# Channels: left grip 7-11, right grip 4-0, top-down. H 0-255, S and B 0-100. Unlisted strip channels are
# sent nearly off (B=1: the firmware ignores B=0 and keeps the old color), the listed ones last.
# Example: px.py "9:85:100:100 2:85:100:100"  -> one green LED in the middle of each grip.
import os, sys, time
want = {int(c): (int(h), int(s), int(b)) for c, h, s, b in (x.split(":") for x in sys.argv[1].split())}
def find():
    for k in sorted(os.listdir("/sys/class/hidraw")):
        d = f"/sys/class/hidraw/{k}/device"
        try:
            if open(d + "/report_descriptor", "rb").read(3) == b"\x06\x7a\xff" and "3537" in open(d + "/uevent").read().upper():
                return "/dev/" + k
        except OSError:
            pass
fd = os.open(find(), os.O_WRONLY | os.O_APPEND)
strip = (0, 1, 2, 3, 4, 7, 8, 9, 10, 11)
order = [c for c in strip if c not in want] + [c for c in strip if c in want]
for ch in order:
    h, s, b = want.get(ch, (0, 0, 1))
    p = [5, 12, 12, 1, 0, h, s, max(1, b), 1, 0xE0 + ch, 0xFF]
    os.write(fd, bytes([0, *p, sum(p) & 0xFF])); time.sleep(0.02)
os.close(fd); print("ok")
