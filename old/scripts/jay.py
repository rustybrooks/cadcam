#!/usr/bin/env python
from campy import *

import os
basedir = os.path.dirname(os.path.realpath(__file__))

size = 5
segments = []
thickness = 3/8.

def geometry(diameter=0, rotation=None, sides=0, center=(0, 0)):
    geom = []

    def point(angle):
        return [
            center[0] + (diameter/2.0)*math.sin(math.radians(angle)),
            center[1] + (diameter/2.0)*math.cos(math.radians(angle)),
        ]

    angle_incr = 360.0/sides
    if rotation is None:
        rotation = -angle_incr/2.0

    geom.append(point(rotation))
    for angle in frange(rotation + angle_incr, 360+rotation, angle_incr):
        geom.append(point(angle))

    #print geom
    return geom

tool = tools['1/16in spiral upcut']
Camtainer('jay.ngc', [
    RectStock(6, 6, 3/8., origin=(-1, -thickness, -1)),
    SVGProfile(
        tool, os.path.join(basedir, 'jay.svg'),
        (0, 0, 0), scale=1/150., depth=.08, offset=0.0, side='inner',
        material_factor=1, stepdown=0.03),
])

Camtainer('jay2.ngc',     CoordProfile(tool, geometry(size, 0, 6, center=(1.75, 1.75)), depth=thickness, start_height=thickness),)

