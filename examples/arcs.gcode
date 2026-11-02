; Regression: slicer arcs are G-code motion, not firmware tool changes.
G90
G1 X100 Y100 Z1 F3000
G2 X120 Y100 I10 J0 F1200
G3 X100 Y100 I-10 J0 F1200
