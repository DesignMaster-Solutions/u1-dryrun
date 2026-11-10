"""Plain-text summary and a self-contained HTML report (top view of the bed + tables)."""
import html

BED = 270


def drag_lines(r):
    return ["DRAG line %d (%s): the file asks for filament only, the firmware moved the head %.1f mm, %s -> %s"
            " at Z%.2f, while pushing %.1f mm of filament%s"
            % (d["line"], d["tool"], d["length_mm"], d["from"], d["to"], d["z"], d["extruded_mm"],
               " (skipped-object offset, Snapmaker/u1-klipper#22)" if r.get("skips") else "")
            for d in r.get("drags") or []]


def summary(r):
    out = ["%s: %d moves, %d tool changes" % (r["file"], r["moves"], r["tool_changes"])]
    if r["motion_time_s"] is not None:
        out.append("motion time %.0f s (no heating), about %.0f s of it firmware tool-change motion"
                   % (r["motion_time_s"], r["firmware_motion_s"]))
    for name, t in sorted(r["tools"].items()):
        out.append("  %s: %.0f mm of filament" % (name, t["extruded_mm"]))
    for k in r.get("skips") or []:
        out.append("what if: object %s skipped at line %d; the file ran as a print" % (k["object"], k["line"]))
    for e in r["errors"]:
        out.append("FIRMWARE ERROR near line %d: %s" % (e["line"], e["message"]))
    for s in r["scars"]:
        out.append("SCAR line %d (%s, %s): %s -> %s at Z%.2f crosses %.1f mm of finished surface, clearance %.2f mm"
                   % (s["line"], s["source"], s["tool"], s["from"], s["to"], s["z"], s["length_mm"], s["clearance_mm"]))
    out += drag_lines(r)
    if r.get("skipped_commands"):
        out.append("not exercised (no such hardware here): " + ", ".join(r["skipped_commands"]))
    if r.get("unmapped_filaments"):
        out.append("head not known for %s: this run printed them on head 0 (the firmware default); pass the"
                   " head the screen shows, e.g. --map T%d=T3"
                   % (", ".join("T%d" % t for t in r["unmapped_filaments"]), r["unmapped_filaments"][0]))
    m = r.get("start_margin")
    if m:
        out.append("start block: line %d (%s) leaves %.2f mm to the %s limit: a head with a %s offset %s %s%.2f mm"
                   " is refused there if it starts the print (head offsets: Moonraker extruder_offset)"
                   % (m["line"], m["code"], m["room_mm"], m["axis"], m["axis"],
                      "below" if m["side"] == "-" else "above", m["side"], m["room_mm"]))
    if not r["errors"] and not r["scars"] and not r.get("drags"):
        out.append("clean: firmware accepted every command, no travel across a finished surface")
    return "\n".join(out)


def render(r):
    part = "".join('<rect x="%d" y="%d" width="2" height="2"/>' % (x * 2, BED - y * 2 - 2)
                   for x, y in r.get("footprint", []))
    lines = "".join(
        '<line x1="%s" y1="%s" x2="%s" y2="%s"/>'
        % (s["from"][0], BED - s["from"][1], s["to"][0], BED - s["to"][1])
        for s in r["scars"]
    )
    rows = "".join(
        "<tr><td>%d</td><td>%s</td><td>%s</td><td>%.2f</td><td>%.1f</td><td>%.2f</td></tr>"
        % (s["line"], s["source"], s["tool"], s["z"], s["length_mm"], s["clearance_mm"])
        for s in r["scars"]
    )
    errors = "".join("<p class=err>Line %d: %s</p>" % (e["line"], html.escape(e["message"])) for e in r["errors"])
    errors += "".join("<p class=err>%s</p>" % html.escape(d) for d in drag_lines(r))
    table = ("<table><tr><th>G-code line</th><th>Issued by</th><th>Tool</th><th>Z</th>"
             "<th>Length over surface (mm)</th><th>Clearance (mm)</th></tr>%s</table>" % rows) if rows else "<p>No scars.</p>"
    return """<!doctype html><meta charset=utf-8><title>u1-dryrun: %s</title>
<style>body{font:15px/1.5 system-ui;max-width:900px;margin:2em auto;padding:0 1em}svg{border:1px solid #888;background:#fafafa;max-width:420px;width:100%%}
line{stroke:#c0392b;stroke-width:1}rect{fill:#b8c4cc}table{border-collapse:collapse;margin-top:1em}td,th{border:1px solid #ccc;padding:.3em .6em}.err{color:#c0392b;font-weight:600}</style>
<h1>%s</h1><p>%d moves, %d tool changes.</p>%s
<svg viewBox="0 0 %d %d" role=img aria-label="Top view of the bed: the part in grey, scar paths in red">%s%s</svg>%s"""  % (
        html.escape(r["file"]), html.escape(r["file"]), r["moves"], r["tool_changes"], errors, BED, BED, part, lines, table)
