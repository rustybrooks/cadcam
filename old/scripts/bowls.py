#!/usr/bin/env python

import os, sys
sys.path.append(os.path.curdir)

from campy import *
from surface import *
from geometry import PolySurface, generate_polygon, polar_parameterize, Line


def xprint(*args):
    out = ""
    for a in args:
        out +=  "(%0.3f, %0.3f)  " % a

    print out

import svg, sys
class SVGBowlProfile(object):
    def __init__(self, file, max_width, outter=True):
        self.outter = outter

        svgf = svg.parse(file)
        a, b = svgf.bbox()
        width, height = (b - a).coord()
        svgf = svgf.translate(a).scale(max_width/width)
        a, b = svgf.bbox()

        self.width, self.height = (b - a).coord()

        self.points = []
        for el in svgf.flatten():
            expected_title = "outter" if self.outter else "inner"
            if el.title() != expected_title:
                continue

            #if self.outter:
            for segment in el.segments():
                self.points.extend([[f - g for f, g in zip(x.coord(), a.coord())] for x in segment])
            #else:
            #    for segment in el.segments():
            #        self.points.extend([[f - g for f, g in zip(x.coord(), a.coord())] for x in segment])

        self.points.sort(key=lambda x: x[0])
        self.cache = {}


    def interpolate(self, p1, p2, val):
        #if p1[0] == p2[0]:
        #    return p2[1]

        if p1 is None:
            val = p2[1]
        else:
            denom = (p2[0] - p1[0])
            if denom == 0:
                val = p2[1]
            else:
                pct = (val - p1[0]) / denom
                val = p1[1]*pct + p2[1]*(1-pct)

        if not self.outter:
            val = self.height - val

        return val

    def value(self, rad):
        if rad not in self.cache:
            #return next(x for x in self.points if x[0] >= rad)[1]
            #lastp = (-1, 0 if self.outter else self.height)
            lastp = None
            #print "-----", rad
            for p in self.points:
                #print "%f > %f == %r" % (p[0], rad, p[0] > rad)
                if p[0] > rad:
                    break

                lastp = p

            val = self.interpolate(lastp, p, rad)
            #print lastp, p, "rad=", rad, "val=", val
            self.cache[rad] = val

        return self.cache[rad]




class RadialBowl(CAM):
    def __init__(
            self, tool,
            minor_radius, major_radius, stock_dimensions, zadjust,
            profile_generator=None, rotation_generator=None, curve_generator=None,
            angle_steps=360, radial_step=None,
            material_factor=1, roughing_tool=None, do_rough=True, outter=True
    ):
        super(RadialBowl, self).__init__(tool=None)
        self._tool = tool
        #self.set_speed(self.tool.rough_speed)
        self.minor_radius = minor_radius
        self.major_radius = major_radius
        self.stock_dimensions = stock_dimensions
        self.rotation_generator = rotation_generator
        self.curve_generator = curve_generator
        self.profile_generator = profile_generator
        self.angle_steps = angle_steps
        self.radial_step = (radial_step or 1/4.)
        self.material_factor = material_factor
        self.roughing_tool = roughing_tool or tool
        self.do_rough = do_rough
        self.outter = outter

        self.zadjust = zadjust

        self.curves = {}
        self.rotations = {}
        self.profiles = {}

    def xy(self, angle, radius):
        return [
            radius*math.cos(math.radians(angle)),
            radius*math.sin(math.radians(angle)),
        ]

    def genval(self, rad, storage, generator):
        if rad not in storage:
            storage[rad] = generator(rad)

        return storage[rad]

    def genrot(self, rad):
        return self.genval(rad, self.rotations, self.rotation_generator)

    def genprof(self, rad):
        return self.genval(rad, self.profiles, self.profile_generator) + self.zadjust

    def gencurve(self, rad):
        return self.genval(rad, self.curves, self.curve_generator)

    def genxy(self, angle_index, rad):
        base_angle = 360.0*angle_index/self.angle_steps
        return self.xy(base_angle + self.genrot(rad), self.gencurve(rad)[angle_index]) + [self.genprof(rad)]

    def generate_surface(self, radstep=None, angle_steps=None, rough_factor=4):
        radstep = radstep or self.radial_step
        angle_steps = angle_steps or self.angle_steps

        polys = []
        for angle_index in range(rough_factor, angle_steps+1, rough_factor):
            lastrad = self.minor_radius
            for rad in frange(self.minor_radius+radstep*rough_factor, self.major_radius, radstep*rough_factor):
                pt1 = self.genxy(angle_index, rad)
                pt2 = self.genxy(angle_index-rough_factor, rad)
                pt3 = self.genxy(angle_index-rough_factor, lastrad)
                pt4 = self.genxy(angle_index, lastrad)
                poly1 = Line((pt1, pt2, pt3))
                poly2 = Line((pt3, pt4, pt1))
                polys.append(poly1)
                if not isinstance(poly1.intersection(poly2), Polygon):
                    polys.append(poly2)

                lastrad = rad

        #print "maxdiff", maxdiff
        return PolySurface(polys)

    def generate(self):
        self.set_tool(self._tool)

        # FIXME consider using adaptive step size by angle
        surface = self.generate_surface(self.radial_step, self.angle_steps, rough_factor=1)
        surface.write_obj("./test_out.obj" if self.outter else "./test_in.obj")

        stock_x = self.stock_dimensions[0]
        stock_y = self.stock_dimensions[1]
        stock_z = self.stock_dimensions[2]
        o_x = -self.stock_dimensions[0]/2.
        o_y = -self.stock_dimensions[1]/2.
        o_z = 0

        self.camtain(
            RectStock(
                stock_x,
                stock_y,
                stock_z,
                origin=(o_x, o_z, o_y)
            ),
            origin=(0, 0, 0)
        )

        R = self.tool.diameter/2.0
        if self.outter:
            s = 1.0 * (self.major_radius + self.tool.diameter) / self.major_radius
            boundary_curve = Line([self.genxy(a, self.major_radius) for a in range(angle_steps)]).scale(s, s)
        else:
            s = (self.major_radius + self.tool.diameter) / self.major_radius
            boundary_curve = Line(generate_polygon(sides=360, diameter=(self.major_radius-self.tool.diameter/2.0) * 2.0))

        clearZ = o_z + stock_z + 0.125
        self.goto(z=clearZ)

        if 1:
            self.camtain(ParallelSurfacing(
                tool=self.roughing_tool,
                clearZ=clearZ,
                stepover=0.5,
                stepdown=1,
                boundary=boundary_curve,
                surface=surface,
                material_factor=self.material_factor,
                direction='y',
                roughZ=0.1,
                minZ=self.zadjust if self.outter else None,
            ))

        if 1:
            rough_factor = self.material_factor
            paths = []
            forward = True
            for angle_index in range(rough_factor, angle_steps+1, rough_factor):
                path = []
                for rad in frange(self.minor_radius+radstep*rough_factor, self.major_radius+self.tool.diameter*0.6, radstep*rough_factor):
                    path.append(self.genxy(angle_index, rad))

                if not forward:
                    path.reverse()
                forward = not forward
                paths.append(path)

            self.camtain(PathSurfacing(
                tool=self.tool,
                surface=surface,
                paths=paths,
                clearZ=clearZ
            ))
        else:
            self.camtain(WaterlineSurfacing(
                tool=self.tool,
                clearZ=clearZ,
                boundary=boundary_curve,
                surface=surface,
                material_factor=material_factor,
                minZ=self.zadjust if self.outter else None,
                stepdown=0.05
            ))

        self.goto(z=clearZ)

tool = tools['1/2in spiral ball']

thickness = 2.5
#minrad = 1.5
maxrad = 2

profile_in = SVGBowlProfile("images/bowl_prof_both_1.svg", maxrad, outter=False)
profile_out = SVGBowlProfile("images/bowl_prof_both_1.svg", maxrad, outter=True)

angle_steps = 360
radstep = 1/8.
material_factor = 1
fudge = 0.15
zextra = 0.0

curve = polar_parameterize(LineString(generate_polygon(5, 2)), angle_steps)
curve2 = polar_parameterize(LineString(generate_polygon(360*2, 2)), angle_steps)

zrange = [
    min([x[1] for x in profile_in.points + profile_out.points]),
    max([x[1] for x in profile_in.points + profile_out.points]),
]
print "zrange=", zrange

dimensions = [4.5, 4.5, zextra + zrange[1] - zrange[0] + fudge]

Camtainer(
    "test/bowl_out.ngc",
    RadialBowl(
        tool=tool,
        minor_radius=0, major_radius=maxrad,
        stock_dimensions=dimensions, zadjust=zextra+fudge,
        rotation_generator=lambda x: x*20.,
        curve_generator=lambda x: [x*el for el in curve],
        profile_generator=lambda x: profile_out.value(x),
        angle_steps=angle_steps, radial_step=radstep, material_factor=material_factor, do_rough=1,
        outter=True,
    )
)

Camtainer(
    "test/bowl_in.ngc",
    RadialBowl(
        tool=tool,
        minor_radius=0, major_radius=maxrad,
        stock_dimensions=dimensions, zadjust=fudge,
        rotation_generator=lambda x: 0.,
        curve_generator=lambda x: [x*el for el in curve2],
        profile_generator=lambda x: profile_in.value(x),
        angle_steps=angle_steps, radial_step=radstep, material_factor=material_factor, do_rough=1,
        outter=False,
    )
)

