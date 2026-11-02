# Arc motion attribution (2026-11-02)

CrazyIvan's forum post 43986/19 reported a clean run with zero tool changes but
12064 seconds attributed to firmware tool-change motion. The original file was
not available in this investigation, so its exact timing was not reproduced.

A minimal G2/G3 file reproduced the inconsistency in the pinned U1 firmware:
124 moves, zero tool changes, 3.6 seconds incorrectly attributed to firmware.
Klipper's arc handler calls gcode_move.cmd_G1 directly for each segment, bypassing
the registered G1 wrapper. Wrap G2/G3 as well and tag their original source lines.
Do not register unsupported commands when an optional handler is absent.

After the change the same fixture produces 124 moves, zero tool changes, zero
firmware-motion seconds, with segments attributed to the correct G2/G3 lines.
Existing straight moves and firmware tool-change motion retain their behavior.
The real-firmware regression runs in tests/e2e.sh on every push.
