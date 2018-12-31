
from campy import *

def xfrange(start, stop, step):
    if start < stop:
        while start < stop:
            yield start
            start += step
    else:
        while start > stop:
            yield start
            start -= step

    if start != stop:
        yield stop


class Arc(CAM):
    def __init__(self, tool=None, thickness=None):
        self.thickness = thickness
        self.tool = tool

    def generate(self):

        self.write("%")
        self.write("G17 G20 G40 G90")

        xc = 2
        yc = 2
        r = 1.0
        end_angle = 150

        circ = CircleProfile(tool=self.tool, center=(xc, yc, self.thickness), radius=r, depth=self.thickness, side='inner', end_angle=end_angle)
        circ.generate(self.f)

        f = open("arctest.draw", "w")
        z1 = 0
        z2 = self.thickness

        x1 = xc + r*math.sin(0)
        y1 = yc + r*math.sin(0)
        for deg in xfrange(0, end_angle, 1):
            rad = -1*math.radians(deg)
            x2 = xc + r*math.sin(rad)
            y2 = yc + r*math.cos(rad)

            print >> f, "line,%f,%f,%f,%f,%f,%f,1.0,0,0" % (x1, z1, y1, x2, z1, y2)
            print >> f, "line,%f,%f,%f,%f,%f,%f,1.0,0,0" % (x1, z2, y1, x2, z2, y2)

            x1 = x2
            y1 = y2


        f.close()

        self.goto(z=1)
        self.goto(x=0, y=0)


width = 3.5
height = 3.5
tool=tools['1/4in spiral upcut']
thickness = .05

Camtainer("test/arctest.ngc", [
    RectStock(width, height, thickness, origin=(0, 0, 0)),
    Arc(tool=tool, thickness=thickness)
])


