/* Legion G9 independent back paddles (HID mode, report ID 1), over the official 0.48 firmware. */
/* The paddles reach the RAW button word at 0x6430 (bits 23-26) but the mapper drops them when they are */
/* not mapped. When the HID report is built (FUN_01e1d064, mode 7), copy three of them into the button */
/* bits nothing else uses (2, 5, 15 = HID buttons 3, 6, 16): */
/*   left top 23 -> 5 (BTN_Z), right top 24 -> 2 (BTN_C), left bottom 25 -> 15 (HID button 16). */
/* The right bottom paddle (26) stays mappable in the Legion app. See docs/paddles.md. */
	.set BTN_RET,   0x1e1d15e
	.set RIGHT_END, 0x1e23afc
	.set RAW,       0x6430

	.section .pb,"ax"
/* @0x1e1d15a, replaces: h[sp+6] = r0 (r0 = mapped 32-bit button word, used again for the hat after) */
	goto pd

	.section .rnop,"ax"
/* @0x1e23960: right static dirty block -> no-op (the steady path repaints the strip in the same tick) */
	goto RIGHT_END

	.section .pcave,"ax"
/* @0x1e23964: rest of that block (44 bytes) */
pd:	r1 = RAW
	r1 = [r1+0]
	r2 = uextra(r1, p:23, l:1)
	r0 <= insert(r2, p:5, l:1)
	r2 = uextra(r1, p:24, l:1)
	r0 <= insert(r2, p:2, l:1)
	r2 = uextra(r1, p:25, l:1)
	r0 <= insert(r2, p:15, l:1)
	h[sp+6] = r0
	goto BTN_RET
