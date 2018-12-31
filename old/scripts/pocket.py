#!/usr/bin/env python

from campy import *
from hsm import *
import math

##if os.path.exists('/usbdrive1/extra/cadcam'):
#    base = '/usbdrive1/extra/cadcam'
#else:
base = '.'

tool = tool = tools['1/2in spiral upcut']
tool.rough_speed = 90
Camtainer("{}/test/panto_pocket.nc".format(base), [
    RectStock(21, 4.5, 1, origin=(-21, -1, 0)),
    RectPocket(
        tool=tool, 
        p1=(-8.5, 2.), 
        p2=(5.5, 5), 
        z=0, depth=.4, stepdown=2, stepover=.15
    ),
#    HSMStraightGroove(tool=tool, p1=(-3.5, 0), p2=(-3.5, 4.5), width=1.5, z=0, depth=.4, stepover=.15, type='semicircle'),
#    HSMStraightGroove(tool=tool, p1=(-17.5, 0), p2=(-17.5, 5), width=1.5, z=0, depth=.4, stepover=.15, type='semicircle'),
])
