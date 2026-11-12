#!/usr/bin/env python3
"""Check a file from a GitHub issue, for .github/workflows/check-file.yml.

  issue_check.py fetch DIR   reads the issue body from $BODY, saves the linked file in DIR and
                             prints ok=, name=, version= and ref= lines for $GITHUB_OUTPUT
  issue_check.py reply DIR   prints the Markdown reply from DIR/summary.txt, DIR/rc and, when
                             there, DIR/checks.txt (the output of tools/check.py)
                             ($VERSION and $RUN_URL come from the workflow)

The body is untrusted: only the whitelisted firmware and fixed file names ever leave this script.
"""
import gzip
import io
import os
import re
import sys
import urllib.request
import zipfile

FIRMWARE = {"2.1.0": "7ac453b", "2.0.0": "93cb12f"}  # same commits as ci.yml and the Dockerfile
DEFAULT = "2.1.0"
MAX_BYTES = 100 * 1024 * 1024
FETCH_FAILED = -2  # rc when the file never reached the firmware
URL = re.compile(r"https://[^\s()<>\"'\[\]]+")


def section(body, title):
    m = re.search(r"^### %s\s*$(.*?)(?=^### |\Z)" % re.escape(title), body, re.M | re.S)
    return m.group(1) if m else body


def link(body):
    m = URL.search(section(body, "File"))
    return m.group(0) if m else None


def firmware(body):
    m = re.search(r"^### Firmware\s+(\S+)\s*$", body, re.M)
    return m.group(1) if m and m.group(1) in FIRMWARE else DEFAULT


def unpack(data, dest):
    """Save the upload as a file u1-dryrun reads; returns its name inside dest."""
    if data[:2] == b"\x1f\x8b":
        name, out = "input.gcode.gz", data
    elif data[:4] == b"PK\x03\x04":
        z = zipfile.ZipFile(io.BytesIO(data))
        names = z.namelist()
        if any(n.startswith("Metadata/") and n.endswith(".gcode") for n in names):
            name, out = "input.gcode.3mf", data
        else:
            inner = next((n for n in names if n.lower().endswith((".gcode", ".gco", ".3mf"))), None)
            if inner is None:
                raise ValueError("the zip has no .gcode or .gcode.3mf inside")
            return unpack(z.read(inner), dest)
    else:
        name, out = "input.gcode", data
    with open(os.path.join(dest, name), "wb") as f:
        f.write(out)
    return name


def download(url):
    req = urllib.request.Request(url, headers={"User-Agent": "u1-dryrun-issue-check"})
    with urllib.request.urlopen(req, timeout=120) as r:
        data = r.read(MAX_BYTES + 1)
    if len(data) > MAX_BYTES:
        raise ValueError("the file is over 100 MB")
    return data


def reply(summary, rc, version, run_url, checks=""):
    if rc == FETCH_FAILED:
        return ("**I could not read the file:** %s.\n\nEdit this issue (attach the zipped file or fix the link) "
                "and the check runs again." % summary.strip()[:2000])
    verdict = {
        0: "**Clean.** The firmware accepted every command and no travel crosses a finished surface.",
        1: "**Scar found.** At least one travel crosses a surface that is already printed, with no clearance.",
        2: "**The firmware rejected this file.** It would stop the print at the line below.",
    }.get(rc, "**The check did not finish.** Nothing below is a verdict on the file.")
    summary = summary.replace("```", "'''")[:55000]
    text = ""
    if checks.strip():
        text = ("\n\nSeparately, four checks that read the file as text, with no firmware (`tools/check.py`). They look "
                "for patterns owners have reported on the forum and say nothing about a scar:\n\n"
                "```\n%s\n```" % checks.replace("```", "'''").strip()[:5000])
    return (
        f"{verdict}\n\n"
        f"Run through Snapmaker's u1-klipper, firmware {version}, in batch mode:\n\n"
        f"```\n{summary.strip()}\n```\n\n"
        f"The full report (`report.html`, with a map of every scar) is the `report` artifact of "
        f"[this run]({run_url}).\n\n"
        "A scar is a geometric prediction, not a measurement: there is no heating, ooze or sensor here, and "
        "the start block before the first layer does not run. If you printed this file, please say below "
        "whether this matches what you saw on the U1, either way." + text
    )


def main(cmd, d):
    os.makedirs(d, exist_ok=True)
    if cmd == "fetch":
        body = os.environ.get("BODY", "")
        version = firmware(body)
        url = link(body)
        try:
            if url is None:
                raise ValueError("no link found: drag the zipped file into the File box, or paste a public link")
            name = unpack(download(url), d)
            ok = "true"
        except Exception as e:  # every failure becomes the reply, never a silent red run
            with open(os.path.join(d, "summary.txt"), "w") as f:
                f.write(str(e))
            with open(os.path.join(d, "rc"), "w") as f:
                f.write(str(FETCH_FAILED))
            name, ok = "", "false"
        print("ok=%s\nname=%s\nversion=%s\nref=%s" % (ok, name, version, FIRMWARE[version]))
    elif cmd == "reply":
        with open(os.path.join(d, "summary.txt")) as f:
            summary = f.read()
        with open(os.path.join(d, "rc")) as f:
            rc = int(f.read().strip() or -1)
        checks = ""
        if os.path.exists(os.path.join(d, "checks.txt")):
            with open(os.path.join(d, "checks.txt")) as f:
                checks = f.read()
        print(reply(summary, rc, os.environ.get("VERSION", DEFAULT), os.environ.get("RUN_URL", ""), checks))
    else:
        sys.exit(__doc__)


if __name__ == "__main__":
    main(*sys.argv[1:3])
