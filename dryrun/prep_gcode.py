"""Copy a G-code file, tagging every move with its source line so findings can point at it."""
import gzip
import re
import sys
import zipfile

MOVE = re.compile(r"^\s*G[0123](\s|$)", re.I)


def read_gcode(path):
    if path.endswith(".3mf"):
        with zipfile.ZipFile(path) as z:
            name = next(n for n in z.namelist() if n.endswith(".gcode"))
            return z.read(name).decode("utf-8", "replace")
    opener = gzip.open if path.endswith(".gz") else open
    with opener(path, "rt", errors="replace") as f:
        return f.read()


# Kept from the start block: machine state only. The rest (nozzle wipes, probing, purge line)
# needs sensors and happens before anything is on the bed, so it cannot scar a print.
KEEP_BEFORE_FIRST_LAYER = re.compile(r"^\s*(M82|M83|G90|G91|G92|M204|M220|M221|EXCLUDE_OBJECT_DEFINE|SET_VELOCITY_LIMIT)\b", re.I)
TOOL = re.compile(r"^\s*T(\d+)\b")


def strip_start_block(lines):
    """Blank the start block, keeping line numbers. Returns the new lines and how many were cut."""
    first = next((i for i, l in enumerate(lines) if l.startswith(";LAYER_CHANGE")), None)
    if first is None:
        return lines, 0
    tool, cut = "0", 0
    out = list(lines)
    for i in range(first):
        m = TOOL.match(lines[i])
        if m:
            tool = m.group(1)
        if lines[i].strip() and not lines[i].startswith(";") and not KEEP_BEFORE_FIRST_LAYER.match(lines[i]):
            out[i] = ""
            cut += 1
    out[first] = "G28\nT%s\n%s" % (tool, lines[first])
    return out, cut


# U1 travel limits: [stepper_x] and [stepper_y] position_min/position_max in the firmware's
# printer.cfg (same on 2.0.0 and 2.1.0).
LIMITS = {"X": (0.0, 271.0), "Y": (0.0, 335.0)}
AXIS = re.compile(r"\b([XY])(-?\d*\.?\d+)")


def start_block_margin(lines):
    """The start block's explicit absolute X/Y target closest to a travel limit, or None.

    The start block is not run (see strip_start_block), but the firmware adds the active head's
    XY offset to each of its moves. Offsets are measured from the midpoint of the four heads
    (extruder.py get_center_base_position), so the lowest head sits at minus half the spread, and
    a target closer to a limit than that offset is refused (forum topic 44046). Relative moves
    and axes a line leaves out are not guessed: macros before them move the head.
    """
    first = next((i for i, l in enumerate(lines) if l.startswith(";LAYER_CHANGE")), None)
    if first is None:
        return None
    absolute, best = True, None
    for i in range(first):
        code = lines[i].split(";", 1)[0].strip().upper()
        if code.startswith(("G90", "G91")):
            absolute = code.startswith("G90")
        elif absolute and MOVE.match(code):
            for axis, value in AXIS.findall(code):
                lo, hi = LIMITS[axis]
                for room, side in ((float(value) - lo, "-"), (hi - float(value), "+")):
                    if best is None or room < best["room_mm"]:
                        best = {"line": i + 1, "code": code, "axis": axis, "target": float(value),
                                "room_mm": round(room, 3), "side": side}
    return best


NON_ASCII = re.compile(r"[^\x00-\x7f]")


def tag_lines(text):
    lines, _ = strip_start_block(text.splitlines())
    out = []
    for i, line in enumerate(lines, 1):
        out.append("%s ;L%d" % (line, i) if MOVE.match(line) else line)
    # Homed from the start, whatever the slicer's start block does or whether it is found.
    # Klipper's batch reader decodes each 4096-byte read on its own and silently drops one that
    # cuts a UTF-8 character (the U1 start G-code has Chinese comments). ASCII cannot be cut.
    return NON_ASCII.sub("_", "G28\n" + "\n".join(out)) + "\n"


if __name__ == "__main__":
    with open(sys.argv[2], "w") as f:
        f.write(tag_lines(read_gcode(sys.argv[1])))
