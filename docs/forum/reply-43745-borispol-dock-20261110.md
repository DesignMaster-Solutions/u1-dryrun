@Mr.Borispol, I have to correct my last post, and you were right. Your heads do go through the models on the way to the tower.

The 0.40 mm I wrote about comes from reading the G-code as text. This time I ran your whole 22 hour file through the U1 firmware code, which knows where each head really is after a tool change, and that shows something the text hides.

What happens on your plate: the tower is at the right back corner. In 94 of the 187 tool changes, the slicer lowers the new head to the layer height right after picking it up, while it is still at its dock exit (X43.5, X94.2 or X161.7 at Y250), and only then sends it to the tower in a straight line. 74 of those trips cross your bunnies at the height of the layer just printed, 24 to 133 mm each, from the first layers up to Z42.85. First one is line 130636 at Z0.45. The other 92 tool changes go to the tower first and lower Z there, which is why only some models get hit.

Why it depends on the tower position: 2.4.1 added a detour that takes the head around the tower before it lowers. On your plate that detour would pass just outside the right edge of the bed (X270.9 on a bed that ends at 270.5), so the slicer drops it, but still acts as if the head had arrived at the tower. On 2.4.0 this detour did not exist.

Full list of the 74 lines: https://github.com/DesignMaster-Solutions/u1-dryrun/blob/main/docs/orca-2.4.1-dock-travel.md
Reported to Snapmaker with the cause in the code: https://github.com/Snapmaker/OrcaSlicer/issues/1168

Until it is fixed, staying on 2.4.0 is the safe choice. If you need 2.4.1, keep the tower at least about 10 mm away from the left and right edges of the bed (on this plate, X around 220 instead of 230.9). That follows from the code; I have not sliced or printed it to confirm.
