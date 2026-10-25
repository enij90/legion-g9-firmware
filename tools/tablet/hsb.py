#!/usr/bin/env python3
# hsb.py STRIP H S B SPEED_HEX : one solid 05 0C command with explicit H/S/B (bright 0xFF).
import os, sys
strip, h, s, b, speed = int(sys.argv[1]), int(sys.argv[2]), int(sys.argv[3]), int(sys.argv[4]), int(sys.argv[5], 16)
def find():
    for k in sorted(os.listdir("/sys/class/hidraw")):
        d = f"/sys/class/hidraw/{k}/device"
        try:
            if open(d + "/report_descriptor", "rb").read(3) == b"\x06\x7a\xff" and "3537" in open(d + "/uevent").read().upper():
                return "/dev/" + k
        except OSError:
            pass
fd = os.open(find(), os.O_WRONLY | os.O_APPEND)
p = [5, 12, 12, 1, strip, h, s, b, 1, speed, 0xFF]
os.write(fd, bytes([0, *p, sum(p) & 0xFF])); os.close(fd)
print("sent", p[4:10])
