#!/usr/bin/env python

from campy import *

class Drawer(CAM):

# ^
# |
# y
#  x --->

######### ######
#   S2  # # F  #
######### ######

######### ######
#   S1  # #  B #
######### ######

    def __init__(self, tool, width, height, depth, thickness, bottom_thickness, finger_size=None):
        self.tool = tool;
        self.width = width
        self.height = height
        self.depth = depth
        self.thickness = thickness
        self.finger_size = finger_size if finger_size else max(thickness, .5)
        self.bottom_thickness = bottom_thickness

    def generate(self):
        print "Need stock of", max(self.height, self.width), "x", (self.depth+.5)*4
        stock = RectStock(max(self.height, self.width), (self.depth+0.5)*4, self.thickness, origin=(0, 0, 0))
        stock.generate(f)
        self.generate_side(f, 0, 0)
        self.generate_side(f, 0, self.depth+.5)
        self.generate_frontback(f, 0, 2*(self.depth+.5))
        self.generate_frontback(f, 0, 3*(self.depth+.5))

    def generate_frontback(self, f, basex=0, basey=0):
        self.generate_foo(f, self.height, basex, basey, inset=0)

    def generate_side(self, f, basex=0, basey=0):
        self.generate_foo(f, self.width, basex, basey, inset=1)

    def generate_foo(self, f, length, basex=0, basey=0, inset=1):

        clearZ = self.thickness + 0.25

        R = self.tool.diameter/2.0

        width_tol = 0.005

        # drawer bottom
        self.goto(z=clearZ)
        
        p1 = (basex-R+self.thickness, basey+R)
        p2 = (basex+length+R-self.thickness, basey+self.bottom_thickness-R)
        r = RectPocket(self.tool, p1, p2, z=self.thickness, depth=self.thickness*1/3., stepover=.75, type='x')
        r.generate(self.f)

        # drawer fingers
        flips = []
        for y in frange(0, self.depth, self.finger_size, include_end=True):
            flips.append(y)

        self.goto(z=clearZ)
        self.goto(x=basex + inset*self.thickness-R, y=basey-R)
        y = 0
        for Z in self.zstep(self.thickness, 0):
            foo=0
            for i in range(len(flips)-1):
                inset = 0 if inset else 1
    
                self.cut(x=basex + self.thickness+R)
                self.cut(x=basex + inset*self.thickness-R)
                self.cut(y=basey + flips[i+1] + (-1 if inset else 1)*(R-width_tol))

            self.cut(x=basex + length - inset*self.thickness+R)
            inset = 0 if inset else 1

            foo=1
            for i in range(len(flips)-1, 0, -1):
                inset = 0 if inset else 1

                self.cut(x=basex + foo*length - (self.thickness+R))
                self.cut(x=basex + foo*length - (inset*self.thickness-R))
                self.cut(y=basey + flips[i-1]  + (1 if inset else -1)*(R-width_tol))

            inset = 0 if inset else 1
            self.cut(y=basey + -R)
            self.cut(x=basex + inset*self.thickness-R)
    
        self.goto(z=clearZ)
        


inside_width = 11
inside_height = 11
depth = 5
thickness = .5
c = Camtainer("drawer.ngc", Drawer(tool=tools['1/8in spiral upcut'],
                                 width=inside_width+thickness*2,
                                 height=inside_height+thickness*2,
                                 depth=depth,
                                 thickness=thickness, bottom_thickness=.25,
                                 finger_size=1.0))


