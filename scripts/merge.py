#!/usr/bin/env python

import math
from matplotlib import pyplot
import shapely
import shapely.geometry
import shapely.affinity

from campy import *
import geometry

def parameterize(curve, numpts):
    return polar_parameterize(curve, numpts)
    #return arclength_parameterize(curve, numpts)

def arclength_parameterize(curve, numpts):
    l = 0
    start = curve.coords[0]
    for pt in curve.coords[1:]:
        l += length([x-y for x, y in zip(pt, start)])
        start = pt

    newcurve = [curve.coords[0]]
    start = curve.coords[0]
    for pt in curve.coords[1:]:
        pct = length([x-y for x, y in zip(pt, start)]) / l
        for i in range(int(numpts*pct)):
            tpct = i / numpts*pct
            newpt = [x + (y-x)*tpct for x, y in zip(start, pt)]
            print tpct, newpt
            newcurve.append(newpt)

        start = pt


    newcurve.append(newcurve[0])
    print newcurve
    return shapely.geometry.LineString(newcurve)

def polar_parameterize(curve, numpts):
    newcurve = []
    for i in range(numpts+1):
        angle = math.radians(360.*i/numpts)
        test_line = shapely.geometry.LineString([(0, 0), (1000*math.sin(angle), 1000*math.cos(angle))])
        inter = curve.intersection(test_line)
        #if isinstance(inter, shapely.geometry.point.Point):
        newcurve.append(inter)
        #else:
        #    list(newcurve.append(inter))[0]

    foo = shapely.geometry.LineString(newcurve)
    return foo

def merge_by_segments(curve1, curve2, factor, parampoints=360, type='polar'):
    # center math is borked
    curve1p = parameterize(curve1, parampoints)
    curve2p = parameterize(curve2, parampoints)

    new_coords = []
    for coord1, coord2 in zip(curve1p.coords, curve2p.coords):
        newcoord = [x*(1-factor) + y*factor for x, y in zip(coord1, coord2)]

        new_coords.append(newcoord)

    if type == 'coords':
        return new_coords
    else:
        return [length(x) for x in new_coords]

def graph_linestring(ls, figure, color='blue'):
    x = [el[0] for el in ls]
    y = [el[1] for el in ls]

    figure.plot(x, y, color=color, alpha=0.9, linewidth=1, solid_capstyle='round')



class MergeTurner(CAM):
    def __init__(self, tool, curve_generator, stepover=None, material_factor=1.0):
        super(MergeTurner, self).__init__(tool=None)

        self._tool = tool
        self.stepover = stepover or 1/4.
        self.material_factor = material_factor
        self.curve_generator = curve_generator

        self.set_speed(tool.rough_speed)

    def generate(self):

        self.set_tool(self._tool)

        xstep = self.stepover*self.tool.diameter * self.material_factor
        xstart, xstop = self.curve_generator(None)

        w = 1
        self.camtain(RectStock(xstop-xstart, w, w, origin=(xstart, -w/2., -w/2.)))

        angle = 0
        for x in frange(xstart, xstop, xstep):
            curve = self.curve_generator(x)

            clearZ = max(curve) + .125
            self.goto(z=clearZ)
            self.goto(a=angle)
            self.goto(x=x)

            for i, z in enumerate(curve):
                self.cut(z=z, a=angle + i*360./len(curve))

            angle += 360

def linear_generator(curves, transitions, rotations=None, scales=None, angle_step=1):
    def generator(x):
        segments = int(360 / angle_step)
        rots = rotations or [0]*len(curves)
        scls = scales or [1]*len(curves)

        if x is None:
            return [transitions[0], transitions[-1]]

        indices = [i for i, el in enumerate(transitions) if x >= el]
        if len(indices) != len(transitions):
            i = indices[-1]
            pct = (x-transitions[i])/(transitions[i+1] - transitions[i])
            rot = rots[i] + (rots[i+1] - rots[i])*pct
            s = scls[i] + (scls[i+1] - scls[i])*pct
            curve = merge_by_segments(
                shapely.affinity.scale(shapely.affinity.rotate(curves[i], rot, origin=(0, 0)), xfact=s, yfact=s, zfact=s, origin=(0, 0)),
                shapely.affinity.scale(shapely.affinity.rotate(curves[i+1], rot, origin=(0, 0)), xfact=s, yfact=s, zfact=s, origin=(0, 0)),
                pct, segments
            )
            return curve
        else:
            return [length(x) for x in parameterize(curves[-1], segments).coords]

    return generator


tool = tools['1/4in spiral ball']

curve1 = shapely.geometry.LineString(geometry.generate_polygon(4, 1))
curve2 = shapely.geometry.LineString(geometry.generate_polygon(3, 1))

"""
#print list(curve1.coords)
#print list(curve2.coords)

fig = pyplot.figure()
sp = fig.add_subplot(111)

#graph_linestring(curve1.coords, sp, 'blue')
#graph_linestring(curve2.coords, sp, 'red')
for i in range(0, 6):
    graph_linestring(shapely.affinity.translate(shapely.geometry.LineString(merge_by_segments(curve1, curve2, i/5.0, type='coords')), i*1.5, 0).coords, sp, 'purple')

pyplot.show()
import sys; sys.exit(1)
"""

gen = linear_generator(curves=[curve1, curve2, curve1], transitions=[0, 3, 6], rotations=[0, 180, 360], scales=[.5, 1.5, .5])
Camtainer("./output/merge_test.ngc", MergeTurner(tool, gen, material_factor=1))
