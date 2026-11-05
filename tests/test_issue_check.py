import gzip
import io
import os
import sys
import tempfile
import unittest
import zipfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "tools"))
import issue_check  # noqa: E402

# What GitHub writes into the issue body from .github/ISSUE_TEMPLATE/check-a-file.yml
FORM = """### File

[helado.zip](https://github.com/user-attachments/files/123/helado.zip)

### Firmware

2.0.0

### What happened when you printed it (optional)

_No response_
"""
GCODE = b";LAYER_CHANGE\nG1 X20 Y20 Z0.2\n"


def zipped(members):
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        for name, data in members.items():
            z.writestr(name, data)
    return buf.getvalue()


class IssueCheckTest(unittest.TestCase):
    def test_reads_link_and_firmware_from_the_form(self):
        self.assertEqual(issue_check.link(FORM), "https://github.com/user-attachments/files/123/helado.zip")
        self.assertEqual(issue_check.firmware(FORM), "2.0.0")

    def test_unknown_firmware_falls_back_to_the_default_and_never_reaches_the_shell(self):
        self.assertEqual(issue_check.firmware("### Firmware\n\n2.0.0; rm -rf /\n"), "2.1.0")
        self.assertEqual(issue_check.firmware("no form here"), "2.1.0")

    def test_no_link(self):
        self.assertIsNone(issue_check.link("### File\n\n_No response_\n"))

    def test_unpack_each_kind_of_upload(self):
        three_mf = zipped({"Metadata/plate_1.gcode": GCODE, "3D/3dmodel.model": b"x"})
        cases = {
            "plain": (GCODE, "input.gcode"),
            "gzip": (gzip.compress(GCODE), "input.gcode.gz"),
            "3mf": (three_mf, "input.gcode.3mf"),
            "zip with a gcode": (zipped({"readme.txt": b"hi", "dir/print.gcode": GCODE}), "input.gcode"),
            "zip with a 3mf": (zipped({"print.gcode.3mf": three_mf}), "input.gcode.3mf"),
        }
        for label, (data, want) in cases.items():
            with self.subTest(label), tempfile.TemporaryDirectory() as d:
                self.assertEqual(issue_check.unpack(data, d), want)
                self.assertTrue(os.path.getsize(os.path.join(d, want)) > 0)

    def test_zip_without_gcode_is_refused(self):
        with tempfile.TemporaryDirectory() as d, self.assertRaises(ValueError):
            issue_check.unpack(zipped({"photo.jpg": b"\xff\xd8"}), d)

    def test_reply_says_the_verdict_and_cannot_break_out_of_the_code_block(self):
        r = issue_check.reply("SCAR line 5 ```\n@someone", 1, "2.1.0", "https://run")
        self.assertIn("scar", r.splitlines()[0].lower())
        self.assertEqual(r.count("```"), 2)
        self.assertIn("https://run", r)
        self.assertIn("firmware 2.1.0", r)
        self.assertIn("did not finish", issue_check.reply("", -1, "2.1.0", "https://run"))


if __name__ == "__main__":
    unittest.main()
