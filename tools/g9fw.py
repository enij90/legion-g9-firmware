#!/usr/bin/env python3
"""Legion G9 firmware tool: fetch the official firmware, make a recovery zip, build patched images.

The official Lenovo firmware is never stored in this repository: `fetch` downloads it from the same
update server the Legion app uses and checks its hash; `build` applies one or more patches (only our
own bytes) on top of it.

  python3 g9fw.py fetch                                  # -> legion-g9_firmware_0.48.zip (official)
  python3 g9fw.py recovery legion-g9_firmware_0.48.zip   # -> legion-g9_firmware_0.49.zip (stock, renamed)
  python3 g9fw.py build legion-g9_firmware_0.48.zip 0.50 ../patches/perled/edits.txt ../patches/paddles/edits.txt
  python3 g9fw.py decrypt legion-g9_firmware_0.48.zip ota_plain.bin

The Legion app flashes any zip named legion-g9_firmware_<version>.zip with an ota.bin inside, from
the phone's Download/legion folder ("Local file"). The controller always reports 0.48, so any
version above 0.48 is accepted, including the stock image renamed to 0.49 (recovery).
"""
import argparse
import hashlib
import io
import sys
import urllib.request
import zipfile

STOCK_VERSION = "0.48"
STOCK_URL = "https://lenovoapi.vgabc.com/firmware/update/x1/download/legion-g9_firmware_0.48.zip"
STOCK_ZIP_SHA256 = "d5d8e764fafc6b7034f17957d33d83dd94f7206cc54711e7ad06ce78c3deedb8"
STOCK_OTA_SHA256 = "300a799883d8aafe83e3f22d8ea841b3a359176f8e41d4f6cd31a7f2fb4bb7fb"
OTA_SIZE = 0x40000

# SFC encryption of the app zone (from file offset 0x4000), 32-byte blocks. Key = 0x2496 ^ index,
# index = offset >> 2, except in the even 16 KiB segments from 0x8000 on, where index is
# (offset >> 2) - 0x2000. The loader zone below 0x4000 uses another cipher and is never touched.
POLY = 0x1021
SFC_KEY = 0x2496
APP0 = 0x4000


def _keystream_xor(block, key):
    state, out = key, bytearray(len(block))
    for i, byte in enumerate(block):
        out[i] = byte ^ (state & 0xFF)
        state = ((state << 1) & 0xFFFF) ^ (POLY if state & 0x8000 else 0)
    return bytes(out)


def key_index(offset):
    index = offset >> 2
    if offset >= 0x8000 and (offset >> 14) % 2 == 0:
        index -= 0x2000
    return index & 0xFFFF


def sfc_block(block, offset):
    """Encrypt or decrypt (same operation) the 32-byte block at file offset `offset`."""
    return _keystream_xor(block, (SFC_KEY ^ key_index(offset)) & 0xFFFF)


def decrypt(ota):
    plain = bytearray(ota)
    for offset in range(APP0, len(ota), 32):
        plain[offset:offset + 32] = sfc_block(ota[offset:offset + 32], offset)
    return plain


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def read_stock(zip_path):
    raw = open(zip_path, "rb").read()
    if sha256(raw) != STOCK_ZIP_SHA256:
        sys.exit(f"{zip_path}: not the official {STOCK_VERSION} zip (sha256 {sha256(raw)})")
    ota = zipfile.ZipFile(io.BytesIO(raw)).read("ota.bin")
    if sha256(ota) != STOCK_OTA_SHA256 or len(ota) != OTA_SIZE:
        sys.exit("ota.bin inside the zip does not match the official image")
    return ota


def write_zip(path, ota):
    info = zipfile.ZipInfo("ota.bin", date_time=(2025, 5, 30, 11, 23, 0))
    info.compress_type = zipfile.ZIP_DEFLATED
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr(info, ota)


def read_edits(path):
    """Edits file: one `<hex file offset>:<hex bytes>` per line, offsets in the decrypted image."""
    edits = []
    for number, line in enumerate(open(path), 1):
        line = line.split("#", 1)[0].strip()
        if not line:
            continue
        offset, data = line.split(":")
        edits.append((int(offset, 16), bytes.fromhex(data)))
        if edits[-1][0] < APP0:
            sys.exit(f"{path}:{number}: offset below the app zone")
    return edits


def apply_edits(ota, edits):
    plain = decrypt(ota)
    expected = bytearray(plain)
    for offset, data in edits:
        expected[offset:offset + len(data)] = data
    out = bytearray(ota)
    blocks = sorted({(offset + i) & ~31 for offset, data in edits for i in range(len(data))})
    for block in blocks:
        out[block:block + 32] = sfc_block(bytes(expected[block:block + 32]), block)
    # Checks: the new image decrypts to stock + edits, nothing else moved, loader untouched.
    if decrypt(bytes(out)) != expected:
        sys.exit("internal error: patched image does not decrypt to the intended bytes")
    if out[:APP0] != ota[:APP0]:
        sys.exit("internal error: loader zone changed")
    changed = sum(1 for a, b in zip(plain, expected) if a != b)
    return bytes(out), changed, len(blocks)


def cmd_fetch(args):
    print(f"downloading {STOCK_URL}")
    data = urllib.request.urlopen(STOCK_URL, timeout=60).read()
    if sha256(data) != STOCK_ZIP_SHA256:
        sys.exit(f"downloaded file has an unexpected sha256 {sha256(data)}: not saved")
    open(args.out, "wb").write(data)
    print(f"saved {args.out} (sha256 ok)")


def cmd_recovery(args):
    ota = read_stock(args.stock)
    out = args.out or "legion-g9_firmware_0.49.zip"
    write_zip(out, ota)
    print(f"wrote {out}: official {STOCK_VERSION} image, unchanged")


def cmd_build(args):
    ota = read_stock(args.stock)
    edits = [edit for path in args.edits for edit in read_edits(path)]
    spans = sorted((offset, offset + len(data)) for offset, data in edits)
    for (_, end), (start, _) in zip(spans, spans[1:]):
        if start < end:
            sys.exit(f"the patches overlap at file offset 0x{start:x}")
    patched, changed, blocks = apply_edits(ota, edits)
    out = args.out or f"legion-g9_firmware_{args.version}.zip"
    write_zip(out, patched)
    print(f"wrote {out}: {changed} bytes changed in {blocks} blocks, ota.bin sha256 {sha256(patched)}")


def cmd_decrypt(args):
    ota = read_stock(args.stock) if args.stock.endswith(".zip") else open(args.stock, "rb").read()
    open(args.out, "wb").write(decrypt(ota))
    print(f"wrote {args.out} (app zone decrypted, loader zone as is)")


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)
    p = sub.add_parser("fetch", help="download the official firmware zip and check its hash")
    p.add_argument("--out", default=f"legion-g9_firmware_{STOCK_VERSION}.zip")
    p.set_defaults(func=cmd_fetch)
    p = sub.add_parser("recovery", help="make the stock recovery zip (official image named 0.49)")
    p.add_argument("stock")
    p.add_argument("--out")
    p.set_defaults(func=cmd_recovery)
    p = sub.add_parser("build", help="apply one or more edits files to the official image")
    p.add_argument("stock")
    p.add_argument("version", help="version in the zip name, above 0.48 (e.g. 0.50)")
    p.add_argument("edits", nargs="+", help="edits files, e.g. ../patches/perled/edits.txt")
    p.add_argument("--out")
    p.set_defaults(func=cmd_build)
    p = sub.add_parser("decrypt", help="write the decrypted image (for disassembly)")
    p.add_argument("stock", help="official zip, or a raw ota.bin")
    p.add_argument("out")
    p.set_defaults(func=cmd_decrypt)
    args = parser.parse_args()
    if getattr(args, "version", None) is not None:
        try:
            if float(args.version) <= float(STOCK_VERSION):
                sys.exit("version must be above 0.48, or the Legion app will not flash it")
        except ValueError:
            sys.exit("version must be a plain number like 0.50 (the Legion app does not accept letters)")
    args.func(args)


if __name__ == "__main__":
    main()
