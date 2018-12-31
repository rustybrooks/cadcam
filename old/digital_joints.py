#!/usr/bin/env python

import math

from campy import *
from hsm import *


class FingerTenons(CAM):
    hsm_stepover = 1/5.0

    def __init__(self, tool, start, width, this_board_thickness, other_board_thickness, axis='Y', side='right',
                 stepdown=None, hsm=True, pin_first=True, pins=None, this_pin_width=None, other_pin_width=None,
                 recess_depth=None, rebate=None):

        super(FingerTenons, self).__init__(tool=None)
        self._tool = tool

        self.start = start
        self.width = width
        self.this_board_thickness = this_board_thickness
        self.other_board_thickness = other_board_thickness
        self.axis = axis
        self.side = side
        self.stepdown = stepdown
        self.hsm = hsm
        self.pin_first = pin_first
        self.pins = pins
        self.this_pin_width = this_pin_width
        self.other_pin_width = other_pin_width
        self.recess_depth = this_board_thickness if recess_depth is None else recess_depth
        self.rebate = rebate

    def generate(self):


        self.set_tool(self._tool)

        if self.hsm:
            return self.generate_hsm()
        else:
            return self.generate_trad()

    def generate_trad(self):
        pass

    def side_plus(self, base, add):
        if self.side == 'right':
            return base + add
        else:
            return base - add

    def generate_hsm(self):
        self.set_speed(self.tool.rough_speed)

        sx, sy, sz = self.start
        R = self.tool.diameter/2.0

        clearZ = sz + 0.25
        self.goto(z=clearZ)
        self.goto(x=self.side_plus(sx, 2*R), y=sy-R)
        self.goto(z=sz-self.recess_depth)

        width_thing = self.pins * (self.this_pin_width + self.other_pin_width) > self.width
        skiplast = self.pin_first and width_thing
        skiplastpip = True
        if self.pin_first and width_thing:
            skiplastpip = False
        if not self.pin_first and not width_thing:
            skiplastpip = False

        for pin in range(self.pins):
            if self.pin_first:
                basey = sy + self.this_pin_width + pin*(self.this_pin_width + self.other_pin_width)
            else:
                basey = sy + pin*(self.this_pin_width + self.other_pin_width)

            if skiplast and pin == self.pins - 1:
                continue

            self.goto(y=basey + R)
            #if not self.pin_first and pin == 0:
            #    self.goto(x=self.side_plus(sx, (R-self.other_board_thickness)))
            #    self.cut(y=sy)

            p1 = (self.side_plus(sx, 2*R), basey)
            p2 = (self.side_plus(sx, -self.other_board_thickness), basey+self.other_pin_width)

            self.camtain(
                RectPocket(
                    self.tool, p1, p2,
                    depth=self.recess_depth,
                    stepover=self.hsm_stepover,
                    stepdown=self.recess_depth,
                    rough_margin=0.0,
                    z=sz, type='y', auto_clear=False
                )
            )

            if not self.pin_first and pin == 0:
                self.cut(y=sy - R)
            else:
                self.goto(x=self.side_plus(p2[0], R), y=basey+R)
                self.cut(x=p2[0])
                self.goto(x=self.side_plus(p2[0], R))

            if skiplastpip and pin == self.pins - 1:
                self.cut(y = p2[1] + R)
            else:
                self.goto(x=self.side_plus(p2[0], R), y=self.other_pin_width + basey - R)
                self.cut(x=p2[0])
                self.goto(x=self.side_plus(p2[0], R))

            self.goto(x=self.side_plus(sx, 2*R))


# hammer1 is the smaller hammer width, hammer2 the larger
# hammer3 is the tail width
# axis is the axis along which the cut will be made.  Only Y supported for now.
class HammerTenonPins(CAM):

    hsm_stepover = 1/4.0

    def __init__(
            self, tool, start, width, pin_board_thickness, tail_board_thickness,
            hammer1, hammer2, hammer3, hammer_thickness=None, axis='Y', side='right',
            stepdown=None, hsm=True
    ):
        super(HammerTenonPins, self).__init__(tool=None)

        self._tool = tool

        if axis != "Y":
            raise Exception("Only Y axis cut supported for now")

        if hammer_thickness is None:
            hammer_thickness = pin_board_thickness/2.0

        float_pins = (width / (hammer2 + hammer3))
        if abs(float_pins - int(float_pins)) > 0.001:
            raise Exception("Non-integer number of pins: %f (1 pin is %0.4f)" % (float_pins, hammer2+hammer3))

        self.start = start
        self.axis = axis
        self.side = side
        self.hammer1 = hammer1
        self.hammer2 = hammer2
        self.hammer3 = hammer3
        self.width = width
        self.pin_board_thickness = pin_board_thickness
        self.tail_board_thickness = tail_board_thickness
        self.hammer_thickness = hammer_thickness
        self.pins = int(float_pins)
        self.stepdown = stepdown if stepdown else tool.diameter
        self.hsm = hsm

    def generate_path(self):
        points1 = []  # for smaller tenon part
        points2 = []  # for larger tenon part

        r = self.tool.diameter/2.0

        hdiff = self.hammer2 - self.hammer1

        sx, sy, sz = self.start
        xoffset = sx - self.tail_board_thickness if self.side == 'right' else sx + self.tail_board_thickness
        if self.axis == "Y":
            for pin in range(self.pins):
                basey = sy + (self.hammer2 + self.hammer3)*pin

                points1.append(dict(x=r,  y=basey))
                points1.append(dict(              y=basey + self.hammer3/2.0 - r))
                #points1.append(dict(x=-r))
                points1.append(dict(x=0))
                points1.append(dict(              y=basey + self.hammer3/2.0 + hdiff/2.0 - r))
                points1.append(dict(x=self.tail_board_thickness + r))
                points1.append(dict(              y=basey + self.hammer3/2.0 + self.hammer2 - hdiff/2.0 + r))
                #points1.append(dict(x=-r))
                points1.append(dict(x=0))
                points1.append(dict(              y=basey + self.hammer3/2.0 + self.hammer2 + r))
                points1.append(dict(x=+r))

                points2.append(dict(x=+r,  y=basey))
                points2.append(dict(              y=basey + self.hammer3/2.0 - r))
                #points2.append(dict(x=-r))
                points2.append(dict(x=0))
                points2.append(dict(x=self.tail_board_thickness + r))
                points2.append(dict(              y=basey + self.hammer3/2.0 + self.hammer2 + r))
                #points2.append(dict(x=-r))
                points2.append(dict(x=0))
                points2.append(dict(x=+r))

            points1.append(dict(x=+r,         y=(self.hammer2 + self.hammer3)*self.pins))
            points2.append(dict(x=+r,         y=(self.hammer2 + self.hammer3)*self.pins))

        # make all points complete
        whole_point = {}
        points1_comp = []
        for point in points1:
            whole_point.update(point)
            foo = whole_point['x']
            newx = xoffset + foo if self.side == 'right' else xoffset - foo
            points1_comp.append(dict(x=newx, y=whole_point['y']))

        whole_point = {}
        points2_comp = []
        for point in points2:
            whole_point.update(point)
            foo = whole_point['x']
            newx = xoffset + foo if self.side == 'right' else xoffset - foo
            points2_comp.append(dict(x=newx, y=whole_point['y']))

        return points1_comp, points2_comp

    def generate(self):


        self.set_tool(self._tool)

        if self.hsm:
            return self.generate_hsm()
        else:
            return self.generate_trad()

    def generate_hsm(self):
        r = self.tool.diameter/2.0


        sx, sy, sz = self.start
        basey = sy
        self.cut(x=-2*r)
        self.cut(y=basey)
        width = basey + self.hammer3/2.0
        Camtainer(
            self.f,
            [
                HSMStraightGroove(self.tool, (0, width/2.0), (self.tail_board_thickness - width/2.0, basey + width/2.0), width=width, z=self.pin_board_thickness, depth=self.pin_board_thickness, stepover=self.hsm_stepover, type='semicircle', safety_margin=(1, 0), rough_margin=0),
                HSMCleanoutCorner(
                    self.tool,
                    corner_point=(self.tail_board_thickness, basey),
                    z=0, stepover=self.hsm_stepover, initial_radius=width/2.0, quadrant=(-1, 1), rough_margin=0.0
                ),

                HSMCleanoutCorner(
                    self.tool,
                    corner_point=(self.tail_board_thickness, basey + self.hammer3/2.0),
                    z=0, stepover=self.hsm_stepover, initial_radius=width/2.0, quadrant=(-1, -1), rough_margin=0.0
                ),
            ],
            self_contained=False
        )
        self.goto(x=-2*r)

        if self.axis == "Y":
            #width = self.hammer3
            width = self.tail_board_thickness
            for pin in range(self.pins-1):
                basey = sy + (self.hammer2 + self.hammer3)*pin + self.hammer3/2.0 + self.hammer2
                self.goto(y=basey)

                Camtainer(self.f, [
                    HSMStraightGroove(
                        self.tool,
                        (0, basey + width/2.0),
                        (self.tail_board_thickness - width/2.0, basey + width/2.0),
                        width=width,
                        z=sz, depth=self.pin_board_thickness,
                        stepover=self.hsm_stepover, type='semicircle', safety_margin=(1, 0), rough_margin=0
                    ),
                    HSMStraightGroove(
                        self.tool, (width/2.0, basey+width/2.0), (width/2.0, basey + self.hammer3 - width/2.0),
                        width=width, z=sz, depth=self.pin_board_thickness, stepover=self.hsm_stepover, type='semicircle', safety_margin=(0, 0), rough_margin=0
                    ),

                    HSMCleanoutCorner(
                        self.tool,
                        corner_point=(self.tail_board_thickness, basey),
                        z=self.pin_board_thickness, depth=self.pin_board_thickness, stepover=self.hsm_stepover, initial_radius=width/2.0, quadrant=(-1, 1), rough_margin=0.0
                    ),

                    HSMCleanoutCorner(
                        self.tool,
                        corner_point=(self.tail_board_thickness, basey + self.hammer3),
                        z=self.pin_board_thickness, depth=self.pin_board_thickness, stepover=self.hsm_stepover, initial_radius=width/2.0, quadrant=(-1, -1), rough_margin=0.0
                    ),
                ])
                self.goto(x=-2*r)


            width = self.hammer3/2.0
            basey = sy + (self.hammer2 + self.hammer3)*(self.pins-1) + self.hammer3/2.0 + self.hammer2
            self.goto(y=basey)
            Camtainer(
                self.f,
                [
                    HSMStraightGroove(
                        self.tool, (0, basey + width/2.0), (self.tail_board_thickness - width/2.0, basey + width/2.0),
                        width=width, z=self.pin_board_thickness, depth=self.pin_board_thickness, stepover=self.hsm_stepover, type='semicircle', safety_margin=(1, 0),
                        rough_margin=0
                    ),
                    HSMCleanoutCorner(
                        self.tool,
                        corner_point=(self.tail_board_thickness, basey),
                        z=self.pin_board_thickness, depth=self.pin_board_thickness, stepover=self.hsm_stepover, initial_radius=width/2.0, quadrant=(-1, 1), rough_margin=0.0
                    ),

                    HSMCleanoutCorner(
                        self.tool,
                        corner_point=(self.tail_board_thickness, basey + self.hammer3/2.0),
                        z=self.pin_board_thickness, depth=self.pin_board_thickness, stepover=self.hsm_stepover, initial_radius=width/2.0, quadrant=(-1, -1), rough_margin=0.0
                    ),
                ],
                self_contained=False
            )
            self.goto(x=-2*r)

            hdiff = (self.hammer2 - self.hammer1)/2.0
            for pin in range(self.pins-1, -1, -1):
                basey = sy + (self.hammer2 + self.hammer3)*pin + self.hammer3/2.0

                Camtainer(self.f, [
                    RectPocket(
                        tool,
                        (-2*r,                          basey+self.hammer2-hdiff+r),
                        (self.tail_board_thickness+r, basey+self.hammer2),
                        z=sz,
                        depth=self.pin_board_thickness-self.hammer_thickness, stepover=self.hsm_stepover, stepdown=self.pin_board_thickness, type='x'
                    ),
                ], self_contained=False)

                Camtainer(self.f, [
                    RectPocket(
                        tool,
                        (-2*r,                        basey+hdiff-r),
                        (self.tail_board_thickness+r, basey),
                        z=sz,
                        depth=self.pin_board_thickness-self.hammer_thickness, stepover=self.hsm_stepover, stepdown=self.pin_board_thickness, type='x'
                    ),
                ], self_contained=False)

        points1, points2 = self.generate_path()

        z1 = sz - self.pin_board_thickness + self.hammer_thickness
        z2 = sz - self.pin_board_thickness

        clearZ = sz + .5
        self.goto(z=clearZ)
        self.goto(**points1[0])
        self.cut(z=z2)

        for point in points2[1:]:
            self.cut(**point)

        #self.goto(z=clearZ)
        #self.goto(**points2[-1])
        self.cut(z=z1)
        for point in reversed(points1[:-1]):
            self.cut(**point)


    def generate_trad(self):
        points1, points2 = self.generate_path()

        sx, sy, sz = self.start
        clearZ = sz + .5

        forward = True
        self.goto(z=clearZ)
        self.goto(**points1[0])

        z1 = sz - self.pin_board_thickness + self.hammer_thickness
        z2 = sz - self.pin_board_thickness
        for Z in self.zstep(sz, z1, auto=False, stepdown=self.stepdown):
            self.cut(z=Z)

            if forward:
                for point in points1[1:]:
                    self.cut(**point)
            else:
                for point in reversed(points1[:-1]):
                    self.cut(**point)

            forward = not forward

        for Z in self.zstep(z1, z2, auto=False, stepdown=self.stepdown):
            self.cut(z=Z)

            if forward:
                for point in points2[1:]:
                    self.cut(**point)
            else:
                for point in reversed(points2[:-1]):
                    self.cut(**point)

            forward = not forward


class HammerTenonTails(CAM):
    hsm_stepover = 1/5.0

    def __init__(
         self, tool, start, width, pin_board_thickness, tail_board_thickness,
         hammer1, hammer2, hammer3, hammer_thickness=None, axis='Y', side='right',
         stepdown=None, hsm=True
):
        super(HammerTenonTails, self).__init__(tool=None)
        self._tool = tool

        if axis != "Y":
            raise Exception("Only Y axis cut supported for now")

        if hammer_thickness is None:
            hammer_thickness = pin_board_thickness/2.0

        float_pins = (width / (hammer2 + hammer3))
        if abs(float_pins - int(float_pins)) > 0.001:
            raise Exception("Non-integer number of pins: %f (1 pin is %0.4f)" % (float_pins, hammer2+hammer3))

        self.start = start
        self.axis = axis
        self.side = side
        self.hammer1 = hammer1
        self.hammer2 = hammer2
        self.hammer3 = hammer3
        self.width = width
        self.pin_board_thickness = pin_board_thickness
        self.tail_board_thickness = tail_board_thickness
        self.hammer_thickness = hammer_thickness
        self.pins = int(float_pins)
        self.stepdown = stepdown if stepdown else tool.diameter
        self.hsm = hsm

    def generate(self):


        self.set_tool(self._tool)

        if self.hsm:
            return self.generate_hsm()
        else:
            return self.generate_trad()

    def generate_hsm(self):
        clearZ = self.start[2] + .5
        hdiff = (self.hammer2 - self.hammer1)/2.0

        sx, sy, sz = self.start

        self.goto(z=clearZ)
        self.goto(x=-self.tool.diameter)

        for pin in range(self.pins):
            basey = sy + self.hammer3/2.0 + pin*(self.hammer2 + self.hammer3)
            centery = basey + self.hammer2/2.0

            self.goto(y=basey)
            Camtainer(
                self.f,
                [
                    HSMStraightGroove(
                        tool=self.tool,
                        p1=(sx, centery),
                        p2=(sx + self.pin_board_thickness - self.hammer_thickness, centery),
                        width=self.hammer1,
                        z=self.tail_board_thickness, depth=self.tail_board_thickness,
                        stepover=self.hsm_stepover,
                        type='semicircle',
                        safety_margin=[1, 0],
                        rough_margin=0.0,
                    ),
                    StarMortise(
                        tool=self.tool,
                        p1=(sx + self.pin_board_thickness - self.hammer_thickness, basey),
                        p2=(sx + self.pin_board_thickness, basey + self.hammer2),
                        z=self.tail_board_thickness,
                        depth=self.tail_board_thickness,
                        stepdown=self.stepdown,
                        through=True,
                        hsm=True,
                    ),
                ]
            )
            self.goto(y=centery)
            self.goto(x=-self.tool.diameter)

    def generate_trad(self):
        clearZ = self.start[2] + .5

        points = []  # for smaller tenon part

        r = self.tool.diameter/2.0

        hdiff = self.hammer2 - self.hammer1

        sx, sy, sz = self.start

        x = [
            -r,
            self.pin_board_thickness - self.hammer_thickness - r,
            self.pin_board_thickness - r,
            self.pin_board_thickness + r,
        ]
        y = [
            0,
            self.hammer3/2.0,
            self.hammer3/2.0 + hdiff/2.0 + r,
            self.hammer3/2.0 + hdiff/2.0 + self.hammer1 - r,
            self.hammer3/2.0 + self.hammer2,
        ]

        if self.axis == "Y":
            for pin in range(self.pins):
                basey = sy + (self.hammer2 + self.hammer3)*pin

                points.append(dict(x=x[0], y=basey+y[0]))
                points.append(dict(x=x[0], y=basey+y[2]))
                points.append(dict(x=x[1], y=basey+y[2]))
                points.append(dict(x=x[1], y=basey+y[1]))
                points.append(dict(x=x[3], y=basey+y[1]))
                points.append(dict(x=x[2], y=basey+y[1]))
                points.append(dict(x=x[2], y=basey+y[4]))
                points.append(dict(x=x[3], y=basey+y[4]))
                points.append(dict(x=x[1], y=basey+y[4]))
                points.append(dict(x=x[1], y=basey+y[3]))
                points.append(dict(x=x[0], y=basey+y[3]))
                #points.append(dict(x=x[0], y=y[5]))

            points.append(dict(x=-r,         y=(self.hammer2 + self.hammer3)*self.pins))

        # make all points complete
        #points_comp = []
        #whole_point = {}
        for point in points:
            point['x'] = sx - point['x'] if self.side == "right" else sx + point['x']

        #    whole_point.update(point)
        #    foo = whole_point['x']
        #    newx = xoffset + foo if self.side == 'right' else xoffset - foo
        #    points_comp.append(dict(x=newx, y=whole_point['y']))

        forward = True
        self.goto(z=clearZ)
        self.goto(**points[0])

        for Z in self.zstep(sz, sz - self.tail_board_thickness, auto=False, stepdown=self.stepdown):
            self.goto(z=Z)

            if forward:
                for point in points[1:]:
                    self.cut(**point)
            else:
                for point in reversed(points[:-1]):
                    self.cut(**point)

            forward = not forward


class StarMortise(CAM):
    hsm_stepover = 1/5.0

    # points1/2 are tuples outlining opposite corners of the mortise
    def __init__(self, tool, p1, p2, z, depth, stepdown=None, through=True, hsm=False, rough_margin=0.0, stepover=None):
        super(StarMortise, self).__init__(None)

        self._tool = tool
        self.p1 = p1
        self.p2 = p2
        self.z = z
        self.depth = depth
        self.stepdown = stepdown if stepdown else tool.diameter
        self.stepover = stepover
        self.through = through
        self.hsm = hsm
        self.rough_margin = rough_margin  # FIXME does nothing yet

    def generate(self):


        self.set_tool(self._tool)

        if self.hsm:
            self.generate_hsm()
        else:
            self.generate_trad()

        self.camtain(RectPocketCornerRelief(tool=self.tool, p1=self.p1, p2=self.p2, z=self.z, depth=self.depth, stepdown=self.stepdown))

    def generate_hsm(self):
        r = self.tool.diameter / 2.0
        px1, py1 = self.p1
        px2, py2 = self.p2

        clearZ = self.z + .25

        self.camtain(HSMRectPocket(
            tool=self.tool, p1=self.p1, p2=self.p2, z=self.z, depth=self.depth,
            stepdown=self.stepdown, stepover=self.hsm_stepover, rough_margin=self.rough_margin,
        ))

        # FIXME this is a full depth cut.  Maybe fine?  I dunno.
        off = r / (2*math.sqrt(2))
        px1 += r
        py1 += r
        px2 -= r
        py2 -= r


    def generate_trad(self):
        points = []  # for smaller tenon part

        r = self.tool.diameter/2.0

        px1, py1 = self.p1
        px2, py2 = self.p2

        width = abs(px2 - px1)
        height = abs(py2 - py1)
        type = 'y' if height > width else 'x'

        self.camtain(RectPocket(
            tool=self.tool, p1=self.p1, p2=self.p2, z=self.z, depth=self.depth,
            stepdown=self.stepdown, stepover=self.hsm_stepover, rough_margin=self.rough_margin, type=type
        ))

        # clearZ = self.z + .25
        #
        # px1 += r
        # py1 += r
        # px2 -= r
        # py2 -= r
        #
        # off = r / (2*math.sqrt(2))
        #
        # points.append(dict(x=px1-off, y=py1-off))
        # points.append(dict(x=px1,     y=py1))
        #
        # points.append(dict(x=px1,     y=py2))
        # points.append(dict(x=px1-off, y=py2+off))
        # points.append(dict(x=px1,     y=py2))
        #
        # points.append(dict(x=px2,     y=py2))
        # points.append(dict(x=px2+off, y=py2+off))
        # points.append(dict(x=px2,     y=py2))
        #
        # points.append(dict(x=px2,     y=py1))
        # points.append(dict(x=px2+off, y=py1-off))
        # points.append(dict(x=px2,     y=py1))
        #
        # points.append(dict(x=px1,     y=py1))
        #
        # if not self.through:
        #     p1 = (px1+r/2., py1+r/2.)
        #     p2 = (px2-r/2., py2-r/2.)
        #     Camtainer(self.f, RectPocket(tool=self.tool, p1=p1, p2=p2, z=self.z, depth=self.depth, stepdown=self.stepdown), self_contained=False)
        #
        # self.goto(z=clearZ)
        # self.goto(x=px1, y=py1)
        #
        # for Z in self.zstep(self.z, self.z - self.depth, auto=False, stepdown=self.stepdown):
        #     self.goto(z=Z)
        #
        #     for point in points:
        #         self.cut(**point)

if __name__ == '__main__':

    tool = tools['1/4in spiral upcut']
    Camtainer("test/test_star.ngc", [
        RectStock(5, 3, 1),
        StarMortise(tool=tool, p1=(1, 1), p2=(4, 2), z=1, depth=.5, through=False, hsm=False),
    ])

    Camtainer("test/test_star_hsm.ngc", [
        RectStock(5, 3, 1),
        StarMortise(tool=tool, p1=(1, 1), p2=(4, 2), z=1, depth=.5, through=False, hsm=True, stepdown=0.5),
    ])

    tool = tools['1/4in spiral upcut']
    thickness1 = 0.732
    thickness2 = thickness1-.20
    w = 2.25*3
    hammer1 = 1.5*.75-.5
    hammer2 = 1.5*.75
    hammer3 = 1.5*.75
    Camtainer("test/test_pin.ngc", [
        RectStock(2.0, w, thickness1, origin=(0, 0, 0)),
        HammerTenonPins(
            tool=tool, start=(0, 0, thickness1), width=w, pin_board_thickness=thickness1, tail_board_thickness=thickness1,
            hammer1=hammer1, hammer2=hammer2, hammer3=hammer3, side='left', stepdown=.1
        ),
        HammerTenonPins(
            tool=tool, start=(6, 0, thickness1), width=w, pin_board_thickness=thickness1, tail_board_thickness=thickness2,
            hammer1=hammer1, hammer2=hammer2, hammer3=hammer3, side='right', stepdown=.1
        ),
        #HammerTedonPins(
        #    tool=tool, start=(6, 0, thickness1), width=w, pin_board_thickness=thickness1, tail_board_thickness=thickness2,
        #    hammer1=hammer1, hammer2=hammer2, hammer3=hammer3, side='right', stepdown=.2
        #),

    ])

    Camtainer("test/test_tail.ngc", [
        RectStock(6.0, w, thickness1, origin=(0, 0, 0)),
        HammerTenonTails(
            tool=tool, start=(0, 0, thickness1), width=w, pin_board_thickness=thickness1, tail_board_thickness=thickness1,
            hammer1=hammer1, hammer2=hammer2, hammer3=hammer3, side='left', stepdown=.1
        ),
        HammerTenonTails(
            tool=tool, start=(6, 0, thickness1), width=w, pin_board_thickness=thickness1, tail_board_thickness=thickness2,
            hammer1=hammer1, hammer2=hammer2, hammer3=hammer3, side='right', stepdown=.1
        ),
    #    HammerTenonTails(
    #        tool=tool, start=(6, 0, thickness1), width=w, pin_board_thickness=thickness1, tail_board_thickness=thickness2,
    #        hammer1=hammer1, hammer2=hammer2, hammer3=hammer3, side='right', stepdown=.2
    #    ),
    ])


    tool = tools['1/8in spiral upcut']
    thickness1 = 0.5
    thickness2 = 0.75
    w = 5
    Camtainer("test/test_finger_1a.ngc", [
        RectStock(6.0, w, thickness1),
        FingerTenons(
            tool, start=(0, 0, thickness1), width=w, this_board_thickness=thickness1, other_board_thickness=thickness2,
            side='left', pin_first=True, pins=5, this_pin_width=.5, other_pin_width=.5
        ),
        FingerTenons(
            tool, start=(6, 0, thickness1), width=w, this_board_thickness=thickness1, other_board_thickness=thickness2,
            side='right', pin_first=True, pins=5, this_pin_width=.5, other_pin_width=.5
        )
    ])

    Camtainer("test/test_finger_2a.ngc", [
        RectStock(6.0, w, thickness2),
        FingerTenons(
            tool, start=(0, 0, thickness2), width=w, this_board_thickness=thickness2, other_board_thickness=thickness1,
            side='left', pin_first=False, pins=5, this_pin_width=.5, other_pin_width=.5
        ),
        FingerTenons(
            tool, start=(6, 0, thickness2), width=w, this_board_thickness=thickness2, other_board_thickness=thickness1,
            side='right', pin_first=False, pins=5, this_pin_width=.5, other_pin_width=.5
        )
    ])

    w = 4.5
    Camtainer("test/test_finger_1b.ngc", [
        RectStock(6.0, w, thickness1),
        FingerTenons(
            tool, start=(0, 0, thickness1), width=w, this_board_thickness=thickness1, other_board_thickness=thickness2,
            side='left', pin_first=True, pins=5, this_pin_width=.5, other_pin_width=.5
        ),
    ])

    Camtainer("test/test_finger_2b.ngc", [
        RectStock(6.0, w, thickness2),
        FingerTenons(
            tool, start=(0, 0, thickness2), width=w, this_board_thickness=thickness2, other_board_thickness=thickness1,
            side='left', pin_first=False, pins=5, this_pin_width=.5, other_pin_width=.5
        ),
    ])


    Camtainer("test/test_finger_1c.ngc", [
        RectStock(6.0, w, thickness1),
        FingerTenons(
            tool, start=(0, 0, thickness1), width=w, this_board_thickness=thickness1, other_board_thickness=thickness2/2.0,
            side='left', pin_first=True, pins=5, this_pin_width=.5, other_pin_width=.5
        ),
    ])
    Camtainer("test/test_finger_2c.ngc", [
        RectStock(6.0, w, thickness2),
        FingerTenons(
            tool, start=(0, 0, thickness2), width=w, this_board_thickness=thickness2, other_board_thickness=thickness1,
            side='left', pin_first=False, pins=5, this_pin_width=.5, other_pin_width=.5, recess_depth=thickness2/2.0,
        ),
    ])