#!/usr/bin/env python

import logging
import math
import sys, os
from os import sys, path
sys.path.append(path.dirname(path.dirname(path.abspath(__file__))))
from campy import *

import gerber
from gerber.render import GerberCairoContext, RenderSettings, theme, render
from gerber.primitives import *

import optparse
import os
import svg


import shapely.affinity
import shapely.ops
from shapely.coords import CoordinateSequence
from shapely.geometry import Point, LineString, MultiLineString, Polygon, MultiPolygon

import campy.geometry


logging.basicConfig()
import textwrap

def write_svg(p):
    with open("test.svg", "w") as f:
        f.write(p._repr_svg_())

        """
        #specify margin in coordinate units
        margin = 5

        bbox = list(p.bounds)
        bbox[0] -= margin
        bbox[1] -= margin
        bbox[2] += margin
        bbox[3] += margin

        width = bbox[2] - bbox[0]
        height = bbox[3] - bbox[1]

        #transform each coordinate unit into "scale" pixels
        scale = 5

        props = {
            'version': '1.1',
            'baseProfile': 'full',
            'width': '{width:.0f}px'.format(width=width*scale),
            'height': '{height:.0f}px'.format(height=height*scale),
            'viewBox': '%.1f,%.1f,%.1f,%.1f' % (bbox[0], bbox[1], width, height),
            'xmlns': 'http://www.w3.org/2000/svg',
            'xmlns:ev': 'http://www.w3.org/2001/xml-events',
            'xmlns:xlink': 'http://www.w3.org/1999/xlink'
        }

        f.write(textwrap.dedent(r'''
            <?xml version="1.0" encoding="utf-8" ?>
            <svg {attrs:s}>
            {data:s}
            </svg>
        ''').format(
            attrs = ' '.join(['{key:s}="{val:s}"'.format(key = key, val = props[key]) for key in props]),
            data=p.svg()
        ).strip())
        """


class GerberLinesetContext(render.GerberContext):
    def __init__(self, units='inch'):
        super(GerberLinesetContext, self).__init__(units=units)

        self.polys = []

    def render_layer(self, layer):
        for prim in layer.primitives:
            self.render(prim)

#        for el in self.polys:
#            print ["({:0.3f}, {:0.3f})".format(x[0], x[1]) for x in el.exterior.coords]
        print "------------------"
        # print ["({:0.3f}, {:0.3f})".format(x[0], x[1]) for x in self.polys[3].exterior.coords]
        union = shapely.ops.unary_union(self.polys)
        return union
        # write_svg(union)
        #for x in [x.exterior.coords for x in union]:
        #    print [a for a in x]
        #ls = campy.geometry.LineSet()
        #for el in union:
        #    ls.add(campy.geometry.Line([a for a in el.exterior.coords]))
        #return ls
        # return campy.geometry.LineSet([[campy.geometry.Line(a) for a in x.exterior.coords] for x in union])

    def _render_line(self, line, color):
        start = line.start
        end = line.end

        if isinstance(line.aperture, Circle):

            """
            width = line.aperture.diameter
            xd = end[0] - start[0]
            yd = end[1] - start[1]
            a = math.atan2(yd, xd)
            b = math.pi - a

            xo = width/2 * math.sin(b)
            yo = width/2 * math.cos(b)

            poly = Polygon([
                (start[0] - xo, start[1] + yo),
                (end[0]   - xo, end[1]   + yo),
                (end[0]   + xo, start[1] - yo),
                (start[0] + xo, start[1] - yo),
            ])
            # print poly.area
            if poly.area == 0:
                pass
                #print "APERT", width, start, end, xd, yd, xo, yo
                #print poly
            elif not poly.is_valid:
                print "APERT", width, start, end, xd, yd, xo, yo
                print poly
            else:
                self.polys.append(poly)
            """

            poly = LineString([start, end]).buffer(
                line.aperture.diameter/2.,
                resolution=16,
                cap_style=shapely.geometry.CAP_STYLE.round,
                join_style=shapely.geometry.JOIN_STYLE.round,

            )
            self.polys.append(poly)

        elif hasattr(line, 'vertices') and line.vertices is not None:
            print "OTHER"
            print [x for x in line.vertices]

    def _render_arc(self, primitive, color):
        raise Exception("Missing render")

    def _render_region(self, primitive, color):
        raise Exception("Missing render")

    def _render_circle(self, primitive, color):
        raise Exception("Missing render")

    def _render_rectangle(self, primitive, color):
        raise Exception("Missing render")

    def _render_obround(self, primitive, color):
        raise Exception("Missing render")

    def _render_polygon(self, primitive, color):
        raise Exception("Missing render")

    def _render_drill(self, primitive, color):
        raise Exception("Missing render")

    def _render_slot(self, primitive, color):
        raise Exception("Missing render")

    def _render_amgroup(self, primitive, color):
        raise Exception("Missing render")

    def _render_test_record(self, primitive, color):
        raise Exception("Missing render")

def cut_coords(c, simplify=0.001):
    machine.goto(z=clearZ)
    coords = c.simplify(simplify).coords
    machine.goto(coords[0][0]+offset-minx, coords[0][1]+offset-miny)
    machine.cut(z=-depth)

    for c in coords:
        machine.cut(c[0]+offset-minx, c[1]+offset-miny)


if __name__ == '__main__':
    depth = .01
    clearZ = 0.25
    offset = 0.1
    steps = 6
    overlap = 0.15
    thickness = 1.6*constants.MM

    machine = set_machine('k2cnc')
    machine.max_rpm = 15000
    machine.min_rpm = 15000
    machine.set_material('mdf')
    machine.set_file('ngc/pcb/pcb.gcode')
    machine.set_tool('engrave-0.1-30')
    machine.set_speed(5)

    b = gerber.load_layer('/tmp/pcb/Gerber_PCB Test 1/Gerber_BottomLayer.GBL')
    ctx = GerberLinesetContext()
    geom = ctx.render_layer(b)

    minx, miny, maxx, maxy = geom.bounds
    width = 2*offset + maxx-minx
    height = 2*offset + maxy - miny
    rect_stock(width, height, thickness, origin=(0, -thickness, 0))
    effective_rad = machine.tool.diameter_at_depth(depth)/2.0
    print "Effective rad:", effective_rad
    print minx, miny, maxx, maxy
    print width, height

    for step in range(1,steps+1):
        bgeom = geom.buffer(effective_rad*step*(1-overlap))

        with open('test{}.svg'.format(step), 'w') as f:
            f.write(bgeom._repr_svg_())

        if isinstance(bgeom, Polygon):
            bgeom = [bgeom]

        for el in bgeom:
            cut_coords(el.exterior)
            for i in el.interiors:
                cut_coords(i)

        machine.goto(z=clearZ)

    #o1 = rest.enforce_direction(clockwise=True).parallel_offset(
    #    machine.tool.diameter_at_depth(depth),
    #    side='right',
    #    # use_ring=False, # I wish I knew better why
    #)
    #for l in o1.lines:
        # if not len(l.coords):
        #     print "... no coords"
        #     continue
        #
        # print len(l.coords), l.coords.__class__
        # coords = l.simplify(0.001).coords
        # machine.goto(z=clearZ)
        # machine.goto(*(coords[0]))
        # machine.cut(z=-depth)
        #
        # for c in reversed(coords):
        #     machine.cut(*c)

    machine.goto(z=clearZ)


