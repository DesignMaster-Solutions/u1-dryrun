#!/bin/bash
# End-to-end: the real firmware on real slices. Usage: tests/e2e.sh [image]
image=${1:-u1-dryrun}
cd "$(dirname "$0")/../examples" || exit 2
run() {  # file expected_exit_code
  out=$(docker run --rm -v "$PWD:/work" "$image" "$1" --out "/tmp/$1")
  rc=$?
  echo "$out" | grep -E "moves|SCAR|CROSSING|ERROR|clean"
  if [ "$rc" != "$2" ]; then echo "FAIL $1: exit $rc, expected $2"; exit 1; fi
}
run sign-orca-2.4.0.gcode.gz 0
run sign-orca-2.4.1.gcode.gz 1
# The slicer fix for the same scar, built by the fork CI and sliced headless on Linux next to the official build.
run sign-orca-2.4.1-linux.gcode.gz 1
run sign-orca-2.4.1-patched-linux.gcode.gz 0
run ring-orcaslicer-2.4.2.gcode.gz 0
# A print that really scratched on a real U1 (file shared by its owner, see README): the same move must keep being flagged.
run helado-pipewrx-orca-2.4.1.gcode.gz 1
echo "$out" | grep -q 'SCAR line 130731 ' || { echo "FAIL helado: the scar at line 130731 moved or vanished"; exit 1; }
# Snapmaker/OrcaSlicer#1168 in 15 layers (docs/orca-2.4.1-dock-travel.md): a sliced project read straight from
# the .3mf; the head must keep being caught going through the part on its way from the dock to the tower.
run tower-right-edge-orca-2.4.1.3mf 1
[ "$(echo "$out" | grep -c "^CROSSING line \(9734\|14909\|20512\) ")" = 3 ] || { echo "FAIL tower-right-edge: expected the 3 crossings at lines 9734, 14909, 20512"; exit 1; }
run out-of-range.gcode 2
# What if I skip an object mid-print? Clean without the skip; with it the stock firmware (2.0.0 and
# 2.1.0, Snapmaker/u1-klipper#22) drags the head 70 mm across the bed on the E-only chute prime.
run skip-then-toolchange.gcode 0
out=$(docker run --rm -v "$PWD:/work" "$image" skip-then-toolchange.gcode --out /tmp/skip --skip B@80); rc=$?
echo "$out" | grep -E "what if|DRAG"
[ "$rc" = 1 ] && echo "$out" | grep -q 'DRAG line 205 (extruder1): .* 70.7 mm, \[92.7, 300.5\] -> \[82.7, 230.5\]' \
  || { echo "FAIL --skip B@80: exit $rc, expected 1 with the drag at line 205"; exit 1; }
# The workaround on the same files: the scar must be gone, on the real firmware.
tmp=$(mktemp -d); trap 'rm -rf "$tmp"' EXIT
for f in helado-pipewrx-orca-2.4.1 sign-orca-2.4.1; do
  gzip -dc "$f.gcode.gz" > "$tmp/$f.gcode"
  python3 ../tools/lift_final_purge.py "$tmp/$f.gcode" | grep -q 'added a Z-hop' || { echo "FAIL $f: no Z-hop added"; exit 1; }
  docker run --rm -v "$tmp:/work" "$image" "$f.gcode" --out "/tmp/lifted-$f" | grep -E "SCAR|ERROR|clean"
  [ "${PIPESTATUS[0]}" = 0 ] || { echo "FAIL $f: still not clean after lift_final_purge.py"; exit 1; }
done
# Keep the generated report inside the container; validate both G2 and G3 provenance.
docker run --rm -v "$PWD/..:/work:ro" --entrypoint sh "$image" -c \
  'python3 /app/dryrun/run.py examples/arcs.gcode --out /tmp/arcs && python3 tests/check_arcs.py /tmp/arcs' || exit 1
echo e2e ok
