"""Copy a G-code file, tagging every move with its source line so findings can point at it."""
import gzip
import re
import sys
import zipfile

MOVE = re.compile(r"^\s*G[01](\s|$)", re.I)


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


def tag_lines(text):
    lines, _ = strip_start_block(text.splitlines())
    out = []
    for i, line in enumerate(lines, 1):
        out.append("%s ;L%d" % (line, i) if MOVE.match(line) else line)
    return "\n".join(out) + "\n"


if __name__ == "__main__":
    with open(sys.argv[2], "w") as f:
        f.write(tag_lines(read_gcode(sys.argv[1])))
