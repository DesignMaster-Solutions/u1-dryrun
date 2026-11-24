@CrazyIvan, thanks, that thread (44046) is where the start-block check came from, and your post made me close the gap it still had: the report only told you to go and compare the offsets yourself.

Now you can give it the offsets Moonraker shows (`extruder_offset`), one per head, and it answers for the head that actually runs the start block:

`python3 dryrun/run.py file.gcode --offset T3=0.05,-0.08`

On Doxpuppr's file from issue #4 it finds T3 at line 172 (`G0 X85 Y1`). With a Y offset of -0.08 mm the move goes to Y0.92 and the report says fine; with -1.3 mm it goes to Y-0.30 and says REFUSED, the print stops at line 172, which is the "Move out of range on Y axis" from 44046.

What it does not do: the GitHub issue form does not have an offsets field yet, so this is the command line only. It judges only the start-block line closest to a limit, not moves after a macro or in relative mode. Commit: https://github.com/DesignMaster-Solutions/u1-dryrun/commit/be478dd
