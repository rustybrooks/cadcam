#!/usr/bin/env python

#from matplotlib import pyplot
#import matplotlib.image as mpimg
import shapely.geometry

from campy import *
from hsm import *
import math

MM = 0.0393701

followers = [6*MM, 10*MM, 12*MM, 13*MM, 16.4*MM, 19*MM, 22*MM]
bits = [1/4., 3/8., 1/2.]



def ball_mill_offset_for_angle(r, angle):
    xoff = r*math.cos(math.radians(angle))
    yoff = r - r*math.sin(math.radians(angle))
    return xoff, yoff


#def interior_outline_to_template(cut_line, cutter_diameter, follower_diameter):
#    router_line = cut_line.parallel_offset(cutter_diameter/2.0, 'right').simplify(.001)
#
#    foo = []
#    for x, y in zip(*router_line.xy):
#        foo.append((2*x, 2*y))
#
#    if isinstance(cut_line, shapely.geometry.LineString):
#        template_center_line = shapely.geometry.LineString(foo)
#    elif isinstance(cut_line, shapely.geometry.LinearRing):
#        template_center_line = shapely.geometry.LinearRing(foo)
#
#    template_border = template_center_line.parallel_offset(follower_diameter/2.0, 'left').simplify(0.001)
#
#    return router_line, template_center_line, template_border


class ArbitraryTemplate(CAM):
    def __init__(self, geometry_params=None, offset=None,
                 template_thickness=0.5, exterior_follower=22*MM, interior_follower=6*MM,
                 stepdown=None, tolerance=0.03, block=None, material_factor=1.0,
                 cutting_tool=None, exterior_tool=None, interior_tool=None, holes=None):
        super(ArbitraryTemplate, self).__init__(tool=None)

        self.offset = offset or [0, 0]
        self.geometry_params = geometry_params
        self.interior_follower = interior_follower
        self.exterior_follower = exterior_follower
        self.template_thickness = template_thickness
        self.stepdown = stepdown if stepdown else 0.04 # 0.02 was very smooth
        self.tolerance = tolerance
        self.block = block
        self.holes = holes
        self.material_factor = material_factor
        self.cutting_tool = cutting_tool
        self.exterior_tool = exterior_tool if exterior_tool else tools['1/2in spiral ball']
        self.interior_tool = interior_tool if interior_tool else tools['1/8in spiral upcut']

        self.fixed_geometry = None

        self.clearZ = 0.25
        self.bmangle = 90.0 - math.degrees(math.atan(self.template_thickness / self.tolerance))
        self.bmx, self.bmy = ball_mill_offset_for_angle(self.exterior_tool.diameter / 2.0, self.bmangle)
        self.template_width, self.template_height = self.dimensions()

    def outline_to_template_cut(self, type, offset):
        cut_line, router_line, t_center_line, cnc_t_border = self.outline_to_template(type)
        if abs(offset) < 0.001:
            return cnc_t_border
        else:
            #return cnc_t_border.parallel_offset(offset, side='right' if type == 'interior' else 'left')
            return cnc_t_border.parallel_offset(offset, side='right' if type == 'interior' else 'right')

    def generate_cutline(self):
        geom = self.generate_geometry()
        segments = []
        for el in geom:
            if el[0] == 'line' or el[0] == 'point':
                segments.append((el[1:]))
            elif el[0] == 'arc':
                _, x, y, rad, a1, a2, direction = el
                for angle in frange(a1, a2, 1.0*self.material_factor):
                    segments.append((
                        x + rad*math.cos(math.radians(angle)),
                        y + rad*math.sin(math.radians(angle)),
                    ))

        #segments.append(segments[0])

        # print "CUT LINE", ["(%0.2f, %0.2f)" % (x, y) for x, y in segments]
        return shapely.geometry.LineString(segments, )

    def outline_to_template(self, type='exterior'):
        # def minmax(ls):
        #     miny = 1e12
        #     maxy = -1e12
        #
        #     for el in ls.coords:
        #        if el[1] > maxy: maxy = el[1]
        #        if el[1] < miny: miny = el[1]
        #
        #     return maxy - miny

        cut_line = self.generate_cutline()
        cutter_diameter = self.cutting_tool.diameter
        follower_diameter = self.interior_follower if type == 'interior' else self.exterior_follower

        router_line = cut_line.parallel_offset(cutter_diameter/2.0, 'right' if type == 'interior' else 'left')

        foo = []
        for x, y in zip(*router_line.xy):
            foo.append((2*x, 2*y))

        if isinstance(cut_line, shapely.geometry.LineString):
            template_center_line = shapely.geometry.LineString(foo)
        elif isinstance(cut_line, shapely.geometry.LinearRing):
            template_center_line = shapely.geometry.LinearRing(foo)


        tooldiam = self.interior_tool.diameter if type == 'interior' else 0
        #template_border = template_center_line.parallel_offset(follower_diameter/2.0, 'right' if type == 'interior' else 'left')
        #cnc_template_border = template_border.parallel_offset(tool.diameter/2.0, 'left' if type == 'interior' else 'right')

        cnc_template_border = template_center_line.parallel_offset((follower_diameter - tooldiam)/2.0, 'left' if type == 'interior' else 'right')
        # if self.geom_type == 'left':
        #    print "border", ["(%0.2f, %0.2f)" % (x, y) for x, y in cnc_template_border.coords]

        return cut_line, router_line, template_center_line, cnc_template_border

    def dimensions(self):
        ls = self.outline_to_template_cut('exterior', 0)

        minx = 1e12
        miny = 1e12
        maxx = -1e12
        maxy = -1e12

        for x, y in zip(*ls.xy):
            if x < minx: minx = x
            if x > maxx: maxx = x
            if y < miny: miny = y
            if y > maxy: maxy = y

        return max(minx, maxx)*2, max(miny, maxy)*2

    def cut_geometry(self, geom, depth):
        for el in geom:
            # print "OFFSET", self.offset
            if el[0] == 'point':
                self.goto(x=self.offset[0] + el[1], y=self.offset[1] + el[2])
                self.cut(z=depth)
            elif el[0] == 'line':
                self.cut(x=self.offset[0] + el[1], y=self.offset[1] + el[2])
            elif el[0] == 'arc':
                _, x, y, rad, a1, a2, direction = el
                self.cut_arc2(self.offset[0] + x, self.offset[1] + y, rad, start_angle=a1, end_angle=a2, clockwise=direction == 'clockwise', cut_to=False, move_to=True)

    def generate_geometry(self):
        return self.geometry(**self.geometry_params)

    def cut_interior_segments(self, offset, depth, comment=None):
        self.comment(comment)
        ls = self.outline_to_template_cut('interior', offset)
        self.cut_linestring(ls, depth)

    def cut_exterior_segments(self, offset, depth, comment=None, direction=1):
        self.comment(comment)
        ls = self.outline_to_template_cut('exterior', offset)
        self.cut_linestring(ls, depth, direction=direction)

    def maximum_interior_offset(self, tolerance):
        return 0
        return .05
        trial = tolerance

        while True:
            # print "Trying", trial
            ls = self.outline_to_template_cut('interior', trial)
            if ls.is_empty:
                break
            else:
                trial += tolerance

        return trial - tolerance

    # replace in subclass
    def geometry(self, **kwargs):
        pass

    """
    # geometry is assumed to be closed
    # geometry composed of intersections of straight line segments can not be made internally
    # so we need to shorten the segments and introduce an arc to represent the movement of the router bit
    def generate_fixed_geometry(self, geom):
        # print "...", geom
        newgeom = []

        first = geom[0]

        if first[0] != 'point':
            raise Exception("First element of geometry must be a point (specifically the starting point)")

        here = first[1:3]
        newgeom.append(first)

        R = self.cutting_tool.diameter/2.0

        geom = geom[1:]
        geom_shift = geom[1:] + geom[:1]

        for this, next in zip(geom[:], geom_shift[:]):
            if this[0] == 'line' and next[0] == 'line':
                v1 = make_vector(here, this[1:3])
                mv1 = make_vector(this[1:3], here)
                v2 = make_vector(this[1:3], next[1:3])
                a = abs(angle_between(mv1, v2))  # FIXME this abs is super fishy
                backoff = R / math.tan(a/2)
                backoff_ratio = 1 - (backoff/length(v1))
                new_endpoint = [x + y*backoff_ratio for x, y in zip(here, v1)]
                newgeom.append(('line', new_endpoint[0], new_endpoint[1]))

                unit_bisect = unit(bisect(mv1, v2))
                minus_unit_bisect = [0-x for x in unit_bisect]

                offsetlen = R*math.cos(math.pi/2 - a/2) + backoff*math.cos(a/2)
                newpt = [x + y * offsetlen for x, y in zip(this[1:3], unit_bisect)]
                x, y = newpt
                a1 = math.degrees(angle_between([1, 0], minus_unit_bisect) + (math.pi/2 - a/2))
                a2 = math.degrees(angle_between([1, 0], minus_unit_bisect) - (math.pi/2 - a/2))
                newgeom.append(('arc', x, y, R, a1, a2, 'clockwise'))

                here = this[1:3]
                hereend = [x + y for x, y in zip(this[1:3], lengthen(v2, 1-backoff_ratio))]
            else:
                print "UNHANDLED:", this[0], next[0]
                pass

        newgeom[0][1:3] = hereend
        self.fixed_geometry = newgeom

        return newgeom

    def scale_geometry(self, geom, scale):
        newgeom = []
        for el in geom:
            newel = list(el)
            if el[0] == 'point' or el[0] == 'line':
                newel[1] *= scale
                newel[2] *= scale
            elif el[0] == 'arc':
                newel[1] *= scale
                newel[2] *= scale
                newel[3] *= scale

            newgeom.append(newel)

        return newgeom

    def offset_geometry_scale(self, geom, offset):
        if offset < 0:
            scale = 1 - abs(offset*2)/(self.geometry_params['diameter'] / math.sqrt(2))
        else:
            scale = 1 + (offset*2)/(self.geometry_params['diameter'] / math.sqrt(2))

        # print "offset=", offset, "scale=", scale
        return self.scale_geometry(geom, scale)

    def offset_geometry(self, geom, offset):
        def _offset(origin, vv1, offset):
            vv2 = [x*offset for x in unit(crossproduct(vv1 + [0], [0, 0, -1]))][:2] # to get CW rotation
            return [x + y for x, y in zip(origin, vv2)]

        if offset == 0:
            return geom

        # print  "====="
        newgeom = []

        first = geom[0]
        next = geom[1]
        here = first[1:3]
        geom = geom[1:]
        geom_shift = geom[1:] + geom[:1]

        newgeom.append(['point'] + here)

        for this, next in zip(geom[:], geom_shift[:]):
            if this[0] == 'line' and next[0] == 'line':
                p1 = here
                p2 = this[1:3]
                p3 = next[1:3]

                ap1 = _offset(p1, make_vector(p1, p2), offset)
                bp2 = _offset(p3, make_vector(p2, p3), offset)

                a = ap1
                b = make_vector(p1, p2)
                c = bp2
                d = make_vector(p2, p3)

                u=(b[0] * (c[1]-a[1]) + b[1]*(a[0]-c[0]))/(d[0]*b[1]-d[1]*b[0])
                intersection = [x + u*y for x, y in zip(c, d)]

                newgeom.append(['line'] + intersection)
                here = p2

            elif this[0] == 'arc':
                _, x, y, r, a1, a2, cw = this
                newthis = list(this)
                newthis[3] = this[3] + offset
                # print "rad = ", newthis[3]
                if newthis[3] > 0:
                    newgeom.append(newthis)
                    arc_start, arc_end = self.arc_start_end(x, y, max(0, r), a1, a2, cw == 'clockwise')
                    here = arc_end
                if newthis[3] < 0:
                    newgeom.append(newthis)
                    arc_start, arc_end = self.arc_start_end(x, y, max(0, r), a1, a2, cw == 'clockwise')
                    here = arc_end

            elif this[0] == 'line':
                v1 = make_vector(here, this[1:3])
                v2 = [x*offset for x in unit(crossproduct(v1 + [0], [0, 0, -1]))][:2] # to get CW rotation
                newthis = list(this)
                newpt = [x + y for x, y in zip(this[1:3], v2)]
                newthis[1:3] = newpt
                newgeom.append(newthis)

                here = this[1:3]

        last = newgeom[-1]
        if last[0] == 'line':
            newgeom[0][1:] = list(last[1:])
        elif last[0] == 'arc':
            # print last
            _, x, y, r, a1, a2, cw = last
            arc_start, arc_end = self.arc_start_end(x, y, max(0, r), a1, a2, cw == 'clockwise')
            # print x, y, arc_start, arc_end
            newgeom[0][1:] = arc_end

        return newgeom
    """
    def generate_hole_dims(self):
        # print "template dims", self.template_width, self.template_height

        if self.holes is None:
            holes = []
            # hole spacing is 1", we want an even number of inches
            hole_width = int(math.ceil(self.template_width))
            if hole_width % 2 == 1:
                hole_width += 1

            hole_height = int(math.ceil(self.template_height))
            if hole_height % 2 == 1:
                hole_height += 1

            print "holes", hole_width, hole_height

            #holes.append((-hole_width/2., 0))
            #holes.append(( hole_width/2., 0))

            holes.append((-hole_width/2., hole_height/2.))
            holes.append(( hole_width/2., hole_height/2.))
            holes.append(( hole_width/2., -hole_height/2.))
            holes.append((-hole_width/2., -hole_height/2.))
        else:
            holes = self.holes

        hole_width = 2 * max([abs(x[0]) for x in holes] or [0])
        hole_height = 2 * max([abs(x[1]) for x in holes] or [0])
        # print "hole dims = ", hole_width, hole_height
        if self.block[0] is None:
            self.block[0] = max(self.template_width, hole_width) + 1.5

        if self.block[1] is None:
            self.block[1] = max(self.template_height, hole_height) + 1.5

        self.camtain(RectStock(*self.block, origin=(-self.block[0] / 2.0, -self.block[2], -self.block[1] / 2.0)))

        return holes

    def generate_rough(self):
        stepover = self.exterior_tool.diameter * 0.2 * self.material_factor  # FIXME
        stepover = min(stepover, self.exterior_tool.diameter*0.95)
        stepdown = self.exterior_tool.diameter/2.0*self.material_factor
        # print "ext stepdown", stepdown

        clearance_width = self.template_width + self.tolerance + self.tool.diameter
        clearance_height = self.template_height + self.tolerance + self.tool.diameter

        diff1 = self.block[0] - clearance_width
        diff2 = self.block[1] - clearance_height
        # print diff1, diff2

        start_offset = (max(diff1, diff2) + self.tool.diameter)/2.0
        end_depth = self.template_thickness + self.bmy
        start_depth = min(stepdown, end_depth)
        # print stepdown, start_depth, end_depth
        for depth in frange(start_depth, end_depth, stepdown):
            # print "depth", depth
            self.cut_exterior_segments(start_offset+self.bmx, -depth)

        for step in frange(
                        start_offset - stepover,
                        (self.tolerance)/2.0,
                        stepover):
            self.cut_exterior_segments(step + self.bmx, -self.template_thickness - self.bmy)

    def generate_exterior(self):
        ## Exterior ####################
        self.goto(z=self.clearZ)
        direction = 1
        for depth in frange(0, self.template_thickness, min(self.stepdown*self.material_factor, .5)*self.tool.diameter):
            offset = -self.tolerance / 2.0 + self.tolerance * depth / self.template_thickness
            self.cut_exterior_segments(offset + self.bmx, -self.bmy - depth, direction=direction)
            direction *= -1

    def generate_interior(self):
        ## Interior ####################
        if self.interior_follower is not None:
            max_interior_offset = self.maximum_interior_offset(self.interior_tool.diameter/4.0) - self.interior_tool.diameter/4.0

            cleanup_offset = 0.025
            stepover = self.interior_tool.diameter * 0.2 * self.material_factor  # FIXME
            stepover = min(stepover, self.interior_tool.diameter*0.95)
            stepdown = self.interior_tool.diameter/2.0*self.material_factor

            self.set_tool(self.interior_tool)
            self.goto(z=self.clearZ)
            start_offset = max_interior_offset
            for depth in frange(min(stepdown, self.template_thickness), self.template_thickness, stepdown):
                self.cut_interior_segments(start_offset, -depth - self.bmy, "Cutting at offset %r" % (start_offset, ))

            for offset in frange(start_offset - stepover, cleanup_offset, stepover):
                self.cut_interior_segments(offset, -self.template_thickness-self.bmy, "Cutting at offset %r" % (offset, ))

            if cleanup_offset > 0:
                self.push_speed(self.interior_tool.finish_speed)
                self.cut_interior_segments(0, -self.template_thickness-self.bmy)
                self.pop_speed()

    def generate_holes(self, holes, rivnut):
        ## Cut holes ####################
        # cut holes and relief for inserts
        # I'm currently using inserts with these dimensions
        # major_dia = .396
        # major_depth = .05
        minor_dia = HoleSize.nuts[rivnut]['minor_dia']
        minor_depth = HoleSize.nuts[rivnut]['minor_length']
        for hole in holes:
            self.goto(z=self.clearZ)
            center = (hole[0], hole[1])
            _type = hole[2] if len(hole) > 2 else 'rivnut'
            # center = (hole[0], hole[1], 0)
            # self.camtain(HSMCirclePocket(
            #     self.tool, center=center, inner_rad=0, outer_rad=major_dia/2.0, depth=major_depth
            # ))

            print hole, _type
            if _type == 'rivnut':
                self.camtain(HelicalDrill(
                    self.tool, center=center, z=-self.template_thickness-self.bmy, outer_rad=minor_dia/2.0,
                    depth=minor_depth, stepdown=self.interior_tool.diameter/3.0
                ))
            else:
                self.camtain(HelicalDrill(
                    self.tool, center=center, z=0, outer_rad=1.05*self.tool.diameter/2.,
                    depth=self.stock.thickness, stepdown=self.interior_tool.diameter / 3.0

                ))

    def generate(self):

        self.set_tool(self.exterior_tool)
        self.set_speed(self.tool.rough_speed)

        holes = self.generate_hole_dims()
        self.goto(z=self.clearZ)
        self.generate_rough()
        self.generate_exterior()
        if holes:
            self.generate_holes(self.holes, 'rivnut-M5')

        self.goto(z=self.clearZ)

    def cut_linestring(self, ls, depth, direction=1):
        if ls.is_empty:
            return

        try:
            ls = ls.simplify(0.001*self.material_factor)
        except NotImplementedError:
            pass

        c = ls.coords
        dist = distance(c[0], c[-1])

        xl, yl = ls.xy
        if dist > 0.001 and direction == -1:
            xl.reverse()
            yl.reverse()

        self.cut(x=self.offset[0] + xl[0], y=self.offset[1] + yl[0])
        self.cut(z=depth)
        for x, y in zip(xl[1:], yl[1:]):
            self.cut(x=self.offset[0] + x, y=self.offset[1] + y)

        # self.cut(x=self.offset[0] + xl[0], y=self.offset[1] + yl[0])


class MortiseTenonTemplate2(ArbitraryTemplate):
    def __init__(self, *args, **kwargs):
        super(MortiseTenonTemplate2, self).__init__(*args, **kwargs)

    def geometry(self, width=0, thickness=0):
        geom = []
        xx = (width-thickness)/2.0
        yy = thickness/2.0

        geom.append(('point', -xx, yy))
        geom.append(('line', xx, yy))
        #geom.append(('arc', xx, 0, yy, 90, 270, 'clockwise'))  ## This seems wrong
        geom.append(('arc', xx, 0, yy, 90, -90, 'clockwise'))
        geom.append(('line', -xx, -yy))
        geom.append(('arc', -xx, 0, yy, 270, 90, 'clockwise'))

        return geom


class PolyTenonTemplate(ArbitraryTemplate):
    def __init__(self, *args, **kwargs):
        super(PolyTenonTemplate, self).__init__(*args, **kwargs)

    def geometry(self, diameter=0, rotation=None, sides=0):
        geom = []

        def point(angle):
            return [
                (diameter/2.0)*math.sin(math.radians(angle)),
                (diameter/2.0)*math.cos(math.radians(angle)),
            ]

        angle_incr = 360.0/sides
        if rotation is None:
            rotation = -angle_incr/2.0

        geom.append(['point'] + point(rotation))
        for angle in frange(rotation + angle_incr, 360+rotation, angle_incr):
            geom.append(['line'] + point(angle))

        return geom


class BoxJointTemplate(ArbitraryTemplate):
    def __init__(self, *args, **kwargs):
        self._offset = 0
        self.teeth = kwargs.pop('teeth', 1)
        self.tooth = kwargs.pop('tooth', 1.0)
        self.height = kwargs.pop('height', 1.0)
        self.stock = kwargs.pop('stock')
        self.rough_stepover = kwargs.pop('rough_stepover', 0.1)
        self.rough_stepdown = kwargs.pop('rough_stepdown', 1)
        self.geom_type = 'whole'
        self._clearZ = kwargs.pop('clearZ', 1)
        super(BoxJointTemplate, self).__init__(*args, **kwargs)
	self.clearZ = self._clearZ

    def geometry(self):
        geom = []
        xx = self.tooth
        yy = self.height

        if self.geom_type == 'whole':
            geom.append(('point', -xx/2.,  -yy/2.))
            geom.append(('line',  -xx/2.,   yy/2.))
            geom.append(('arc',   0,       yy/2., xx/2., 180, 0, 'clockwise'))
            geom.append(('line',  xx/2.,   -yy/2.))
            geom.append(('arc',   0,      -yy/2., xx/2., 0, -180, 'clockwise'))
        elif self.geom_type == 'right':
            geom.append(('arc',   0,       -yy / 2., xx/2., -90, -180, 'clockwise'))
            geom.append(('line',  -xx/2.,  yy/2.))
            geom.append(('arc',   0,       yy/2., xx/2., 180, 90, 'clockwise'))
        elif self.geom_type == 'left':
            #geom.append(('point', -xx/2.,  -yy/2.))
            #geom.append(('line',  -xx/2.,   yy/2.))
            geom.append(('arc',   0,       yy/2., xx/2., 90, 0, 'clockwise'))
            geom.append(('line',  xx/2.,   -yy/2.))
            geom.append(('arc',   0,      -yy/2., xx/2., 0, -90, 'clockwise'))

        # print self.geom_type
        return geom

    def generate_profile(self):
        # cut profile of template
        for t in range(-1, self.teeth+1):
            if t == -1:
                self.geom_type = 'left'
            elif t == self.teeth:
                self.geom_type = 'right'
            else:
                self.geom_type = 'whole'

            self.offset = [self.space*t - self._offset, 0]
            # self.goto(z=self.clearZ)
            self.generate_exterior()

    def generate_rough(self):
        for t in range(-1, self.teeth):
            bx1 = 0 - self.exterior_tool.diameter/2.
            bx2 = bx1 + self.space + self.exterior_tool.diameter # FIXME dunno why this isn't symmetrical

            by1 = -self.stock.height / 2. - self.exterior_tool.diameter
            by2 = self.stock.height / 2. + self.exterior_tool.diameter
            box = Line([[bx1, by1], [bx1, by2], [bx2, by2], [bx2, by1], [bx1, by1]])

            box = Line(box.difference(self.line).exterior.coords)
            box = Line(box.difference(self.line.translate(x=self.space)).exterior.coords)

            self.goto(z=self.clearZ)
            self.camtain(HSMPocket(
                tool=self.exterior_tool,
                segs=LineSet([box.translate(x=self.space*t - self._offset)]),
                stepover=self.rough_stepover, stepdown=self.rough_stepdown,
                material_factor=self.material_factor,
                z=0,
                depth=self.template_thickness + self.bmy,
            ))

    def generate(self):

        self.set_tool(self.exterior_tool)
        self.set_speed(80)

        # space = (2*self.tooth - self.cutting_tool.diameter/2.)*2. + self.exterior_follower/2.
        self.offset = [0, 0]
        self.space = 4*self.tooth

        self.camtain(self.stock)

        self.line = Line(self.outline_to_template_cut('exterior', self.bmx + self.tolerance/2. + self.exterior_tool.diameter*.05).coords)
        # bounds = line.bounds()
        # tooth_width = bounds[2] - bounds[0]
        # offset = (self.stock.width - space*self.teeth)/2.
        self._offset = (self.space*(self.teeth-1))/2.

        holddowns = [x for x in self.holes if len(x) > 2 and x[2] != 'rivnut']
        if holddowns:
            self.generate_holes(holddowns, 'rivnut-1/4-20')
            self.tool = None
            self.set_tool(self.exterior_tool)
            self.camtain(self.stock)
            self.end_program()
            self.f.next_part()

        # self.generate_rough()
        # self.end_program()
        # self.f.next_part()
        # self.tool = None
        # self.set_tool(self.exterior_tool)
        # self.camtain(self.stock)

        self.generate_profile()

        rivnuts = [x for x in self.holes if len(x) < 3 or x[2] == 'rivnut']
        if rivnuts:
            self.end_program()
            self.f.next_part()
            self.tool = None
            self.set_tool(self.exterior_tool)
            self.camtain(self.stock)
            self.generate_holes([x for x in self.holes if len(x) < 3 or x[2] == 'rivnut'], 'rivnut-1/4-20')

        self.goto(z=self.clearZ)


class BaseGrid(CAM):
    def __init__(self, rows, cols, thickness):
        tool = tools['1/4in spiral upcut']
        super(BaseGrid, self).__init__(tool=tool)
        self.rows = rows
        self.cols = cols
        self.thickness = thickness

    def generate(self):
        #self.set_speed(50)
        self.set_speed(self.tool.rough_speed)

        self.camtain(RectStock(self.cols+2, self.rows+2, self.thickness, origin=(-(self.cols+2)/2.0, 0, -(self.rows+2)/2.0)))
        R = self.tool.diameter / 2.0

        clearZ = .25

        nut = HoleSize.nuts['rivnut-M5']
        for row in range(self.rows):
            y = 0.5 + -self.rows/2. + row
            for col in range(self.cols):
                if row % 2 == 0:
                    x = .5 + -self.cols/2. + col
                else:
                    x = self.cols/2. - col - 0.5

                c = [x, y, self.thickness]
                self.goto(z=clearZ)
                #self.camtain(HelicalDrill(tool=self.tool, center=c, outer_rad=nut['major_dia']/2.0, depth=nut['major_length']))
                self.camtain(CircleProfile(tool=self.tool, center=c, radius=nut['major_dia']/2.0, depth=nut['major_length'], stepdown=R/2.))
                self.camtain(HelicalDrill(tool=self.tool, center=c, outer_rad=nut['minor_dia']/2.0, depth=self.thickness))

        self.goto(z=clearZ)
        self.write("M0")  # pause

        width = self.cols
        height = self.rows
        rradius = 0.5

        xxx = width/2.0
        yyy = height/2.0

        self.goto(x=-xxx+rradius, y=yyy)
        for depth in frange(self.thickness, 0, self.tool.diameter/2.0):
            if depth == 0:
                offset = 0
                self.push_speed(self.tool.finish_speed)
            else:
                offset = 0.020

            radius = rradius + offset/2.0
            xx = xxx + offset
            yy = yyy + offset

            self.cut(x=-xx+radius, y=yy)
            self.cut(z=depth)

            self.cut(x=xx-radius, y=yy)
            self.cut_arc2(xx-radius, yy-radius, radius, 90, 0, adjust_tool_radius=False, clockwise=True)

            self.cut(x=xx, y=-yy+radius)
            self.cut_arc2(xx-radius, -yy+radius, radius, 0, 270, adjust_tool_radius=False, clockwise=True)

            self.cut(x=-xx+radius, y=-yy)
            self.cut_arc2(-xx+radius, -yy+radius, radius, 270, 180, adjust_tool_radius=False, clockwise=True)
            
            self.cut(x=-xx, y=yy-radius)
            self.cut_arc2(-xx+radius, yy-radius, radius, 180, 90, adjust_tool_radius=False, clockwise=True)

        self.pop_speed()
        self.goto(z=clearZ)

      
# This is all hard-coded for now because it's a temp thing that I don't know if I'll use again
class CNCMortise(MortiseTenonTemplate2):
    def __init__(self):

        tool = tools['1/4in spiral upcut']
        #super(CNCMortise, self).__init__(tool=tool)

        self.material_factor = .8
        th = 0.413
        self.geometry_params = {'width': 2.390, 'thickness': th}
        self.tool = tool
        self.template_thickness = 0.75

        self.set_speed(tool.rough_speed)

    def geometry(self, width=0, thickness=0):
        geom = []
        yy = (width-thickness)/2.0
        xx = thickness/2.0

        foo = width/2 - 1/8. + .153
        geom.append(('point', xx, yy-foo))
        geom.append(('line', xx, -yy-foo))
        geom.append(('arc', 0, -yy-foo, xx, 0, -180, 'clockwise'))
        geom.append(('line', -xx, yy-foo))
        geom.append(('arc', 0, yy-foo, xx, 180, 0, 'clockwise'))

        return geom

    def generate(self):

        geom = self.generate_cutline()
        geom = geom.parallel_offset(self.tool.diameter/2.0, 'right')
        stepdown = self.tool.diameter/2.0*self.material_factor
        for depth in frange(self.template_thickness-stepdown, 0.0, stepdown):
            self.cut_linestring(geom, depth)
            #print geom

        self.goto(z=self.template_thickness+0.25)
#        self.goto(x=-3.5)


tool = tools['1/8in spiral ball']
if __name__ == "__main__":
    # actual measurements
    # width from 1.170 to 1.212 - 42 thou
    # height 5.130 to 5.183 - 53 thou
    # slot 6.25mm / .244 in 4.181 in long
    #
    # smaller one
    # width 1.080 to 1.180
    # height from 3.000 to 3.108
    # thickness 1/2ish
    # inside line 2.175
    # with 3/8" bit, gives 1.33" wide tennon
    #Camtainer(
    #    "./test/tenon_halfx3.ngc",
    #    MortiseTenonTemplate(
    #        tool, tenon_width=3.0, tenon_thickness=3/8.,
    #        exterior_follower=10*MM, interior_follower=6*MM,
    #        tolerance=.100, stepdown=1/8., template_thickness=1/2.
    #    )
    #)

    """
    Camtainer(
        "./test/tenon_halfx3_block.ngc",
        MortiseTenonTemplate(
            tenon_width=3.0, tenon_thickness=3/8.,
            exterior_follower=10*MM, interior_follower=6*MM,
            tolerance=.125, template_thickness=0.5, block=[None, None, 1], material_factor=1
        )
    )
    """
    """
    Camtainer(
        "./test/tenon_halfx3_2.ngc",
        MortiseTenonTemplate2(
            geometry_params=dict(width=3.0, thickness=3/8.),
            exterior_follower=10*MM, interior_follower=6*MM,
            tolerance=.125, template_thickness=0.5, block=[None, None, 1], material_factor=5,
            cutting_tool=tools['1/4in spiral upcut'],
            interior_tool=tools['1/8in spiral upcut'],
        )
    )
    """
    """
    Camtainer(
        "./test/tenon_4.ngc",
        PolyTenonTemplate(
            geometry_params=dict(diameter=2.0*math.sqrt(2), sides=4),
            exterior_follower=10*MM, interior_follower=6*MM,
            tolerance=.100, stepdown=1/8., template_thickness=1/2.,
            cutting_tool=tools['1/4in spiral upcut'], block=[None, None, 1],
            interior_tool=tools['1/4in spiral upcut'],
            exterior_tool=tools['1/4in spiral upcut'],
            material_factor=1
        )
    )
    """
    """
    Camtainer(
        "./test/tenon_5.ngc",
        PolyTenonTemplate(
            geometry_params=dict(diameter=2.0*math.sqrt(2), sides=5),
            exterior_follower=10*MM, interior_follower=6*MM,
            tolerance=.100, stepdown=1/8., template_thickness=1/2.,
            cutting_tool=tools['1/2in spiral upcut'], block=[None, None, 1]
        )
    )
    """
    """
    Camtainer(
        "./test/tenon_14_6_1_26.ngc",
        PolyTenonTemplate(
            geometry_params=dict(diameter=1.26*1.130/1.110, sides=6),  # adjustment factor is to make better fit
            exterior_follower=6*MM,
            interior_follower=6*MM,
            tolerance=.100, template_thickness=.500,
            cutting_tool=tools['1/4in spiral upcut'],
            interior_tool=tools['1/4in spiral upcut'],
            exterior_tool=tools['1/2in spiral upcut'],
            block=[None, None, 1], material_factor=1,
            holes=[[-2, 0], [0, 0], [2, 0]]
        )
    )
    """

    """
    Camtainer(
        "./test/tenon_38_6_1_26.ngc",
        PolyTenonTemplate(
            geometry_params=dict(diameter=1.26, sides=6),
            exterior_follower=6*MM,
            interior_follower=6*MM,
            tolerance=.100, template_thickness=.500,
            cutting_tool=tools['3/8in spiral upcut'],
            interior_tool=tools['1/4in spiral upcut'],
            exterior_tool=tools['1/4in spiral upcut'],
            block=[None, None, 1], material_factor=1,
            holes=[[-2, 0], [0, 0], [2, 0]]
        )
    )

    Camtainer(
        "./test/tenon_12_6_1_26.ngc",
        PolyTenonTemplate(
            geometry_params=dict(diameter=1.26, sides=6),
            exterior_follower=6*MM,
            interior_follower=6*MM,
            tolerance=.100, template_thickness=.500,
            cutting_tool=tools['1/2in spiral upcut'],
            interior_tool=tools['1/4in spiral upcut'],
            exterior_tool=tools['1/4in spiral upcut'],
            block=[None, None, 1], material_factor=1,
            holes=[[-2, 0], [0, 0], [2, 0]]
        )
    )
"""

# Camtainer("test/grid_4x3.ngc", BaseGrid(rows=3, cols=4, thickness=0.5))

# Camtainer("test/table_mortise.ngc", CNCMortise())


thickness = 1.5
height = 4.5

# teeth = 11; width = 20
teeth = 11; width = 21
material_factor = 1

Camtainer("test/box_jig_quarter_inch.nc", [
    BoxJointTemplate(
        clearZ = 1,
        stock=RectStock(width, height, thickness, origin=(-width/2., -thickness, -height/2.)),
        teeth=teeth, height=1.25, tooth=3/8.,
        geometry_params={},
        exterior_follower=6*MM,
        interior_follower=None,
        tolerance=0.050, template_thickness=0.5,
        cutting_tool=tools['1/4in spiral upcut'],
        interior_tool=None,
        exterior_tool=tools['1/4in spiral ball'],
        block=[None, None, 1], material_factor=material_factor,
        rough_stepover=.25, rough_stepdown=1.5, stepdown=0.10,
        holes=[
            [-7, 1.95], [7, 1.95],
            [-8, -1.25, 'through'], [-8, 1.25, 'through'],
            [-4, 1.25, 'through'], [-4, -1.25, 'through'],
            [0, -1.25, 'through'], [0, 1.25, 'through'],
            [4, +1.25, 'through'], [4, -1.25, 'through'],
            [8, -1.25, 'through'], [8, 1.25, 'through'],
            [-7, -1.95], [7, -1.95],
        ]
    )
])


