SECTIONS {
  .pb    0x1e1d15a : { *(.pb) }
  .ph    0x1e1d21a : { *(.ph) }
  .desc  0x1e32458 : { *(.desc) }
  .rnop  0x1e23960 : { *(.rnop) }
  .pcave 0x1e23964 : { *(.pcave) }
}
