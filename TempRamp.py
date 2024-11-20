#!/usr/bin/python

# Cura or Super/Prusa/OrcaSlicer post processing script
# Author:   mhdm.dev
# Licence:  MIT https://opensource.org/license/MIT
#
# Description: Smooths out temperature increases over a few layers - the temperature ramps up by
# 1°C every few layers (configurable). To use, set the Printing Temperature for the initial layer to
# around 5-10 degrees lower than the Printing Temperature.
#
# Improves on issues affecting the first few layers: elephant's foot and glossy->matte transition
#
# Why it works: Compensates for the filament being deposited at a higher temperature in the first
# few layers. The causes for that are many. The first layer is printed slower which means more time
# for heat to transfer into the filament. The tip of the nozzle is not cooled as much by the part
# cooling fan as it's shielded by the bed and any air that does reach it will have been partially
# warmed already. Usually the slicers have the fan ramp up over the first few layers so there's even
# less airflow than usual. There's extra heat around as print itself is warmer: it's both shielded
# by and effectively heated by the bed.
#
# WARNING: Do NOT use for any prints with complicated temperature profiles like multi-material
# unless you manually verify every single M104 command in the output gcode is correct.
#
# Cura:
# Set "Initial Printing Temperature" to 5-10°C lower than "Printing Temperature"
#
# Super/Prusa/OrcaSlicer:
# In "Post-processing scripts" add: /path/to/TempRamp.py
# In Filament->Temperature->Extruder settings set "First layer" 5-10°C lower than "Other layers"

if __name__ == '__main__':
    # Standalone script
    from optparse import OptionParser
    parser = OptionParser()
    parser.add_option('--increase-by', type='float', default=1.0)
    (options, args) = parser.parse_args()
    class Script:
        def getSettingValueByKey(self, key):
            return options.__getattribute__(key)
else:
    # Cura API
    from ..Script import Script
    __version__ = '1.0'


class TempRamp(Script):

    def getSettingData(self):
        return {
            "name": "Temp Ramp",
            "key": "TempRamp",
            "metadata": {},
            "version": 2,
            "settings": {
                "increase_by": {
                    "label": "Increase amount each layer",
                    "description": "Increase nozzle temperature by this amount each layer",
                    "type": "float",
                    "minimum_value": 0.2,
                    "default_value": 1
                }
            }
        }

    def execute(self, data):
        increase_by = self.getSettingValueByKey('increase_by')

        target_temp = 0
        current_temp = 0
        for layer_i, layer in enumerate(data[:-2]):
            lines = layer.split('\n')

            for line_i, line in enumerate(lines):
                if line.startswith('M104 S'):
                    if current_temp == 0:
                        current_temp = float(line[6:])
                        target_temp = current_temp
                    else:
                        target_temp = float(line[6:])
                        if target_temp <= current_temp + increase_by:
                            current_temp = target_temp
                        else:
                            current_temp += increase_by
                            lines[line_i] = 'M104 S{}'.format(round(current_temp))

            if current_temp < target_temp:
                current_temp = min(current_temp + increase_by, target_temp)
                gcode = 'M104 S{}'.format(round(current_temp))
                lines[-1:-1] = [gcode]

            data[layer_i] = '\n'.join(line for line in lines if line is not None)

        return data

if __name__ == '__main__':
    with open(args[0]) as f:
        file = f.read()
    idx = file.find('; custom gcode: start_gcode')
    data = [file[0:idx]]
    while idx != -1:
        nidx = file.find(';LAYER_CHANGE\n', idx + 1)
        data.append(file[idx:nidx])
        idx = nidx
    idx = data[-1].rfind('; custom gcode: end_gcode')
    data[-1:] = [data[-1][0:idx], data[-1][idx:], '']

    TempRamp().execute(data)
    with open(args[0], 'w') as f:
        f.writelines(data)
