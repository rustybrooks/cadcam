from .cammath import frange
from .tools import *
from . import constants

import copy
import math
import os



class Material(object):
    def __init__(self, name, sfm_hss, sfm_carbide, fpt_hss, fpt_carbide):
        self.name = name
        self.sfm_hss = sfm_hss
        self.sfm_carbide = sfm_carbide
        self.fpt_hss = fpt_hss
        self.fpt_carbide = fpt_carbide

    def __str__(self):
        return "Material({})".format(self.name)


class Environment(object):
    def __init__(self, min_rpm, max_rpm, max_feedrates):
        self.tool = None
        self.material = None
        self.material_factor = 1
        self.speed = None
        self.probe_speed = 1
        self.speed_stack = []
        self.location = None
        self.files = {}
        self.f = None
        self.level = 0

        self.min_rpm = min_rpm
        self.max_rpm = max_rpm
        self.max_feedrates = max_feedrates
        self.peak_feedrate = max(max_feedrates)

    def __del__(self):
        for k, v in self.files.items():
            self.close_file(k)

    @classmethod
    def format_movement(cls, x=None, y=None, z=None, a=None, rate=None):
        movement = []
        for var, axis in zip((x, y, z, a, rate), ('X', 'Y', 'Z', 'A', 'F')):
            if var is not None: 
                if str(var).strip().startswith('['):
                    movement.append("%s%s" % (axis, var))
                else:
                    movement.append('%s%.6f' % (axis, var))

        return movement

    def close_file(self, name):
        f = self.files[name]
        f.write("M30\n")
        f.write("%\n")
        f.close()
        del self.files[name]

    def set_file(self, filename):
        if filename not in self.files:
            dir = os.path.split(filename)[0]
            if not os.path.exists(dir):
                os.makedirs(dir)
            self.files[filename] = open(filename, 'w')
            self.f = self.files[filename]

            self.write("%")
            self.write("G17 G20 G40 G90")  # FIXME revisit this later

        self.filename = filename
        self.f = self.files[filename]

    def set_tool(self, tool, feed_class='low', rpm_range=None, ):
        if isinstance(tool, (str, unicode)):
            this_tool = tools[tool]
        else:
            this_tool = tool

        self.feed_class = feed_class
        self.tool = copy.copy(this_tool)
        self.tool.rpm_range = rpm_range or [self.min_rpm, self.max_rpm]
        # self.tool.calculate_feedrates(material=self.material, machine=self, base_feedrate=base_feedrate)
        self.tool.comment(self)

    def set_material(self, material):
        if isinstance(material, (str, unicode)):
            self.material = materials[material]
        else:
            self.material = material

    def write(self, txt):
        if self.f is None:
            print "Can't write, f=None", txt
        else:
            prefix = " "*((self.level-1)*4)
            self.f.write(prefix + txt + '\n')
            # sys.stdout.write(txt + '\n');

        self.f.flush()  # required?

    def set_speed(self, rate):
        if rate is None:
            return

        if isinstance(rate, (int, float)):
            self.speed = rate
        else:
            self.speed = self.tool.calculate_feedrate(material=self.material, machine=self, feed_type=rate, feed_class=self.feed_class)

        # print 'set_speed', rate, self.speed

    def push_speed(self, rate):
        self.speed_stack.append(self.speed)
        self.set_speed(rate)

    def pop_speed(self):
        rate = self.speed_stack.pop()
        self.set_speed(rate)

    def end_program(self):
        self.write("M30")
        self.write("%")

    def pause_program(self):
        self.comment("PAUSE")
        self.write("M0")

    def comment(self, c):
        c = c.replace('(', '[').replace(')', ']')
        self.write("(%s)" % (c,))

    def goto(self, x=None, y=None, z=None, a=None, point=None, rate=None):
        if point is not None:
            x, y, z = point

        # self.record_linear_move((x, y, z), speed=self.rapid_speed)
        self.write("G0 %s" % (" ".join(self.format_movement(x, y, z, a, rate))))

    def cut(self, x=None, y=None, z=None, a=None, point=None, rate=None):
        if point is not None:
            x, y, z = point

        if self.speed is not None and rate is None:
            feed = self.speed
            self.speed = None
        elif rate is not None:
            feed = rate
        else:
            feed = None

        # self.record_linear_move((x, y, z))
        self.write("G1 %s" % (" ".join(self.format_movement(x, y, z, a, feed))))

    # x, y forms the center of your arc
    # if I did this right, I think it presumes you're at bx, by already
    def cut_arc_center_rad(
            self, x, y, radius, start_angle, end_angle, rate=None, z=None, clockwise=True, cut_to=False,
            move_to=False, return_to=False, inside=None, adjust_tool_radius=True, comment=None
    ):

        if comment:
            self.comment(comment)

        if adjust_tool_radius:
            if inside is True:
                radius -= self.tool.diameter / 2.0
            elif inside is False:
                radius += self.tool.diameter / 2.0

        bx = x + math.cos(math.radians(start_angle)) * radius
        by = y + math.sin(math.radians(start_angle)) * radius

        bx2 = x + math.cos(math.radians(end_angle)) * radius
        by2 = y + math.sin(math.radians(end_angle)) * radius

        if cut_to:
            self.cut(x=bx, y=by, rate=rate)
        elif move_to:
            self.goto(x=bx, y=by, rate=rate)

        if radius <= 0:
            pass
            # print "Arc radius = {}, skipping".format(radius)
        else:
            self.cut_arc(bx2, by2, x - bx, y - by, rate=rate, z=z, clockwise=clockwise)

        if return_to:
            if cut_to:
                self.cut(x=bx, y=by, rate=rate)
            elif move_to:
                self.goto(x=bx, y=by, rate=rate)

    def cut_arc(self, x=None, y=None, I=None, J=None, rate=None, z=None, clockwise=True):
        if self.speed is not None and rate is None:
            feed = "F%0.3f " % self.speed
            self.speed = None
        elif rate is not None:
            feed = "F%0.3f " % rate
        else:
            feed = ""

        Z = "Z%6f" % z if z is not None else ""

        # self.record_arc_move(x, y, z, I, J, clockwise)
        self.write("%s X%.6f Y%.6f I%.6f J%6f %s %s" % ('G2' if clockwise else 'G3', x, y, I, J, Z, feed))

    def probe(self, axis='z', rate=None, to=None, toward=True, halt_on_error=True):
        if self.speed is not None and rate is None:
            feed = "F%0.3f " % self.speed
            self.speed = None
        elif rate is not None:
            feed = "F%0.3f " % rate
        else:
            feed = ""

        if toward:
            gcode = 'G38.2' if halt_on_error else 'G38.3'
        else:
            gcode = 'G38.4' if halt_on_error else 'G38.5'

        self.write("{} {}{} {}".format(gcode, axis.upper(), to, feed))

    def calc_stepover(self, stepover=None, max_stepover=None, depth=None):
        diam = self.tool.diameter_at_depth(depth or 0)
        max_stepover = max_stepover or diam*0.95

        if str(stepover)[-1] == '%':
            stepover = diam*float(stepover[:-1])/100.

        if str(max_stepover)[-1] == '%':
            max_stepover = diam*float(max_stepover[:-1])/100.

        factor = self.material_factor
        return min(stepover * factor, max_stepover)

    def calc_stepdown(self, stepdown=None, max_stepdown=3, depth=None):
        diam = self.tool.diameter_at_depth(depth or 0)
        max_stepdown = max_stepdown or diam*2

        if str(stepdown)[1] == '%':
            stepdown = self.tool.diameter*float(stepdown[:-1])

        if str(max_stepdown)[-1] == '%':
            max_stepdown = diam*float(max_stepdown[:-1])/100.

        factor = self.material_factor
        return min(stepdown * factor, max_stepdown)

    def zstep(self, z1, z2, stepdown=None, auto_step=False):
        if stepdown is None:
            stepdown = self.calc_stepdown()

        diff = float(z1 - z2)
        stepdown = diff / int(math.ceil(diff / stepdown))
        for z in frange(max(z2, z1 - stepdown), z2, stepdown):
            if auto_step:
                self.push_speed(self.tool.plunge_speed)
                self.cut(z=z)
                self.pop_speed()

            yield z

    def zstep_size(self, stepdown=None, finish_mode=False):
        return (
        self.tool.zstep_pass_rough if finish_mode else self.tool.zstep_pass_finish) if stepdown is None else stepdown

    # FIXME probably broken for counter-clockwise?
    def arc_start_end(self, x, y, radius, start_angle, end_angle, clockwise=True, adjust_tool_radius=False, inside=None):
        if adjust_tool_radius:
            if inside is True:
                radius -= self.tool.diameter / 2.0
            elif inside is False:
                radius += self.tool.diameter / 2.0

        bx = x + math.cos(math.radians(start_angle)) * radius
        by = y + math.sin(math.radians(start_angle)) * radius

        bx2 = x + math.cos(math.radians(end_angle)) * radius
        by2 = y + math.sin(math.radians(end_angle)) * radius

        return [[bx, by], [bx2, by2]]

    def push_level(self):
        self.level += 1

    def pop_level(self):
        self.level -= 1
        if self.level < 0:
            raise Exception("popped too many levels")


# machine =

# FIXME load from file shared with fusion etc
tools = {}
tools['1/8in spiral upcut'] = StraightRouterBit(diameter=1/8., tool_material='hss', flutes=2)
tools['1/16in spiral upcut'] = StraightRouterBit(diameter=1/16., tool_material='hss', flutes=2)
tools['1/4in spiral upcut'] = StraightRouterBit(diameter=1/4., tool_material='hss', flutes=2)
tools['3/8in spiral upcut'] = StraightRouterBit(diameter=3/8., tool_material='hss', flutes=2)
tools['1/2in spiral upcut'] = StraightRouterBit(diameter=1/2., tool_material='hss', flutes=2)

tools['1/2in 4-flute endmill'] = StraightRouterBit(diameter=1/2., tool_material='hss', flutes=4)
tools['1/4in 4-flute endmill'] = StraightRouterBit(diameter=1/4., tool_material='hss', flutes=4)
tools['1/8in 4-flute endmill'] = StraightRouterBit(diameter=1/8., tool_material='hss', flutes=4)

tools['1/8in spiral ball'] = BallRouterBit(diameter=1/8., tool_material='hss', flutes=2)
tools['1/4in spiral ball'] = BallRouterBit(diameter=1/4., tool_material='hss', flutes=2)
tools['3/8in spiral upcut'] = StraightRouterBit(diameter=3/8., tool_material='hss', flutes=2)
tools['1/2in spiral ball'] = BallRouterBit(diameter=1/2., tool_material='hss', flutes=2)

tools['1 1/2in straight bit'] = StraightRouterBit(diameter=1.5, tool_material='hss', flutes=2)
tools['1/2in dovetail'] = DovetailRouterBit(minor_diameter=5/8., major_diameter=1/2., height=7/8., tool_material='hss', flutes=2)
tools['30degV'] = VRouterBit(included_angle=30.0, diameter=1/4., tool_material='hss', flutes=1)

tools['probe'] = Tool('hss', 1, 1)
tools['probe'].feeds['probe'] = 1

tools['engrave-0.1mm-30'] = VRouterBit(included_angle=30.0, diameter=1/8., tip_diameter=0.1*constants.MM, tool_material='hss', flutes=1)
tools['engrave-0.1mm-10'] = VRouterBit(included_angle=10.0, diameter=1/8., tip_diameter=0.1*constants.MM, tool_material='hss', flutes=1)
tools['engrave-0.01in-15'] = VRouterBit(included_angle=15.0, diameter=1/8., tip_diameter=0.01, tool_material='hss', flutes=3)

tools['tiny-0.6mm'] = StraightRouterBit(diameter=.6*constants.MM, tool_material='hss', flutes=2)
tools['tiny-0.7mm'] = StraightRouterBit(diameter=.7*constants.MM, tool_material='hss', flutes=2)
tools['tiny-0.8mm'] = StraightRouterBit(diameter=.8*constants.MM, tool_material='hss', flutes=2)
tools['tiny-0.9mm'] = StraightRouterBit(diameter=.9*constants.MM, tool_material='hss', flutes=2)
tools['tiny-1.0mm'] = StraightRouterBit(diameter=1.0*constants.MM, tool_material='hss', flutes=2)
tools['tiny-1.2mm'] = StraightRouterBit(diameter=1.2*constants.MM, tool_material='hss', flutes=2)
tools['tiny-1.4mm'] = StraightRouterBit(diameter=1.4*constants.MM, tool_material='hss', flutes=2)
tools['tiny-1.6mm'] = StraightRouterBit(diameter=1.6*constants.MM, tool_material='hss', flutes=2)
tools['tiny-1.8mm'] = StraightRouterBit(diameter=1.8*constants.MM, tool_material='hss', flutes=2)
tools['tiny-2.0mm'] = StraightRouterBit(diameter=2.0*constants.MM, tool_material='hss', flutes=2)
tools['tiny-2.2mm'] = StraightRouterBit(diameter=2.2*constants.MM, tool_material='hss', flutes=2)
tools['tiny-2.4mm'] = StraightRouterBit(diameter=2.4*constants.MM, tool_material='hss', flutes=2)
tools['tiny-3mm'] = StraightRouterBit(diameter=3*constants.MM, tool_material='hss', flutes=2)

tools['k40-laser'] = Laser(focused_beam_width=0.010)  # Just a guess - measure...

# fpt is for diameter of 1/8 1/4 1/2 1
# http://www.micro-machine-shop.com/SFM_Formulae_Chart_2.pdf
materials = {
    'none': Material(
        name='none', sfm_hss=[0, 0], sfm_carbide=[0, 0],
        fpt_hss=[(0, 0), (0, 0), (0, 0), (0, 0)], fpt_carbide=[(0, 0), (0, 0), (0, 0), (0, 0)],
    ),
    'aluminum': Material(
        name='aluminum', sfm_hss=[250, 800], sfm_carbide=[600, 1200],
        fpt_hss=[], fpt_carbide=[.0080, .0040, .0020, .0010],
    ),
    'steel': Material(
        name='steel', sfm_hss=[], sfm_carbide=[100, 350],
        fpt_hss=[],
        fpt_carbide=[.0050, .0030, .0020, .0010],
    ),
    'hardwood': Material(
        name='hardwood', sfm_hss=[600, 1000], sfm_carbide=[600, 1000],
        fpt_hss=[],
        fpt_carbide=[(.025, .027), (.025, .027), (.013, .016), (.004, .007),],
    ),
    'softwood': Material(
        name='softwood', sfm_hss=[600, 1000], sfm_carbide=[600, 1000],
        fpt_hss=[],
        fpt_carbide=[(.025, .027), (.025, .027), (.013, .016), (.004, .007),],
    ),
    'mdf': Material(
        name='mdf',
        sfm_hss=[600, 1000],
        sfm_carbide=[600, 1000],
        fpt_hss=[(.025, .027), (.025, .027), (.013, .016), (.004, .007),],
        fpt_carbide=[(.025, .027), (.025, .027), (.013, .016), (.004, .007), ],
    ),
    # FIXME - these numbers are pure guesses
    'fr4-1oz': Material(
        name='FR4 PCB, 1oz copper',
        sfm_hss=[250, 800],
        sfm_carbide=[600, 1000],
        fpt_hss=[(.025, .027), (.025, .027), (.013, .016), (.004, .007), (.001, .002), (.0005, .001)],
        fpt_carbide=[(.025, .027), (.025, .027), (.013, .016), (.004, .007),],
    ),
    'foam': Material(
        name='foam',
        sfm_hss=[100, 5000],
        sfm_carbide=[100, 5000],
        fpt_hss=[(.025, .027), (.025, .027), (.013, .016), (.004, .007),],
        fpt_carbide=[(.025, .027), (.025, .027), (.013, .016), (.004, .007),],
    ),
    # 'soft-plastic': Material(),
    # 'hard-plastic': Material(),
}


machines = {
    'k2cnc': Environment(min_rpm=10000, max_rpm=20000, max_feedrates=[144, 144, 20]),
    'lms': Environment(min_rpm=10000, max_rpm=20000, max_feedrates=[144, 144, 20]),
}

holes = HoleSize()
