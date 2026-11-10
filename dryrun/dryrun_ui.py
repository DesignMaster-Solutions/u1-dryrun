"""Klipper extras module: starts the file as a print, the way the touchscreen does (--skip only).

Fed as console input (the default run), a file never enters the firmware's print state, and
what the U1 does after "Skip object" depends on it (Snapmaker/u1-klipper#22). Here the file goes
through the firmware's own virtual_sdcard: SDCARD_PRINT_FILE once klippy reports ready, and
klippy is asked to exit when the print ends (batch mode already exits on the first error).
Same approach as the U1 Fix Pack harness (fixpack_ui.py, same author, GPL-3.0).
"""
import os


class DryrunUI:
    def __init__(self, config):
        self.printer = config.get_printer()
        self.reactor = self.printer.get_reactor()
        self.requested = False
        self.printer.register_event_handler("klippy:ready", self._ready)

    def _ready(self):
        self.print_stats = self.printer.lookup_object("print_stats")
        # Loaded heads: batch mode has no pins, so each filament switch is told "present"
        # through the firmware's own pin-event entry point. No runout timer runs.
        now = self.reactor.monotonic()
        for _, sensor in self.printer.lookup_objects("filament_motion_sensor"):
            sensor.encoder_event(now, True)
        # The auto-feed startup check calls the RFID reader, which batch mode cannot load.
        for _, feed in self.printer.lookup_objects("filament_feed"):
            if feed.filament_detect is None:
                self.reactor.update_timer(feed._check_init_state_timer, self.reactor.NEVER)
        self.reactor.register_timer(self._watch, self.reactor.NOW)

    def _watch(self, eventtime):
        if self.printer.get_state_message()[1] != "ready":
            return eventtime + 0.2
        if not self.requested:
            self.requested = True
            gcode = self.printer.lookup_object("gcode")
            self.reactor.register_callback(lambda e: gcode.run_script(
                # --map goes first: the firmware refuses it once the print has started
                os.environ.get("DRYRUN_BEFORE_PRINT", "") + "\nSDCARD_PRINT_FILE FILENAME=%s"
                % os.environ["DRYRUN_PRINT"]))
        # batch mode never waits on the MCU, so a whole print can run between two polls
        elif self.print_stats.state in ("complete", "cancelled", "error"):
            self.printer.request_exit("exit")
            return self.reactor.NEVER
        return eventtime + 0.2


def load_config(config):
    return DryrunUI(config)
