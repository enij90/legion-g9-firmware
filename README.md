# Legion G9 firmware patches

Patches for the firmware of the **Lenovo Legion G9** controller (2025), the one that docks to the
Legion Tab Gen 3 (Legion Y700 2025). There are two patches, and you can build an image with either
one or with both:

- **Per-LED lighting**: each of the 10 LEDs on the grips can be set on its own, with its own color and
  brightness, instead of one color per side. I use it with
  [Colores](https://github.com/Hooandee/decky-colores) for an ambilight where every LED follows its own
  piece of the screen edge, and the Legion button follows the LED next to it.
- **Independent back paddles and M button**: the four paddles become buttons of their own (L4, R4, L5
  and R5 on a Steam Deck layout) instead of copies of other buttons, and the M button opens the Quick
  Access menu.

I run them on my [Armada port for the Legion Tab Gen 3](https://github.com/enij90/armada-tb321fu).

**Experimental**: so far tested only on my own controller. Read [Recovery](docs/recovery.md) before
flashing.

**Only for the original G9 (2025)**: USB `3537:1134`, product name "Legion Gaming Controller G9",
firmware line `legion-g9`. The **G9 2026** and the **G9 Wuji** run different firmware
(`legion-g9-2026`, `legion-g9-wuji`): do not flash this on them.

This repository has no firmware in it. The tool downloads the official Lenovo firmware from the same
update server the Legion app uses, checks its hash, and applies only my patch bytes on top of it.

## Which image

| you want | patches | zip version | tested |
|---|---|---|---|
| per-LED lighting and the paddles | `perled` + `paddles` | 0.50 | yes |
| only the paddles and M | `paddles` | 0.51 | yes |
| only per-LED lighting | `perled` | 0.52 | not in this form (an older per-LED-only image was) |
| the stock firmware back | none | 0.49 | yes |

The patches do not depend on each other. Lighting you do not patch stays stock, and so do the
buttons. Each image keeps its number when the patches are updated: the sha256 in the table below
tells the builds apart.

## Build

Needs Python 3 (standard library only).

1. Download the official firmware:

   ```sh
   cd tools
   python3 g9fw.py fetch    # official legion-g9_firmware_0.48.zip, hash checked
   ```

2. Build the image you chose. `build` applies only the patches listed at the end of the command:

   ```sh
   # per-LED lighting + paddles and M
   python3 g9fw.py build legion-g9_firmware_0.48.zip 0.50 ../patches/perled/edits.txt ../patches/paddles/edits.txt
   # paddles and M only
   python3 g9fw.py build legion-g9_firmware_0.48.zip 0.51 ../patches/paddles/edits.txt
   # per-LED lighting only
   python3 g9fw.py build legion-g9_firmware_0.48.zip 0.52 ../patches/perled/edits.txt
   ```

   Each command writes `legion-g9_firmware_<version>.zip`. The version is only a number for the
   Legion app (see [Flash](#flash)), and it must be a plain number: the app does not accept letters
   in it. Do not rename the zip, since the app reads the version from the file name.

To go back to the stock firmware:

```sh
python3 g9fw.py recovery legion-g9_firmware_0.48.zip    # stock image as legion-g9_firmware_0.49.zip
```

The images I tested, newest first. The version only changes the zip name, so `ota.bin` is the same
whatever number you build it with:

| patches | `ota.bin` sha256 |
|---|---|
| per-LED (Legion button follows the right grip) + paddles and M | `9c8e280f1de747de77e03496d4a18f4ce9a48a58931ac8ae7b7a8e0d7d21bff4` |
| paddles and M only | `4f0a5345d75a050248e76d2fe92921c8ddb8e552f0014ad102be0e46c01e4b74` |
| per-LED (off on black) + paddles and M | `10ca54870a83c2b8ba403e664c803b5403ee370c89adf0f8027611ecb797b5cd` |
| per-LED + paddles and M | `eae7b77f90ec4738fed115eb278d0d9dd1597a450b72eaa46bdfbd9ec6261097` |
| per-LED only (older patch) | `d0acd4d869bb500a8f2a8a75797694a203172d7aa04841df21baeccac2f94a75` |

Until the per-LED Legion button update, the zip numbers counted my test builds (0.69 to 0.80;
[docs/perled.md](docs/perled.md) still names some of them). Since then each image has the fixed
number above.

## Flash

You need the official Legion controller app for Android (package `com.legion.xtouch`). It is not on the
Play Store; Lenovo's download page is <https://lenovoshare.vgabc.com/download.html> (in Chinese: the
**下载G9安装包** button, "download the G9 package"). I flashed with version 2.0.51 of the app; the page
currently offers 2.0.31.

1. Copy the zip to the `Download/legion` folder of the phone with the Legion app.
2. Connect the G9 to the phone, open the app, go to the firmware update and choose **Local file**, then
   pick the zip.

The app takes the version from the file name and only flashes a version above the one the controller
reports. The controller reports 0.48 with the patches too, so the fixed numbers above keep working:
you can flash 0.50 again over 0.50, or switch to 0.51 and back, and the stock recovery zip named 0.49
always goes in.

## Using per-LED

With Colores, each grip LED follows its own piece of the screen edge:

https://github.com/user-attachments/assets/490ddd0e-5a0a-4dd6-ab39-dcf86cef98fa

Per-LED needs my build of Colores, which samples 5 points per side of the screen and drives each LED:

1. Download `Colores.zip` from the
   [release on my fork](https://github.com/enij90/decky-colores/releases/latest) and install it in Decky
   (developer mode, install from file). The source is the
   [`g9-perled`](https://github.com/enij90/decky-colores/tree/g9-perled) branch.
2. Per-LED is off by default: create an empty file named `g9-perled` in the plugin settings folder
   (`~/homebrew/settings/Colores/`) and restart Decky.

Only enable it with an image that has the per-LED patch. On any other firmware, including the
paddles-only image, each per-LED command paints the whole grip, and the grips jump between colors.

The Legion button takes the color of the 4th LED from the bottom of the right grip, the one next to
it. Everything else (effects, single colors, the Legion app) works as with the stock firmware. To drive
the LEDs from your own program, the protocol is in [docs/perled.md](docs/perled.md).

## Using the paddles and M

Leave the paddles **unmapped** in the Legion app. The four paddles and M then send buttons of their own
(`BTN_Z`, `BTN_C` and `BTN_TRIGGER_HAPPY1`–`3`); for the last three the patch turns 4 unused padding
bits of the report into new HID buttons. On Linux they need InputPlumber map entries to show up as L5,
R5 and the Quick Access button: see [docs/paddles.md](docs/paddles.md).

**M does not register every press yet**: it is also the controller's own key for remapping, and maybe
for other combinations, so now and then a press does not open the Quick Access menu.

**Note:** in my Armada port L4 and R4 already work; L5, R5 and M come with the next Armada update (OTA).
Until then they do nothing unless you add the map entries by hand as shown in
[docs/paddles.md](docs/paddles.md#until-the-next-armada-update). Other distributions using InputPlumber
need the G9 profile from Armada, adapted as described in
[docs/paddles.md](docs/paddles.md#other-distributions-with-inputplumber).

## How it was made

The patches are written in pi32v2 assembly ([patches/perled/perled.s](patches/perled/perled.s),
[patches/paddles/paddles.s](patches/paddles/paddles.s)) and assembled with the Jieli toolchain. The
assembled bytes are committed in each `edits.txt`, so building the firmware does not need the toolchain;
`tools/assemble.sh <name>` regenerates them.

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
