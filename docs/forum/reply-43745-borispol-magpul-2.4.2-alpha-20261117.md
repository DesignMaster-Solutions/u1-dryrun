@Mr.Borispol, @magpul, I sliced the first public build after 2.4.1, Snapmaker Orca 2.4.2-alpha (macOS, command line), and it is not safe to leave 2.4.0 yet for this problem.

The head still comes down at the dock on the tool changes where the prime tower is near an edge: KOI Fish 222 of 453, Bounding Bunny plate 3 94 of 186, the small right-edge plate 8 of 15. The counts are identical to 2.4.1. On the small plate the firmware replay still shows the head crossing the part at layer height, so #1168 is not fixed in this build, which matches the December plan.

One part did change: the final travel to the tower now lifts first. The two-colour sign that scratched in 2.4.1 comes out clean on the firmware replay (0 scars), and the release notes list that fix (#1149).

If you print with the tower near an edge, stay on 2.4.0 until the December build. I will slice both projects again then and post here.
