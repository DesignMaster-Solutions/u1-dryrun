#!/usr/bin/env python3
"""u1-dryrun: run a sliced G-code through Snapmaker's real U1 Klipper, without a printer.

Exit code: 0 clean, 1 surface scars found, 2 the firmware rejected the file.
"""
import argparse
import json
import os
import shutil
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import analyze  # noqa: E402
import prep_cfg  # noqa: E402
import prep_gcode  # noqa: E402
import report  # noqa: E402

KLIPPER = os.environ.get("U1_KLIPPER", "/opt/klipper")
DICTS = os.environ.get("U1_DICTS", "/opt/dicts")
TIMEOUT_S = int(os.environ.get("U1_TIMEOUT_S", "900"))


def run_klippy(gcode_path, out):
    prep_cfg.main(os.path.join(KLIPPER, "lava"), os.path.join(out, "cfg"))
    here = os.path.dirname(os.path.abspath(__file__))
    shutil.copy(os.path.join(here, "dryrun_tracer.py"), os.path.join(KLIPPER, "klippy/extras/"))
    board, tool = "at32f403a_config.dict", "at32f415_config.dict"
    cmd = ["python3", os.path.join(KLIPPER, "klippy/klippy.py"), os.path.join(out, "cfg/printer.cfg"),
           "-i", gcode_path, "-o", os.path.join(out, "mcu.out"), "-v",
           "-l", os.path.join(out, "klippy.log"), "-d", os.path.join(DICTS, board)]
    for i in range(4):
        cmd += ["-d", "e%d=%s" % (i, os.path.join(DICTS, tool))]
    env = dict(os.environ, DRYRUN_TRACE=os.path.join(out, "trace.txt"))
    try:
        return subprocess.run(cmd, env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                              timeout=TIMEOUT_S).returncode
    except subprocess.TimeoutExpired:
        return -1  # a macro is waiting on hardware; the trace so far is still analyzed


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("gcode", help=".gcode or .gcode.3mf")
    ap.add_argument("--out", default="u1-dryrun-report")
    ap.add_argument("--clearance", type=float, default=analyze.CLEARANCE,
                    help="mm above a finished surface below which a travel counts as a scar")
    args = ap.parse_args()
    os.makedirs(args.out, exist_ok=True)
    tagged = os.path.join(args.out, "input.gcode")
    text = prep_gcode.read_gcode(args.gcode)
    with open(tagged, "w") as f:
        f.write(prep_gcode.tag_lines(text))
    rc = run_klippy(tagged, args.out)
    result = analyze.analyze(os.path.join(args.out, "trace.txt"), clearance=args.clearance,
                             line_types=analyze.line_types_from_gcode(text))
    result.update(file=os.path.basename(args.gcode), klippy_rc=rc,
                  start_margin=prep_gcode.start_block_margin(text.splitlines()))
    with open(os.path.join(args.out, "report.json"), "w") as f:
        json.dump(result, f, indent=2)
    with open(os.path.join(args.out, "report.html"), "w") as f:
        f.write(report.render(result))
    print(report.summary(result))
    if result["errors"] or rc != 0:
        return 2
    return 1 if result["scars"] else 0


if __name__ == "__main__":
    sys.exit(main())
