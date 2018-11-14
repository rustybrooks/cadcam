import gerber
from gerber.render import render
from gerber.primitives import *
import logging
import math
import shapely.ops
import sys
import os.path


import shapely.affinity
import shapely.ops
from shapely.geometry import LineString

from . import operation, machine, helical_drill


class GerberGeometryContext(render.GerberContext):
    def __init__(self, units='inch'):
        super(GerberGeometryContext, self).__init__(units=units)

        self.polys = []

    def render_layer(self, layer):
        for prim in layer.primitives:
            self.render(prim)

        return shapely.ops.unary_union(self.polys)

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


class GerberDrillContext(render.GerberContext):
    def __init__(self, units='inch'):
        super(GerberDrillContext, self).__init__(units=units)

        self.holes = []

    def render_layer(self, layer):
        for prim in layer.primitives:
            self.render(prim)

        return self.holes

    def _render_line(self, line, color):
        raise Exception("Missing render")

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
        self.holes.append(
            (primitive.position, primitive.radius)
        )

    def _render_slot(self, primitive, color):
        raise Exception("Missing render")

    def _render_amgroup(self, primitive, color):
        raise Exception("Missing render")

    def _render_test_record(self, primitive, color):
        raise Exception("Missing render")


# FIXME making 2 sided boards has not been tested or really considered.  Won't work without some refactoring
@operation(required=['gerber_file', 'tool_radius'])
def pcb_isolation_geometry(gerber_file=None, adjust_zero=True, stepover='20%', stepovers=1, tool_radius=None):
    flipx = False

    ext = os.path.splitext(gerber_file)[-1].lower()
    if ext == ".gbl":
        flipx = True
    elif ext == '.gtl':
        pass
    else:
        raise Exception("only gerber top and bottom copper layer supported: {}".format(gerber_file))

    b = gerber.load_layer(gerber_file)
    ctx = GerberGeometryContext()
    geom = ctx.render_layer(b)

    minx, miny, maxx, maxy = geom.bounds

    if flipx:
        geom = shapely.affinity.scale(geom, xfact=-1)
        geom = shapely.affinity.translate(geom, xoff=maxx+minx)
        minx, miny, maxx, maxy = geom.bounds

    if adjust_zero:
        geom = shapely.affinity.translate(geom, xoff=-minx, yoff=-miny)

    geoms = []
    for step in range(1, stepovers+1):
        bgeom = geom.buffer(tool_radius*step*(1-stepover))
        if isinstance(bgeom, Polygon):
            bgeom = [bgeom]

        geoms.append(bgeom)

    return geom.bounds, geoms


@operation(required=['gerber_file', 'depth'], operation_feedrate='cut')
def pcb_isolation_mill(
    gerber_file, adjust_zero=True, stepover='20%', stepovers=1, depth=None, clearz=None, border=0.1, auto_clear=True
):
    def _cut_coords(c, simplify=0.001):
        machine().goto(z=clearz)
        coords = c.simplify(simplify).coords
        machine().goto(coords[0][0] + border, coords[0][1] + border)
        machine().cut(z=-depth)

        for c in coords:
            machine().cut(c[0] + border, c[1] + border)

    clearz = clearz or 0.25
    tool_radius = machine().tool.diameter_at_depth(depth)/2.0

    foo = pcb_isolation_geometry(
        gerber_file=gerber_file,
        adjust_zero=adjust_zero,
        stepover=stepover,
        stepovers=stepovers,
        tool_radius=tool_radius,
    )
    print "foo =", foo
    bounds, geoms = foo

    for g in geoms:
        for p in g:
            _cut_coords(p.exterior)
            for i in p.interiors:
                _cut_coords(i)

    if auto_clear:
        machine().goto(z=clearz)

    minx, miny, maxx, maxy = bounds
    return [minx, miny, maxx+2*border, maxy+2*border], geoms


@operation(required=['drill_file', 'depth'], operation_feedrate='drill')
def pcb_drill(
    drill_file, depth=None, xoff=0, yoff=0, flipx=False, clearz=None, auto_clear=True
):
    clearz = clearz or 0.25

    b = gerber.load_layer(drill_file)
    ctx = GerberDrillContext()
    holes = ctx.render_layer(b)
    for h in holes:
        x, y = h[0]
        helical_drill(center=(x+xoff, y+yoff), outer_rad=h[1], z=0, depth=depth, stepdown="10%")

    if auto_clear:
        machine().goto(z=clearz)


# FIXME - tabs not supported, add if I ever need
@operation(required=['bounds', 'depth'], operation_feedrate='cut')
def pcb_cutout(bounds=None, depth=None, stepdown="50%", tabs=None, clearz=None, auto_clear=True):
    clearz = clearz or 0.25

    minx, miny, maxx, maxy = bounds
    width = maxx - minx
    height = maxy - miny

    x1 = 0-machine().tool.diameter/2
    x2 = width+machine().tool.diameter/2
    y1 = 0-machine().tool.diameter/2
    y2 = height+machine().tool.diameter/2
    for Z in machine().zstep(0, -depth, stepdown):
        print Z
        machine().goto(x1, y1)
        machine().cut(z=Z)
        machine().cut(x=x1, y=y2)
        machine().cut(x=x2, y=y2)
        machine().cut(x=x2, y=y1)
        machine().cut(x=x1, y=y1)

    if auto_clear:
        machine().goto(z=clearz)


def pcb_mill_and_drill(
    gerber_files, drill_file, adjust_zero=True, stepover='20%', stepovers=1, depth=None, border=0.1,
    clearZ=None, auto_clear=True
):
    pass