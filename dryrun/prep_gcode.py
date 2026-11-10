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


def parse_maps(specs):
    """["T4=T3", ...] -> [(4, 3)]: which head the screen assigned to a slicer filament."""
    maps = []
    for spec in specs or []:
        m = re.match(r"^T?(\d+)=T?([0-3])$", spec, re.I)
        if not m:
            raise ValueError("--map wants T<filament>=T<head 0-3>, as on the screen (T4=T3), got %r" % spec)
        maps.append((int(m.group(1)), int(m.group(2))))
    return maps


def unmapped_filaments(text, maps=()):
    """Slicer filaments above T3 that the file selects and no --map names. The firmware default
    table (print_task_config.py) sends every one of them to head 0; on the printer the screen
    sets the real head when the print starts."""
    used = {int(m.group(1)) for m in re.finditer(r"^T(\d+)\s*(;.*)?$", text, re.M)}
    return sorted(t for t in used if t > 3 and t not in {f for f, _ in maps})


def parse_skips(specs, text):
    """["NAME@LINE", ...] -> [(name, line)]: the object the user skips on the screen, and the
    file line the print is at when they press it. The name must be one the file defines."""
    defined = set(re.findall(r"^EXCLUDE_OBJECT_DEFINE\b.*?\bNAME=(\S+)", text, re.M))
    n_lines, skips = len(text.splitlines()), []
    for spec in specs or []:
        name, _, line = spec.rpartition("@")
        if not name or not line.isdigit() or not 1 <= int(line) <= n_lines:
            raise ValueError("--skip wants OBJECT@LINE with a line of this file (1-%d), got %r" % (n_lines, spec))
        if name not in defined:
            raise ValueError("--skip %s: the file defines no such object; it has: %s"
                             % (name, ", ".join(sorted(defined)) or "none (objects not labelled)"))
        skips.append((name, int(line)))
    return skips


def map_lines(maps):
    return ["SET_PRINT_EXTRUDER_MAP CONFIG_EXTRUDER=%d MAP_EXTRUDER=%d" % m for m in maps]


def tag_lines(text, maps=(), skips=()):
    lines, _ = strip_start_block(text.splitlines())
    out = []
    for i, line in enumerate(lines, 1):
        out.append("%s ;L%d" % (line, i) if MOVE.match(line) else line)
    for name, at in skips:  # before that line, as one entry: line numbers stay the file's own
        out[at - 1] = "DRYRUN_LINE N=%d\nEXCLUDE_OBJECT NAME=%s\n%s" % (at, name, out[at - 1])
    # Homed from the start, whatever the slicer's start block does or whether it is found.
    # Klipper's batch reader decodes each 4096-byte read on its own and silently drops one that
    # cuts a UTF-8 character (the U1 start G-code has Chinese comments). ASCII cannot be cut.
    # As a print (--skip) the firmware refuses the map once the print has started: run.py sends
    # it before the print instead, as the screen does.
    head = ([] if skips else map_lines(maps)) + ["G28"]
    return NON_ASCII.sub("_", "\n".join(head + ["\n".join(out)])) + "\n"


if __name__ == "__main__":
    with open(sys.argv[2], "w") as f:
        f.write(tag_lines(read_gcode(sys.argv[1])))
