#!/bin/bash
# Rebuild patches/<name>/edits.txt from <name>.s with the Jieli pi32v2 toolchain (optional: edits.txt is
# committed, so building a firmware does not need the toolchain).
#   JL_TOOLCHAIN=~/jieli/pi32v2/bin tools/assemble.sh perled
#   JL_TOOLCHAIN=~/jieli/pi32v2/bin tools/assemble.sh paddles
set -euo pipefail
T=${JL_TOOLCHAIN:?set JL_TOOLCHAIN to the pi32v2/bin directory of the Jieli Linux toolchain}
NAME=${1:?usage: assemble.sh <patch name, e.g. perled or paddles>}
DIR=$(cd "$(dirname "$0")/../patches/$NAME" && pwd)
WORK=$(mktemp -d)
trap 'rm -rf "$WORK"' EXIT
XIP=$((0x1dfc000))   # file offset = address - XIP

"$T/clang" -target pi32v2 -mcpu=r3 -integrated-as -c "$DIR/$NAME.s" -o "$WORK/$NAME.o"
"$T/ld" -T "$DIR/$NAME.ld" "$WORK/$NAME.o" -o "$WORK/$NAME.elf"
: > "$WORK/edits.txt"
# One line per output section, in the linker script order.
for section in $(grep -o '^ *\.[a-z0-9]* *0x' "$DIR/$NAME.ld" | awk '{print $1}'); do
  address=$(grep -E "^ *\\$section +0x" "$DIR/$NAME.ld" | awk '{print $2}')
  "$T/objcopy" -O binary -j "$section" "$WORK/$NAME.elf" "$WORK/section.bin"
  printf '%x:%s\n' $((address - XIP)) "$(od -An -v -tx1 "$WORK/section.bin" | tr -d ' \n')" >> "$WORK/edits.txt"
done
if cmp -s "$WORK/edits.txt" "$DIR/edits.txt"; then
  echo "$NAME: edits.txt unchanged"
else
  cp "$WORK/edits.txt" "$DIR/edits.txt"
  echo "$NAME: edits.txt updated"
fi
