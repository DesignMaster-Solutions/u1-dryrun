I could reproduce the cause in the sliced file, without a printer.

I sliced a 38 mm block that changes filament at Z38 (colour only at the top, like your mask) with Snapmaker Orca 2.4.1, once with the regular prime tower and once with "No sparse layers". With the setting on, the tower only grows on layers that have a tool change, so when the second colour finally starts at layer 189 the tower is still one layer tall. The file then sends the new head down to the tower's own height: `G1 Z.2`, while the part already stands 37.85 mm tall on the same bed. That matches what you found, the head next to the print at about bed height. With the regular tower the same project keeps the tower level with the part.

I added a small check for it, a Python script with no dependencies that reads the sliced file and says when the tower is printed far below the part: https://github.com/DesignMaster-Solutions/u1-dryrun/blob/main/tools/tower_below_print.py

```
$ python3 tower_below_print.py no-sparse-layers-orca-2.4.1.gcode.gz
TOWER BELOW PRINT: 1 time(s); worst at line 18936: the tower is printed at Z0.2 while the part is already printed up to Z37.85 (37.65 mm lower).
```

The project and the sliced file are in the repository's `examples/` folder, so anyone can repeat it.

Limits: this is my own test block, not your mask, and I have not printed it. The script compares heights; it does not model the shape of the toolhead, so it cannot tell how close a given print gets to an actual collision. If you still have the sliced file of the mask and can share it, I can run it and tell you the line where it goes down.
