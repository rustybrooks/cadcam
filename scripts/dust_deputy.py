#!/usr/bin/env python

from campy import *

tool=tools['1/4in spiral upcut']

x1 = 5.625
x2 = x1 + 5.625*2 + .25

Camtainer(
    'test/dust_deputy.nc', [
            RectStock(24, 12, .5),
            CircleProfile(tool=tool, center=(x1, x1), z=0.5, radius=11/2., stepdown=0.5, depth=0.5, side='outer'),
#            BoltCircle(tool=tool, center=(x1, x1), z=0.5, radius=4.25/2., stepdown=.25, depth=0.5, bolts=6, bolt_size='1/4-20'),
            CircleProfile(tool=tool, center=(x2, x1), z=0.5, radius=7.5/2., stepdown=0.5, depth=0.5, side='inner'),
            CircleProfile(tool=tool, center=(x2, x1), z=0.5, radius=11/2., stepdown=0.5, depth=0.5, side='outer'),
        ]
)
