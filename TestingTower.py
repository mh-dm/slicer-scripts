#!/usr/bin/python

# Cura or Super/Prusa/OrcaSlicer post processing script
# Author:   mhdm.dev
# Licence:  MIT https://opensource.org/license/MIT
#
# Description: Turn any print into a Testing Tower. With this script you can tune:
#              Speed/Feedrate
#              Travel and/or Print Acceleration
#              Retract/Prime Acceleration
#              Max E Acceleration
#              XY, Z or E Jerk
#              Junction Deviation
#              Lin Advance
#              Nozzle or Bed Temperature
#              Retract or Prime Speed
#              .. and more!
#
# Options involving priming or retracting REQUIRE "Relative Extrusion" (Cura) /
# "Use relative E distances" (other slicers) to work!
#
# Note that by default the first layer is not changed to avoid interfering with the setup, purging,
# skirts or brims, and to reduce the chance the print will detach from the buildplate.
#
# Super/Prusa/OrcaSlicer:
# In "Post-processing scripts" add:
# /path/to/TestingTower.py --command=A --start-value=B --value-change=C
#
# For example, if your print has 100 layers then:
# TestingTower.py --command=speed --start-value=101 --value-change=1
# would result in printing the layers at 100% (no change), 101%, 102%, ..., 199% speed.
#
# See all possible options in TestingTower.getSettingData().
#
# Inspired by script from https://github.com/5axes/Calibration-Shapes so thank you 5axes

import re

if __name__ == '__main__':
    # Standalone script
    class Script:
        def getSettingValueByKey(self, key):
            return args.__getattribute__(key)

    retract_re = re.compile(r'^G1 E(-[0-9]+[.]?[0-9]*) F([0-9]+)')
    prime_re = re.compile(r'^G1 E([0-9]+[.]?[0-9]*) F([0-9]+)')
    re_amount_i = 0
    re_speed_i = 1
else:
    # Cura API
    from ..Script import Script
    __version__ = '1.0'

    retract_re = re.compile(r'^G1 F([0-9]+) E(-[0-9]+[.]?[0-9]*)')
    prime_re = re.compile(r'^G1 F([0-9]+) E([0-9]+[.]?[0-9]*)')
    re_speed_i = 0
    re_amount_i = 1

class TestingTower(Script):

    def getSettingData(self):
        return {
            "name": "Testing Tower",
            "key": "TestingTower",
            "metadata": {},
            "version": 2,
            "settings": {
                "command": {
                    "label": "Command",
                    "description": "GCode Command",
                    "type": "enum",
                    "options": {
                        "speed": "Speed %",
                        "acceleration": "Print&Travel Acceleration mm/s^2",
                        "tacceleration": "Travel Acceleration mm/s^2",
                        "pacceleration": "Print Acceleration mm/s^2",
                        "racceleration": "Retract&Prime Acceleration mm/s^2",
                        "eacceleration": "E Max Acceleration mm/s^2",
                        "jerk": "XY Jerk mm/s",
                        "zjerk": "Z Jerk mm/s",
                        "ejerk": "E Jerk mm/s",
                        "junction": "Junction Deviation mm",
                        "lin-advance": "Linear advance mm/(mm/s)",
                        "nozzle-temp": "Nozzle Temp °C",
                        "bed-temp": "Bed Temp °C",
                        "retract-speed": "Retract speed mm/s",
                        "retract-distance": "Retract distance mm",
                        "prime-speed": "Prime speed mm/s",
                        "extra-prime": "Extra prime mm"
                    },
                    "default_value": "speed"
                },
                "start_value": {
                    "label": "Start value",
                    "description": "The start value for this test tower",
                    "type": "float",
                    "default_value": 100.0
                },
                "value_change": {
                    "label": "Value change",
                    "description": "How the value changes every (few) layer(s). Could be negative.",
                    "type": "float",
                    "default_value": 1.0
                },
                "start_layer": {
                    "label": "Start layer",
                    "description": "The test starts at this layer. Note 0 is the initial layer",
                    "type": "int",
                    "default_value": 1,
                    "minimum_value": 0,
                    "maximum_value_warning": 100
                },
                "change_value_every": {
                    "label": "Change Value Every ? Layers",
                    "description": "The value changes every this number of layers.",
                    "type": "int",
                    "default_value": 1,
                    "minimum_value": 1,
                    "maximum_value_warning": 100
                }
            }
        }

    def execute(self, data):
        command = self.getSettingValueByKey('command')
        start_value = self.getSettingValueByKey('start_value')
        value_change = self.getSettingValueByKey('value_change')
        change_value_every = self.getSettingValueByKey('change_value_every')
        start_layer = self.getSettingValueByKey('start_layer')
        # Offset for layer_i 0 being Cura's prelude and layer_i 1 being the printer Start G-code
        start_layer += 2

        current_value = start_value - value_change

        num_layers = len(data)
        current_prime = -1
        for layer_i, layer in enumerate(data[:-2]):
            if layer_i < start_layer:
                continue

            lines = layer.split('\n')
            if (layer_i - start_layer) % change_value_every == 0:
                current_value += value_change
                gcode = None
                if command == 'speed':
                    gcode = 'M220 S{}'.format(round(current_value))
                    lcd_gcode = 'M117 Speed ' + gcode
                    if layer_i == start_layer:
                        gcode = 'M220 B\n' + gcode
                elif command == 'acceleration':
                    gcode = 'M204 S{}'.format(round(current_value))
                    lcd_gcode = 'M117 Accel ' + gcode
                elif command == 'tacceleration':
                    gcode = 'M204 T{}'.format(round(current_value))
                    lcd_gcode = 'M117 TAccel ' + gcode
                elif command == 'pacceleration':
                    gcode = 'M204 P{}'.format(round(current_value))
                    lcd_gcode = 'M117 PAccel ' + gcode
                elif command == 'racceleration':
                    gcode = 'M204 R{}'.format(round(current_value))
                    lcd_gcode = 'M117 RAccel ' + gcode
                elif command == 'eacceleration':
                    gcode = 'M201 E{}'.format(round(current_value))
                    lcd_gcode = 'M117 EAccel ' + gcode
                elif command == 'jerk':
                    gcode = 'M205 X{:.2f} Y{:.2f}'.format(current_value, current_value)
                    lcd_gcode = 'M117 XYJerk ' + gcode
                elif command == 'zjerk':
                    gcode = 'M205 Z{:.2f}'.format(current_value)
                    lcd_gcode = 'M117 ZJerk ' + gcode
                elif command == 'ejerk':
                    gcode = 'M205 E{:.2f}'.format(current_value)
                    lcd_gcode = 'M117 EJerk ' + gcode
                elif command == 'junction':
                    gcode = 'M205 J{:.3f}'.format(current_value)
                    lcd_gcode = 'M117 Junction ' + gcode
                elif command == 'lin-advance':
                    gcode = 'M900 K{:.3f}'.format(current_value)
                    lcd_gcode = 'M117 Lin Adv ' + gcode
                elif command == 'nozzle-temp':
                    gcode = 'M104 S{}'.format(round(current_value))
                    lcd_gcode = 'M117 Nozzle Temp ' + gcode
                elif command == 'bed-temp':
                    gcode = 'M104 S{}'.format(round(current_value))
                    lcd_gcode = 'M117 Bed Temp ' + gcode
                elif command == 'retract-speed':
                    lcd_gcode = 'M117 Retract Speed {}'.format(round(current_value))
                elif command == 'retract-distance':
                    lcd_gcode = 'M117 Retract Dist {:.3f}'.format(current_value)
                elif command == 'prime-speed':
                    lcd_gcode = 'M117 Prime Speed {}'.format(round(current_value))
                elif command == 'extra-prime':
                    lcd_gcode = 'M117 Extra Prime {:.3f}'.format(current_value)

                lines[1:1] = [gcode, lcd_gcode] if gcode else [lcd_gcode]

            for line_i, line in enumerate(lines):
                if command == 'retract-speed':
                    match = retract_re.match(line)
                    if match:
                        lines[line_i] = 'G1 F{} E{}'.format(
                            round(current_value * 60), match.groups()[re_amount_i])
                elif command == 'retract-distance':
                    match = retract_re.match(line)
                    if match:
                        lines[line_i] = 'G1 F{} E{:.3f}'.format(
                            match.groups()[re_speed_i], -current_value)
                        current_prime = current_value
                        continue
                    match = prime_re.match(line)
                    if match:
                        if current_prime != -1:
                            lines[line_i] = 'G1 F{} E{:.3f}'.format(
                                match.groups()[re_speed_i], current_prime)
                elif command == 'prime-speed':
                    match = prime_re.match(line)
                    if match:
                        lines[line_i] = 'G1 F{} E{}'.format(
                            round(current_value * 60), match.groups()[re_amount_i])
                elif command == 'extra-prime':
                    match = prime_re.match(line)
                    if match:
                        prime_distance = float(match.groups()[re_amount_i]) + current_value
                        lines[line_i] = 'G1 F{} E{:.3f}'.format(
                            match.groups()[re_speed_i], prime_distance)

            if layer_i == num_layers - 3 and command == 'speed':
                lines.insert(-1, 'M220 R')

            data[layer_i] = '\n'.join(lines)

        return data

if __name__ == '__main__':
    from argparse import ArgumentParser
    parser = ArgumentParser()
    settings = TestingTower().getSettingData()['settings']
    parser.add_argument('--command', choices=settings['command']['options'], required=True)
    parser.add_argument('--start-value', type=float, required=True)
    parser.add_argument('--value-change', type=float, required=True)
    parser.add_argument('--start-layer', type=int, default=1)
    parser.add_argument('--change-value-every', type=int, default=1)
    # This is so ugly due to cpython->argparse issue 59330
    parser.add_argument(metavar='gcode-file', dest='gcode_file')
    args = parser.parse_args()

    with open(args.gcode_file) as f:
        file = f.read()
    idx = file.find('; custom gcode: start_gcode')
    data = [file[0:idx]]
    while idx != -1:
        nidx = file.find(';LAYER_CHANGE\n', idx + 1)
        data.append(file[idx:nidx])
        idx = nidx
    idx = data[-1].rfind('; custom gcode: end_gcode')
    data[-1:] = [data[-1][0:idx], data[-1][idx:], '']

    TestingTower().execute(data)
    with open(args.gcode_file, 'w') as f:
        f.writelines(data)
