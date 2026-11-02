"""Check a real-firmware arc trace, including source-line attribution."""
import json
import sys
from pathlib import Path

out = Path(sys.argv[1])
result = json.loads((out / "report.json").read_text())
assert not result["errors"], result["errors"]
assert result["tool_changes"] == 0
assert result["firmware_motion_s"] == 0, result["firmware_motion_s"]
rows = [line.split() for line in (out / "trace.txt").read_text().splitlines() if line.startswith("M ")]
for number in (4, 5):
    arc = [row for row in rows if int(row[6]) == number]
    assert len(arc) > 10, (number, len(arc))
    assert all(row[9] == "G" for row in arc), arc[:1]
print("arc motion and source lines ok")
