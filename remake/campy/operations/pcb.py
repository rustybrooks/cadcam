import gerber
from gerber.render import render
import gerber.primitives as primitives
import shapely.ops


import shapely.affinity
import shapely.ops
from shapely.geometry import LineString, Polygon, MultiPolygon, Point, MultiPoint

from . import operation, machine, helical_drill


class OurRenderContext(render.GerberContext):
    def __init__(self, units='inch'):
        super(OurRenderContext, self).__init__(units=units)

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
        raise Exception("Missing render")

    def _render_slot(self, primitive, color):
        raise Exception("Missing render")

    def _render_amgroup(self, primitive, color):
        raise Exception("Missing render")

    def _render_test_record(self, primitive, color):
        raise Exception("Missing render")


class GerberGeometryContext(OurRenderContext):
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

        if isinstance(line.aperture, primitives.Circle):
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


class GerberDrillContext(render.GerberContext):
    def __init__(self, units='inch'):
        super(GerberDrillContext, self).__init__(units=units)

        self.hole_pos = []
        self.hole_size = []

    def render_layer(self, layer):
        for prim in layer.primitives:
            self.render(prim)

        return MultiPoint(self.hole_pos), self.hole_size

    def _render_drill(self, primitive, color):
        self.hole_pos.append(Point(primitive.position))
        self.hole_size.append(primitive.radius)


def pcb_trace_geometry(gerber_file=None, gerber_data=None):
    if gerber_file is not None:
        b = gerber.load_layer_data(gerber_data, gerber_file)
    else:
        b = gerber.load_layer(gerber_file)

    ctx = GerberGeometryContext()
    return ctx.render_layer(b)


def pcb_drill_geometry(gerber_file=None, gerber_data=None):
    if gerber_data is not None:
        b = gerber.load_layer_data(gerber_data, gerber_file)
    else:
        b = gerber.load_layer(gerber_file)

    ctx = GerberDrillContext()
    return ctx.render_layer(b)


# FIXME making 2 sided boards has not been tested or really considered.  Won't work without some refactoring
@operation(required=['gerber_file', 'tool_radius'])
def pcb_isolation_geometry(
    gerber_file=None, gerber_data=None, stepover='20%', stepovers=1, tool_radius=None,
    flipx=False, flipy=False,
):
    geom = pcb_trace_geometry(gerber_file=gerber_file, gerber_data=gerber_data)

    if flipx:
        minx, miny, maxx, maxy = flipx
        geom = shapely.affinity.scale(geom, xfact=-1, origin=(0, 0))
        geom = shapely.affinity.translate(geom, xoff=maxx+minx)

    if flipy:
        minx, miny, maxx, maxy = flipy
        geom = shapely.affinity.scale(geom, yfact=-1, origin=(0, 0))
        geom = shapely.affinity.translate(geom, yoff=maxy+miny)

    geoms = []
    for step in range(1, stepovers+1):
        bgeom = geom.buffer(tool_radius*step*(1-stepover))
        if isinstance(bgeom, shapely.geometry.Polygon):
            bgeom = shapely.geometry.MultiPolygon([bgeom])

        geoms.append(bgeom)

    return geom, geoms


@operation(required=['gerber_file', 'depth'], operation_feedrate='cut')
def pcb_isolation_mill(
    gerber_file=None, gerber_data=None, stepover='20%', stepovers=1, depth=None, clearz=None,
    border=0.1, auto_clear=True, flipx=False, flipy=False,
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
    geom, geoms = pcb_isolation_geometry(
        gerber_file=gerber_file,
        gerber_data=gerber_data,
        stepover=stepover,
        stepovers=stepovers,
        tool_radius=tool_radius,
        flipx=flipx, flipy=flipy,
    )

    for g in geoms:
        for p in g:
            _cut_coords(p.exterior)
            for i in p.interiors:
                _cut_coords(i)

    if auto_clear:
        machine().goto(z=clearz)

    return geom, geoms


@operation(required=['gerber_file', 'depth'], operation_feedrate='drill')
def pcb_drill(
    gerber_file=None, gerber_data=None, depth=None, flipx=False, flipy=False, clearz=None, auto_clear=True
):
    clearz = clearz or 0.25

    geoms = []
    hole_geom, hole_rads = pcb_drill_geometry(gerber_file=gerber_file, gerber_data=gerber_data)

    if flipx:
        minx, miny, maxx, maxy = flipx
        hole_geom = shapely.affinity.scale(hole_geom, xfact=-1, origin=(0, 0))
        hole_geom = shapely.affinity.translate(hole_geom, xoff=maxx+minx)

    if flipy:
        minx, miny, maxx, maxy = flipy
        hole_geom = shapely.affinity.scale(hole_geom, yfact=-1, origin=(0, 0))
        hole_geom = shapely.affinity.translate(hole_geom, yoff=maxy+miny)

    for h, r in zip(hole_geom, hole_rads):
        geoms.append(h.buffer(r, resolution=16))
        helical_drill(center=h.coords[0], outer_rad=r, z=0, depth=depth, stepdown="10%")

    if auto_clear:
        machine().goto(z=clearz)

    return MultiPolygon(geoms)


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
        machine().goto(x1, y1)
        machine().cut(z=Z)
        machine().cut(x=x1, y=y2)
        machine().cut(x=x2, y=y2)
        machine().cut(x=x2, y=y1)
        machine().cut(x=x1, y=y1)

    if auto_clear:
        machine().goto(z=clearz)


