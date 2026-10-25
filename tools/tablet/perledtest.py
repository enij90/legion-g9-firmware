#!/usr/bin/env python3
# Per-LED test (patched firmware): strip-0 solid 05 0C commands with speed = 0xE0 + channel.
# usage: perledtest.py static | wave SECONDS | stock
#   static: 10 distinct hues, right ch 0-4, left ch 7-11 (held)
#   wave:   moving rainbow along both bars at ~10 fps
#   stock:  one normal command (speed 0x80) -> back to stock single-colour behaviour
import os, sys, time
CH = [0, 1, 2, 3, 4, 7, 8, 9, 10, 11]
def find():
    for k in sorted(os.listdir("/sys/class/hidraw")):
        d = f"/sys/class/hidraw/{k}/device"
        try:
            if open(d + "/report_descriptor", "rb").read(3) == b"\x06\x7a\xff" and "3537" in open(d + "/uevent").read().upper():
                return "/dev/" + k
        except OSError:
            pass
fd = os.open(find(), os.O_WRONLY | os.O_APPEND)
def send(hue, speed, sat=100, bri=100):
    p = [0x05, 0x0C, 0x0C, 0x01, 0, hue & 0xFF, sat, bri, 1, speed, 0xFF]
    os.write(fd, bytes([0, *p, sum(p) & 0xFF]))
    time.sleep(0.01)
mode = sys.argv[1]
if mode == "static":
    for i, ch in enumerate(CH):
        send(i * 25, 0xE0 + ch)
elif mode == "wave":
    t0, f = time.time(), 0
    while time.time() - t0 < float(sys.argv[2]):
        for i, ch in enumerate(CH):
            send(f * 8 + (i % 5) * 50, 0xE0 + ch)
        f += 1
elif mode == "stock":
    send(0, 0x80)
os.close(fd)
print("done", mode)
