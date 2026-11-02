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
run ring-orcaslicer-2.4.2.gcode.gz 0
run out-of-range.gcode 2
echo e2e ok
