@magpul, fair enough, keep the file. You do not need to send it. The counter is one Python file with nothing to install, and it prints only line numbers and Z heights, nothing of the model:

```
curl -LO https://raw.githubusercontent.com/DesignMaster-Solutions/u1-dryrun/main/tools/dock_drops.py
python3 dock_drops.py yourfile.gcode
```

It answers in a second: how many of the 246 tool changes lower the head at the dock, how many un-retract there, and how many mm of filament that is in total. On my small example at the stock 10 mm it says 15 of 15 and 142 mm. At your 5 mm that is 72 mm.

If you paste those lines in the morning with how the print came out, that is the comparison I cannot make without a printer. Good luck with the 8 hours.
