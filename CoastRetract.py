#!/usr/bin/python

# Cura or Super/Prusa/OrcaSlicer post processing script
# Author:   mhdm.dev
# Licence:  MIT https://opensource.org/license/MIT
#
# Turns a 'coast' followed by a retract into a combined coast-retract move. Imagine printing one
# (perimeter) loop. With coasting the extrusion stops slightly before the nozzle completes the full
# loop. This is either configured through coasting settings (Cura) or with the "Seam gap" setting.
# Also supports combining wipes with retracts.
#
# Why this improves quality:
# 1) Each retract has some associated oozing which would result in a big blob in a single spot.
# Making the retract happen as the head moves over a small distance reduces that blob's appearance.
# 2) A single combined move is significantly faster than two separate moves which means less time
# for oozing. Especially so when accounting for acceleration time.
# 3) Coasting rather than Wiping: Even with a perfectly tuned Linear/Pressure Advance there will be
# some oozing at the end of a print move. Coasting compensates while Wiping can only spread it out.
#
# Requires "Relative Extrusion" (Cura) / "Use relative E distances" (rest) to work!
#
# Important: Enable Linear/Pressure Advance and tune it first! Your tuned retraction distance should
# significantly under 3mm, even on bowden.
#
# Cura:
# Option 1:
# Turn "Enable Coasting" on and try a "Coasting Volume" of around 0.015 mm^3, which is equivalent to
# a coast distance of 0.015/0.2/0.5 = 0.15mm when using 0.2 line height and 0.5 line width.
# Set "Outer Wall Wipe Distance" to 0, because Cura emits moves in
# coast -> wipe -> retract order instead of coast -> retract -> wipe and doesn't offer an option.
# Warning: Cura's coasting is unreliable - it generates coasts only in most of the places it should
#
# Option 2:
# When Cura's coasting is too unreliable turn it off and set "Outer Wall Wipe Distance" to 0.2-0.6mm
# The script will then automatically combine wipes with retracts.
#
# Tip: If you still get bloby seams (the ones involving retractions!) try setting "Retraction Extra
# Prime Amount" to -0.25 mm^3. Cura will warn you but ignore it. This setting is equivalent to
# priming 0.1mm less than retracting. The blobs should be gone but you might get tiny pinholes in
# which case try around -0.1 mm^3 (and so on until you get the balance right).
# Warning: The first thing Cura adds to any print gcode is a retract. Check the output gcode to make
# sure your machine/start g-code wasn't unintentionally modified. If it was, just add this to the
# end of your start g-code:
# G92 E0 ; Reset Extruder
#
# SuperSlicer / OrcaSlicer:
# In "Post-processing scripts" add: /path/to/CoastRetract.py
# In Printer Settings -> Extruder [1] -> General wipe settings try setting:
# "Seam gap" to 0.15mm (and "for external perimeters" to 0)
# Turn on "Retract on layer change" to ensure SuperSlicer places retracts before Z moves and not
# after (which looks like a bug to me ..)
# Set "Wipe while retracting" to off. CoastRetract is faster which means less time for oozing.
# Set "Extra Wipe for external perimeters" to 0/off because it emits moves in
# coast -> wipe -> retract order instead of coast -> retract -> wipe and doesn't offer an option.
#
# If you only want wipe retract or you don't have coasting (Prusaslicer):
# In "Post-processing scripts" add: /path/to/CoastRetract.py
# Set "Wipe while retracting" to off. There's no good way to configure it to do a single simple
# combined wipe retract (also looks like a bug to me ..)
# Set "Extra Wipe for external perimeters" to 0.2-0.6 mm
#
# Tip: If you still get bloby seams (the ones involving retractions!) try setting "Extra length on
# restart" to -0.1 mm. The blobs should be gone but you might get tiny pinholes in which case try
# around -0.05 mm (and so on until you get the balance right).


import re

if __name__ == "__main__":
    # Standalone script
    from optparse import OptionParser
    parser = OptionParser()
    (options, args) = parser.parse_args()
    class Script:
        def getSettingValueByKey(self, key):
            return options.__getattribute__(key)
    class Logger:
        def log(level, message):
            print(level, message)

    retract_re = re.compile(r"^G1 E(-[0-9]+[.]?[0-9]*) F([0-9]+)")
    retract_amount_i = 0
    retract_speed_i = 1
    travel_re = re.compile(r"^G1 (.+)")
else:
    # Cura API
    from ..Script import Script
    from UM.Logger import Logger
    __version__ = '1.0'

    retract_re = re.compile(r"^G1 F([0-9]+) E(-[0-9]+[.]?[0-9]*)")
    retract_speed_i = 0
    retract_amount_i = 1
    travel_re = re.compile(r"^G[01] ?F?[0-9]* (.+)")


class CoastRetract(Script):

    def getSettingData(self):
        return {
            "name": "Coast Retract",
            "key": "CoastRetract",
            "metadata": {},
            "version": 2,
            "settings": {}
        }

    def execute(self, data):
        for layer_i, layer in enumerate(data):
            lines = layer.split("\n")
            for idx, line in enumerate(lines):
                match = retract_re.match(line)
                if not match:
                    continue
                for i in range(idx - 1, -1, -1):
                    if not lines[i].startswith('G'):
                        # Skip past comments or non-relevant instructions
                        continue
                    travel_match = travel_re.match(lines[i])
                    if lines[i].find(" E") != -1:
                        travel_match = None
                    break
                else:
                    continue
                if not travel_match:
                    continue

                amount = float(match.groups()[retract_amount_i])
                # In theory, we should increase the speed of the combined move. In practice, it doesn't
                # matter since sqrt(coast_distance^2 + retract_distace^2) ~= retract_distace
                speed = round(float(match.groups()[retract_speed_i]))

                # Combine into single move
                lines[i] = "G1 F{} {} E{:.3f}".format(speed, travel_match.groups()[0], amount)
                lines[i] = lines[i].rstrip('0').rstrip('.')
                lines[idx] = None

            data[layer_i] = "\n".join(line for line in lines if line is not None)

        return data

if __name__ == "__main__":
    with open(args[0]) as f:
        data = [f.read()]

    CoastRetract().execute(data)
    with open(args[0], "w") as f:
        f.writelines(data)
