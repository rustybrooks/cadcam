#!/usr/bin/env python

#import math
from campy import *
from hsm import *
#import shapely
#import shapely.geometry

class SpoilBoard(CAM):
    def __init__(self, tool, width, height, thickness):
        super(SpoilBoard, self).__init__(tool=tool)

        self.width = width
        self.height = height
        self.thickness = thickness

    def generate(self):

        clearZ = self.thickness + .25

        mod_width = 2.0 * int(self.width / 2.0)
        width_start = (self.width - mod_width)/2.0

        stepover = 1/4.

        yadd = 1
        slot_width = 0.5
        odd = True
        last = width_start-1
        for X in frange(width_start + 1, min(width_start + mod_width, self.width - 1.0), 2.0):

            if X - last < 2: break
            last = X
            if odd:
                p1 = [X, yadd]
                p2 = [X, self.height-yadd]
            else:
                p2 = [X, yadd]
                p1 = [X, self.height-yadd]

            #print p1, p2
            odd = not odd

            self.goto(z=clearZ)
            #self.goto(*p1)

            Camtainer(f, [
                HSMStraightGroove(tool=self.tool, p1=p1, p2=p2, z=self.thickness, depth=self.thickness, width=slot_width,
                                  stepover=stepover,
                                  #rough_margin=0.025,
                                  rough_margin=.01,
                                  through=False, plunge=True),
            ], self_contained=False)


        rad = .75/2
        odd = True
        firstX = width_start + 2
        lastX = width_start + mod_width-2.0

        num = int(math.floor((self.width-2)/6.0)) - 1
        if abs(6 - (lastX - 6*num)) < .001:
            firstX -= 2
            lastX -= 2

        clearance_rad = .285/2.0
	
        for X in frange(lastX, firstX, 6.0, include_end=False):
            cams = [
                Goto(z=clearZ),
                HSMCirclePocket(tool=self.tool, center=(X, yadd, self.thickness), inner_rad=0, outer_rad=rad, depth=.3, stepover=stepover),
                HSMCirclePocket(tool=self.tool, center=(X, yadd, self.thickness), outer_rad=clearance_rad, depth=self.thickness, stepover=stepover),
                Goto(z=clearZ),
                HSMCirclePocket(tool=self.tool, center=(X, self.height/2.0, self.thickness), inner_rad=0, outer_rad=rad, depth=.3, stepover=stepover),
                HSMCirclePocket(tool=self.tool, center=(X, self.height/2.0, self.thickness), outer_rad=clearance_rad, depth=self.thickness, stepover=stepover),
                Goto(z=clearZ),
                HSMCirclePocket(tool=self.tool, center=(X, self.height-yadd, self.thickness), inner_rad=0, outer_rad=rad, depth=.3, stepover=stepover),
                HSMCirclePocket(tool=self.tool, center=(X, self.height-yadd, self.thickness), outer_rad=clearance_rad, depth=self.thickness, stepover=stepover),
                Goto(z=clearZ),
            ]

            self.set_speed(self.tool.drill_speed)
            Camtainer(f, cams if odd else list(reversed(cams)), self_contained=False)

            odd = not odd



width = 26.2
height = 16.1

tool = tools['1/4in spiral upcut']
thickness = .75

Camtainer("spoil_slots_test.ngc", [
    RectStock(8, 4, thickness+.1),
    SpoilBoard(tool, width=8, height=4, thickness=thickness)
])

Camtainer("spoil_slots.ngc", [
    RectStock(width, height, thickness),
    SpoilBoard(tool, width=width, height=height, thickness=thickness)
])

offset = 0
tool = tools['1 1/2in straight bit']
tool.rough_speed = 45
Camtainer("spoil_face.ngc", [
    RectStock(width, height, thickness),
    RectPocket(tool, (-offset, -offset), (width+offset, height+offset), z=0, depth=0.02, stepover=.5, type='x')
])
