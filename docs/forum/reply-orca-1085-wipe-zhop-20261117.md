I ran your second table on the two official macOS builds (2.4.2-alpha and 2.4.1, command line, same project from this issue, no filament sets either value). It reproduces on both, so this part is older than the alpha, unlike row 3 of the retraction table.

| setting | printer value, heads 1 to 4 | `filament_flow_step_size` | head 4 on 2.4.1 | head 4 on 2.4.2-alpha | expected |
|---|---|---|---|---|---|
| `wipe_distance` (longest wipe path) | 1,2,3,4 | 2,1,1,1 | 1 mm | 1 mm | 4 mm |
| `wipe_distance` | 1,2,3,4 | 1,1,1,1 | not run | 4 mm | 4 mm |
| `z_hop_types` (spiral arcs, `G2/G3` with Z) | Normal, Normal, Normal, Spiral | 2,1,1,1 | 0 | 0 | spiral |
| `z_hop_types` | Normal, Normal, Normal, Spiral | 1,1,1,1 | not run | 81 | spiral |
| `z_hop_types` | Spiral, Normal, Normal, Normal | 2,1,1,1 | not run | 81 | no spiral |

Head 1 is right in every row (1 mm wipe; 0 spiral arcs, or 697 in the last row where it is the spiral head). The 0 and 81 are the same counts you got on your build. The last row is the mirror of yours: with spiral only on head 1, head 4 lifts in spirals too, so head 4 is taking head 1's value, the same fallback as row 3.

How I measured: per head, the XY path between `; WIPE_START` and `; WIPE_END` (longest one), and the number of `G2`/`G3` lines that carry a Z.

What I did not do: I did not build your patch or PR #1194, nothing was printed, GUI and Windows/Linux not tried, and I only ran head 1 and head 4 because the project uses those two.
