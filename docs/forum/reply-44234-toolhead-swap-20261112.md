I can't tell you the cause from here, but I can tell you what the firmware is checking when it stops, which may narrow it down.

I read the tool change code of the U1 firmware (Snapmaker/u1-klipper, release 2.1.0). Each head has three sensors: one says "I am in my dock", one says "I am on the carriage", one confirms the grab. At every tool change the firmware reads them before parking, after parking, before picking and after picking. If the readings are not exactly "one head on the carriage, the others in their docks" after 10 tries, the print pauses with a code that starts with `0002-0523`. The last four digits say which check failed (for example 0042 = the head did not return to its dock, 0023 = no head was picked, 0045 = pogo pins not connected), and the four before them say which head (0 to 3).

So two things would help a lot:

1. The full code shown with the message (or in the Fluidd console at the moment it stops). I wrote down what each one means here: https://github.com/DesignMaster-Solutions/u1-dryrun/blob/main/docs/toolhead-swap-codes.md
2. In the Fluidd console, with the printer idle, `QUERY_PARK_STA NAME=extruder` (and `extruder1`, `extruder2`, `extruder3`). Each answers with its state and the three sensors. A docked head that does not answer "PARKED" is the one to look at.

About the bang: is it always the same head, and does it happen while the head is being picked up or dropped at the back, or in the middle of the plate? If it is always the same head at the dock, that points to that head or its dock. If it happens with different heads, or the file is new since the snow leopard, share the sliced file and the slicer version and I will run it through the same firmware on my side and tell you whether the file itself commands a move that goes out of range.

Limits: this comes from reading the source, I have not reproduced your stop, and I don't know which code the screen text "Toolhead swapping anomaly" corresponds to.
