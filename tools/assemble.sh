#!/bin/bash
# Rebuild patches/perled/edits.txt from perled.s with the Jieli pi32v2 toolchain (optional: edits.txt is
# committed, so building a firmware does not need the toolchain).
#   JL_TOOLCHAIN=~/jieli/pi32v2/bin tools/assemble.sh
set -euo pipefail
T=${JL_TOOLCHAIN:?set JL_TOOLCHAIN to the pi32v2/bin directory of the Jieli Linux toolchain}
DIR=$(cd "$(dirname "$0")/../patches/perled" && pwd)
WORK=$(mktemp -d)
trap 'rm -rf "$WORK"' EXIT
XIP=$((0x1dfc000))   # file offset = address - XIP

"$T/clang" -target pi32v2 -mcpu=r3 -integrated-as -c "$DIR/perled.s" -o "$WORK/perled.o"
"$T/ld" -T "$DIR/perled.ld" "$WORK/perled.o" -o "$WORK/perled.elf"
: > "$WORK/edits.txt"
# One line per output section, in the linker script order.
for section in $(grep -o '^ *\.[a-z0-9]* *0x' "$DIR/perled.ld" | awk '{print $1}'); do
  address=$(grep -E "^ *\\$section +0x" "$DIR/perled.ld" | awk '{print $2}')
  "$T/objcopy" -O binary -j "$section" "$WORK/perled.elf" "$WORK/section.bin"
  printf '%x:%s\n' $((address - XIP)) "$(od -An -v -tx1 "$WORK/section.bin" | tr -d ' \n')" >> "$WORK/edits.txt"
done
if cmp -s "$WORK/edits.txt" "$DIR/edits.txt"; then
  echo "edits.txt unchanged"
else
  cp "$WORK/edits.txt" "$DIR/edits.txt"
  echo "edits.txt updated"
fi
