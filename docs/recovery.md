# Recovery

## Back to stock

Flash the stock recovery zip like any other:

```sh
python3 tools/g9fw.py recovery legion-g9_firmware_0.48.zip   # -> legion-g9_firmware_0.49.zip
```

It contains the official `ota.bin` unchanged; only the name says 0.49, so the Legion app accepts it.
I went back and forth this way many times while developing the patch.

## If the controller no longer starts

The G9 is a Jieli AC695X. Its download mode (UBOOT) reads and writes the whole flash over USB and does
not depend on the application firmware, so a bad image can be rewritten. Entering it on the G9 needs an
FTDI adapter on the USB lines and [jl-uboot-tool](https://github.com/kagaimiq/jl-uboot-tool); I had to
do it once, after an early experiment. Always keep a full flash backup if you go this way.

The per-LED patch only touches the lighting code (render and the color command branch); the USB, input
and update paths are stock.
