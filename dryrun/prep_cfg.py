"""Build the dry-run config from Snapmaker's own lava/printer.cfg.

Only sections that talk to hardware or services absent in batch mode are removed;
kinematics, limits, macros and tool-change logic stay exactly as shipped.
"""
import os
import re
import sys

# shortcut: list found by running klippy until it loaded; re-check on each firmware bump.
REMOVE = re.compile(
    r"^(mqtt|timelapse|fm175xx_reader|filament_detect|resonance_tester"
    r"|sc7a20 .*|lis2dw .*|sensor_accelerometer_identify .*|gcode_macro SHAPER_CALIBRATE"
    r"|homing_precise_corexy|homing_xyz_override)$"
)


def strip_sections(text, remove=REMOVE):
    out, skipping = [], False
    for line in text.splitlines():
        m = re.match(r"^\[([^\]]+)\]", line)
        if m:
            skipping = bool(remove.match(m.group(1)))
        out.append("#DRYRUN " + line if skipping else line)
    return "\n".join(out) + "\n"


# A real print needs klippy "ready"; power_loss_check's ready handler queries the MCU, which never
# answers in batch mode, so the handlers after it would never run.
REMOVE_FOR_PRINT = re.compile(REMOVE.pattern[:-2] + r"|power_loss_check( .*)?)$")


def main(src_dir, dst_dir, remove=REMOVE):
    os.makedirs(dst_dir, exist_ok=True)
    for name in os.listdir(src_dir):
        if name.endswith(".cfg"):
            with open(os.path.join(src_dir, name)) as f:
                text = strip_sections(f.read(), remove)
            with open(os.path.join(dst_dir, name), "w") as f:
                f.write(text)
    with open(os.path.join(dst_dir, "printer.cfg")) as f:
        text = f.read()
    with open(os.path.join(dst_dir, "printer.cfg"), "w") as f:
        f.write("[dryrun_tracer]\n\n" + text)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
