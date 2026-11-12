@magpul, good to hear the test print kept it on the tower. I have now done what I had not done yesterday: sliced with your tool change G-code (the .docx), "Wall gap" off, rectangle prime tower, Snapmaker Orca 2.4.1 command line, the small two-colour example, 15 tool changes.

| Tool change G-code | Tool change retraction | Un-retract written before the move to the tower |
|---|---|---|
| stock | 10 mm | 15 of 15 (2 mm the first, 10 mm the others) |
| yours | 5 mm | 15 of 15 (2 mm the first, 5 mm the others) |
| yours | 3 mm | 15 of 15 (2 mm the first, 3 mm the others) |

So in the file the order did not change. With yours at 5 mm the second tool change reads:

```
T0
G90
M106 P2 S178
M106 S255
M104 S215 T0
G1 Z.45 F30000
G1 E5 F1800
G1  X266.000 Y110.100 F30000
```

The un-retract is still the line before the travel. What changed is its length: it is your "retraction length (tool change)", so 5 mm instead of 10. That fits what you saw. The head retracted 5 mm when it was parked and gets 5 mm back at the dock, which mostly refills the nozzle, and the excess shows up at the tower. My guess is that the shorter retraction is what is helping you, and that the stock G-code with 3 to 5 mm would behave the same. I have not printed either, so your overnight print is the real answer.

One thing your settings do not change: with "Wall gap" off, 15 of 15 tool changes still lower the head at the dock and cross the plate at layer height (#1168). On a tall part with the tower behind it that is the nozzle dragging over the part, with or without a string. If you can share the sliced file of the overnight print, I will run it through the U1 firmware and tell you which travels touch.

Not done: nothing printed, and these three slices were read as text, not run through the firmware.
