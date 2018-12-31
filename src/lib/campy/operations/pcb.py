import gerber
from gerber.render import render
import gerber.primitives as primitives
import math
import os
import shapely.affinity
import shapely.geometry
import shapely.ops
import zipfile

from . import operation, machine, helical_drill, rect_stock, zprobe
from .. import constants, environment, geometry


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
        self.remove_polys = []

    def render_layer(self, layer):
        for prim in layer.primitives:
            self.render(prim)

        return shapely.ops.unary_union(self.polys)

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
            self.polys.append(poly)

        elif hasattr(line, 'vertices') and line.vertices is not None:
            print "OTHER"
            print [x for x in line.vertices]

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

        self.polys.append(box)

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

        self.polys.append(circle)

    def _render_region(self, primitive, color):
        pass
        # p = shapely.geometry.MultiPolygon()
        # for prim in primitive.primitives:
        #     if isinstance(prim, Line):
        #                 mask.ctx.line_to(*self.scale_point(prim.end))
        #             else:
        #                 center = self.scale_point(prim.center)
        #                 radius = self.scale[0] * prim.radius
        #                 angle1 = prim.start_angle
        #                 angle2 = prim.end_angle
        #                 if prim.direction == 'counterclockwise':
        #                     mask.ctx.arc(center[0], center[1], radius,
        #                                  angle1, angle2)
        #                 else:
        #                     mask.ctx.arc_negative(center[0], center[1], radius,
        #                                           angle1, angle2)
        #         mask.ctx.fill()
        #         self.ctx.mask_surface(mask.surface, self.origin_in_pixels[0])

        if not self.invert and primitive.level_polarity == 'dark':
            pass  # add
        else:
            pass  # remove


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
    gerber_file=None, gerber_data=None, gerber_geometry=None, stepover='45%', outline_separation=0.020, tool_radius=None,
    flipx=False, flipy=False, depth=None,
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

    geoms = []
    offset = (outline_separation - tool_radius)
    stepovers = int(math.ceil(offset/stepover))
    stepover = offset/stepovers
    for step in range(1, stepovers+1):
        print "stepover =", step*stepover
        bgeom = geom.buffer(step*stepover)
        if isinstance(bgeom, shapely.geometry.Polygon):
            bgeom = shapely.geometry.MultiPolygon([bgeom])

        geoms.append(bgeom)

    return geom, geoms


@operation(required=['depth', 'outline_separation'], operation_feedrate='vector_engrave')
def pcb_isolation_mill(
    gerber_file=None, gerber_data=None, gerber_geometry=None, stepover='45%', outline_separation=None, depth=None, clearz=None,
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

        # px = w1*x1 + w2*x2 + w3*x3
        # py = w1*y1 + w2*y2 + w3*y3
        # w1 = ((y2-y3)(px-x3) + (x3-x2)(py-y3)) / ((y2-y3)(x1-x3) + (x3-x2)(y1-y3))
        # w2 = ((y3-y1)(px-x3) + (x1-x3)(py-y3)) / ((y2-y3)(x1-x3) + (x3-x2)(y1-y3))
        # w3 = 1 - w2 - w1
        # z = w1*z1 + w2*z2 + z3*z3

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
                if length > zrad/1.5:
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
        zvar = _zadjust(*coords[0])
        machine().cut(z="[{}-{}]".format(zvar, depth))

        for c in _zadjust_geom(coords, zrad):
            zvar = _zadjust(*coords[0])
            machine().cut(c[0], c[1], "[{}-{}]".format(zvar, depth))

    clearz = clearz or 0.125
    tool_radius = machine().tool.diameter_at_depth(depth)/2.0
    geom, geoms = pcb_isolation_geometry(
        gerber_file=gerber_file,
        gerber_data=gerber_data,
        gerber_geometry=gerber_geometry,
        stepover=stepover,
        outline_separation=outline_separation,
        tool_radius=tool_radius,
        flipx=flipx, flipy=flipy, depth=depth,
    )
    geom = shapely.affinity.translate(geom, xoff=xoff, yoff=yoff)
    delauney = None

    # FIXME
    if zprobe_radius:
        # first lets get a good zero
        zprobe(center=(0, 0), z=0, zretract=1/16., depth=0.5, rate=5, tries=3, setz=True, clearz=True)

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


def pcb_outline_geometry(gerber_file=None, gerber_data=None):
    if gerber_data is not None:
        b = gerber.load_layer_data(gerber_data, gerber_file)
    else:
        b = gerber.load_layer(gerber_file)

    ctx = GerberGeometryContext()
    return ctx.render_layer(b)


@operation(required=['depth'], operation_feedrate='drill')
def pcb_drill(
        gerber_file=None, gerber_data=None, gerber_geometry=None, depth=None, flipx=False, flipy=False, clearz=None, auto_clear=True,
        xoff=0, yoff=0,
):
    clearz = clearz or 0.125

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
    for h in hole_geom:
        geoms.append(h.buffer(h.coords[0][2], resolution=16))
        helical_drill(center=h.coords[0][:2], outer_rad=h.coords[0][2], z=0, depth=depth, stepdown="10%")

    if auto_clear:
        machine().goto(z=clearz)

    return shapely.geometry.MultiPolygon(geoms)


# FIXME - tabs not supported, add if I ever need
@operation(required=['bounds', 'depth'], operation_feedrate='cut', comment="PCB Cutout bounds={bounds}")
def pcb_cutout(gerber_file=None, gerber_data=None, gerber_geometry=None, bounds=None, depth=None, stepdown="50%", clearz=None, auto_clear=True, xoff=0, yoff=0):
    clearz = clearz or 0.125

    # if gerber_geometry:
    #     geom = gerber_geometry
    #     minx, miny, maxx, maxy = geom.bounds
    # elif gerber_data or gerber_file:
    #     geom = pcb_outline_geometry(gerber_file=gerber_file, gerber_data=gerber_data)
    #     minx, miny, maxx, maxy = geom.bounds
    # else:
    minx, miny, maxx, maxy = bounds
    # print "outline = ({},{}) to ({},{}) offset by ({}, {})".format(minx, miny, maxx, maxy, xoff, yoff)

    x1 = minx-machine().tool.diameter/2
    x2 = maxx+machine().tool.diameter/2
    y1 = miny-machine().tool.diameter/2
    y2 = maxy+machine().tool.diameter/2
    for Z in machine().zstep(0, -depth, stepdown):
        machine().goto(xoff+x1, yoff+y1)
        machine().cut(z=Z)
        machine().cut(x=xoff+x1, y=yoff+y2)
        machine().cut(x=xoff+x2, y=yoff+y2)
        machine().cut(x=xoff+x2, y=yoff+y1)
        machine().cut(x=xoff+x1, y=yoff+y1)

    if auto_clear:
        machine().goto(z=clearz)


class PCBProject(object):
    def __init__(
        self, gerber_input, border=None, auto_zero=True, thickness=1.7*constants.MM, posts=None, fixture_width=None,
    ):
        self.gerber_input = gerber_input
        if isinstance(border, (int, float)):
            self.border = [border, border, border, border]
        else:
            self.border = border

        self.thickness = thickness
        self.layers = None
        self.auto_zero = auto_zero
        self.posts = posts
        self.fixture_width = fixture_width

        self.load(gerber_input)

    def identify_file(self, fname):
        ext = os.path.splitext(fname)[-1].lower()
        if ext == ".gbl":
            return 'bottom-copper'
        elif ext == '.gtl':
            return 'top-copper'
        elif ext == '.drl':
            return 'drill'
        elif ext == '.gko':
            return 'outline'
        else:
            return None

    def load(self, gerber_input):
        self.layers = {
        }

        union_geom = shapely.geometry.GeometryCollection()
        if os.path.isdir(gerber_input):
            for fname in os.listdir(gerber_input):
                ftype = self.identify_file(fname)
                if ftype is None:
                    continue

                self.layers[ftype] = {
                    'filename': fname,
                    'data': open(fname).read()
                }

        elif os.path.splitext(gerber_input)[-1].lower() == '.zip':
            z = zipfile.ZipFile(gerber_input)
            for i in z.infolist():
                ftype = self.identify_file(i.filename)
                if ftype is None:
                    continue

                self.layers[ftype] = {
                    'filename': i.filename,
                    'data': z.read(i.filename),
                }
        else:
            raise Exception("Input not supported: supply either a directory or zip file containing gerber files")

        for k, v in self.layers.items():
            if k == 'drill':
                g = pcb_drill_geometry(gerber_data=v['data'], gerber_file=v['filename'])
            elif k == 'outline':
                g = pcb_outline_geometry(gerber_data=v['data'], gerber_file=v['filename'])
            else:
                g = pcb_trace_geometry(gerber_data=v['data'], gerber_file=v['filename'])

            v['geometry'] = g
            union_geom = union_geom.union(g)

        self.bounds = union_geom.bounds
        minx, miny, maxx, maxy = self.bounds

        if self.auto_zero:
            newminx = 0
            newminy = 0
            xoff = -minx
            yoff = -miny
        else:
            newminx = minx - self.border[0]
            newminy = miny - self.border[1]
            xoff = yoff = 0

        for k, v in self.layers.items():
            v['geometry'] = shapely.affinity.translate(v['geometry'], xoff=xoff+self.border[0], yoff=yoff+self.border[1])

        self.bounds = [
            newminx,
            newminy,
            newminx + (maxx - minx) + self.border[0] + self.border[2],
            newminy + (maxy - miny) + self.border[1] + self.border[3],
        ]

    def auto_set_stock(self, side='top'):
        minx, miny, maxx, maxy = self.bounds
        width = maxx - minx
        height = maxy - miny

        px = 0
        if self.posts == 'x':
            px = 0.5

        if side == 'bottom' and self.fixture_width > 0:
            rect_stock(
                (width * 1.2)+px, height * 1.2, self.thickness,
                origin=(self.fixture_width + minx - width - width*.1, -self.thickness, maxy - height - height*.1)
            )
        else:
            rect_stock(
                (width * 1.2)+px, height * 1.2, self.thickness,
                origin=(minx - width * .1, -self.thickness, maxy - height - height * .1)
            )

    # drill = 'top' or 'bottom' depending on which side to drill from
    # cutout = 'top' or 'bottom' depending on which side to cut out from
    @operation(required=['output_directory', 'iso_bit', 'drill_bit', 'cutout_bit'])
    def pcb_job(
        self,
        output_directory=None, file_per_operation=True, outline_separation=0.020, outline_depth=0.010,
        cutout=None, drill=None,
        iso_bit=None, drill_bit=None, cutout_bit=None, post_bit=None,
        panelx=1, panely=1, flip='y', zprobe_radius=None,
    ):
        def _xoff(xi, side='top'):
            minx, miny, maxx, maxy = self.bounds
            pxoff = 0
#            if self.posts == 'x':
#                pxoff = 1/4.

            if self.fixture_width > 0 and side == 'bottom':
                return self.fixture_width - (xi+1) * (maxx - minx + environment.tools[cutout_bit].diameter)
            else:
                return xi*(maxx-minx+environment.tools[cutout_bit].diameter)

        def _yoff(yi):
            minx, miny, maxx, maxy = self.bounds
            return yi*(maxy-miny+environment.tools[cutout_bit].diameter)

        if not os.path.exists(output_directory):
            os.makedirs(output_directory)

        # .... TOP ....
        if not file_per_operation:
            machine().set_file(os.path.join(output_directory, 'pcb_top_all.ngc'))
            self.auto_set_stock(side='top')

        if self.posts != 'none':
            if file_per_operation:
                machine().set_file(os.path.join(output_directory, 'pcb_top_0_posts.ngc'))
                self.auto_set_stock(side='top')

            machine().set_tool(post_bit)
            if self.posts == 'x':
                minx, miny, maxx, maxy = self.bounds
                helical_drill(center=(minx - 1/8, (miny+maxy)/2.), outer_rad=1/16., z=0, depth=.6, stepdown="10%")
                helical_drill(center=(maxx + 1/4. + 1/8., (miny+maxy)/2.), outer_rad=1/16., z=0, depth=.6, stepdown="10%")
            elif self.posts == 'y':
                raise Exception("not implemented")

        if file_per_operation:
            machine().set_file(os.path.join(output_directory, 'pcb_top_1_iso.ngc'))
            self.auto_set_stock(side='top')

        machine().set_tool(iso_bit)
        l = self.layers['top-copper']
        for x in range(panelx):
            for y in range(panely):
                pcb_isolation_mill(
                    gerber_geometry=l['geometry'],
                    xoff=_xoff(x), yoff=_yoff(y),
                    outline_separation=outline_separation,
                    depth=outline_depth,
                    zprobe_radius=zprobe_radius,
                )

        if drill == 'top':
            if file_per_operation:
                machine().set_file(os.path.join(output_directory, 'pcb_top_2_drill.ngc'))
                self.auto_set_stock(side='top')

            machine().set_tool(drill_bit)

            l = self.layers['drill']
            for x in range(panelx):
                for y in range(panely):
                    pcb_drill(
                        gerber_geometry=l['geometry'],
                        xoff=_xoff(x), yoff=_yoff(y),
                        depth=self.thickness,
                        flipy=False
                    )

        if cutout == 'top':
            if file_per_operation:
                machine().set_file(os.path.join(output_directory, 'pcb_top_3_cutout.ngc'))
                self.auto_set_stock(side='top')

            machine().set_tool(cutout_bit)
            for x in range(panelx):
                for y in range(panely):
                    pcb_cutout(bounds=self.bounds, depth=self.thickness, xoff=_xoff(x), yoff=_yoff(y))

        # .... BOTTOM ....
        l = self.layers['bottom-copper']

        if not file_per_operation:
            machine().set_file(os.path.join(output_directory, 'pcb_bottom_all.ngc'))
            self.auto_set_stock(side='bottom')

        if file_per_operation:
            machine().set_file(os.path.join(output_directory, 'pcb_bottom_1_iso.ngc'))
            self.auto_set_stock(side='bottom')

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

        if drill == 'bottom':
            if file_per_operation:
                machine().set_file(os.path.join(output_directory, 'pcb_bottom_2_drill.ngc'))
                self.auto_set_stock(side='bottom')

            machine().set_tool(drill_bit)

            l = self.layers['drill']
            for x in range(panelx):
                for y in range(panely):
                    pcb_drill(
                        gerber_geometry=l['geometry'],
                        xoff=_xoff(x, side='bottom'), yoff=_yoff(y),
                        depth=self.thickness,
                        flipx=self.bounds if flip == 'x' else False,
                        flipy=self.bounds if flip == 'y' else False,
                    )

        if cutout == 'bottom':
            if file_per_operation:
                machine().set_file(os.path.join(output_directory, 'pcb_bottom_3_cutout.ngc'))
                self.auto_set_stock(side='bottom')

            machine().set_tool(cutout_bit)
            for x in range(panelx):
                for y in range(panely):
                    pcb_cutout(bounds=self.bounds, depth=self.thickness, xoff=_xoff(x, side='bottom'), yoff=_yoff(y))

    #
    #
    #     geoms = [x for x in [
    #         bottom_trace_geom,
    #         #        # top_trace_geom,
    #         drill_geom
    #     ] if x]
    #     geometry.shapely_to_svg('drill.svg', geoms, marginpct=0)
    #     geometry.shapely_to_svg('drill2.svg', list(reversed(bottom_iso_geoms)) + [drill_geom], marginpct=0)
    # #    geometry.shapely_to_svg('drill.svg', union_geom, marginpct=0)