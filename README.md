# Legion G9 firmware patches

Patches for the firmware of the **Lenovo Legion G9** controller (2025), the one that docks to the
Legion Tab Gen 3 (Legion Y700 2025). The first one, **per-LED lighting**, lets each of the 10 LEDs on the grips be set on its own,
with its own color and brightness, instead of one color per side. I use it with
[Colores](https://github.com/Hooandee/decky-colores) for an ambilight where every LED follows its own
piece of the screen edge, on my [Armada port for the Legion Tab Gen 3](https://github.com/enij90/armada-tb321fu).

**Experimental**: so far tested only on my own controller. Read [Recovery](docs/recovery.md) before
flashing.

**Only for the original G9 (2025)**: USB `3537:1134`, product name "Legion Gaming Controller G9",
firmware line `legion-g9`. The **G9 2026** and the **G9 Wuji** run different firmware
(`legion-g9-2026`, `legion-g9-wuji`): do not flash this on them.

This repository has no firmware in it. The tool downloads the official Lenovo firmware from the same
update server the Legion app uses, checks its hash, and applies only my patch bytes on top of it.

## Build

Needs Python 3 (standard library only).

```sh
cd tools
python3 g9fw.py fetch                                   # official legion-g9_firmware_0.48.zip, hash checked
python3 g9fw.py build legion-g9_firmware_0.48.zip ../patches/perled/edits.txt 0.69
python3 g9fw.py recovery legion-g9_firmware_0.48.zip    # stock image as legion-g9_firmware_0.49.zip
```

`build` writes `legion-g9_firmware_0.69.zip`. Its `ota.bin` must have sha256
`d0acd4d869bb500a8f2a8a75797694a203172d7aa04841df21baeccac2f94a75`: that is the exact image I tested.

## Flash

You need the official Legion controller app for Android (package `com.legion.xtouch`). It is not on the
Play Store; Lenovo's download page is <https://lenovoshare.vgabc.com/download.html> (in Chinese: the
**下载G9安装包** button, "download the G9 package"). I flashed with version 2.0.51 of the app; the page
currently offers 2.0.31.

1. Copy the zip to the `Download/legion` folder of the phone with the Legion app.
2. Connect the G9 to the phone, open the app, go to the firmware update and choose **Local file**, then
   pick the zip.

The app takes the version from the file name and only flashes a version above the one the controller
reports. The controller reports 0.48 with the patch too, so any number above 0.48 works, and so does
the stock recovery zip named 0.49.

## Using per-LED

With Colores: per-LED needs my Colores branch
[`g9-perled`](https://github.com/enij90/decky-colores/tree/g9-perled), which samples 5 points per side
of the screen and drives each LED. It is off by default: create an empty file named `g9-perled` in the
plugin settings folder (`~/homebrew/settings/Colores/`) and restart Decky. Do not enable it without the
patched firmware: the stock one paints the whole strip with these commands.

Everything else (effects, single colors, the Legion app) works as with the stock firmware. To drive the
LEDs from your own program, the protocol is in [docs/perled.md](docs/perled.md).

## How it was made

The patch is written in pi32v2 assembly ([patches/perled/perled.s](patches/perled/perled.s)) and
assembled with the Jieli toolchain. The assembled bytes are committed in `edits.txt`, so building the
firmware does not need the toolchain; `tools/assemble.sh` regenerates them.

Along the way I found that half of the firmware image is encrypted with a shifted key, which every
earlier tool decrypted wrong: see [docs/sfc-key.md](docs/sfc-key.md). `tools/g9fw.py decrypt` writes
the correct plain image for disassembly.

## Credits

- [Colores](https://github.com/Hooandee/decky-colores) by Hooandee, and the Armada OS fork by
  [jl-casella](https://github.com/jl-casella/decky-colores) that my branch builds on: the lighting
  plugin the per-LED mode was made for.
- [kagaimiq/jl-uboot-tool](https://github.com/kagaimiq/jl-uboot-tool): flash access through the Jieli
  download mode, my last-resort recovery.
- [dank0i/cyclone2](https://github.com/dank0i/cyclone2): reverse engineering of a twin GameSir controller,
  a great map of this firmware family.
- [Armada](https://github.com/armada-os/armada), the OS I run the G9 with, and
  [my port of it to the Legion Tab Gen 3](https://github.com/enij90/armada-tb321fu).

Lenovo, Legion and GameSir are trademarks of their owners. Not affiliated with them.
