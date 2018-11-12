#!/usr/bin/env python

import sys, os
if __name__ == '__main__' and __package__ is None:
    from os import sys, path
    sys.path.append(path.dirname(path.dirname(path.abspath(__file__))))
    from campy import *
else:
    from .campy import *

width = 3
height = 3
thickness = .75
offset = 0


def spoil_holes():
    nut = holes.nuts['rivnut-1/4-20']

    for x in range(1, width, 2):
        for y in range(1, height, 2):



machine = set_machine('k2cnc')
machine.max_rpm = 15000
machine.min_rpm = 15000
machine.set_material('mdf')
machine.set_tool('1/4in spiral upcut')
machine.set_file('ngc/spoil/spoil_holes.ngc')
rect_stock(width, height, thickness)
spoil_holes()

machine.set_file('ngc/spoil/spoil_face.ngc')
rect_pocket((-offset, -offset), (width+offset, width+offset), z=0, depth=0.02, stepover='50%', stepdown='50%', type='x')
