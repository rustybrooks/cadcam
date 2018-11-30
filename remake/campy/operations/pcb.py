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
    gerber_file=None, gerber_data=None, gerber_geometry=None, stepover='20%', stepovers=1, tool_radius=None,
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

    geoms = []
    for step in range(1, stepovers+1):
        bgeom = geom.buffer(tool_radius*step*(1-stepover))
        if isinstance(bgeom, shapely.geometry.Polygon):
            bgeom = shapely.geometry.MultiPolygon([bgeom])

        geoms.append(bgeom)

    return geom, geoms


@operation(required=['depth'], operation_feedrate='vector_engrave')
def pcb_isolation_mill(
    gerber_file=None, gerber_data=None, gerber_geometry=None, stepover='20%', stepovers=1, depth=None, clearz=None,
    auto_clear=True, flipx=False, flipy=False, simplify=0.001, zprobe_radius=None,
):
    def _cut_coords(c):
        machine().goto(z=clearz)

        if simplify:
            coords = c.simplify(simplify).coords
        machine().goto(coords[0][0], coords[0][1])
        machine().cut(z=-depth)

        for c in coords:
            machine().cut(c[0], c[1])

    clearz = clearz or 0.125
    tool_radius = machine().tool.diameter_at_depth(depth)/2.0
    geom, geoms = pcb_isolation_geometry(
        gerber_file=gerber_file,
        gerber_data=gerber_data,
        gerber_geometry=gerber_geometry,
        stepover=stepover,
        stepovers=stepovers,
        tool_radius=tool_radius,
        flipx=flipx, flipy=flipy,
    )

    # FIXME
    if zprobe_radius:
        # first lets get a good zero
        zprobe(center=(0, 0), z=0, zretract=1/16., depth=0.5, rate=5, tries=3, setz=True, clearz=True)

        points = []
        minx, miny, maxx, maxy = geom.bounds
        width = maxx - miny
        height = maxy - miny

        if zprobe_radius == 'auto':
            autox = width/5.
            autoy = height/5.
            print autox, autoy
            zprobe_radius = min(max(0.25, autox, autoy), 1)  # just a guess really

        xspace = zprobe_radius
        yspace = zprobe_radius/math.sqrt(2)

        divx = width/xspace
        divy = height/yspace
        xspace *= divx/round(divx)
        yspace *= divy/round(divy)

        samplesx = int(width/xspace)+1
        samplesy = int(height/yspace)+1
        print divx, samplesx
        print divy, samplesy
        #xoff = (width - (samplesx*xspace))/2.0
        #yoff = (height - (samplesy*yspace))/2.0

        print xspace, yspace, samplesx, samplesy, width/samplesx, height/samplesy
        varnum = 500
        pointmap = {}
        for y in range(samplesy):
            rowspace = 0 if y % 2 == 0 else xspace/2.0
            sx = samplesx if y % 2 == 0 else samplesx - 1
            for x in range(sx):
                print ".....", x, y
                cx = round(minx + xspace*x + rowspace, 3)
                cy = round(miny + yspace*y, 3)
                point = shapely.geometry.Point(cx, cy)
                points.append(point)
                zprobe(center=(cx, cy), z=.125, depth=.25, rate=5, tries=1, storez=varnum)
                pointmap[(cx, cy)] = [varnum, point]
                varnum += 1

        pg = shapely.geometry.MultiPoint(points)
        delauney = shapely.ops.triangulate(pg, edges=False)
        box = shapely.geometry.box(minx, miny, maxx, maxy)
        geometry.shapely_to_svg('points.svg', [box, pg, shapely.geometry.MultiPolygon(delauney)])

    for g in geoms:
        for p in g:
            _cut_coords(p.exterior)
            for i in p.interiors:
                _cut_coords(i)

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
        gerber_file=None, gerber_data=None, gerber_geometry=None, depth=None, flipx=False, flipy=False, clearz=None, auto_clear=True
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
    print "outline = ({},{}) to ({},{}) offset by ({}, {})".format(minx, miny, maxx, maxy, xoff, yoff)

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
        self, gerber_input, border=None, auto_zero=True, thickness=1.7*constants.MM
    ):
        self.gerber_input = gerber_input
        if isinstance(border, (int, float)):
            self.border = [border, border, border, border]
        else:
            self.border = border

        self.thickness = thickness
        self.layers = None
        self.auto_zero = auto_zero

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
            newminy = miny - self.border[0]
            xoff = yoff = 0

        # union_geom = shapely.affinity.translate(union_geom, xoff=minx, yoff=miny)
        for k, v in self.layers.items():
            v['geometry'] = shapely.affinity.translate(v['geometry'], xoff=xoff+self.border[0], yoff=yoff+self.border[1])

        self.bounds = [
            newminx,
            newminy,
            newminx + (maxx - minx) + self.border[0] + self.border[2],
            newminy + (maxy - miny) + self.border[1] + self.border[3],
        ]

    def auto_set_stock(self):
        minx, miny, maxx, maxy = self.bounds
        width = maxx - minx
        height = maxy - miny
        rect_stock(
            width * 1.2, height * 1.2, self.thickness,
            origin=(minx - width * .1, -self.thickness, maxy - height - height * .1)
        )

    # drill = 'top' or 'bottom' depending on which side to drill from
    # cutout = 'top' or 'bottom' depending on which side to cut out from
    @operation(required=['output_directory', 'iso_bit', 'drill_bit', 'cutout_bit'])
    def pcb_job(
        self,
        output_directory=None, file_per_operation=True, outline_stepovers=2, outline_depth=0.010,
        cutout=None, drill=None,
        iso_bit=None, drill_bit=None, cutout_bit=None,
        panelx=1, panely=1, flip='y', zprobe_radius=None,
    ):
        def _xoff(xi):
            minx, miny, maxx, maxy = self.bounds
            return xi*(maxx-minx+environment.tools[cutout_bit].diameter)

        def _yoff(yi):
            minx, miny, maxx, maxy = self.bounds
            return yi*(maxy-miny+environment.tools[cutout_bit].diameter)

        if not os.path.exists(output_directory):
            os.makedirs(output_directory)

        # .... TOP ....
        if not file_per_operation:
            machine().set_file(os.path.join(output_directory, 'pcb_top_all.ngc'))
            self.auto_set_stock()

        if file_per_operation:
            machine().set_file(os.path.join(output_directory, 'pcb_top_1_iso.ngc'))
            self.auto_set_stock()

        machine().set_tool(iso_bit)

        l = self.layers['top-copper']
        for x in range(panelx):
            for y in range(panely):
                pcb_isolation_mill(
                    gerber_geometry=shapely.affinity.translate(l['geometry'], xoff=_xoff(x), yoff=_yoff(y)),
                    stepovers=outline_stepovers,
                    depth=outline_depth,
                    zprobe_radius=zprobe_radius,
                )

        if drill == 'top':
            if file_per_operation:
                machine().set_file(os.path.join(output_directory, 'pcb_top_2_drill.ngc'))
                self.auto_set_stock()

            machine().set_tool(drill_bit)

            l = self.layers['drill']
            for x in range(panelx):
                for y in range(panely):
                    pcb_drill(
                        gerber_geometry=shapely.affinity.translate(l['geometry'], xoff=_xoff(x), yoff=_yoff(y)),
                        depth=self.thickness,
                        flipy=False
                    )

        if cutout == 'top':
            if file_per_operation:
                machine().set_file(os.path.join(output_directory, 'pcb_top_3_cutout.ngc'))
                self.auto_set_stock()

            machine().set_tool(cutout_bit)
            for x in range(panelx):
                for y in range(panely):
                    pcb_cutout(bounds=self.bounds, depth=self.thickness, xoff=_xoff(x), yoff=_yoff(y))

        # .... BOTTOM ....
        l = self.layers['bottom-copper']

        if not file_per_operation:
            machine().set_file(os.path.join(output_directory, 'pcb_bottom_all.ngc'))
            self.auto_set_stock()

        if file_per_operation:
            machine().set_file(os.path.join(output_directory, 'pcb_bottom_1_iso.ngc'))
            self.auto_set_stock()

        machine().set_tool(iso_bit)

        for x in range(panelx):
            for y in range(panely):
                pcb_isolation_mill(
                    gerber_geometry=shapely.affinity.translate(l['geometry'], xoff=_xoff(x), yoff=_yoff(y)),
                    stepovers=outline_stepovers,
                    depth=outline_depth,
                    flipx=self.bounds if flip == 'x' else False,
                    flipy=self.bounds if flip == 'y' else False,
                    zprobe_radius=zprobe_radius,
                )

        if drill == 'bottom':
            if file_per_operation:
                machine().set_file(os.path.join(output_directory, 'pcb_bottom_2_drill.ngc'))
                self.auto_set_stock()

            machine().set_tool(drill_bit)

            l = self.layers['drill']
            for x in range(panelx):
                for y in range(panely):
                    pcb_drill(
                        gerber_geometry=shapely.affinity.translate(l['geometry'], xoff=_xoff(x), yoff=_yoff(y)),
                        depth=self.thickness,
                        flipx=self.bounds if flip == 'x' else False,
                        flipy=self.bounds if flip == 'y' else False,
                    )

        if cutout == 'bottom':
            if file_per_operation:
                machine().set_file(os.path.join(output_directory, 'pcb_bottom_3_cutout.ngc'))
                self.auto_set_stock()

            machine().set_tool(cutout_bit)
            for x in range(panelx):
                for y in range(panely):
                    pcb_cutout(bounds=self.bounds, depth=self.thickness, xoff=_xoff(x), yoff=_yoff(y))

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
