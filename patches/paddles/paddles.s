/* Legion G9 independent back paddles (HID mode, report ID 1), over the official 0.48 firmware. */
/* The paddles reach the RAW button word at 0x6430 (bits 23-26) but the mapper drops them when they are */
/* not mapped. When the HID report is built (FUN_01e1d064, mode 7), copy three of them into the button */
/* bits nothing else uses (2, 5 = HID buttons 3, 6): left top 23 -> 5 (BTN_Z), right top 24 -> 2 (BTN_C). */
/* The report descriptor turns the 4 padding bits after the hat into HID buttons 17-20 */
/* (BTN_TRIGGER_HAPPY1-4 on Linux), without changing its length; the hat byte gets */
/*   left bottom 25 -> 4 (button 17), right bottom 26 -> 5 (button 18), M 30 -> 6 (button 19). */
/* See docs/paddles.md. */
	.set BTN_RET,   0x1e1d15e
	.set HAT_RET,   0x1e1d21e
	.set RIGHT_END, 0x1e23afc
	.set RAW,       0x6430

	.section .pb,"ax"
/* @0x1e1d15a, replaces: h[sp+6] = r0 (r0 = mapped 32-bit button word, used again for the hat after) */
	goto pd

	.section .ph,"ax"
/* @0x1e1d21a, replaces: b[sp+5] = r0 (hat, the only store of byte 5 of the report) */
	goto hk

	.section .desc,"a"
/* @0x1e32458, report descriptor of report ID 1, after the hat. Was: 4-bit constant padding, then */
/* buttons 1-16 (75 04 95 01 81 01 05 09 19 01 29 10 15 00 25 01 75 01 95 10 81 02). Now buttons */
/* 17-20 in those 4 bits, then buttons 1-16; logical minimum 0 is still set by the hat. Same 22 bytes. */
	.byte 0x05, 0x09, 0x19, 0x11, 0x29, 0x14, 0x25, 0x01, 0x75, 0x01, 0x95, 0x04, 0x81, 0x02
	.byte 0x19, 0x01, 0x29, 0x10, 0x95, 0x10, 0x81, 0x02

	.section .rnop,"ax"
/* @0x1e23960: right static dirty block -> no-op (the steady path repaints the strip in the same tick) */
	goto RIGHT_END

	.section .pcave,"ax"
/* @0x1e23964: rest of that block (404 bytes) */
pd:	r1 = RAW
	r1 = [r1+0]
	r2 = uextra(r1, p:23, l:1)
	r0 <= insert(r2, p:5, l:1)
	r2 = uextra(r1, p:24, l:1)
	r0 <= insert(r2, p:2, l:1)
	h[sp+6] = r0
	goto BTN_RET

/* hat byte: r0 = hat (0-7, 15 = centred); r1 and r2 are free here */
hk:	r1 = RAW
	r1 = [r1+0]
	r2 = uextra(r1, p:25, l:1)
	r0 <= insert(r2, p:4, l:1)
	r2 = uextra(r1, p:26, l:1)
	r0 <= insert(r2, p:5, l:1)
	r2 = uextra(r1, p:30, l:1)
	r0 <= insert(r2, p:6, l:1)
	b[sp+5] = r0
	goto HAT_RET
