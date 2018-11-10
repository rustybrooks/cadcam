#!/usr/bin/env python

from campy import *

import os
basedir = os.path.dirname(os.path.realpath(__file__))

thickness = 3/8.

tool = tools['1/8in spiral upcut']
##Camtainer('svg_square_plain.ngc', [
#    RectStock(2.75, 2.5, thickness, origin=(0, -thickness, 0)),
#    SVGProfile(tool, os.path.join(basedir, 'square_plain.svg'), (0, 0, 0), scale=1/150., depth=.1, stepdown=0.1, offset=0.0, side='inner', material_factor=1),
#])

Camtainer('svg_square_ink.ngc', [
    RectStock(2.75, 2.5, thickness, origin=(0, -thickness, 0)),
    SVGProfile(tool, os.path.join(basedir, 'square_ink.svg'), (0, 0, 0), scale=1/100., depth=.1, stepdown=0.1, offset=0.0, side='inner', material_factor=1),
])