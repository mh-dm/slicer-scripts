#!/usr/bin/python

# Cura or Super/Prusa/OrcaSlicer post processing script
# Author:   mhdm.dev
# Licence:  MIT https://opensource.org/license/MIT
#
# Description: Slowly reduce the bed temperature over the last few layers of a print
#
# Allows you to take prints off the buildplate a bit earlier.
#
# Super/Prusa/OrcaSlicer:
# In "Post-processing scripts" add: /path/to/BedCool.py

if __name__ == '__main__':
    # Standalone script
    from optparse import OptionParser
    parser = OptionParser()
    parser.add_option('--num-final-layers', type='int', default=5)
    parser.add_option('--reduce-by', type='float', default=1.0)
    (options, args) = parser.parse_args()
    class Script:
        def getSettingValueByKey(self, key):
            return options.__getattribute__(key)
else:
    # Cura API
    from ..Script import Script
    __version__ = '1.0'


class BedCool(Script):

    def getSettingData(self):
        return {
            "name": "Bed Cool",
            "key": "BedCool",
            "metadata": {},
            "version": 2,
            "settings": {
                "num_final_layers": {
                    "label": "Number of final layers",
                    "description": "Number of final layers to affect",
                    "type": "int",
                    "minimum_value": 1,
                    "default_value": 5
                },
                "reduce_by": {
                    "label": "Reduce amount each layer",
                    "description": "Reduce by this amount the bed temp of each final layer",
                    "type": "float",
                    "minimum_value": 0.1,
                    "default_value": 1.0
                }
            }
        }

    def execute(self, data):
        num_final_layers = self.getSettingValueByKey('num_final_layers')
        reduce_by = self.getSettingValueByKey('reduce_by')

        num_layers = len(data)

        change_layer_start = (num_layers - 2) - num_final_layers
        current_bed_temp = 0
        for layer_i, layer in enumerate(data[:-2]):
            lines = layer.split('\n')
            for line in lines:
                if line.startswith('M140 S'):
                    current_bed_temp = round(float(line[6:]))

            if layer_i >= change_layer_start and current_bed_temp > 0:
                current_bed_temp -= reduce_by
                gcode = 'M140 S{}'.format(round(current_bed_temp))
                lines[1:1] = [gcode]

            data[layer_i] = '\n'.join(lines)

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

    BedCool().execute(data)
    with open(args[0], 'w') as f:
        f.writelines(data)
