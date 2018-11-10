#!/usr/bin/env python

from campy import *

class ATest(CAM):
    def __init__(self, tool):
        super(ATest, self).__init__(tool)
        self.set_speed(tool.rough_speed)

    def generate(self):

        stepover = 0.5
        self.camtain(RectStock(4, 1, 1, origin=(0, -.5, -.5)))
        self.goto(x=-.25, y=0, z=.5)
        self.goto(x=4.25, a=360*4.5/(self.tool.diameter*stepover))

tool = tools['1/4in spiral upcut']
Camtainer("./test/a-test.ngc", ATest(tool))
