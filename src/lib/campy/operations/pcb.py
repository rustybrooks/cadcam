import gerber
from gerber.render import render, theme, RenderSettings
import gerber.primitives as primitives
import logging
import math
import os
import shapely.affinity
import shapely.geometry
import shapely.ops
import svgwrite
import zipfile

from . import operation, machine, helical_drill, rect_stock, zprobe, drill_cycle
from lib.campy import geometry, constants, environment, cammath
# from lib.campy import *

logger = logging.getLogger(__name__)


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


class GerberSVGContext(OurRenderContext):
    def __init__(self, svg_file, width, height, flipx=False, units='inch'):
        super(GerberSVGContext, self).__init__(units=units)

        self.dwg = svgwrite.Drawing(
            svg_file,
            profile='full',
            size=(width, height),
        )

        self.mask_count = 0
        self.layer_mask = None
        self.layer_mask_name = None
        self.flipx = flipx

    def save(self):
        self.dwg.save()

    def render_layers(self, layers, theme=theme.THEMES['default']):
        # Calculate scale parameter
        x_range = [10000, -10000]
        y_range = [10000, -10000]
        for layer in layers:
            bounds = layer.bounds
            import logging
            if bounds is not None:
                layer_x, layer_y = bounds
                x_range[0] = min(x_range[0], layer_x[0])
                x_range[1] = max(x_range[1], layer_x[1])
                y_range[0] = min(y_range[0], layer_y[0])
                y_range[1] = max(y_range[1], layer_y[1])
        width = x_range[1] - x_range[0]
        height = y_range[1] - y_range[0]

        self.bounds = [x_range[0], y_range[0], width, height]

        bgsettings = theme['background']
        c = list(bgsettings.color)

        self.group = self.dwg.add(
            self.dwg.g(
                transform="scale({}, -1)".format(-1 if self.flipx else 1),
            )
        )

        self.group.add(
            self.dwg.rect(
                (self.bounds[0], self.bounds[1]), (self.bounds[2], self.bounds[3]),
                fill="rgb(%d, %d, %d)" % (c[0]*255, c[1]*255, c[2]*255),
            )
        )

        self.dwg.viewbox(
            self.bounds[0] + (-1*width if self.flipx else 0),
            self.bounds[1] + -1*height,
            self.bounds[2],
            self.bounds[3]
        )

        for layer in layers:
            settings = theme.get(layer.layer_class, RenderSettings())
            self.render_layer(layer, settings=settings)

    def render_layer(self, layer, settings):
        self.invert = settings.invert

        self.layer_mask_name = "mask{}".format(self.mask_count)
        self.mask_count += 1
        self.layer_mask = self.dwg.mask((self.bounds[0], self.bounds[1]), (self.bounds[2], self.bounds[3]), id=self.layer_mask_name)
        self.dwg.defs.add(self.layer_mask)

        self.layer_mask.add(
            self.dwg.rect(
                (self.bounds[0], self.bounds[1]), (self.bounds[2], self.bounds[3]),
                fill='white' if self.invert else 'black',
            )
        )

        if settings is None:
            settings = theme.THEMES['default'].get(layer.layer_class, RenderSettings())

        c = list(settings.color)
        fgcolor = "rgb(%d, %d, %d)" % (c[0]*255, c[1]*255, c[2]*255)

        for prim in layer.primitives:
            self.render(prim)

        self.group.add(
            self.dwg.rect(
                (self.bounds[0], self.bounds[1]), (self.bounds[2], self.bounds[3]),
                fill=fgcolor, mask='url(#{})'.format(self.layer_mask_name),
                fill_opacity=settings.alpha,
            )
        )

    def _render_line(self, line, color):
        start = line.start
        end = line.end

        if line.level_polarity != 'dark':
            logger.warn("line polarity! = %r", line.level_polarity)

        if isinstance(line.aperture, primitives.Circle):
            self.layer_mask.add(
                self.dwg.line(
                    start, end,
                    stroke='white' if not self.invert and line.level_polarity == 'dark' else 'black',
                    stroke_width=line.aperture.diameter,
                    stroke_linejoin='round', stroke_linecap='round',
                )
            )
        elif hasattr(line, 'vertices') and line.vertices is not None:
            raise Exception("render_line don't know what to do")

    def _render_rectangle(self, primitive, color):
        x1, y1 = primitive.lower_left

        center = primitive.position
        if primitive.hole_diameter > 0:
            raise Exception('fixme')
            maskname = "mask{}".format(self.mask_count)
            self.mask_count += 1
            d = primitive.hole_diameter
            r = d/1.
            mask = self.dwg.mask((center[0]-r, center[1]-r), (d, d), id=maskname)
            mask.add(self.dwg.circle(center, r, fill="#ffffff"))
            self.dwg.defs.add(mask)

        if primitive.hole_width > 0 and primitive.hole_height > 0:
            if primitive.hole_width > 0 and primitive.hole_height > 0:
                raise Exception('fixme')
                maskname = "mask{}".format(self.mask_count)
                self.mask_count += 1

                cx, cy = center
                w = primitive.hole_width
                h = primitive.hole_height

                mask = self.dwg.mask(((cx-w)/2., (cy-h)/2.), (w, h), id=maskname)
                mask.add(self.dwg.rect(
                    ((cx - w) / 2., (cy - h) / 2.), (w, h), file="#ffffff"
                ))
                self.dwg.defs.add(mask)

        self.layer_mask.add(self.dwg.rect(
            (x1, y1),
            (primitive.width, primitive.height),
            fill='white' if not self.invert and primitive.level_polarity == 'dark' else 'black',
        ))

    def _render_circle(self, primitive, color):
        center = primitive.position

        if hasattr(primitive, 'hole_diameter') and primitive.hole_diameter is not None and primitive.hole_diameter > 0:
            raise Exception('fixme')
            # maskname = "mask{}".format(self.mask_count)
            self.mask_count += 1
            d = primitive.hole_diameter
            r = d/1.
            mask = self.dwg.mask((center[0]-r, center[1]-r), (d, d), id=maskname)
            mask.add(self.dwg.circle(center, r, fill="#ffffff"))
            self.dwg.defs.add(mask)

        if (hasattr(primitive, 'hole_width') and hasattr(primitive, 'hole_height')
            and primitive.hole_width is not None and primitive.hole_height is not None
            and primitive.hole_width > 0 and primitive.hole_height > 0):
            raise Exception('fixme')

            cx, cy = center
            w = primitive.hole_width
            h = primitive.hole_height

            mask = self.dwg.mask(((cx-w)/2., (cy-h)/2.), (w, h), id=maskname)
            mask.add(self.dwg.rect(
                ((cx - w) / 2., (cy - h) / 2.), (w, h), file="#ffffff"
            ))
            self.dwg.defs.add(mask)

        self.layer_mask.add(self.dwg.circle(
            center=center, r=primitive.radius,
            fill='white' if not self.invert and primitive.level_polarity == 'dark' else 'black',
        ))

    def _render_region(self, region, color):
        coords = [region.primitives[0].start]
        for prim in region.primitives:
            if isinstance(prim, primitives.Line):
                coords.append(prim.end)
            else:
                logger.warn('notline')

        self.layer_mask.add(self.dwg.polygon(
            coords,
            fill='white' if not self.invert and region.level_polarity == 'dark' else 'black',
        ))

    def _render_arc(self, arc, color):
        is_circle = False
        two_pi = 2 * math.pi
        angle1 = arc.start_angle
        angle2 = arc.end_angle
        if angle1 == angle2 and arc.quadrant_mode != 'single-quadrant':
            is_circle = True
            # Make the angles slightly different otherwise Cario will draw nothing
            if angle1 == 0:
                if arc.direction == 'counterclockwise':
                    angle1 = two_pi
                else:
                    angle2 = two_pi
            else:
                angle2 -= 0.000000001
        if isinstance(arc.aperture, primitives.Circle):
            width = arc.aperture.diameter if arc.aperture.diameter != 0 else 0.001
        else:
            width = max(arc.aperture.width, arc.aperture.height, 0.001)

        step = abs(angle2 - angle1) / 25.
        if arc.direction == 'counterclockwise':
            if not is_circle and (angle1 > angle2):
                angle1 -= two_pi
        else:
            pass

        angles = list(cammath.frange(angle1, angle2, step))

        coords = [(arc.center[0] + arc.radius*math.cos(a), arc.center[1] + arc.radius*math.sin(a)) for a in angles]

        self.layer_mask.add(
            self.dwg.polyline(
                coords,
                stroke='white' if not self.invert and arc.level_polarity == 'dark' else 'black',
                stroke_width=width,
                stroke_linejoin='round', stroke_linecap='round',
                fill_opacity=0,
            )
        )

    def _render_drill(self, primitive, color):
        self._render_circle(primitive, color)


class GerberGeometryContext(OurRenderContext):
    def __init__(self, units='inch'):
        super(GerberGeometryContext, self).__init__(units=units)

        self.polys = []
        self.remove_polys = []
        self.running_poly = None

    def update_running(self, p, add=True):
        if add:
            self.polys.append(p)
            if self.running_poly:
                self.running_poly = self.running_poly.union(p)
            else:
                self.running_poly = p
        else:
            self.remove_polys.append(p)
            self.running_poly = self.running_poly.difference(p)

    def render_layer(self, layer, union=True):
        for prim in layer.primitives:
            self.render(prim)

        clear = shapely.ops.unary_union(self.remove_polys)
        if union:
            # adds = shapely.ops.unary_union(self.polys)
            # return adds.difference(clear)
            return self.running_poly
        else:
            ret = []
            for p in self.polys:
                np = p.difference(clear)
                if np.bounds:
                    ret.append(np)
            return ret

    def _render_line(self, line, color):
        start = line.start
        end = line.end

        if isinstance(line.aperture, primitives.Circle):
            poly = shapely.geometry.LineString([start, end]).buffer(
                line.aperture.diameter/2.,
                resolution=16,
                cap_style=shapely.geometry.CAP_STYLE.round,
                join_style=shapely.geometry.JOIN_STYLE.round,
            )
            if not poly.exterior and not poly.interiors:
                pass
            else:
                self.update_running(poly)

        elif hasattr(line, 'vertices') and line.vertices is not None:
            raise Exception("render_line don't know what to do")

    def _render_rectangle(self, primitive, color):
        x1, y1 = primitive.lower_left
        x2 = x1 + primitive.width
        y2 = y1 + primitive.height
        box = shapely.geometry.box(x1, y1, x2, y2, ccw=False)

        center = primitive.position
        if primitive.hole_diameter > 0:
            circle = shapely.geometry.Point(*center).buffer(distance=primitive.hole_diameter)
            if primitive.level_polarity == 'dark':
                box = box.difference(circle)
            else:
                raise Exception("render_rectangle doesn't really know what to do with non-dark circle in it...")

        if primitive.hole_width > 0 and primitive.hole_height > 0:
            cx, cy = center
            w = primitive.hole_width
            h = primitive.hole_height
            box2 = shapely.geometry.box((cx-w)/2., (cy-h)/2., (cx+w)/2., (cy+h)/2)
            if primitive.level_polarity == 'dark':
                box = box.difference(box2)
            else:
                raise Exception("render_rectangle doesn't really know what to do with non-dark circle in it...")

        self.update_running(box)

    def _render_circle(self, primitive, color):
        center = primitive.position
        if not self.invert and primitive.level_polarity == 'dark':
            circle = shapely.geometry.Point(*center).buffer(distance=primitive.radius)
        else:
            raise Exception("render_circle doesn't know what to do with polarity!=dark")

        if hasattr(primitive, 'hole_diameter') and primitive.hole_diameter is not None and primitive.hole_diameter > 0:
            hole = shapely.geometry.Point(*center).buffer(distance=primitive.hole_diameter)
            circle = circle.difference(hole)

        if (hasattr(primitive, 'hole_width') and hasattr(primitive, 'hole_height')
            and primitive.hole_width is not None and primitive.hole_height is not None
            and primitive.hole_width > 0 and primitive.hole_height > 0):

            if primitive.hole_width > 0 and primitive.hole_height > 0:
                cx, cy = center
                w = primitive.hole_width
                h = primitive.hole_height
                box2 = shapely.geometry.box((cx - w) / 2., (cy - h) / 2., (cx + w) / 2., (cy + h) / 2)
                if primitive.level_polarity == 'dark':
                    circle = circle.difference(box2)

        self.update_running(circle)

    def _render_region(self, region, color):
        coords = [region.primitives[0].start]
        for prim in region.primitives:
            if isinstance(prim, primitives.Line):
                coords.append(prim.end)
            else:
                pass
                logger.warn('notline')
        poly = shapely.geometry.Polygon(coords)
        self.update_running(poly, add=not self.invert and region.level_polarity == 'dark')

    def _render_arc(self, arc, color):
        is_circle = False
        two_pi = 2 * math.pi
        angle1 = arc.start_angle
        angle2 = arc.end_angle
        if angle1 == angle2 and arc.quadrant_mode != 'single-quadrant':
            is_circle = True
            # Make the angles slightly different otherwise Cario will draw nothing
            if angle1 == 0:
                if arc.direction == 'counterclockwise':
                    angle1 = two_pi
                else:
                    angle2 = two_pi
            else:
                angle2 -= 0.000000001
        if isinstance(arc.aperture, primitives.Circle):
            width = arc.aperture.diameter if arc.aperture.diameter != 0 else 0.001
        else:
            width = max(arc.aperture.width, arc.aperture.height, 0.001)

        step = abs(angle2 - angle1) / 25.
        if arc.direction == 'counterclockwise':
            if not is_circle and (angle1 > angle2):
                angle1 -= two_pi
        else:
            pass

        angles = list(cammath.frange(angle1, angle2, step))

        coords = [(arc.center[0] + arc.radius*math.cos(a), arc.center[1] + arc.radius*math.sin(a)) for a in angles]
        arc_geom = shapely.geometry.LineString(coords).buffer(
            width/2.,
            cap_style=shapely.geometry.CAP_STYLE.round if isinstance(arc.aperture, primitives.Circle) else shapely.geometry.CAP_STYLE.flat
        )
        self.update_running(arc_geom)


class GerberDrillContext(render.GerberContext):
    def __init__(self, units='inch'):
        super(GerberDrillContext, self).__init__(units=units)

        self.hole_pos = []

    def render_layer(self, layer):
        for prim in layer.primitives:
            self.render(prim)

        return shapely.geometry.MultiPoint(self.hole_pos)

    def _render_drill(self, primitive, color):
        self.hole_pos.append(shapely.geometry.Point(primitive.position[0], primitive.position[1], primitive.radius))


# FIXME making 2 sided boards has not been tested or really considered.  Won't work without some refactoring
@operation(required=['tool_radius'])
def pcb_isolation_geometry(
    gerber_file=None, gerber_data=None, gerber_geometry=None, stepover='40%', outline_separation=0.020, tool_radius=None,
    flipx=False, flipy=False,
):
    if gerber_geometry:
        geom = gerber_geometry
    else:
        geom = pcb_trace_geometry(gerber_file=gerber_file, gerber_data=gerber_data)

    if flipx:
        minx, miny, maxx, maxy = flipx
        geom = shapely.affinity.scale(geom, xfact=-1, origin=(0, 0))
        geom = shapely.affinity.translate(geom, xoff=maxx+minx)

    if flipy:
        minx, miny, maxx, maxy = flipy
        geom = shapely.affinity.scale(geom, yfact=-1, origin=(0, 0))
        geom = shapely.affinity.translate(geom, yoff=maxy+miny)

    if isinstance(geom, shapely.geometry.MultiPolygon):
        in_geoms = geom.geoms
    else:
        in_geoms = []

    # union_geom = shapely.geometry.GeometryCollection()

    geoms = []
    offset = (outline_separation - tool_radius)
    stepovers = int(math.ceil(offset/stepover))
    stepover = offset/stepovers

    if False:
        for g in in_geoms:
            for step in range(1, stepovers+1):
                # print "stepover =", step*stepover
                bgeom = g.buffer(step * stepover)
                # bgeom = g.buffer(step * stepover).difference(union_geom)
                if isinstance(bgeom, shapely.geometry.Polygon):
                    bgeom = shapely.geometry.MultiPolygon([bgeom])

                # union_geom = union_geom.union(bgeom)

                geoms.append(bgeom)
    else:
        union_geom = shapely.ops.cascaded_union(in_geoms)
        for step in range(1, stepovers+1):
            bgeom = union_geom.buffer(step*stepover)
            if isinstance(bgeom, shapely.geometry.Polygon):
                bgeom = shapely.geometry.MultiPolygon([bgeom])

            geoms.append(bgeom)

    return geom, geoms


@operation(required=['depth', 'outline_separation'], operation_feedrate='vector_engrave')
def pcb_isolation_mill(
    gerber_file=None, gerber_data=None, gerber_geometry=None, stepover='40%', outline_separation=None, depth=None, clearz=None,
    xoff=0, yoff=0,
    auto_clear=True, flipx=False, flipy=False, simplify=0.001, zprobe_radius=None,
):
    def _zadjust(x, y):
        if not delauney:
            machine().write("#100=0")
            return "#100"

        pt = shapely.geometry.Point(x, y)

        try:
            match = next(x for x in delauney if x.contains(pt))
        except StopIteration:
            raise Exception("Did not find triangle for point {}".format(list(pt.coords)))

        vars = {
            'px': x,
            'py': y,
        }
        for i, p in enumerate(match.exterior.coords):
            vars['x{}'.format(i+1)] = p[0]
            vars['y{}'.format(i+1)] = p[1]
            vars['z{}'.format(i+1)] = "#{}".format(int(round(p[2])))

        machine().write("#100=[[{y2}-{y3}]*[{x1}-{x3}] + [{x3}-{x2}]*[{y1}-{y3}]]".format(**vars))  # denom
        machine().write("#102=[[[[{y2}-{y3}]*[{px}-{x3}] + [{x3}-{x2}]*[{py}-{y3}]]]/#100]".format(**vars))  # w1 num
        machine().write("#103=[[[[{y3}-{y1}]*[{px}-{x3}] + [{x1}-{x3}]*[{py}-{y3}]]]/#100]".format(**vars))  # w2 num
        machine().write("#104=[1 - #102 - #103]")
        machine().write("#105=[#102*{z1} + #103*{z2} + #104*{z3}]".format(**vars))
        return "#105"

    def _zadjust_geom(_coords, zrad):
        outcoords = []
        lastc = None
        for c in _coords:
            if lastc:
                length = abs(geometry.distance(c, lastc)) if lastc else 0
                xl = c[0] - lastc[0]
                yl = c[1] - lastc[1]
                if zrad and length > zrad/1.5:
                    # print length, ">", zrad / 1.5, length > zrad / 1.5
                    segments = int(1.5*math.ceil(length/zrad))
                    for i in range(segments-1):
                        tc = (
                            round(lastc[0] + xl * i / segments, 3),
                            round(lastc[1] + yl * i / segments, 3),
                        )
                        # print i, lastc, c, tc
                        outcoords.append(tc)

            outcoords.append(c)
            lastc = c

        return outcoords

    def _cut_coords(c, zrad):
        machine().goto(z=clearz)

        if simplify:
            coords = c.simplify(simplify).coords
        else:
            coords = c.coords

        machine().goto(*coords[0])

        if zrad:
            zvar = _zadjust(*coords[0])
            machine().cut(z="[{}-{}]".format(zvar, depth))
        else:
            machine().cut(z=-1*depth)

        for c in _zadjust_geom(coords, zrad):
            if zrad:
                zvar = _zadjust(*coords[0])
                machine().cut(c[0], c[1], "[{}-{}]".format(zvar, depth))
            else:
                machine().cut(c[0], c[1], -1*depth)

    clearz = clearz or 1*constants.MM
    logger.warn("tool radius - depth=%r, base dia=%r, diameter at=%r", depth, machine().tool.diameter_at_depth(0), machine().tool.diameter_at_depth(depth))
    tool_radius = machine().tool.diameter_at_depth(depth)/2.0
    geom, geoms = pcb_isolation_geometry(
        gerber_file=gerber_file,
        gerber_data=gerber_data,
        gerber_geometry=gerber_geometry,
        stepover=stepover,
        outline_separation=outline_separation,
        tool_radius=tool_radius,
        flipx=flipx, flipy=flipy,
    )
    geom = shapely.affinity.translate(geom, xoff=xoff, yoff=yoff)
    delauney = None

    # FIXME
    if zprobe_radius:
        # first lets get a good zero
        zprobe(center=(0, 0), z=0, zretract=1/16., depth=0.5, rate=5, tries=1, setz=True)

        points = []
        minx, miny, maxx, maxy = geom.bounds

        # This is a little BS - we go outside our BB a little because of offsets.  Probably better to calc this
        o = .08
        minx -= o
        miny -= o
        maxx += o
        maxy += o

        width = maxx - minx
        height = maxy - miny

        if zprobe_radius == 'auto':
            autox = width/5.
            autoy = height/5.
            zprobe_radius = min(max(0.325, autox, autoy), 1)  # just a guess really

        xspace = zprobe_radius
        yspace = zprobe_radius/math.sqrt(2)

        divx = width/xspace
        divy = height/yspace
        xspace = width/round(divx)
        yspace = height/round(divy)

        samplesx = int(round(divx)) + 1
        samplesy = int(round(divy)) + 1

        # print "w, h =", width, height
        # print xspace, yspace, samplesx, samplesy

        varnum = 500
        for y in range(samplesy):
            rowspace = 0 if y % 2 == 0 else xspace/2.0
            sx = samplesx if y % 2 == 0 else samplesx - 1
            for x in range(sx):
                cx = minx + xspace*x + rowspace
                cy = miny + yspace*y
                point = shapely.geometry.Point(cx, cy, varnum)
                points.append(point)
                zprobe(center=(cx, cy), z=.125, depth=.25, rate=5, tries=1, storez=varnum)
                varnum += 1

        pg = shapely.geometry.MultiPoint(points)
        delauney = shapely.ops.triangulate(pg, edges=False)
        box = shapely.geometry.box(minx, miny, maxx, maxy)
        geometry.shapely_to_svg('points.svg', [box, pg, shapely.geometry.MultiPolygon(delauney)])

        machine().pause_program()

    for g in geoms:
        g = shapely.affinity.translate(g, xoff=xoff, yoff=yoff)
        for p in g:
            _cut_coords(p.exterior, zprobe_radius)
            for i in p.interiors:
                _cut_coords(i, zprobe_radius)

    if auto_clear:
        machine().goto(z=clearz)

    return geom, geoms


def pcb_layer(gerber_file=None, gerber_data=None):
    if gerber_data is not None:
        return gerber.load_layer_data(gerber_data, gerber_file)
    else:
        return gerber.load_layer(gerber_file)


def pcb_trace_geometry(gerber_file=None, gerber_data=None, union=True):
    b = pcb_layer(gerber_file=gerber_file, gerber_data=gerber_data)
    ctx = GerberGeometryContext()
    return ctx.render_layer(b, union=union)


def pcb_drill_geometry(gerber_file=None, gerber_data=None):
    b = pcb_layer(gerber_file=gerber_file, gerber_data=gerber_data)
    ctx = GerberDrillContext()
    return ctx.render_layer(b)


def pcb_outline_geometry(gerber_file=None, gerber_data=None, union=True):
    b = pcb_layer(gerber_file=gerber_file, gerber_data=gerber_data)
    ctx = GerberGeometryContext()
    return ctx.render_layer(b, union=union)


@operation(required=['depth'], operation_feedrate='drill')
def pcb_drill(
        gerber_file=None, gerber_data=None, gerber_geometry=None, depth=None, flipx=False, flipy=False, clearz=None, auto_clear=True,
        xoff=0, yoff=0,
):
    clearz = clearz or 1*constants.MM

    geoms = []
    if gerber_geometry:
        hole_geom = gerber_geometry
    else:
        hole_geom = pcb_drill_geometry(gerber_file=gerber_file, gerber_data=gerber_data)

    if flipx:
        minx, miny, maxx, maxy = flipx
        hole_geom = shapely.affinity.scale(hole_geom, xfact=-1, origin=(0, 0))
        hole_geom = shapely.affinity.translate(hole_geom, xoff=maxx+minx)

    if flipy:
        minx, miny, maxx, maxy = flipy
        hole_geom = shapely.affinity.scale(hole_geom, yfact=-1, origin=(0, 0))
        hole_geom = shapely.affinity.translate(hole_geom, yoff=maxy+miny)

    hole_geom = shapely.affinity.translate(hole_geom, xoff=xoff, yoff=yoff)

    tool_dia = machine().tool.diameter
    logger.warn("tool dia = %r", tool_dia)
    drill_holes = [x for x in hole_geom if x.coords[0][2] <= tool_dia]
    helical_holes = [x for x in hole_geom if x.coords[0][2] > tool_dia]

    machine().goto(z=1*constants.MM)
    if drill_holes:
        drill_cycle(
            centers=[x.coords[0][:2] for x in drill_holes], z=0, depth=depth, retract_distance=1*constants.MM, rate=2, auto_clear=False
        )

    for h in helical_holes:
        geoms.append(h.buffer(h.coords[0][2], resolution=16))
        helical_drill(center=h.coords[0][:2], outer_rad=h.coords[0][2], z=0, depth=depth, stepdown="10%")

    if auto_clear:
        machine().goto(z=clearz)

    return shapely.geometry.MultiPolygon(geoms)


# FIXME - should use outline if available
@operation(required=['bounds', 'depth'], operation_feedrate='cut', comment="PCB Cutout bounds={bounds}")
def pcb_cutout(gerber_file=None, gerber_data=None, gerber_geometry=None, bounds=None, depth=None, stepdown="50%", clearz=None, auto_clear=True, xoff=0, yoff=0):
    clearz = clearz or 1*constants.MM

    # if gerber_geometry:
    #     geom = gerber_geometry
    #     minx, miny, maxx, maxy = geom.bounds
    # elif gerber_data or gerber_file:
    #     geom = pcb_outline_geometry(gerber_file=gerber_file, gerber_data=gerber_data)
    #     minx, miny, maxx, maxy = geom.bounds
    # else:
    minx, miny, maxx, maxy = bounds
    # logger.warn("outline = ({},{}) to ({},{}) offset by ({}, {})".format(minx, miny, maxx, maxy, xoff, yoff))

    x1 = minx-machine().tool.diameter/2
    x2 = maxx+machine().tool.diameter/2
    y1 = miny-machine().tool.diameter/2
    y2 = maxy+machine().tool.diameter/2

    tab_width = .25

    xt1 = (x1+x2)/2 - tab_width/2.
    xt2 = xt1 + tab_width
    yt1 = (y1+y2)/2 - tab_width/2.
    yt2 = yt1 + tab_width

    for Z in machine().zstep(0, -depth, stepdown):
        machine().goto(xoff+x1, yoff+y1)
        machine().cut(z=Z)

        machine().cut(y=yoff+yt1)
        machine().goto(z=clearz)
        machine().goto(y=yoff+yt2)
        machine().cut(z=Z)
        machine().cut(y=yoff+y2)

        machine().cut(x=xoff+xt1)
        machine().goto(z=clearz)
        machine().goto(x=xoff+xt2)
        machine().cut(z=Z)
        machine().cut(x=xoff+x2)

        machine().cut(y=yoff+yt2)
        machine().goto(z=clearz)
        machine().goto(y=yoff+yt1)
        machine().cut(z=Z)
        machine().cut(y=yoff+y1)

        machine().cut(x=xoff+xt2)
        machine().goto(z=clearz)
        machine().goto(x=xoff+xt1)
        machine().cut(z=Z)
        machine().cut(x=xoff+x1)

    if auto_clear:
        machine().goto(z=clearz)


class PCBProject(object):
    def __init__(self, gerber_input=None ):
        self.gerber_input = gerber_input
        # if isinstance(border, (int, float)):
        #     self.border = [border, border, border, border]
        # else:
        #     self.border = border

        # self.thickness = thickness
        self.layers = None
        # self.auto_zero = auto_zero
        # self.posts = posts
        # self.fixture_width = fixture_width

        self.load(gerber_input)

    @classmethod
    def identify_file(cls, fname):
        ext = os.path.splitext(fname)[-1].lower()
        if ext == ".gbl":
            return 'bottom', 'copper'
        elif ext == '.gtl':
            return 'top', 'copper'
        elif ext == '.drl':
            return 'both', 'drill'
        elif ext == '.gko':
            return 'both', 'outline'
        elif ext == '.gts':
            return 'top', 'solder-mask'
        elif ext == '.gbs':
            return 'bottom', 'solder-mask'
        elif ext == '.gto':
            return 'top', 'silk-screen'
        elif ext == '.gbo':
            return 'bottom', 'silk-screen'
        else:
            return None

    def load(self, gerber_input):
        self.layers = {
        }

        if gerber_input is None:
            logger.warn("gerber_input is None, bailing")
            return

        if isinstance(gerber_input, (list, tuple)):
            for f in gerber_input:
                ftype = self.identify_file(f[0])
                logger.warn("Loading %r type=%r", f[0], ftype)
                if ftype is None:
                    continue

                self.layers[ftype] = {
                    'filename': f[0],
                    'data': f[1].read(),
                }
        elif os.path.isdir(gerber_input):
            logger.warn("gerber_input is directory")
            for fname in os.listdir(gerber_input):
                ftype = self.identify_file(fname)
                if ftype is None:
                    continue

                self.layers[ftype] = {
                    'filename': fname,
                    'data': open(fname).read()
                }

        elif os.path.splitext(gerber_input)[-1].lower() == '.zip':
            logger.warn("gerber_input is zip")
            z = zipfile.ZipFile(gerber_input)
            for i in z.infolist():
                ftype = self.identify_file(i.filename)
                logger.warn("Loading %r type=%r", i.filename, ftype)
                if ftype is None:
                    continue

                self.layers[ftype] = {
                    'filename': i.filename,
                    'data': z.read(i.filename),
                }
        else:
            raise Exception("Input not supported: supply either a directory or zip file containing gerber files")

        self.process_layers()

    def get_layer(self, layer):
        v = self.layers[layer]
        return pcb_layer(gerber_data=v['data'], gerber_file=v['filename'])

    def process_layers(self, union=True):
        union_geom = shapely.geometry.GeometryCollection()

        for k, v in self.layers.items():
            if k == ('both', 'drill'):
                g = pcb_drill_geometry(gerber_data=v['data'], gerber_file=v['filename'])
            elif k[1] == ('outline'):
                g = pcb_outline_geometry(gerber_data=v['data'], gerber_file=v['filename'], union=union)
            else:
            # elif k[1] == ('copper'):
                g = pcb_trace_geometry(gerber_data=v['data'], gerber_file=v['filename'], union=union)

            # logger.warn('%r - %r', k, g.bounds)
            if union:
                v['geometry'] = g
                union_geom = union_geom.union(g)
            else:
                v['geometry'] = g
                union_geom = union_geom.union(shapely.ops.unary_union(g))

        self.bounds = union_geom.bounds
        minx, miny, maxx, maxy = self.bounds

        # if self.auto_zero:
        #     newminx = 0
        #     newminy = 0
        #     xoff = -minx
        #     yoff = -miny
        # else:
        newminx = 0
        newminy = 0
        xoff = -minx
        yoff = -miny
#            newminx = minx - self.border[0]
#            newminy = miny - self.border[1]
#            xoff = yoff = 0

        if union:
            for k, v in self.layers.items():
                v['geometry'] = shapely.affinity.translate(v['geometry'], xoff=xoff, yoff=yoff)  # +self.border[0] / +self.border[1]
        else:
            for k, v in self.layers.items():
                v['geometry'] = [
                    shapely.affinity.translate(x, xoff=xoff + self.border[0], yoff=yoff + self.border[1]) for x in v['geometry']
                ]

        self.bounds = [
            newminx,
            newminy,
            newminx + (maxx - minx),  #  + self.border[0] + self.border[2],
            newminy + (maxy - miny),  #  + self.border[1] + self.border[3],
        ]

    def load_layer(self, file_name, fobj):
        ftype = self.identify_file(file_name)
        logger.warn("load layer, file=%r, fobj=%r, ftype=%r", file_name, fobj, ftype)
        if ftype is None:
            return None

        this = {
            'filename': file_name,
            'data': fobj.read()
        }
        self.layers[ftype] = this

        return this

    def layer_to_svg(self, layer_key, svg_file, width=600, height=600):
        geoms = self.layers[layer_key]['geometry']
        geometry.shapely_to_svg(
            svg_file,
            geoms,
            marginpct=0, width=width, height=height,
        )

    def auto_set_stock(self, side='top', posts=None, fixture_width=None, thickness=None):
        minx, miny, maxx, maxy = self.bounds
        width = maxx - minx
        height = maxy - miny

        px = 0
        if posts == 'x':
            px = 0.5

        if side == 'bottom' and fixture_width > 0:
            rect_stock(
                (width * 1.2)+px, height * 1.2, thickness,
                origin=(fixture_width + minx - width - width*.1, -thickness, maxy - height - height*.1)
            )
        else:
            rect_stock(
                (width * 1.2)+px, height * 1.2, thickness,
                origin=(minx - width * .1, -thickness, maxy - height - height * .1)
            )

    # drill = 'top' or 'bottom' depending on which side to drill from
    # cutout = 'top' or 'bottom' depending on which side to cut out from
    @operation(required=['output_directory', 'iso_bit', 'drill_bit', 'cutout_bit'])
    def pcb_job(
        self,
        output_directory=None, file_per_operation=True, outline_separation=0.020, outline_depth=0.010,
        cutout=None, drill=None,
        iso_bit=None, drill_bit=None, cutout_bit=None, post_bit=None,
        panelx=1, panely=1, flip='y', zprobe_radius=None, side='both',
        border=None, thickness=1.7 * constants.MM, posts=None, fixture_width=None,
    ):
        def _xoff(xi, side='top'):
            minx, miny, maxx, maxy = self.bounds
            pxoff = 0
            if posts == 'x':
                pxoff = 1/4.

            if fixture_width > 0 and side == 'bottom':
                return fixture_width - (xi+1) * (maxx - minx + cutout_bit.diameter)
            else:
                return pxoff + xi*(maxx-minx+cutout_bit.diameter)

        def _yoff(yi):
            minx, miny, maxx, maxy = self.bounds
            return yi*(maxy-miny+cutout_bit.diameter)

        if not os.path.exists(output_directory):
            os.makedirs(output_directory)

        # .... TOP ....
        if side in ['top', 'both']:
            if not file_per_operation:
                machine().set_file(os.path.join(output_directory, 'pcb_top_all.ngc'))
                self.auto_set_stock(side='top', posts=posts, thickness=thickness, fixture_width=fixture_width, )

            if posts != 'none':
                if file_per_operation:
                    machine().set_file(os.path.join(output_directory, 'pcb_top_0_posts.ngc'))
                    self.auto_set_stock(side='top', posts=posts, thickness=thickness, fixture_width=fixture_width, )

                machine().set_tool(post_bit)
                if posts == 'x':
                    minx, miny, maxx, maxy = self.bounds
                    helical_drill(center=(minx - 1/8, (miny+maxy)/2.), outer_rad=1/8., z=0, depth=.65, stepdown="10%")
                    helical_drill(center=(maxx + 1/4. + 1/8., (miny+maxy)/2.), outer_rad=1/8., z=0, depth=.65, stepdown="10%")
                elif posts == 'y':
                    raise Exception("not implemented")

                machine().pause_program()

            if file_per_operation:
                machine().set_file(os.path.join(output_directory, 'pcb_top_1_iso.ngc'))
                self.auto_set_stock(side='top', posts=posts, thickness=thickness, fixture_width=fixture_width, )

            machine().set_tool(iso_bit)
            l = self.layers[('top', 'copper')]
            for x in range(panelx):
                for y in range(panely):
                    pcb_isolation_mill(
                        gerber_geometry=l['geometry'],
                        xoff=_xoff(x), yoff=_yoff(y),
                        outline_separation=outline_separation,
                        depth=outline_depth,
                        zprobe_radius=zprobe_radius,
                    )

            if drill == 'top' and ('both', 'drill') in self.layers:
                if file_per_operation:
                    machine().set_file(os.path.join(output_directory, 'pcb_top_2_drill.ngc'))
                    self.auto_set_stock(side='top', posts=posts, thickness=thickness, fixture_width=fixture_width, )

                machine().set_tool(drill_bit)

                l = self.layers[('both', 'drill')]
                for x in range(panelx):
                    for y in range(panely):
                        pcb_drill(
                            gerber_geometry=l['geometry'],
                            xoff=_xoff(x), yoff=_yoff(y),
                            depth=thickness,
                            flipy=False
                        )

            if cutout == 'top':
                if file_per_operation:
                    machine().set_file(os.path.join(output_directory, 'pcb_top_3_cutout.ngc'))
                    self.auto_set_stock(side='top', posts=posts, thickness=thickness, fixture_width=fixture_width, )

                machine().set_tool(cutout_bit)
                for x in range(panelx):
                    for y in range(panely):
                        pcb_cutout(bounds=self.bounds, depth=thickness, xoff=_xoff(x), yoff=_yoff(y), stepdown="15%")

        if side in ['bottom', 'both']:
            # .... BOTTOM ....
            l = self.layers[('bottom', 'copper')]

            if not file_per_operation:
                machine().set_file(os.path.join(output_directory, 'pcb_bottom_all.ngc'))
                self.auto_set_stock(side='bottom', posts=posts, thickness=thickness, fixture_width=fixture_width, )

            if file_per_operation:
                machine().set_file(os.path.join(output_directory, 'pcb_bottom_1_iso.ngc'))
                self.auto_set_stock(side='bottom', posts=posts, thickness=thickness, fixture_width=fixture_width, )

            machine().set_tool(iso_bit)

            for x in range(panelx):
                for y in range(panely):
                    pcb_isolation_mill(
                        gerber_geometry=l['geometry'],
                        xoff=_xoff(x, side='bottom'), yoff=_yoff(y),
                        outline_separation=outline_separation,
                        depth=outline_depth,
                        flipx=self.bounds if flip == 'x' else False,
                        flipy=self.bounds if flip == 'y' else False,
                        zprobe_radius=zprobe_radius,
                    )

            if drill == 'bottom' and ('both', 'drill') in self.layers:
                if file_per_operation:
                    machine().set_file(os.path.join(output_directory, 'pcb_bottom_2_drill.ngc'))
                    self.auto_set_stock(side='bottom', posts=posts, thickness=thickness, fixture_width=fixture_width, )

                machine().set_tool(drill_bit)

                l = self.layers[('both', 'drill')]
                for x in range(panelx):
                    for y in range(panely):
                        pcb_drill(
                            gerber_geometry=l['geometry'],
                            xoff=_xoff(x, side='bottom'), yoff=_yoff(y),
                            depth=thickness,
                            flipx=self.bounds if flip == 'x' else False,
                            flipy=self.bounds if flip == 'y' else False,
                        )

            if cutout == 'bottom':
                if file_per_operation:
                    machine().set_file(os.path.join(output_directory, 'pcb_bottom_3_cutout.ngc'))
                    self.auto_set_stock(side='bottom', posts=posts, thickness=thickness, fixture_width=fixture_width, )

                machine().set_tool(cutout_bit)
                for x in range(panelx):
                    for y in range(panely):
                        pcb_cutout(bounds=self.bounds, depth=thickness, xoff=_xoff(x, side='bottom'), yoff=_yoff(y), stepdown="15%")

