#!/bin/sh
# Slice the two-colour sign (examples/ring.stl + inlay.stl) with a Snapmaker Orca Linux build, headless.
# Usage: tools/slice_sign_linux.sh <extracted AppImage dir (squashfs-root)> <out dir>
# Needs xvfb-run and the host WebKitGTK 4.1 runtime (Ubuntu 24.04: libwebkit2gtk-4.1-0); extract the
# AppImage with --appimage-extract first. Used for the A/B of the #1149 fix: slice with the patched and the
# unpatched build, then `python3 tools/ab_final_purge.py <base>/plate_1.gcode <patched>/plate_1.gcode`.
set -e
ROOT=$1; OUT=$2
[ -x "$ROOT/AppRun" ] && [ -n "$OUT" ] || { echo "usage: $0 <squashfs-root> <out dir>" >&2; exit 2; }
HERE=$(cd "$(dirname "$0")/.." && pwd)
PROF=$(mktemp -d)
# "system" makes the CLI treat the flattened presets as the U1 system presets; with the default "User" it
# rejects the process with "process not compatible with printer" (return -17).
python3 "$HERE/examples/flatten_profiles.py" "$ROOT/resources/profiles/Snapmaker" "$PROF" system
mkdir -p "$OUT"
timeout 300 xvfb-run -a "$ROOT/AppRun" --arrange 0 --allow-newer-file \
  --load-settings "$PROF/machine.json;$PROF/process.json" \
  --load-filaments "$PROF/fil1.json;$PROF/fil2.json" --load-filament-ids "1,2" \
  --slice 0 --outputdir "$OUT" "$HERE/examples/ring.stl" "$HERE/examples/inlay.stl"
rm -rf "$PROF"
ls "$OUT"/plate_1.gcode
