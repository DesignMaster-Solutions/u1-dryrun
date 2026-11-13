# U1 tool change pauses: what the code `0002-0523-HHHH-CCCC` says

Read from the U1 firmware source, not measured on a printer: Snapmaker/u1-klipper at 7ac453b ("firmware 2.1.0"), `klippy/kinematics/extruder.py` and `klippy/extras/park_detector.py`. Written for forum topic 44234 (a bang, then a pause on tool change).

## The three sensors of each head

Each head has a `[park_detector extruderN]` with three inputs: `park_pin` (the head is in its dock), `active_pin` (the head is on the carriage) and `grab_valid_pin`. The firmware prints them as three letters, T or F, in that order, for example `[FTT]`.

- parked = park T, active F
- picked = park F, active T
- anything else is `UNKNOWN`

At a tool change the firmware reads them before parking, after parking, before picking and after picking. Each check is repeated up to 10 times; if it still fails the print pauses with `0002-0523-HHHH-CCCC`, where `HHHH` is the head (0 to 3) and `CCCC` is the case below.

To read the sensors yourself, in the Fluidd console: `QUERY_PARK_STA NAME=extruder` (or `extruder1`, `extruder2`, `extruder3`). It answers with the state and the three pins.

## The cases

| CCCC | When | Firmware message |
|---|---|---|
| 0007 to 0017 | before the change | more than one head reads as picked (`multi-act`); the number says which pair or group |
| 0018 | before the change | some head reads `UNKNOWN` |
| 0040 | before the change | head `HHHH` reads as detached (park F, active F) |
| 0041 | before the change | head `HHHH` reads parked and picked at once |
| 0019 | before parking | the head on the carriage does not read as picked |
| 0020 | after parking | the head just parked does not read as parked |
| 0042 | after parking | failed to return to park position (`[FTT]` or `[FTF]`) |
| 0043 | after parking | detached (`[FFT]` or `[FFF]`) |
| 0044 | after parking | parked and picked at once (`[TTT]` or `[TTF]`) |
| 0021 | before picking | the head to pick does not read as parked |
| 0022 | after picking | another head reads as picked instead of the target |
| 0023 | after picking | no head reads as picked (all read parked) |
| 0024 to 0034 | after picking | more than one head reads as picked |
| 0035 | after picking | some head reads `UNKNOWN` |
| 0045 | after picking | pogo pins of head `HHHH` not connected (`[FFT]`) |
| 0046 | after picking | head `HHHH` detached (`[FFF]`) |
| 0047 | after picking | head `HHHH` parked and picked at once |

0040 to 0047 are only used when `grab_hall_sensor_type` is on (the default in this source); with it off the same failures come out as 0018, 0020 and 0035.

## Limits

- Source reading only. Which text the touchscreen shows for each code is not in this repository, so "Toolhead swapping anomaly" is not mapped to one row here.
- The codes say which sensor reading was wrong, not why (a head that did not seat, a dirty contact, a move that hit something on the way).
- A sliced file can be ruled in or out separately: `dryrun file.gcode` replays it on this same firmware and reports any commanded move out of range or through printed material.
