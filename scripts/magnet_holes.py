#!/usr/bin/env python
from campy import *
from hsm import *

import os
basedir = os.path.dirname(os.path.realpath(__file__))

width = 9.271
height = 1.112
space = 1.75
ztol = 0.02
stepdown = 0.020

holes = 4
dist = width/(holes+1)
coords = [(dist*i, height/2) for i in range(1, holes+1)]

tool = tools['1/4in 4-flute endmill']
Camtainer('magnet_holes.nc', [
    RectStock(width, height, .5, origin=(0, -.5, 0)),
    Goto(z=.25),
    HelicalDrill(
        tool, 
        (width/2 - space/2, height/2, ztol), 
        outer_rad=.493/2, depth=.130+ztol, stepdown=stepdown, speed=6
    ),
    Goto(z=.25),
    HelicalDrill(
        tool, 
        (width/2 + space/2, height/2, ztol), 
        outer_rad=.493/2, depth=.130+ztol, stepdown=stepdown, speed=6
    ),
    Goto(z=.25),
    DrillCycle(coords=coords, depth=.25, clearZ=0.25, feed=1, shallow=True, retract_to_z=False),
    Goto(z=.25),
])
