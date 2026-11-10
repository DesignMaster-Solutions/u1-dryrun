#!/usr/bin/env python3
"""u1-dryrun: run a sliced G-code through Snapmaker's real U1 Klipper, without a printer.

Exit code: 0 clean, 1 surface scars or a dragged head found, 2 the firmware rejected the file.
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


def run_klippy(gcode_path, out, as_print=False, before_print=()):
    """Console input by default. as_print: through the firmware's virtual_sdcard, as on the printer.
    shortcut: only --skip runs as a print, so earlier results do not move; make it the default
    once the example files give the same report both ways."""
    cfg = os.path.join(out, "cfg")
    prep_cfg.main(os.path.join(KLIPPER, "lava"), cfg, prep_cfg.REMOVE_FOR_PRINT if as_print else prep_cfg.REMOVE)
    here = os.path.dirname(os.path.abspath(__file__))
    shutil.copy(os.path.join(here, "dryrun_tracer.py"), os.path.join(KLIPPER, "klippy/extras/"))
    env = dict(os.environ, DRYRUN_TRACE=os.path.join(out, "trace.txt"))
    if as_print:
        shutil.copy(os.path.join(here, "dryrun_ui.py"), os.path.join(KLIPPER, "klippy/extras/"))
        with open(os.path.join(cfg, "printer.cfg"), "a") as f:
            # later duplicate sections override earlier ones in Klipper's config parser
            f.write("\n[dryrun_ui]\n\n[virtual_sdcard]\npath: %s\n" % os.path.dirname(os.path.abspath(gcode_path)))
        # A U1 in use has a saved bed mesh, loaded at boot; without one that load is an error and
        # batch mode stops. A flat mesh on the shipped probe grid: zero Z correction.
        os.makedirs(os.path.join(cfg, "snapmaker"), exist_ok=True)
        with open(os.path.join(cfg, "snapmaker", "bed_mesh_default.json"), "w") as f:
            json.dump({"version": 1, "profile": {"points": [[0.0] * 13 for _ in range(13)], "mesh_params": {
                "min_x": 3.0, "max_x": 267.0, "min_y": 3.0, "max_y": 267.0, "x_count": 13, "y_count": 13,
                "mesh_x_pps": 2, "mesh_y_pps": 2, "algo": "bicubic", "tension": 0.2}}}, f)
        env["DRYRUN_PRINT"] = os.path.basename(gcode_path)
        env["DRYRUN_BEFORE_PRINT"] = "\n".join(before_print)
    board, tool = "at32f403a_config.dict", "at32f415_config.dict"
    cmd = ["python3", os.path.join(KLIPPER, "klippy/klippy.py"), os.path.join(cfg, "printer.cfg"),
           "-i", "/dev/stdin" if as_print else gcode_path, "-o", os.path.join(out, "mcu.out"), "-v",
           "-l", os.path.join(out, "klippy.log"), "-d", os.path.join(DICTS, board)]
    for i in range(4):
        cmd += ["-d", "e%d=%s" % (i, os.path.join(DICTS, tool))]
    # as a print, stdin stays open and empty: batch mode exits when its input ends
    p = subprocess.Popen(cmd, env=env, stdin=subprocess.PIPE if as_print else subprocess.DEVNULL,
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        return p.wait(timeout=TIMEOUT_S)
    except subprocess.TimeoutExpired:
        p.kill()
        p.wait()
        return -1  # a macro is waiting on hardware; the trace so far is still analyzed


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("gcode", help=".gcode or .gcode.3mf")
    ap.add_argument("--out", default="u1-dryrun-report")
    ap.add_argument("--clearance", type=float, default=analyze.CLEARANCE,
                    help="mm above a finished surface below which a travel counts as a scar")
    ap.add_argument("--map", action="append", metavar="T4=T3",
                    help="head the screen assigned to a slicer filament above T3 (without it the "
                         "firmware default applies: head 0); repeatable")
    ap.add_argument("--skip", action="append", metavar="OBJECT@LINE",
                    help="what if I skip this object on the screen when the print is at this file "
                         "line? Runs the file as a real print (virtual_sdcard); repeatable")
    args = ap.parse_args()
    text = prep_gcode.read_gcode(args.gcode)
    try:
        maps = prep_gcode.parse_maps(args.map)
        skips = prep_gcode.parse_skips(args.skip, text)
    except ValueError as e:
        ap.error(str(e))
    os.makedirs(args.out, exist_ok=True)
    tagged = os.path.join(args.out, "input.gcode")
    with open(tagged, "w") as f:
        f.write(prep_gcode.tag_lines(text, maps, skips))
    rc = run_klippy(tagged, args.out, as_print=bool(skips), before_print=prep_gcode.map_lines(maps))
    result = analyze.analyze(os.path.join(args.out, "trace.txt"), clearance=args.clearance,
                             line_types=analyze.line_types_from_gcode(text),
                             e_only_lines=analyze.e_only_lines_from_gcode(text))
    result.update(file=os.path.basename(args.gcode), klippy_rc=rc, unmapped_filaments=prep_gcode.unmapped_filaments(text, maps),
                  start_margin=prep_gcode.start_block_margin(text.splitlines()),
                  skips=[{"object": n, "line": l} for n, l in skips])
    with open(os.path.join(args.out, "report.json"), "w") as f:
        json.dump(result, f, indent=2)
    with open(os.path.join(args.out, "report.html"), "w") as f:
        f.write(report.render(result))
    print(report.summary(result))
    if result["errors"] or rc != 0:
        return 2
    return 1 if result["scars"] or result["drags"] else 0


if __name__ == "__main__":
    sys.exit(main())
