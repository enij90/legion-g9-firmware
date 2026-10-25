#!/usr/bin/env python3
# Read-only: GCM 05 0C op 0 for strips 0,1,2 (no writes).
import os, time, select
def find():
    for k in sorted(os.listdir("/sys/class/hidraw")):
        d = f"/sys/class/hidraw/{k}/device"
        try:
            if open(d + "/report_descriptor", "rb").read(3) == b"\x06\x7a\xff" and "3537" in open(d + "/uevent").read().upper():
                return "/dev/" + k
        except OSError:
            pass
fd = os.open(find(), os.O_RDWR)
while select.select([fd], [], [], 0.05)[0]:
    os.read(fd, 64)
for s in (0, 1, 2):
    p = [5, 12, 6, 0, s]; os.write(fd, bytes([0, *p, sum(p) & 0xFF])); t = time.time(); got = "no reply"
    while time.time() - t < 0.5:
        if select.select([fd], [], [], 0.1)[0]:
            r = os.read(fd, 64)
            if r[:2] == b"\x05\x0c": got = r[:r[2] + 1].hex(" "); break
    print("strip", s, got)
os.close(fd)
