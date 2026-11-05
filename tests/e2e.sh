#!/bin/bash
# End-to-end: the real firmware on real slices. Usage: tests/e2e.sh [image]
image=${1:-u1-dryrun}
cd "$(dirname "$0")/../examples" || exit 2
run() {  # file expected_exit_code
  out=$(docker run --rm -v "$PWD:/work" "$image" "$1" --out "/tmp/$1")
  rc=$?
  echo "$out" | grep -E "moves|SCAR|ERROR|clean"
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
run out-of-range.gcode 2
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
