[//]: # (Copyright 2024 Mihail Dumitrescu mhdm.dev)
[//]: # (Provided under "MIT Licence" terms.)
[//]: # (SPDX-License-Identifier: MIT)

# A small collection of slicer scripts

This is a small set of 3d printing slicer scripts to help improve the quality and/or speed of your prints. Scripts support Cura and/or SuperSlicer / OrcaSlicer / PrusaSlicer.
See the list of `.py` files and read the description inside.

## Cura instructions

The simplest way is to place the desired script into Cura's scripts folder. For example into `~/.local/share/cura/5.4/scripts` if using Cura version 5.4 on Linux.

Another way is to clone this repo into say `~/slicer-scripts`, delete `~/.local/share/cura/5.4/scripts`, then turn into a link with `ln -s -T ~/slicer-scripts ~/.local/share/cura/5.4/scripts`. On a minor point version update, Cura will make a full copy of the scripts folder so you'll need to redo the linking.

Unfortunately any changes to scripts only take effect on restart so you'll have to start Cura fresh then go to Extensions -> Post Processing -> Modify G-Code.

## SuperSlicer and co. instructions

Download the desired scripts or clone this repo.

In Print Settings -> Output options -> "Post-processing scripts" you'd add something like:
```
/path/to/CoastRetract.py
/path/to/TempRamp.py --increase-by=1.6
/path/to/ExampleScript.py --example-option=1 --other-option=speed
```

Note I only test on SuperSlicer so OrcaSlicer / PrusaSlicer support is theoretical.

## Contributing

For most of the scripts I'd rather the good options/changes make it into the slicers themselves so there's less of a need to write / maintain scripts.
