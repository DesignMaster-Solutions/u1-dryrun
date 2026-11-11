# u1-dryrun

Run a sliced G-code file through Snapmaker's real U1 firmware code, on your laptop or in CI, with no printer attached. In seconds you learn whether the firmware would stop the print, and whether the nozzle would drag across a surface that is already finished.

It runs [Snapmaker/u1-klipper](https://github.com/Snapmaker/u1-klipper) in Klipper's batch mode with Snapmaker's own `printer.cfg`, kinematics, limits and tool-change code. There is no reimplementation of the firmware: if the firmware changes, rebuild against the new commit.

Entered in the Snapmaker Innovation Fund, Phase 2: [U1 Dry Run on the Snapmaker forum](https://forum.snapmaker.com/t/43986). The same firmware runner drives [U1 Fix Pack](https://github.com/DesignMaster-Solutions/u1-fixpack), which reproduces two open u1-klipper bugs and tests a patch for each.

**No install:** open a [Check a sliced file](https://github.com/DesignMaster-Solutions/u1-dryrun/issues/new?template=check-a-file.yml) issue, drag in your zipped `.gcode` or `.gcode.3mf` (or paste a public link), pick the firmware, and a bot answers in the issue in about 5 minutes with the same verdict and report. The file runs in a GitHub Actions container with no network. It becomes public in the issue, so only attach what you can share. To run it on your own machine instead:

```
$ docker build -t u1-dryrun https://github.com/DesignMaster-Solutions/u1-dryrun.git
$ docker run --rm -v "$PWD:/work" u1-dryrun my-print.gcode.3mf

sign-orca-2.4.1.gcode.gz: 34368 moves, 15 tool changes
motion time 7120 s (no heating), about 48 s of it firmware tool-change motion
  extruder: 27244 mm of filament
  extruder1: 5436 mm of filament
SCAR line 38910 (gcode, extruder1): [65.52, 143.71] -> [19.84, 224.85] at Z3.05 crosses 82.0 mm of finished surface, clearance 0.00 mm
```

Exit code: `0` clean, `1` scars, a dragged head or a head crossing the part on its way to the prime tower found, `2` the firmware rejected the file. A self-contained `report.html` and `report.json` land in `u1-dryrun-report/`.

Large plates work in a default Docker (8 GB): a 22 h 38 min farm plate shared by a U1 owner ([forum topic 43745](https://forum.snapmaker.com/t/43745/12): 223 MB, 8.8 million lines, 7,859,224 moves, 186 tool changes) runs whole in 7 minutes on a laptop. The time allowed grows with the file; a run that is still cut says `NOT FINISHED` and exits `2`, it is never reported clean (`-e U1_TIMEOUT_S=<seconds>` sets the limit by hand).

It reads files from Snapmaker Orca and from the official OrcaSlicer: real files from both are in [`examples/`](examples/) and run through the firmware on every push.

Releases: https://github.com/DesignMaster-Solutions/u1-dryrun/releases (zip of the runner, the tools, the Dockerfile and the GitHub Action, to build the image from a download instead of the repository URL). Project site: https://designmaster-solutions.github.io/u1-dryrun/.

### Installing Docker

- **macOS or Windows:** install Docker Desktop and start it once.
- **Linux (Ubuntu, Mint, Debian):**
  ```
  sudo apt install docker.io docker-buildx
  sudo usermod -aG docker $USER
  ```
  Then log out and back in, or reboot, so the group change applies. `docker version` should list both Client and Server without a permission error. `$USER` is typed as is; the shell fills in your login name.

Demo video, 2 minutes: https://designmaster-solutions.github.io/u1-dryrun/demo.mp4 (real output, synthetic voice). Sample reports from real runs: [Orca 2.4.0, clean](https://designmaster-solutions.github.io/u1-dryrun/sample/orca-2.4.0.html) [Orca 2.4.1, scar](https://designmaster-solutions.github.io/u1-dryrun/sample/orca-2.4.1.html), and [the 2.4.1 file that scratched a real print](https://designmaster-solutions.github.io/u1-dryrun/sample/pipewrx-helado-2.4.1.html).

## What it found first

In October a user reported on the forum that [Orca 2.4.1 scratches finished prints during the final toolchange, and 2.4.0 does not](https://forum.snapmaker.com/t/snapmaker-orca-2-4-1-nozzle-scratches-prints-during-final-toolchange-works-in-2-4-0/43865). They found it the expensive way: by printing, then comparing G-code by hand.

The same regression shows up here without a printer. Same model, same default U1 profiles, the two official slicer releases, both files in [`examples/`](examples/):

| Slicer | Last move before the final toolchange | Result |
|---|---|---|
| Snapmaker Orca 2.4.0 | lifts to Z3.65, then travels to the tower | clean, exit 0 |
| Snapmaker Orca 2.4.1 | travels to the tower at Z3.05, the height of the surface it just printed | `SCAR line 38910`, 82 mm of finished surface at 0.00 mm clearance, exit 1 |

**Workaround and cause.** [`tools/lift_final_purge.py`](tools/lift_final_purge.py) adds a Z-hop around that one travel and changes nothing else (Python 3, no dependencies). Run it on a sliced file, or add it in Orca under Others > Post-processing Scripts: `python3 /path/to/lift_final_purge.py;`. On the file that really scratched, the dry run goes from one scar to clean on firmware 2.0.0 and 2.1.0 ([report](https://designmaster-solutions.github.io/u1-dryrun/sample/pipewrx-helado-2.4.1-lifted.html)); a dry run cannot say what the nozzle does to the plastic, so this still needs a real print. What changed in the slicer, with the lines: [docs/orca-2.4.1-final-purge.md](docs/orca-2.4.1-final-purge.md). Snapmaker engineering confirmed the regression on 5 November 2026 and said it will be fixed in the next Snapmaker Orca version ([forum](https://forum.snapmaker.com/t/43865/10)). A Linux build of the slicer fix proposed in [#1149](https://github.com/Snapmaker/OrcaSlicer/issues/1149) slices the test plate clean on both firmwares, leaves every other tool change as it was, and puts the final purge back one layer up and unretracted, as 2.4.0 did; 2.4.1 runs it on top of the last tower layer ([A/B](docs/orca-2.4.1-final-purge.md#built-and-sliced-5-november-2026)).

The missing lift only hurts when the path crosses the part. On the small two-color coaster I tried first, the last extrusion was at the part's edge next to the tower and both versions came out clean. That is why a check on the real toolpath is better than reading the G-code for a `Z` word.

![Top view of the same part from both slicers: 2.4.0 lifts and travels clean, 2.4.1 drags 82 mm across the finished surface](docs/orca-2.4.0-vs-2.4.1.png)

As a fidelity check, the firmware's own motion time lands next to the slicer's estimate, computed by different code: 7120 s against 1h 59m 13s (7153 s) on 2.4.1, and 7264 s against 2h 1m 36s (7296 s) on 2.4.0.

## What it checks

- **Firmware errors.** Anything Klipper would stop on, such as `Move out of range`, a macro error or a bad parameter, with the G-code line. This uses the real limits from Snapmaker's config.
- **Surface scars.** A non-extruding move that crosses printed material with the nozzle within 0.05 mm of it (`--clearance`), for 5 mm or more, where that material is never covered later. Moves are read after the firmware processed them, so tool-change motion issued by the firmware counts too, and ramped lifts are followed along their slope. Prime tower and support material are ignored, because nobody keeps them; a travel that crosses the part itself while the slicer is printing support still counts. On the real file from [u1-klipper#22](https://github.com/Snapmaker/u1-klipper/issues/22) this removed three first-layer findings that were all travels over support. When the firmware stops the print, the layer in progress and the one below it are not checked: the layers that would have covered them never ran, and on that same file with two objects skipped they showed up as four scars that were ordinary same-layer travels.
- **A new head crossing the part on its way to the prime tower.** After a tool change the head should reach the tower lifted. If it travels at layer height through 5 mm or more of what the current layer has just printed, before its first tower extrusion, the report says `CROSSING line N` and exits 1, even though later layers cover the mark and it is not a scar. Found on a real 22 h plate from Snapmaker Orca 2.4.1 ([forum 43745](https://forum.snapmaker.com/t/43745/12), [OrcaSlicer#1168](https://github.com/Snapmaker/OrcaSlicer/issues/1168)): 52 of its 186 tool changes, 5.0 to 40.5 mm each, Z0.45 to Z42.85 ([details](docs/orca-2.4.1-dock-travel.md)). The sliced example files in this repo exit with the same code as before. Files without a prime tower are not checked for this.
- **Tool use.** Tool changes, filament per tool, and how much motion time the firmware's tool changes add.
- **What if I skip an object?** `--skip OBJECT@LINE` (repeatable) presses "Skip" on that object when the print reaches that line of the file, and runs the file as a real print through the firmware's own `virtual_sdcard`. On stock 2.0.0 and 2.1.0 the next filament-only move after a tool change can carry the skipped object's XY ([u1-klipper#22](https://github.com/Snapmaker/u1-klipper/issues/22)): the report shows it as `DRAG line N`, with where the head went and how much filament it pushed on the way, or as a firmware error if the target is off the bed. Try it: `examples/skip-then-toolchange.gcode` is clean, and with `--skip B@80` the chute prime at line 205 drags the head 70.7 mm across the bed. Object names are the file's `EXCLUDE_OBJECT_DEFINE NAME=` values; a wrong name lists them. Checked against a real print: on the file from the #22 report (stock 2.0.0, two objects skipped near line 311388, `--map T4=T3`) the Dry Run stops at line 319758 with `Move out of range on Y axis: 81.489 337.635 10.850`, the line and the Y the printer logged. The second file of that report (three objects skipped near lines 195168 and 195724) does not stop: `DRAG line 295270`, the head moved 222.4 mm from the chute to [28.11, 202.42] while pushing 10.0 mm of filament; the report from the printer says 222 mm, to about (28.1, 202.4). That run also lists 8 scars the same file does not have without the Skip: the travel into the object after a skipped one starts where the head stood before it and crosses finished parts on the way (at line 207895, the first, it starts 0.4 mm lower and 48 mm away instead of 8 mm). All 8 are the first move after the `EXCLUDE_OBJECT_END` of a skipped object (lines 207895, 215427, 315713, 322732, 392687, 401815, 421571, 507349). With the [U1 Fix Pack patch for #22](https://github.com/DesignMaster-Solutions/u1-fixpack/blob/main/patches/0022-exclude-object-manual-move.patch) mounted over the firmware's `exclude_object.py`, the same run has no `DRAG` and the same 8 scars ([both outputs](https://github.com/DesignMaster-Solutions/u1-fixpack/tree/main/docs/evidence/issue-22)), so they are a second effect of Skip that the #22 fix does not touch. The Fix Pack has a [second patch](https://github.com/DesignMaster-Solutions/u1-fixpack/blob/main/patches/0022b-exclude-object-lift-before-travel.patch) for it, which lifts where the head is before that first travel: with both mounted the same run is `clean`, with none of the 8 ([output](https://github.com/DesignMaster-Solutions/u1-fixpack/blob/main/docs/evidence/issue-22/dryrun-real-print-B-patched-0022b-2.1.0.txt)). That is what the firmware moved here; nobody has looked for the marks on a print.
- **What if the prime tower comes off the bed?** The slicer labels the models but not the tower, so there is nothing to skip on the screen ([forum topic 44109](https://forum.snapmaker.com/t/44109)). [`tools/skippable_tower.py`](tools/skippable_tower.py) labels the tower as the object `prime_tower` (Python 3, no dependencies; run it on a sliced file or add it in Orca under Others > Post-processing scripts) and changes nothing else: `examples/sign-orca-2.4.0.gcode.gz` is `clean` before and after it. Skipped at layer 8 with `--skip prime_tower@26495`, the firmware finishes the print, does all 15 tool changes and uses 187 mm less filament. One finding: at the last tool change the firmware's own move to the dock crosses 37.5 mm of the finished top at Z3.05 (`SCAR line 48402 (firmware)`), because the slicer's lift on the way to the tower went with the tower. After the skip the heads start on the part without priming, so expect a weak start after each tool change; whether that beats a lost print is the owner's call. Run through the firmware only; nobody has skipped a tower on a printer with it yet.
- **Files with more than four filaments.** The slicer numbers them T0 to T31 and the screen assigns each one to a head when the print starts. The file does not carry that choice, so pass it: `--map T4=T3` (repeatable) sends it to the firmware with its own `SET_PRINT_EXTRUDER_MAP`. Without it the firmware default applies (every filament above T3 on head 0) and the report says which filaments that was. Found on 9 November 2026 on a real file printed on a stock U1 with T1 and T4 ([u1-klipper#22](https://github.com/Snapmaker/u1-klipper/issues/22)): unmapped, the 3,686 mm of T4 were simulated on head 0; with `--map T4=T3` they are on `extruder3`, the head that printed them.

## How it works

1. `Dockerfile` builds the pinned `u1-klipper` commit (Snapmaker's firmware 2.1.0, released 4 November 2026; `--build-arg U1_KLIPPER_REF=93cb12f` builds 2.0.0, and CI runs every check on both) and generates the data dictionaries for its MCUs from Snapmaker's own Kconfig files.
2. `dryrun/prep_cfg.py` comments out the config sections that talk to hardware or services absent here (MQTT, RFID, accelerometers, physical homing). Everything else loads as shipped.
3. `dryrun/prep_gcode.py` tags each move with its line number, homes all axes before the first line, replaces the slicer's start block with `G28` and the first tool, and turns non-ASCII characters (the U1 start G-code has Chinese comments) into `_`, because Klipper's batch reader drops any 4 KB block that cuts a UTF-8 character.
4. `dryrun/dryrun_tracer.py` is a Klipper extras module. It records every `toolhead.move`, turns `G28` into "the axis is at its endstop", and simulates the dock: at the dock Y, sliding X onto a tool's park X releases it and sliding off grabs it. That lets the firmware's own `_cmd_SWITCH_EXTRUDER` run its full sequence and pass its own park and pick checks.
5. `dryrun/analyze.py` builds a height map from the extrusion moves and looks for travel across finished cells.

## What it does not do

**Field report, 2 November 2026.** A U1 owner ran it on Linux Mint on a vanilla OrcaSlicer file they had already printed without trouble ([their post](https://forum.snapmaker.com/t/u1-dry-run-test-a-sliced-file-on-the-real-u1-firmware-no-printer-needed/43986/19)): 1,038,009 moves accepted, 14,091 s of motion for a file named 4h7m (heating is not counted), clean. So a known-good print produced no false alarm on someone else's machine. Their first run also found a real bug, and their output exposed a second one (the [4 KB read](https://github.com/DesignMaster-Solutions/u1-dryrun/commit/786819e) and the [arc attribution](https://github.com/DesignMaster-Solutions/u1-dryrun/commit/6328497)), both fixed the same day.

**First check against a print that really scratched, 4 November 2026.** The user who reported the 2.4.1 regression shared the exact file they printed on their U1 when the nozzle rubbed the part during the final tool change ([their post](https://forum.snapmaker.com/t/43865/3): `helado paleta 2.4.1.gcode`, Snapmaker Orca 2.4.1, sliced 29 October). The tool flags one scar in it, the same on firmware 2.0.0 and 2.1.0: line 130731, inside the last `; CP TOOLCHANGE UNLOAD` block and on the last layer, the nozzle travels from the part (X132.5 Y137.7) to the prime tower (X18.0 Y140.0) at Z12.05 with no lift, across 10.0 mm of finished surface at 0.00 mm clearance, and the retraction only comes after that travel. That is the move they described: the final tool change, on the way to the tower, without enough Z lift ([report](https://designmaster-solutions.github.io/u1-dryrun/sample/pipewrx-helado-2.4.1.html)). They answered on 5 November ([their reply](https://forum.snapmaker.com/t/43865/7)): the scratch is consistent with this move, though they did not measure the exact position on the part, so the match stays by the kind of move and the moment it happens, not by a measured position. They also gave permission to keep the file here, so [`examples/helado-pipewrx-orca-2.4.1.gcode.gz`](examples/helado-pipewrx-orca-2.4.1.gcode.gz) now runs in `tests/e2e.sh` on both firmwares on every change. Their own comparison on this print: Orca 2.4.0 does a 0.40 mm Z-hop before that travel and does not scratch; 2.4.1 does not lift. If you have a U1 and a print that scratched, or one that failed mid-way, please run it and open an issue with the result, either way.

**Marked as the solution, 7 November 2026.** The user who reported the 2.4.1 regression marked [the post that traces the missing lift to the change in Orca's `append_tcr2` (PR #937) and links the upstream issue #1149](https://forum.snapmaker.com/t/43865/9) as the accepted answer in their topic, which then closed.

**Confirmed by Snapmaker, 11 November 2026.** On the upstream issue, a Snapmaker developer [answered](https://github.com/Snapmaker/OrcaSlicer/issues/1149#issuecomment-6787079927) that the move to the tower after the print is finished is unnecessary and will be removed in the November version of Snapmaker Orca. Until that version is out, the workaround above still applies. Not yet checked: no build with the change exists to replay.

- No physics: no heating, no ooze, no flow, no real sensors. Motion time excludes heating waits.
- Commands that wait on hardware are skipped and listed in every report: defect detection, timelapse, auto feed, flow calibration, bed mesh, chamber wait.
- The start block before the first `;LAYER_CHANGE` is not run, because nozzle wiping and probing need sensors and nothing is on the bed yet to scar. One thing about it is checked: the report names its explicit absolute X/Y target closest to a travel limit, and the head offset that target can take. The stock purge line `G0 X85 Y1` leaves 1.00 mm, so a head whose Y offset is below -1.00 mm stops the print right there ([forum topic 44046](https://forum.snapmaker.com/t/44046), reproduced on the real firmware in [u1-fixpack](https://github.com/DesignMaster-Solutions/u1-fixpack#start-line-refused-on-some-toolheads-forum-44046)). Compare it with your heads' `extruder_offset` in Moonraker. Moves after a macro or in relative mode are not guessed.
- A scar is a geometric prediction, not a measurement. A soft material or a warped part changes what really happens.

## Use it in CI

```yaml
- uses: DesignMaster-Solutions/u1-dryrun@main
  with:
    gcode: out/plate_1.gcode
```

The step fails on any scar or firmware error, which makes it a regression test for slicer forks, start-gcode changes and firmware mods.

## Development

```
python3 -m unittest discover -s tests   # analysis, no Docker
docker build -t u1-dryrun . && tests/e2e.sh   # real firmware on the example files
```

`examples/flatten_profiles.py` has the profile recipe used to slice the examples with the Snapmaker Orca command line. Its `wipe_tower_filament` removal works around a crash in the CLI when that key is set.

Built by [Design Master Solutions](https://www.designmastersolutions.com/) with AI coding assistance. GPL-3.0, like Klipper. Not affiliated with Snapmaker.
