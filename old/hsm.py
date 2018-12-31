#!/usr/bin/env python

#  Some high-speed machining exploration
import math

from campy import *


# This assumes you want a *through* groove.  It is not going to cut down to the needed dimension for you
# type is 'circle' or 'semicircle' for now
# safety margin is the multiple of how far back to start in units of width/2 (radius of circle being cut)
#    There is no reason to have a margin of more than 2.0 or less than 0
#
# rough_margin is a terrible word.  It's basically how much size to leave over after roughing for the final pass
# it's in absolute distance, not a percent
#
# if you need to plunge in, go to your clear height first
class HSMStraightGroove(CAM):
    def __init__(self, tool, p1, p2, width, z, depth, stepover=None, type='semicircle', safety_margin=None, rough_margin=0.0, through=True, plunge=False):
        super(HSMStraightGroove, self).__init__(tool=None)

        self._tool = tool
        self.p1 = p1
        self.p2 = p2
        self.z = z
        self.width = width
        self.type = type
        self.safety_margin = safety_margin if safety_margin is not None else ([1, 1] if through else [0, 0])
        self.stepover = stepover if stepover else 1/8.0  # FIXME just a guess!
        self.rough_margin = rough_margin
        self.through = through
        self.plunge = plunge
        self.depth = depth

    def generate(self):


        self.set_tool(self._tool)
        self.set_speed(self.tool.rough_speed) # FIXME
        clearZ = self.z + 0.25

        self.comment("HSMStraightGroove p1=%r, p2=%r, width=%r, z=%r" % (list(self.p1), list(self.p2), self.width, self.z))
        self.goto(z=clearZ)

        p1x, p1y = self.p1
        p2x, p2y = self.p2

        #rough_z = self.z + self.rough_margin  # replace rough_z once we have proper slot finishing
        rough_z = self.z - self.depth
        rough_width = self.width - 2*self.rough_margin

        R = self.tool.diameter/2.0
        pathR = rough_width/2.0 - R

        vector = (p2x - p1x, p2y - p1y)
        lv = length(vector)
        av = math.degrees(angle_between([1, 0], vector))
        unit_vector = [foo/lv for foo in vector]
        #r_vector = [foo*pathR for foo in unit_vector]
        #step_vector = [foo*self.stepover for foo in unit_vector]

        safety_distance_start = self.width*self.safety_margin[0]/2
        safety_distance_end = self.width*self.safety_margin[1]/2

        if not self.through:
            safety_distance_end -= (self.width/2.0)

            #if self.type == 'circle':
            safety_distance_start -= (self.width/2.0)

        start = [a - safety_distance_start*b for a, b in zip(self.p1, unit_vector)]

        # start_point = [-safety_distance_start*foo+bar for foo, bar in zip(unit_vector, self.p1)] + [rough_z]
        # end_point = [(-safety_distance_end + lv)*foo+bar for foo, bar in zip(unit_vector, self.p1)] + [rough_z]

        if self.plunge:
            here = [-safety_distance_start*foo+bar for foo, bar in zip(unit_vector, self.p1)] + [self.z]
            startrad = min(R, self.width/2)
            self.camtain(HelicalDrill(self.tool, center=here, outer_rad=startrad, depth=self.depth))

            stepsize = self.stepover*self.tool.diameter
            if startrad + stepsize < self.width/2.0:
                for rad in frange(startrad + stepsize, self.width/2.0, stepsize):
                    self.cut_arc2(here[0], here[1], radius=rad, start_angle=0, end_angle=0, clockwise=False, move_to=True, inside=True)


        self.goto(z=clearZ)
        self.goto(x=start[0], y=start[1])
        self.goto(z=rough_z)
        forward = True

        for step in frange(-safety_distance_start, lv + safety_distance_end, self.tool.diameter*self.stepover):
            here = [step*foo+bar for foo, bar in zip(unit_vector, self.p1)] + [rough_z]
            if self.type == 'circle':
                self.cut_arc2(here[0], here[1], radius=pathR, start_angle=av-90, end_angle=av-90, clockwise=False, cut_to=True)
            elif self.type == 'semicircle':
                # FIXME without return_to is better?
                #self.cut_arc2(here[0], here[1], radius=pathR, start_angle=av, end_angle=av-180, clockwise=False, cut_to=True, return_to=True)
                self.cut_arc2(here[0], here[1], radius=pathR, start_angle=av-90, end_angle=av+90, clockwise=False, cut_to=True, return_to=False)

            elif self.type == 'swing':
                # FIXME without return_to is better?
                #self.cut_arc2(here[0], here[1], radius=pathR, start_angle=-90, end_angle=90, clockwise=False, cut_to=True, return_to=True)
                if forward:
                    self.cut_arc2(here[0], here[1], radius=pathR, start_angle=av, end_angle=av-180, clockwise=False, cut_to=True, return_to=False)
                else:
                    self.cut_arc2(here[0], here[1], radius=pathR, start_angle=av, end_angle=av+180, clockwise=True, cut_to=True, return_to=False)

                forward = not forward

        # replace this with a slot finishing thingy
        if self.rough_margin > 0:
            xoff = math.cos(math.radians(90-av))*(self.width/2 - R)
            yoff = math.sin(math.radians(90-av))*(self.width/2 - R)

            c1 = [(-safety_distance_start)*foo+bar for foo, bar in zip(unit_vector, self.p1)] + [self.z - self.depth]
            c2 = [(lv+safety_distance_end)*foo+bar for foo, bar in zip(unit_vector, self.p1)] + [self.z - self.depth]

            self.cut(x=c2[0] - xoff, y=c2[1] + yoff, z=self.z - self.depth)
            self.cut(x=c1[0] - xoff, y=c1[1] + yoff)

            self.goto(x=c1[0] + xoff, y=c1[1] - yoff)
            self.cut(x=c2[0] + xoff, y=c2[1] - yoff)

        # should probably go to clearZ after...


# This is a groove that follows a (symetric) boundary path
class HSMPathGroove(CAM):
    def __init__(
            self, tool, path, width_path, z, depth, stepover=None, type='semicircle', safety_margin=None, rough_margin=0.0,
            through=True, plunge=False, climb=True, stepdown=None, material_factor=None
    ):
        super(HSMPathGroove, self).__init__(tool=None)

        self._tool = tool
        self.path = path
        self.width_path = width_path
        self.z = z
        self.type = type
        self.safety_margin = safety_margin if safety_margin is not None else ([1, 1] if through else [0, 0])
        self.stepover = stepover if stepover else 1/8.0  # FIXME just a guess!
        self.rough_margin = rough_margin
        self.through = through
        self.plunge = plunge
        self.depth = depth
        self.material_factor = material_factor
        self.stepdown = stepdown
        self.climb = climb

    def generate(self):


        self.set_tool(self._tool)
        self.set_speed(self.tool.rough_speed) # FIXME

        self.comment("HSMPathGroove z=%r" % (self.z, ))

        #rough_z = self.z + self.rough_margin  # replace rough_z once we have proper slot finishing
        rough_z = self.z - self.depth

        R = self.tool.diameter/2.0


"""
class HSMCleanoutCorner(CAM):
    def __init__(self, tool, corner_point, z, initial_radius=None, stepover=None, quadrant=(1, 1), depth=None, type='circle', rough_margin=0.0):
        super(HSMCleanoutCorner, self).__init__(tool=None)

        self._tool = tool
        self.corner_point = corner_point
        self.z = z
        self.stepover = stepover
        self.type = 'circle'
        self.rough_margin = rough_margin
        self.initial_radius = initial_radius
        self.quadrant = quadrant

    def generate(self):
        

        self.set_tool(self._tool)
        self.set_speed(self.tool.rough_speed) # FIXME


        r = self.tool.diameter / 2.0

        for rad in frange(self.initial_radius, r, self.stepover*self.tool.diameter):
            center = (
                self.corner_point[0] + self.quadrant[0]*(rad + self.rough_margin),
                self.corner_point[1] + self.quadrant[1]*(rad + self.rough_margin),
            )
            if rad-r > 0:
                self.cut_arc2(center[0], center[1], radius=rad-r, start_angle=0, end_angle=0, clockwise=True, cut_to=True, return_to=False)
            else:
                self.goto(x=center[0], y=center[1])

        # FIXME
        if self.rough_margin > 0.0:
            pass
"""


class HSMRectPocket(CAM):
    def __init__(
        self, tool, p1, p2, z, depth, stepdown=1, stepover=1/5., rough_margin=None, climb=None, corner_relief=False,
        material_factor=1, finish_offset=0, finish_passes=0
    ):
        super(HSMRectPocket, self).__init__(tool=None)
        self._tool = tool
        self.depth = depth
        self.stepover = stepover
        self.stepdown = stepdown
        self.rough_margin = rough_margin
        self.z = z
        self.climb = climb
        self.material_factor = material_factor
        self.corner_relief = corner_relief
        self.finish_offset = finish_offset
        self.finish_passes = finish_passes

        self.p1 = p1
        self.p2 = p2

    def generate(self):

        self.set_tool(self._tool)

        segs = LineSet([
            Line([
                [self.p1[0], self.p1[1]],
                [self.p1[0], self.p2[1]],
                [self.p2[0], self.p2[1]],
                [self.p2[0], self.p1[1]],
                [self.p1[0], self.p1[1]]
            ])
        ])

        self.camtain(HSMPocket(
            self.tool, segs=segs, stepover=self.stepover, stepdown=self.stepdown, z=self.z, depth=self.depth,
            material_factor=self.material_factor, climb=self.climb, finish_offset=self.finish_offset, finish_passes=self.finish_passes
        ))

        if self.corner_relief:
            print "CORNER"
            self.camtain(RectPocketCornerRelief(
                tool=self.tool, p1=self.p1, p2=self.p2, z=self.z, depth=self.depth, stepdown=self.stepdown,
            ))


class HSMCirclePocket(CAM):
    def __init__(
            self, tool, center, inner_rad=None, z=None, outer_rad=None, depth=None, stepover=0.25, stepdown=.2,
            comment=None, climb=True, speed=None, material_factor=1,
    ):
        super(HSMCirclePocket, self).__init__()
        # self._tool = tool
        # self.center = center
        # self.inner_rad = inner_rad
        # self.outer_rad=outer_rad
        # self.depth = depth or 0
        # self.stepover = stepover
        # self.stepdown = stepdown
        # self.comment_message = comment
        # self.climb = climb
        # self.z = z
        # self.material_factor = material_factor
        # self.speed = speed

    def generate(self):
        self.depth = self.depth or 0

        # self.set_tool(self._tool)

        stepdown = self.calc_stepdown()
        stepover = self.calc_stepover()
        clearZ = self.z + 0.25

        self.comment(self.comment or "HSM Circle Pocket")
        self.push_speed(self.speed or self.tool.rough_speed)

        R = self.tool.diameter / 2.0

        if self.inner_rad is not None and self.inner_rad > 0:
            startrad = self.inner_rad+R
        else:
            startrad = min(R, self.outer_rad)

        self.camtain(HelicalDrill(
                self.tool, center=self.center, outer_rad=startrad, z=self.z, depth=self.depth,
                clockwise=self.climb, speed=self.speed, stepdown=self.stepdown,
        ))

        for Z in self.zstep(self.z, self.z-self.depth, stepdown):
            self.goto(z=clearZ)
            self.goto(*self.center)
            self.goto(z=Z)
            for rad in frange(startrad, self.outer_rad, stepover):
                self.cut_arc2(self.center[0], self.center[1], radius=rad-R, start_angle=0, end_angle=0, clockwise=self.climb, cut_to=True, return_to=False)

        self.pop_speed()


class HSMFacing(CAM):
    def __init__(self, tool, p1, p2, z, depth, stepdown=None, stepover=.9, rough_margin=0.0, type=None):
        super(HSMFacing, self).__init__(tool=None)
        self._tool = tool
        self.depth = depth
        self.stepover = stepover
        self.stepdown = stepdown if stepdown is not None else depth
        self.rough_margin = rough_margin
        self.z = z
        self.type = type
        self.clearZ = self.z + 0.25

        self.p1 = p1
        self.p2 = p2

    def generate(self):

        self.set_tool(self._tool)
        stepover = self.calc_stepover()
        stepdown = self.calc_stepdown()

        px1 = min(self.p1[0], self.p2[0])
        px2 = max(self.p1[0], self.p2[0])
        py1 = min(self.p1[1], self.p2[1])
        py2 = max(self.p1[1], self.p2[1])

        R = self.tool.diameter / 2.0

        right_to_left = False
        self.goto(z=self.clearZ)
        easyR = R*1.05
        for Z in self.zstep(self.z, self.z - self.depth, stepdown):
            tx1 = px1 - easyR
            tx2 = px2 + easyR
            ty1 = py1 - R + stepover
            ty2 = py2 + R - stepover

            if right_to_left:
                self.goto(tx1, ty2-R)
            else:
                self.goto(tx2, ty1+R)
            self.goto(z=Z)

            # self.cut_arc2(tx1+R, ty2-R, R, start_angle=180, end_angle=90)
            end_cycle = False
            while True:
                if right_to_left:
                    # left to right segment
                    self.cut_arc2(tx1 + R, ty2 - R, R, start_angle=180, end_angle=90)
                    self.cut(x=tx2-R)
                    self.cut_arc2(tx2 - R, ty2 - R, R, start_angle=90, end_angle=0)

                    self.goto(y=ty1+R)

                    # right to left segment
                    self.cut_arc2(tx2-R, ty1+R, R, start_angle=0, end_angle=-90)
                    self.cut(x=tx1+R)
                    self.cut_arc2(tx1+R, ty1+R, R, start_angle=-90, end_angle=-180)
                else:
                    # left to right segment
                    self.cut_arc2(tx2 - R, ty1 + R, R, start_angle=0, end_angle=-90)
                    self.cut(x=tx1 + R)
                    self.cut_arc2(tx1 + R, ty1 + R, R, start_angle=-90, end_angle=-180)

                    self.goto(y=ty2 - R)

                    # right to left segment
                    self.cut_arc2(tx1 + R, ty2 - R, R, start_angle=180, end_angle=90)
                    self.cut(x=tx2 - R)
                    self.cut_arc2(tx2 - R, ty2 - R, R, start_angle=90, end_angle=0)

                ty1 += stepover
                ty2 -= stepover

                diff = ty2 - ty1
                if diff <= 0:
                    if -diff < stepover:
                        end_cycle = True
                        right_to_left = not right_to_left
                    break

                if right_to_left:
                    self.goto(y=ty2-R)
                else:
                    self.goto(y=ty1+R)

            if end_cycle:
                if right_to_left:
                    self.cut(x=tx1)
                else:
                    self.cut(x=tx2)


class HSMPocket(Voronoi):
    def __init__(
        self, tool, stepover=None, segs=None, z=0, depth=None, stepdown=None, material_factor=1, climb=False,
        finish_offset=0, finish_passes=0,
    ):
        super(HSMPocket, self).__init__(tool=None)
        self._tool = tool
        self.stepover = stepover or 0.10
        self.stepdown = stepdown or 1.5
        self.depth = depth
        self.material_factor = material_factor
        self.climb = climb
        self.z = z
        self.finish_offset = finish_offset
        self.finish_passes = finish_passes

        self.segs = segs
        R = tool.diameter/2.
        self.segs = self.segs.enforce_direction(clockwise=True)
        # self.segs = self.segs.simplify(0.001)

        self.scaled_segs, self.scale, self.offset = self.get_scaled_segs(offset=R + self.finish_offset)
        self.print_scale = 1.0 / self.scale

        self.clearZ = self.z + 1/4.

    def so(self, c):
        return c.x * self.print_scale + self.offset[0], c.y * self.print_scale + self.offset[1]

    # rapid from prev, to nxt
    # while staying inside c1(r1) and c2(r)
    def rapid_to_next(self, prv_tang, nxt_tang, c1, r1, c2, r2, prv, nxt):
        rad_default = 0.03
        rad = min(rad_default, 0.9 * r1, 0.9 * r2)

        prv_tang.normalize()
        nxt_tang.normalize()

        prv_normal = -1 * prv_tang.xy_perp()
        nxt_normal = nxt_tang.xy_perp()

        cen1 = prv + rad * prv_normal  # + rad1*prv_tang
        cen2 = nxt - rad * nxt_normal  # rapid_tang # + rad1*prv_tang

        rapid_tang = cen2 - cen1
        rapid_tang.normalize()

        trg1 = cen1 + rad * rapid_tang.xy_perp()  # prv_tang
        src2 = cen2 + rad * rapid_tang.xy_perp()

        soc = self.so(cen1)
        self.cut_arc3(
                x=soc[0], y=soc[1], start_pt=self.so(prv), end_pt=self.so(trg1), radius=self.print_scale*rad,
                clockwise=True, cut_to=False, comment='lead out arc - rapid_to_next'
        )  # lead-out arc

        self.cut(*self.so(src2))

        soc = self.so(cen2)
        self.cut_arc3(
                x=soc[0], y=soc[1], start_pt=self.so(src2), end_pt=self.so(nxt), radius=self.print_scale*rad,
                clockwise=True, comment='lead in arc - rapid_to_next'
        )  # lead-in arc

    def rapid_to_new_branch(self, prv_tang, nxt_tang, c1, r1, c2, r2, prv, nxt):
        # rapid from prev, to nxt
        # while staying inside c1(r1) and c2(r)
        rad_default = 0.03
        rad1 = min(rad_default, 0.9 * r1)  # wrong? we get the new-branch r1 here, while we would want the old-branch r1
        rad2 = min(rad_default, 0.9 * r2)
        prv_tang.normalize()
        nxt_tang.normalize()

        prv_normal = -1 * prv_tang.xy_perp()
        nxt_normal = nxt_tang.xy_perp()

        cen1 = prv + rad1 * prv_normal  # + rad1*prv_tang

        cen2 = nxt - rad2 * nxt_normal  # rapid_tang # + rad1*prv_tang

        rapid_tang = cen2 - cen1
        rapid_tang.normalize()

        trg1 = cen1 + rad1 * prv_tang
        src2 = cen2 - rad2 * nxt_tang

        soc = self.so(cen1)
        # This was commented in ovd sample
        self.cut_arc3(
            x=soc[0], y=soc[0], start_pt=self.so(prv), end_pt=self.so(trg1), radius=self.print_scale*rad1,
            clockwise=True, comment='lead out arc - rapid_to_new_branch'
        )  # lead-out arc
        self.goto(z=self.clearZ)
        self.goto(*self.so(src2))
        self.cut(z=self.currentZ)
        soc = self.so(cen2)
        self.cut_arc3(
            x=soc[0], y=soc[1], start_pt=self.so(src2), end_pt=self.so(nxt), radius=self.print_scale*rad2,
            clockwise=True, comment='lead in arc - rapid_to_new_branch'
        )

    def final_lead_out(self, prv_tang, nxt_tang, c1, r1, c2, r2, prv, nxt):
        rad_default = 0.03
        rad1 = min(rad_default, 0.9 * r1)  # wrong? we get the new-branch r1 here, while we would want the old-branch r1
        prv_tang.normalize()
        prv_normal = -1 * prv_tang.xy_perp()
        cen1 = prv + rad1 * prv_normal  # + rad1*prv_tang
        trg1 = cen1 + rad1 * prv_tang
        soc = self.so(cen1)
        self.cut_arc3(
            x=soc[0], y=soc[1], start_pt=self.so(prv), end_pt=self.so(trg1), radius=self.print_scale*rad1,
            clockwise=True, comment='lead out arc - final_lead_out'
        )  # lead-out arc

    def spiral_clear(self, out_tangent, in_tangent, c1, r1, c2, r2, out1, in1):
        self.goto(z=self.clearZ)

        self.camtain(
            HelicalDrill(
                tool=self.tool, center=self.so(c1), z=self.z, depth=self.z - self.currentZ,
                outer_rad=min(r1*self.print_scale, self.tool.diameter*.9), stepdown=self.calc_stepdown()/4.,
                clockwise=self.climb,
            )
        )
        # end spiral at in1
        # archimedean spiral
        # r = a + b theta

        stepover = min(self.stepover*self.material_factor, .95)*self.tool.diameter

        in1_dir = in1 - c1
        in1_theta = math.atan2(in1_dir.y, in1_dir.x)
        b = stepover*self.scale / (2 * math.pi)
        a = r1 - b * in1_theta

        # figure out the start-angle
        theta_min = in1_theta
        theta_max = in1_theta
        dtheta = 0.1
        min_r = 0.001
        while True:
            r = a + b * theta_min
            if r < min_r:
                break
            else:
                theta_min = theta_min - dtheta

        Npts = (theta_max - theta_min) / dtheta
        Npts = int(Npts)
        p = ovd.Point(c1)
        self.goto(*self.so(p))
        self.goto(z=self.currentZ)

        theta_end = 0
        for n in range(Npts + 1):
            theta = theta_min + n * dtheta
            r = a + b * theta
            theta = theta - 2 * abs(in1_theta - math.pi / 2)
            trg = c1 + r * ovd.Point(-math.cos(theta), math.sin(theta))
            self.cut(*self.so(trg))
            theta_end = theta

        # add a complete circle after the spiral.
        Npts = (2 * math.pi) / dtheta
        Npts = int(Npts)
        for n in range(Npts + 2):
            theta = theta_end + (n + 1) * dtheta
            r = r1  # a + b*theta
            trg = c1 + r * ovd.Point(-math.cos(theta), math.sin(theta))
            self.cut(*self.so(trg))

    def generate(self):

        self.set_tool(self._tool)

        self.generate_pocket()
        self.generate_finishing_pass()

    def generate_finishing_pass(self):
        R = self.tool.diameter/2.
        finish_pass_offset = float(self.finish_offset) / self.finish_passes if self.finish_passes else 0
        for offset in frange(self.finish_offset - finish_pass_offset, 0, finish_pass_offset):
            these_segs = self.segs.parallel_offset(offset + R, side='left').enforce_direction(clockwise=True)
            # Just doing first line for now, figure out better later...  Actually maybe just use openvoronois method...
            self.camtain(CoordProfile(
                tool=self.tool, segments=these_segs.lines[0].coords, start_height=self.z, depth=self.depth, stepdown=self.stepdown
            ))

    def generate_pocket(self):
        self.climb = True
        self.currentZ = 0 # for "pendown" replacement

        stepover = self.calc_stepover()
        vd = self.vd()

        pi = ovd.PolygonInterior(True)
        vd.filter_graph(pi)
        ma = ovd.MedialAxis()
        vd.filter_graph(ma)

        mapocket = ovd.MedialAxisPocket(vd.getGraph())
        mapocket.setWidth(stepover*self.scale)
        mapocket.debug(False)
        mapocket.run()
        mic_components = mapocket.get_mic_components()
        # for mic_list in mic_components:
        mic_list = mic_components[0]  # mapocket.get_mic_list()

        for self.currentZ in self.zstep(self.z, self.z - self.depth, auto=False):

            # the rest of the MICs are then cleared
            first = True
            previous_out1 = ovd.Point()
            out_tangent = ovd.Point()
            for n in range(1, len(mic_list)):
                mic = mic_list[n]

                cen2, r2, out1, in1, out2, in2, previous_center, previous_radius, new_branch, prev_branch_center, prev_branch_radius = mic

                in_tangent = in2 - in1
                # rapid traverse to in1
                if not first:
                    if new_branch:
                        # new branch re-position move
                        self.rapid_to_new_branch(
                            out_tangent, in_tangent, prev_branch_center, prev_branch_radius, cen2,
                            r2, previous_out1, in1
                        )
                    else:
                        # normal arc-rapid-arc to next MIC
                        self.rapid_to_next(
                            out_tangent, in_tangent, previous_center, previous_radius, cen2, r2, previous_out1, in1
                        )
                else:
                    # spiral-clear the start-MIC. The spiral should end at in1
                    self.comment("Before spiral clear")
                    self.spiral_clear(
                        out_tangent, in_tangent, previous_center, previous_radius, cen2, r2, previous_out1, in1
                    )
                    first = False

                # in bi-tangent
                self.cut(*self.so(in2))

                # draw arc
                soc = self.so(cen2)
                self.cut_arc3(
                    x=soc[0], y=soc[1], start_pt=self.so(in2), end_pt=self.so(out2), radius=self.print_scale*r2,
                    clockwise=True, cut_to=False, comment='arc between bi-tangent?'
                )

                # # out bi-tangent
                self.cut(*self.so(out1))

                previous_out1 = out1  # this is used as the start-point for the rapid on the next iteration
                out_tangent = out1 - out2

                if n == len(mic_list) - 1:
                    # end of operation. do a final lead-out arc.
                    self.final_lead_out(
                        out_tangent, in_tangent, previous_center, previous_radius, cen2, r2, previous_out1, in1
                    )



if __name__ == '__main__':
    tool = tool=tools['1/4in spiral upcut']

    # Camtainer("./test/test_hsm_oak_5step_circle.nc", [
    #     RectStock(1.5, 4, .75),
    #     HSMStraightGroove(tool=tool, p1=(0, 0), p2=(0, 1.5), width=0.5, z=.75, depth=.5, stepover=1/5., type='circle')
    # ])
    #
    # Camtainer("./test/test_hsm_oak_3step_semicircle.nc", [
    #     RectStock(1.5, 4, .75),
    #     HSMStraightGroove(tool=tool, p1=(0, 0), p2=(0, 1.5), width=0.5, z=.75, depth=.5, stepover=1/3., type='semicircle')
    # ])
    #
    # Camtainer("./test/test_hsm_oak_2step_semicircle.nc", [
    #     RectStock(1.5, 4, .75),
    #     HSMStraightGroove(tool=tool, p1=(0, 0), p2=(0, 1.5), width=0.5, z=.75, depth=.5, stepover=1/2., type='semicircle')
    # ])

    """
    tool = tool=tools['1/8in spiral upcut']
    Camtainer("./test/test_hsm_groove_circle.nc", [
        RectStock(4, 4, 1),
        HSMStraightGroove(tool=tool, p1=(2, 0), p2=(2, 4), width=.5, z=1, depth=.5, stepover=.2, type='circle')
    ])

    Camtainer("./test/test_hsm_groove_swing.nc", [
        RectStock(4, 4, 1),
        HSMStraightGroove(tool=tool, p1=(2, 0), p2=(2, 4), width=.5, z=1, depth=.5, stepover=.2, type='swing')
    ])

    Camtainer("./test/test_hsm_groove_semicircle.nc", [
        RectStock(4, 4, 1),
        HSMStraightGroove(tool=tool, p1=(1, 0), p2=(3, 4), width=.5, z=1, depth=.5, stepover=.2, type='semicircle')
    ])
    segments=[(1, 1, 0), (3, 1, 4)]
    segments_to_drawable("./test/test_hsm_groove_semicircle.draw", segments, close=False, mode='w')

    Camtainer("./test/test_hsm_groove_semicircle2.nc", [
        Goto(0, 0, 1.25),
        RectStock(4, 4, 1),
        HSMStraightGroove(tool=tool, p1=(1, 1), p2=(3, 1), width=.5, z=1, depth=.5, stepover=.5, type='circle', through=False, plunge=True),
    ])
    segments = [(1, 1, 1), (3, 1, 1)]
    segments_to_drawable("./test/test_hsm_groove_semicircle2.draw", segments, close=False, mode='w')
    segments = [(1, .5, 1), (3, .5, 1)]
    segments_to_drawable("./test/test_hsm_groove_semicircle2.draw", segments, close=False, mode='a')

#    Camtainer("./test/test_hsm_groove_semicircle_f.nc", [
#        RectStock(4, 4, 1),
#        HSMStraightGroove(tool=tool, p1=(1, 0), p2=(3, 4), width=.5, z=1, depth=.5, stepover=.2, type='semicircle', rough_margin=.025)
#    ])

    Camtainer("./test/test_hsm_face.nc", [
        RectStock(4, 2, 2),
        HSMFacing(
            tool=tools['1/2in 4-flute endmill'],
            p1=(0, 0), p2=(9.3, 1), z=-0.014,
            depth=.020, stepover=.75, stepdown=.01, rough_margin=0.01
        )
    ])
"""

    ### Bowtie
    segs = LineSet([Line([
        [0.0, 0.0],
        [0.5, .35],
        [1.0, 0.0],
        [1.0, 1.0],
        [0.5, .65],
        [0.0, 1.0],
        [0.0, 0.0],
    ])])

    Camtainer(
        'test/test_pockets.nc', [
            RectStock(6, 6, 2, origin=(0, -2, 0)),
            HSMPocket(
                tool=tools['1/4in 4-flute endmill'],
                segs=segs.translate(4, 4).scale(2, 2, 2), stepover=0.50, stepdown=2,
                material_factor=1,
                z=0, depth=0.5,
            ),
            HSMRectPocket(
                tool=tools['1/4in 4-flute endmill'],
                p1=(.5, .5), p2=(2.5, 2.5), z=0, depth=1, stepover=0.5, stepdown=2,
            ),
            HSMCirclePocket(
                tool=tools['1/4in 4-flute endmill'], outer_rad=1,
                center=(1.5, 4), z=0, depth=1, stepover=0.5, stepdown=2,
            ),
        ]
    )

