The first half of this can be had today, and I measured what the firmware does with it.

The slicer labels each model as an object the U1 can skip, but not the prime tower, so when the tower comes off the bed there is nothing to pick on the screen. I wrote a small post-processing script that labels the tower as an object called `prime_tower` and changes nothing else in the file: https://github.com/DesignMaster-Solutions/u1-dryrun/blob/main/tools/skippable_tower.py (Python 3, no dependencies; run it on the sliced file, or add it in Orca under Others > Post-processing scripts).

I ran it through the U1 firmware code offline (U1 Dry Run, no printer) on a two-colour sign sliced with Snapmaker Orca 2.4.0, 15 tool changes:

- Labelled and not skipped: same result as the original file, clean.
- Tower skipped at layer 8: the firmware finishes the print and does all 15 tool changes, with 187 mm less filament. One problem shows up: at the last tool change the head's move to the dock crosses 37.5 mm of the finished top surface at print height, because the lift the slicer does on the way to the tower is skipped together with the tower.

What it does not give you is the second half of the request, purging somewhere else. After the skip each head starts on the part without priming, so expect a weak start after every tool change. Where that lands in infill or on a hidden side, it may still beat losing a long print.

Limits: this is the firmware run offline. Nobody has skipped a tower on a real U1 with it yet. If you try it, I would like to hear what the first lines after a tool change look like.

**Update, 11 November, a few hours later.** That scar was my script's fault, not the firmware's. The first version put the retract, the 1.5 mm lift and the `T` command that the slicer writes before each tool change inside the tower object, so skipping the tower dropped the lift too. The tower object now starts after the tool change ([commit b6ca3f1](https://github.com/DesignMaster-Solutions/u1-dryrun/commit/b6ca3f1)). Same file, tower skipped at layer 8: the run is clean, 15 tool changes, 197 mm less filament, no travel across a finished surface. If you took the script before this update, take it again. The limits above still stand: firmware run offline, not tried on a printer.
