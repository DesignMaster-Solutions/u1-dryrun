# Snapmaker Orca 2.4.1: no Z-hop before the final purge

The nozzle drags across the finished top layer on the last trip to the prime tower. Reported by a U1 owner in
[this forum topic](https://forum.snapmaker.com/t/43865): 2.4.0 lifts 0.40 mm before that trip and does not scratch,
2.4.1 goes at print height. Line numbers below are at tag `v2.4.1` of
[Snapmaker/OrcaSlicer](https://github.com/Snapmaker/OrcaSlicer) unless they say otherwise.

**Workaround today:** [`tools/lift_final_purge.py`](../tools/lift_final_purge.py) adds a Z-hop around that one travel.

## What changed

`src/libslic3r/GCode.cpp`, `WipeTowerIntegration::append_tcr2()`, in commit `b626b4be6` ("Feature sync gitlab to github main", #937):

```cpp
// v2.4.0, line 748
if (should_travel_to_tower || gcodegen.m_need_change_layer_lift_z) {

// v2.4.1, line 812 (same on main at f5fd7289e)
if (!tcr.priming && (tcr.is_finish_first || will_go_down)) {
```

`should_travel_to_tower` is still computed at line 834, but nothing reads it any more.

## Why only the last tool change

- The final purge comes from `WipeTowerIntegration::finalize()`, which calls `append_tcr2(gcodegen, m_final_purge, -1)`.
  It is built with `is_finish_first = false` (`WipeTower2.cpp` 1817, then 1387) and `finalize()` has already moved
  to the purge height, so `will_go_down` is false. The new condition is false, so nothing lifts or travels there.
- Real tool changes get their lift elsewhere: `toolchange_retract_str` is delivered through the
  `[change_filament_gcode]` placeholder (`GCode.cpp` 964), and the tower only writes that placeholder inside
  `toolchange_Change()` (`WipeTower2.cpp` 2327). The final purge has none, so its first move is the bare
  `G1 X.. Y.. F30000` of the tower G-code, at print height.

## Measured in G-code

| File | What happens before the final purge |
|---|---|
| [`helado-pipewrx-orca-2.4.1`](../examples/helado-pipewrx-orca-2.4.1.gcode.gz) (the print that scratched) | Line 130731 `G1  X17.984 Y139.987 F30000` at Z12.05, straight after the last extrusion at X132.503 Y137.672. The retraction comes after it, at line 130739. |
| [`sign-orca-2.4.1`](../examples/sign-orca-2.4.1.gcode.gz) | `G1  X19.842 Y224.850 F30000` at Z3.05, the last object layer. No lift. |
| [`sign-orca-2.4.0`](../examples/sign-orca-2.4.0.gcode.gz) | `G1 X63.037 Y150.93 Z3.65`, `G1 X32.75 Y238.85 Z3.65`, `G1 Z3.25`, `G1 E2`, then the purge at Z3.25. |

Same settings on both sign files: `z_hop = 0.4`, `z_hop_types = Auto Lift`.

## Proposed fix in the slicer (not built yet)

```diff
--- a/src/libslic3r/GCode.cpp
+++ b/src/libslic3r/GCode.cpp
@@ append_tcr2
     const bool will_go_down = !is_approx(z, current_z);
-    if (!tcr.priming && (tcr.is_finish_first || will_go_down)) {
+    // The final purge (new_extruder_id == -1) has no [change_filament_gcode], so nothing else lifts
+    // before its first move. Also honour a pending layer-change lift, as v2.4.0 did.
+    const bool is_final_purge = new_extruder_id < 0;
+    if (!tcr.priming && (tcr.is_finish_first || will_go_down || is_final_purge || gcodegen.m_need_change_layer_lift_z)) {
```

`!needs_toolchange` cannot be the test: `need_toolchange(unsigned)` receives -1 as 0xFFFFFFFF and returns true.

How a build of the fix is judged: slice the same plate with the patched build and with the same source
without the patch, then run `python3 tools/ab_final_purge.py base.gcode patched.gcode`. It passes only if
the base still has the bare travel into the final purge, the patched file does not, and every other tool
change block is identical line for line. The fork builds both on Linux
([patched](https://github.com/DesignMaster-Solutions/OrcaSlicer/actions/runs/41959375186),
[base f5fd7289e](https://github.com/DesignMaster-Solutions/OrcaSlicer/actions/runs/41965190378)).

## Not proven

- Why 2.4.0 stayed safe looks like this, from reading the code: there the final purge landed one layer higher
  (Z3.25 over the last object layer at Z3.05), so `finalize()` called `change_layer()`, which sets
  `m_need_change_layer_lift_z`, and that term of the old condition produced the lifted travel. Why 2.4.1 keeps the
  purge on the same layer was not traced.
- The patch has not been compiled yet. Its expected G-code comes from reading the code.
