/* Legion G9 per-LED lighting, over the official 0.48 firmware. Addresses are in the decrypted image. */
/* Store = spare bytes +5..+7 (R,G,B) and +9 (brightness) of each channel state (0x7128 + ch*0x1c). */
/* Handler (strip 0 colour branch): packet speed b[r13+9] in 0xE0..0xEB -> stash[speed-0xE0] = colour, */
/* brightness; then skip the stock whole-strip repaint and go to the reply. */
/* Render (steady), static mode + stored speed in range: per ch 0-11 anim mode [0x7128+ch*0x1c]=0, SETCH(ch, stash). */
/* Render (dirty): skip the whole-strip repaint blocks in per-LED mode. See docs/perled.md. */
	.set HOOK_RET,    0x1e21b94
	.set SKIP_END,    0x1e21bc4
	.set RIGHT_A_DISP,0x1e23942
	.set STEADY_DISP, 0x1e23b6a
	.set STEADY_R0,   0x1e23b70
	.set STEADY_END,  0x1e23c88
	.set SETCH,       0x1e1a946
	.set CHBASE,      0x7128

	.set STOCK_A,     0x1e23754
	.set AFTER_A,     0x1e23b1a

	.section .p1,"ax"
/* @0x1e2374e, replaces: if (r0 == 0) goto AFTER_A (6 B); r0 = dirty flag */
	goto c1
	nop

	.section .cave2,"ax"
/* @0x1e000f8 (free 0xFF padding before entry, used by 0.59): skip dirty A blocks in per-LED mode */
c1:	if (r0 == 0) goto la
	r0 = 20148
	r1 = 1379
	r1 = b[r0+r1](u)
	if (r1 != 0) goto ls
	r1 = 1382
	r0 = b[r0+r1](u)
	if (r0 < 224) goto ls
la:	goto AFTER_A
ls:	goto STOCK_A

	.section .h1,"ax"
	goto hk

	.section .p2,"ax"
	goto c2
	nop
	nop

	.section .cave,"ax"
	goto RIGHT_A_DISP
hk:	r4 = r5 + 1372
	r1 = b[r13+9](u)
	if (r1 < 224) goto HOOK_RET
	if (r1 > 235) goto HOOK_RET
/* r1 = 0xE0 + ch, so r1 * 0x1C + (CHBASE - 0xE0 * 0x1C) = CHBASE + ch * 0x1C */
	r2 = r1 * 0x1C
	r3 = CHBASE - 0xE0 * 0x1C
	r2 = r2 + r3
	r3 = r0 >> 16
	b[r2+5] = r3
	r3 = r0 >> 8
	b[r2+6] = r3
	b[r2+7] = r0
	r3 = b[r13+7](u)
	r3 = r3 * 0x5
	r3 = r3 >> 1
/* B = 1 (B = 0 is not accepted, so this is the lowest) turns the LED off instead of a faint white */
	if (r3 >= 3) goto hb
	r3 = 0
hb:	b[r2+9] = r3
/* per-LED: skip the stock painter 0x1e1cbec, FUN_01e1afc6 x2 and 0x1e1f4ee; go to the branch end (ack epilogue) */
	goto SKIP_END
c2:	r0 = 1388
	r0 = b[r4+r0](u)
	if (r0 != 0) goto STEADY_DISP
	r0 = 1382
	r0 = b[r4+r0](u)
	if (r0 < 224) goto STEADY_R0
	r5 = 0
	r4 = CHBASE
lp:	r2 = 0
	[r4+0] = r2
	r1 = b[r4+9](u)
	b[r4+8] = r1
	r1 = b[r4+7](u)
	r2 = b[r4+6](u)
	r3 = b[r4+5](u)
	r1 <= insert(r2, p:8, l:8)
	r1 <= insert(r3, p:16, l:8)
	r0 = r5
	call SETCH
	r4 += 0x1C
	r5 += 1
	if (r5 != 12) goto lp
	goto STEADY_END
