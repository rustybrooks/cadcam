#!/usr/bin/env python

import openvoronoi as ovd    # https://github.com/aewallin/openvoronoi
import os
import shapely
import shapely.geometry
import shapely.affinity
import time
# import truetypetracer as ttt                   # https://github.com/aewallin/truetype-tracer

from geometry import *
from shapely.geometry import LineString, MultiLineString, Polygon, MultiPolygon, LinearRing, box

from functools import wraps
import inspect


def generate_wrapper(fn):
    @wraps(fn)
    def wrapper(self, *args, **kwds):
        if hasattr(self, '_tool') and self._tool:
            self.set_tool(self._tool)

        if hasattr(self, '_comment'):
            self.comment(self._comment)

        return fn(self, *args, **kwds)
    return wrapper


class CAMMeta(type):
    def __new__(cls, name, bases, attrs):
        if '__init__' in attrs:
            attrs['__init__'] = initializer(attrs['__init__'])

        if 'generate' in attrs:
            attrs['generate'] = generate_wrapper(attrs['generate'])

        return super(CAMMeta, cls).__new__(cls, name, bases, attrs)


def initializer(func):
    names, varargs, keywords, defaults = inspect.getargspec(func)

    @wraps(func)
    def wrapper(self, *args, **kargs):
        def _set(n, a):
            if n == 'tool':
                setattr(self, 'tool', None)
                setattr(self, '_tool', a)
            elif n == 'comment':
                setattr(self, '_comment', a)
            else:
                setattr(self, n, a)

        for name, arg in list(zip(names[1:], args)) + list(kargs.items()):
            _set(name, arg)

        for name, default in zip(reversed(names), reversed(defaults)):
            if not hasattr(self, name):
                _set(name, default)

        func(self, *args, **kargs)

    return wrapper


class CAM(object):
    __metaclass__ = CAMMeta
#    tool = None
#    material = None
#     material_factor = 1

    def __init__(self, tool=None, material=None, material_factor=1, speed=None, rapid_speed=100, **kwargs):
        # self._tool = tool
        # self.speed = None
        self.speed_stack = []
        self.distances = []
        self.speeds = []
        self.location = None
        # self.rapid_speed = 100  # FIXME
        self._save_speed = None
        self.f = None

    def set_output_fh(self, fh):
        self.f = fh

    def calc_stepover(self, stepover=None, material_factor=None, tool=None, max_stepover=0.95):
        stepover = stepover or self.stepover
        factor = material_factor or self.material_factor
        tool = tool or self.tool
        return min(stepover * factor, max_stepover) * tool.diameter

    def calc_stepdown(self, stepdown=None, material_factor=None, tool=None, max_stepdown=3):
        stepdown = stepdown or self.stepdown
        factor = material_factor or self.material_factor
        tool = tool or self.tool
        print stepdown, factor, max_stepdown, tool.diameter
        return min(stepdown * factor, max_stepdown) * tool.diameter

    def camtain(self, items, **kwargs):
        kwargs['tool'] = kwargs.get('tool', self.tool)
        kwargs['speed'] = kwargs.get('speed', self.speed)
        Camtainer(self.f, items, **kwargs)

    def zstep(self, z1, z2, stepdown=None, auto=True):
        if stepdown is None:
            stepdown = self.calc_stepdown()

        diff = float(z1 - z2)
        stepdown = diff / int(math.ceil(diff / stepdown))
        for z in frange(max(z2, z1 - stepdown), z2, stepdown):
            if auto:
                self.push_speed(self.tool.drill_speed)
                self.cut(z=z)
                self.pop_speed()

            yield z

    def zstep_size(self, stepdown=None, finish_mode=False):
        return (
        self.tool.zstep_pass_rough if finish_mode else self.tool.zstep_pass_finish) if stepdown is None else stepdown

    def genwrite(self, filename):
        with open(filename, "w") as self.f:
            self.write("%")
            self.write("G17 G20 G40 G90")  # FIXME revisit this later
            self.generate(self.f)
            self.end_program()

    def write(self, txt):
        if self.f is None:
            print "Can't write, f=None", txt
        else:
            self.f.write(txt + '\n')
            # sys.stdout.write(txt + '\n');

    @classmethod
    def format_movement(cls, x=None, y=None, z=None, a=None, rate=None):
        movement = []
        for var, axis in zip((x, y, z, a, rate), ("X", "Y", "Z", "A")):
            if var is not None: movement.append("%s%.6f" % (axis, var))

        return movement

    def push_speed(self, rate):
        self.speed_stack.append(self.speed)
        self.set_speed(rate)

    def pop_speed(self, ):
        rate = self.speed_stack.pop()
        self.set_speed(rate)

    def set_speed(self, rate):
        # print "Setting speed", rate
        self.speed = rate
        self._save_speed = rate

    def set_material(self, material):
        self.material = material

    def set_tool(self, tool):
        if not tool:
            return

        print "in set tool", self.tool, "==", tool
        if self.tool != tool:
            # so, due to the crappiness of my setup, I need to actually make a new file for every tool change
            if self.tool:
                print "!!!!!!!!!!!!!!!!!!!!!!!!!!!! new tool"
                self.end_program()
                self.f.next_part()

            # self.write("T%d" % (self.tool.index, ))
            self.set_speed(tool.rough_speed)
            tool.comment(self)

        self.tool = tool

    def end_program(self):
        self.write("M30")
        self.write("%")

    def comment(self, str):
        self.write("(%s)" % (str,))

    def record_linear_move(self, point, speed=None):
        if self.location is None:
            self.location = [x if x is not None else y for x, y in zip(point, (0, 0, 0))]
            return

        self.new_location = [x if x is not None else y for x, y in zip(point, self.location)]

        distance = length([x - y for x, y in zip(self.location, self.new_location)])
        self.distances.append(distance)
        self.speeds.append(speed or self._save_speed)
        self.location = self.new_location

    def record_arc_move(self, point, I, J, clockwise):
        if self.location is None:
            self.location = [x if x is not None else y for x, y in zip(point, (0, 0, 0))]
            return

        self.new_location = [x if x is not None else y for x, y in zip(point, self.location)]
        # ...
        self.location = self.new_location

    def goto(self, x=None, y=None, z=None, a=None, point=None, rate=None):
        if point is not None:
            x, y, z = point

        self.record_linear_move((x, y, z), speed=self.rapid_speed)
        self.write("G0 %s" % (" ".join(self.format_movement(x, y, z, a, rate))))

    def cut(self, x=None, y=None, z=None, a=None, point=None, rate=None):
        if point is not None:
            x, y, z = point

        if self.speed is not None and rate is None:
            feed = "F%0.3f " % self.speed
            self.speed = None
        elif rate is not None:
            feed = "F%0.3f " % rate
        else:
            feed = ""

        self.record_linear_move((x, y, z))
        self.write("G1 %s%s" % (feed, " ".join(self.format_movement(x, y, z, a, rate))))

    def to_arc(self, x, y, radius, start_angle, end_angle, clockwise=True, inside=None, adjust_tool_radius=True,
               cut_to=False, move_to=False, rate=None):
        if adjust_tool_radius:
            if inside is True:
                radius -= self.tool.diameter / 2.0
            elif inside is False:
                radius += self.tool.diameter / 2.0

        bx = x + math.cos(math.radians(start_angle)) * radius
        by = y + math.sin(math.radians(start_angle)) * radius

        # bx2 = x + math.cos(math.radians(end_angle))*radius
        # by2 = y + math.sin(math.radians(end_angle))*radius

        if cut_to:
            self.cut(x=bx, y=by, rate=rate)
        elif move_to:
            self.goto(x=bx, y=by, rate=rate)

    @classmethod
    def arc_start_end(cls, x, y, radius, start_angle, end_angle, clockwise=True, adjust_tool_radius=False, inside=None):
        if adjust_tool_radius:
            if inside is True:
                radius -= cls.tool.diameter / 2.0
            elif inside is False:
                radius += cls.tool.diameter / 2.0

        bx = x + math.cos(math.radians(start_angle)) * radius
        by = y + math.sin(math.radians(start_angle)) * radius

        bx2 = x + math.cos(math.radians(end_angle)) * radius
        by2 = y + math.sin(math.radians(end_angle)) * radius

        return [[bx, by], [bx2, by2]]

    def cut_arc3(
            self, x, y, radius, start_pt, end_pt, rate=None, z=None, clockwise=True,
            cut_to=False, move_to=False, return_to=False, inside=None, adjust_tool_radius=True, comment=None,
    ):
        start = (start_pt[0] - x, start_pt[1] - y)
        end = (end_pt[0] - x, end_pt[1] - y)
        theta1 = math.degrees(math.atan2(start[1], start[0]))
        theta2 = math.degrees(math.atan2(end[1], end[0]))

        if not clockwise:
            while (theta2 - theta1) > -1e-9:
                theta2 -= 360
        else:
            while (theta2 - theta1) < 1e-9:
                theta2 += 360

        return self.cut_arc2(
                x, y, radius=radius, start_angle=theta1, end_angle=theta2, rate=rate, z=z, clockwise=clockwise,
                cut_to=cut_to, move_to=move_to, return_to=return_to, inside=inside,
                adjust_tool_radius=adjust_tool_radius,
                comment=comment
        )

    # x, y forms the center of your arc
    # if I did this right, I think it presumes you're at bx, by already
    def cut_arc2(
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

    def cut_linestring(self, ls, depth, clearz):
        coords = ls.coords

        self.goto(z=clearz)
        self.goto(coords[0][0], coords[0][1])
        self.cut(z=depth)

        for c in coords[1:]:
            self.cut(c[0], c[1])

    def drill_cycle(self, coords=None, depth=0, clearZ=0, peck=0, feed=None, shallow=False, dwell=None,
                    retract_to_z=False):
        pre = "G98" if retract_to_z else "G99"
        if shallow and dwell is None:
            cmd = "G81 R%0.3f Z%0.3f F%0.3f" % (clearZ, depth, feed)
        elif shallow and dwell is not None:
            cmd = "G82 R%0.3f Z%0.3f P%0.3f F%0.3f" % (clearZ, depth, dwell, feed)
        elif not shallow and dwell is None:
            cmd = "G83 R%0.3f Z%0.3f P%0.3f F%0.3f Q%0.3f" % (clearZ, depth, dwell, feed, peck)
        elif not shallow and dwell is not None:
            cmd = "G83 R%0.3f Z%0.3f P%0.3f F%0.3f Q%0.3f" % (clearZ, depth, dwell, feed, peck)

        coordstr = '\n'.join("X%0.3f Y%0.3f" % (x, y) for x, y in coords[1:])
        whole_command = "X%0.3f Y%0.3f\n%s %s\n%s G80" % (coords[0][0], coords[0][1], pre, cmd, coordstr)
        #         print whole_command
        self.write(whole_command)

    def add(self, cam):
        cam.generate(self.f)

    def total_distance(self):
        return sum(self.distances)

    def total_time(self):
        return sum([a / float(b / 60.0) for a, b in zip(self.distances, self.speeds)])


def _dist(a, b):
    if a is None or b is None:
        return 1e12
    return math.sqrt((a[0] - b[0])**2 + (a[1]-b[1])**2)

# from hsm import HSMStraightGroove, HSMCleanoutCorner, HSMRectPocket

# feed rate formula/data
# ipm = rpm*ipt*teeth
# ipm = inches/minute
# ipt = inches/tooth
#
# rpm = cs * 3.82 / d
# cs = cutting speed (fpm)
# d = diam

# fpm = .262*d*rpm
# ipr = ipm/RPM or chipload*teeth
# chipload = ipm / (RPM*F) or ipr/teeth

# sfm chip-load: 1/8 1/4 1/2 1
# fpm_carbide_endmill = {
#     'Aluminum Alloys': [600-1200 .0010 .0020 .0040 .0080],
#     'Brass': [200-350 .0010 .0020 .0030 .0050],
#     'Bronze': [200-350 .0010 .0020 .0030 .0050],
#     'Carbon Steel': [100-600 .0010 .0015 .0030 .0060],
#     'Cast Iron': [80-350 .0010 .0015 .0030 .0060],
#     'Cast Steel': [200-350 .0005 .0010 .0020 .0040],
#     'Cobalt Base Alloys': [20-80 .0005 .0008 .0010 .0020],
#     'Copper': [350-900 .0010 .0020 .0030 .0060],
#     'Die Steel': [50-300 .0005 .0010 .0020 .0040],
#     'Graphite': [600-1000 .0020 .0050 .0080 .0100],
#     'Inconel/Monel': [30-50 .0005 .0010 .0015 .0030],
#     'Magnesium': [900-1300 .0010 .0020 .0040 .0080],
#     'Malleable Iron': [200-500 .0005 .0010 .0030 .0070],
#     'Nickel Base Alloys': [50-100 .0002 .0008 .0010 .0020],
#     'Plastic': [600-1200 .0010 .0030 .0060 .0100],
#     'Stainless Steel - Free Machining': [100-300 .0005 .0010 .0020 .0030],
#     'Stainless Steel - Other': [50-250 .0005 .0010 .0020 .0030],
#     'Steel - Annealed': [100-350 .0010 .0020 .0030 .0050],
#     'Steel - Rc 18-24': [100-500 .0004 .0008 .0015 .0045],
#     'Steel - Rc 25-37': [25-120 .0003 .0005 .0010 .0030],
#     'Titanium': [100-200 .0005 .0008 .0015 .0030],
#     }

# fpm_carbide_drills = {
# 'Aluminum Alloys': [150-400 .0010 .0050 .0030 .0050],
# 'Brass & Bronze': [100-300 .0005 .0010 .0020 .0040],
# 'Low Carbon Steel': [85-150 .0005 .0010 .0020 .0040],
# 'Cast Iron': [100-300 .0010 .0020 .0030 .0050],
# 'Hardened Steel RC-50': [30-90 .0005 .0010 .0020 .0030],
# 'Copper': [150-400 .0010 .0030 .0050 .0060],
# 'Die Steel': [50-250 .0005 .0005 .0020 .0040],
# 'Inconel/Monel': [30-90 .0005 .0005 .0010 .0015],
# 'Magnesium': [200-650 .0015 .0030 .0050 .0080],
# 'Malleable Iron': [80-250 .0010 .0020 .0030 .0050],
# 'Nickel Base Alloys': [30-90 .0005 .0006 .0010 .0015],
# 'Plastic': [250-600 .0015 .0030 .0040 .0060],
# 'Stainless Steel - Soft': [50-150 .0005 .0005 .0020 .0040],
# 'Stainless Steel - Hard': [30-90 .0005 .0005 .0010 .0015],
# 'Titanium - Soft': [60-200 .0005 .0020 .0040 .0050],
# 'Titanium - Hard': [45-200 .0005 .0008 .0020 .0040],


class Material(object):
    def __init__(self, name, sfm_hss, sfm_carbide, fpt_hss, fpt_carbide):
        self.name = name
        self.sfm_hss = sfm_hss
        self.sfm_carbide = sfm_carbide


# http://www.micro-machine-shop.com/SFM_Formulae_Chart_2.pdf
materials = {
    'aluminum': Material(
        name='aluminum', sfm_hss=[250, 800], sfm_carbide=[600, 1200],
        fpt_hss=[], fpt_carbide=[.0010, .0020, .0040, .0080],
    ),
    'steel': Material(
        name='steel', sfm_hss=[], sfm_carbide=[100, 350],
        fpt_hss=[], fpt_carbide=[.0010, .0020, .0030, .0050],
    ),
    'hardwood': Material(
        name='', sfm_hss=[], sfm_carbide=[],
        fpt_hss=[], fpt_carbide=[(.003, .005), (.009, .011), (.019, .021), (.019, .021)],
    ),
    'softwood': Material(
        name='', sfm_hss=[], sfm_carbide=[],
        fpt_hss=[], fpt_carbide=[(.004, .006), (.011, .013), (.021, .023), (.021, .023)],
    ),
    'mdf': Material(
        name='', sfm_hss=[], sfm_carbide=[],
        fpt_hss=[], fpt_carbide=[(.004, .007), (.013, .016), (.025, .027), (.025, .027)],
    ),
}


MM = 0.0393701


class HoleSize(object):

##        # these are not really screws, but they are push in threaded rivets I like
#        "Rivet-M5":     [0,     "",     0,    "",  .268,    "H",     0,    ""     ],  # H might be too small...
#        "Rivet-1/4-20": [0,     "",     0,    "",  .350,     "",     0,    ""     ],

    nuts = {
        'rivnut-M5': {
            'minor_dia': .268,
            'minor_length': 0.51,
            'major_dia': .396,
            'major_length': .05
        },
        'rivnut-1/4-20': {
            'minor_dia': .350,
            'minor_length': .538,
            'major_dia': .490,
            'major_length': .05,
        },
    }

    # all measurements in mm
    # list is
    # http://www.littlemachineshop.com/reference/tapdrillsizes.pdf
    screws = {
        # inch thread
        "1/4-20": [.1887, "7",    .2010, "7/32", .2188, "F", .2570, "H", .2660],
        "1/4-28": [.2062, "3",    .2130, "1",    .2280, "F", .2570, "H", .2660],
        "1/4-32": [.2117, "7/32", .2188, "1",    .2280, "F", .2570, "H", .2660],

        # metric thread
        "M1.5-.35":     [ 1.15, "56",   1.25, "55",    1.60, "1/16", 1.65, "52"   ],
        "M1.6-.35":     [ 1.25, "55",   1.35, "54",    1.70, "51",   1.75, "50"   ],
        "M1.8-.35":     [ 1.45, "53",   1.55, "1/16",  1.90, "49",   2.00, "5/64" ],
        "M2-.45":       [ 1.55, "1/16", 1.70, "51",    2.210, "45",  2.20, "44"   ],
        "M2-.40":       [ 1.60, "52",   1.75, "50",    2.10, "45",   2.20, "44"   ],
        "M2.2-.45":     [ 1.75, "50",   1.90, "48",    2.30, "3/32", 2.40, "41"   ],
        "M2.5-.45":     [ 2.05, "46",   2.20, "44",    2.65, "37",   2.75, "7/64" ],
        "M3-.60":       [ 2.40, "41",   2.60, "37",    3.15, "1/8",  3.30, "30"   ],
        "M3-.50":       [ 2.50, "39",   2.70, "36",    3.15, "1/8",  3.30, "30"   ],
        "M3.5-.60":     [ 2.90, "32",   3.10, "31",    3.70, "27",   3.85, "24"   ],
        "M4-.75":       [ 3.25, "30",   3.50, "28",    4.20, "19",   4.40, "17"   ],
        "M4-.70":       [ 3.30, "30",   3.50, "28",    4.20, "19",   4.40, "17"   ],
        "M4.5-.75":     [ 3.75, "25",   4.00, "22",    4.75, "13",   5.00, "9"    ],
        "M5-1.00":      [ 4.00, "21",   4.40, "11/64", 5.25, "5",    5.50, "7/32" ],
        "M5-.90":       [ 4.10, "20",   4.40, "17",    5.25, "5",    5.50, "7/32" ],
        "M5-.80":       [ 4.20, "19",   4.50, "16",    5.25, "5",    5.50, "7/32" ],
        "M5.5-.90":     [ 4.60, "14",   4.90, "10",    5.80, "1",    6.10, "B"    ],
        "M6-1.00":      [ 5.00, "8",    5.40, "4",     6.30, "E",    6.60, "G"    ],
        "M6-0.75":      [ 5.25, "4",    5.50, "7/32",  6.30, "E",    6.60, "G"    ],
    }

    @classmethod
    # type is thread or clearance
    # subtype for thread is 75 or 50
    # subtype for clearance is close or standard
    def screw(self, screw, type, subtype, bit_name=False):
        index = 0 if type == "thread" else 4
        if subtype == "50" or subtype == "standard":
            index += 2

        if bit_name:
            index += 1

        return self.screws[screw][index]


class Stock(CAM):
    def __init__(self):
        pass

    def write(self, txt):
        self.f.write(txt + '\n')


class RectStock(Stock):
    def __init__(self, width, height, thickness, origin=(0, 0, 0)):
        # self.width = width
        # self.height = height
        # self.thickness = thickness
        # self.origin = origin
        pass

    def generate(self):
        self.write("(RectSolid %f %f %f origin=%f %f %f)" % (self.width, self.height, self.thickness, self.origin[0], self.origin[1], self.origin[2]))


class CylinderStock(Stock):
    def __init__(self):
        pass


class File(object):
    def __init__(self, filename):

        self.part = 1

        if isinstance(filename, str):
            self.f = open(filename, "w")
            self.filename = filename
            self.fileroot, self.fileext = os.path.splitext(self.filename)
        else:
            self.f = filename  # otherwise we assume it's some writable obj

    def next_part(self):
        print ".......... next part"
        filename = self.f.name
        # print "filename ==", filename
        if filename:
            self.f.close()
            self.part += 1
            self.f = open(self.fileroot + "_part_%d" % (self.part, ) + self.fileext, "w")
            self.write("%\n")
            self.write("G17 G20 G40 G90\n")  # FIXME revisit this later

    def write(self, txt):
        self.f.write(txt)


# by default, is self_contained if given a file name, otherwise is not
class Camtainer(object):
    def __init__(self, filename=None, cams=[], self_contained=None, origin=None, speed=None, tool=None):
        self.origin = origin
        self.speed = speed
        self.tool = tool

        if self_contained is None:
            if isinstance(filename, str):
                self.self_contained = True
            else:
                self.self_contained = False
        else:
            self.self_contained = self_contained

        if isinstance(cams, list):
            self.cams = cams
        else:
            self.cams = [cams]

        self.file_handle = File(filename)
        self.write()

    def add(self, cam):
        if isinstance(cam, list):
            self.cams.extend(cam)
        else:
            self.cams.append(cam)

    def generate(self):
        #
        
        for cam in self.cams:
            cam.tool = self.tool
            cam.speed = self.speed
            cam.set_output_fh(self.file_handle)
            cam.generate()

    def write(self):
        c = CAM(tool=None)
        c.set_output_fh(self.file_handle)

        if self.self_contained:
            c.write("%")
            c.write("G17 G20 G40 G90")  # FIXME revisit this later

        if self.origin is not None:
            c.goto(*self.origin)

        self.generate()

        if self.self_contained:
            c.end_program()

    def drawable_write(self, file_handle):
        self.generate()


class Tool(object):
    index_counter = 0

    def __init__(self):
        self.index_counter += 1
        self.index = self.index_counter

    def comment(self, cam):
        pass


class StraightRouterBit(Tool):
    def __init__(self, diameter, rough_speed=None, drill_speed=None):
        super(StraightRouterBit, self).__init__()

        self.zstep_pass_rough = diameter/2
        self.zstep_pass_finish = diameter/2
        self.zstep_depth_finish = 0.05
        self.diameter = diameter
        self.cutting_length = 5 # FIXME

        self.drill_speed = drill_speed or 20  # rename!
        self.rough_speed = rough_speed or 60 # FIXME make this a config param
        self.rough_rotate_speed = 10
        self.fine_rotate_speed = 5
        self.finish_speed = 50

    def comment(self, cam):
        print cam.comment
        cam.comment("FlatMill %f %f" % (self.cutting_length, self.diameter/2.0))


class BallRouterBit(StraightRouterBit):
    def comment(self, cam):
        cam.comment("BallMill %f %f" % (self.cutting_length, self.diameter/2.0))


class DovetailRouterBit(Tool):
    def __init__(self, minor_diameter=None, major_diameter=None, height=None):
        super(DovetailRouterBit, self).__init__()

        self.major_diameter = major_diameter
        self.minor_diameter = minor_diameter
        self.height = height

        self.zstep_pass_rough = major_diameter/2
        self.zstep_pass_finish = major_diameter/2
        self.zstep_depth_finish = 0.05
        self.cutting_length=1

        self.drill_speed = 20  # rename!
        self.rough_speed = 100
        self.rough_rotate_speed = 10
        self.fine_rotate_speed = 5
        self.finish_speed = 30


class VRouterBit(Tool):
    def __init__(self, included_angle, diameter=None, drill_speed=None, rough_speed=None):
        super(VRouterBit, self).__init__()

        self.included_angle=included_angle
        self.diameter = diameter
        self.cutting_length = 1

        self.drill_speed = drill_speed or 20  # rename!
        self.rough_speed = rough_speed or 60 # FIXME make this a config param
        self.rough_rotate_speed = 10
        self.fine_rotate_speed = 5
        self.finish_speed = 30

    def comment(self, cam):
        cam.comment("VMill %f %f %f" % (self.cutting_length, self.diameter/2.0, self.included_angle))


class Laser(Tool):
    def __init__(self, ):
        super(Laser, self).__init__()

        self.diameter = .01

        self.zstep_pass_rough = 0.25
        self.zstep_pass_finish = 0.25
        self.zstep_depth_finish = 0.05
        self.cutting_length=1

        self.drill_speed = 100  # rename!
        self.rough_speed = 100
        self.rough_rotate_speed = 100
        self.fine_rotate_speed = 100
        self.finish_speed = 100





class Goto(CAM):
    def __init__(self, *args, **kwargs):
        super(Goto, self).__init__(tool=None)
        self.args = args
        self.kwargs = kwargs

    def generate(self):
        self.goto(*self.args, **self.kwargs)


class DrillCycle(CAM):
    def __init__(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs

    def generate(self):
        self.drill_cycle(*self.args, **self.kwargs)


# takes a outline and makes a profile, based on tooling
# It is only considering offset in XY dimensions at the moment
class ThreeDProfile(CAM):
    # segments is a list of (x, y, z) points defining the line
    # This represets the path at the TOP of the path.  It will iterate the path to a given depth
    def __init__(self, segments, tool, depth, side='right', tolerance=0.001, stepdown=None):
        super(ThreeDProfile, self).__init__(tool=tool)

        self.clearance=0.25
        self.depth = depth
        self.stepdown = stepdown

        R = tool.diameter/2.0
        self.geom = shapely.geometry.LineString(segments)
        #.parallel_offset(R, side)
        self.geom_simple = self.geom
        #.simplify(tolerance)

        if isinstance(self.geom_simple, shapely.geometry.MultiLineString):
            self.coords = [x.coords for x in self.geom_simple.geoms]
        else:
            self.coords = [self.geom_simple.coords]


        # self.geom_simple = self.geom

        #try:
        #    self.coords = self.geom_simple.coords
        #except:
        #    self.coords = self.geom.coords

        # self.coords = shapely.geometry.LineString(segments).coords

        # self.maxz = max([x[2] for x in segments])
        # self.minz = max([x[2] for x in segments])
        self.maxz = 0
        self.minz = 0

    def safediv(self, a, b):
        if b == 0:
            return 0
        else:
            return a/b

    def generate(self):


        clearZ = self.maxz + self.clearance

        for coord in self.coords:
            if len(coord) == 0: continue
            closed = False if False in [self.safediv(abs(a - b), a) < .00001 for a, b in zip(coord[0], coord[-1])] else True

            first = list(coord)[0]
            if closed:
                self.goto(z=clearZ)
                self.goto(x=first[0], y=first[1])

            self.set_speed(self.tool.rough_speed)
            for depth in self.zstep(0, -self.depth, self.stepdown, auto=False):
                self.comment("Starting path at depth %f" % (depth, ))
                if not closed:
                    self.goto(z=clearZ)
                    self.goto(x=first[0], y=first[1])

                # print list(coord)
                self.cut(z=depth)
                for (x, y, _) in coord:
                    self.cut(x=x, y=y)

            self.goto(z=clearZ)


# FIXME convert to use Line() instance
class CoordProfile(CAM):
    # segments is a list of (x, y) points defining the line
    # This represets the path at the TOP of the path.  It will iterate the path to a given depth
    def __init__(self, tool, segments, start_height=0, depth=0, stepdown=None):
        super(CoordProfile, self).__init__(tool=None)

        self._tool = tool
        self.clearance = start_height + 0.25
        self.depth = depth
        self.start_height = start_height
        self.stepdown = stepdown if stepdown else self.tool.diameter/3.0

        R = tool.diameter/2.0
        self.geom = shapely.geometry.LineString(segments)
        #.parallel_offset(R, side)
        self.geom_simple = self.geom
        #.simplify(tolerance)

        if isinstance(self.geom_simple, shapely.geometry.MultiLineString):
            self.coords = [x.coords for x in self.geom_simple.geoms]
        else:
            self.coords = [self.geom_simple.coords]

    def safediv(self, a, b):
        if b == 0:
            return 0
        else:
            return a/b

    def generate(self):

        self.set_tool(self._tool)

        clearZ = self.start_height + self.clearance
        self.goto(z=clearZ)

        for coord in self.coords:
            if len(coord) == 0: continue
            closed = False if False in [self.safediv(abs(a - b), a) < .00001 for a, b in zip(coord[0], coord[-1])] else True

            first = list(coord)[0]
            if closed:
                self.goto(z=clearZ)
                self.goto(x=first[0], y=first[1])

            self.set_speed(self.tool.rough_speed)
            for depth in frange(0, self.depth, self.stepdown):
                self.comment("Starting path at depth %f" % (depth, ))
                if not closed:
                    self.goto(z=clearZ)
                    self.goto(x=first[0], y=first[1])

                # print list(coord)
                self.cut(z=self.start_height - depth)
                for (x, y) in coord:
                    self.cut(x=x, y=y)

            self.goto(z=clearZ)


class SVGProfile(CAM):
    # offset is the fraction of the tool diameter you want to offset, in the direction of 'side'
    def __init__(
            self, tool, file, topleft, depth, 
            scale=1.0, translate=None, rotate=None,
            offset=1.0, stepdown=None, side='inner', comment=None, material_factor=1):
        super(SVGProfile, self).__init__(tool=tool)

        # self.tool = tool
        # self.material_factor = material_factor
        # self.topleft = topleft
        # self.depth = depth
        self.stepdown = stepdown if stepdown else self.tool.diameter/2.0
        # self.side = side
        # self.comment = comment
        # self.offset = offset
        # self.file = file
        # self.scale = scale
        # self.rotate = rotate
        # self.translate = translate

    def generate(self):
#        self.set_speed(self.tool.rough_speed)

        # print "scale = ", self.scale
        svgf = svg.parse(self.file).scale(self.scale)
        #svgf = svg.parse(self.file)
        a, b = svgf.bbox()
        width, height = b.coord()
        self.clearZ = self.topleft[2] + 0.125
        self.generate_group(svgf.items)

        # print "distance =", self.total_distance()
        # print "time =", "%0.2d:%0.2d" % (int(self.total_time()/60), (self.total_time() % 60))

    def generate_segment(self, segment):
        points = [x.coord() for x in segment]
        # print points

        # print min(self.depth, self.stepdown*self.material_factor)
        for step in frange(min(self.depth, self.stepdown*self.material_factor), self.depth, self.stepdown*self.material_factor):
            newpoint = points[0]
            dist = length([x - y for x, y in zip(self.location, newpoint)]) if self.location else 1

            if dist > 0.001:
                self.goto(z=self.clearZ)
                self.goto(*newpoint)

            self.cut(z=self.topleft[2] - step)

            for p in points[1:]:
                self.cut(*p)

            points.reverse()


    def generate_group(self, items):
        for el in items:
            if isinstance(el, svg.Group):
                self.generate_group(el.items)
            elif isinstance(el, svg.Line):
                for segment in el.segments(0.001):
                    self.generate_segment(segment)
            elif isinstance(el, (svg.Path, svg.Rect)):
                for segment in el.simplify(0.001):
                    self.generate_segment(segment)
            elif isinstance(el, svg.Circle):
                for segment in el.segments(0.001):
                    self.generate_segment(segment)
            else:
                print "Dunno wtf this is", repr(el)


class CircleProfile(CAM):
    # segments is a list of (x, y) points defining the line
    def __init__(self, tool, center, z, radius, depth, stepdown=None, side="inner", comment=None, start_angle=0, end_angle=360, material_factor=1):
        super(CircleProfile, self).__init__(tool=None)
        self._tool = tool
        self.material_factor = material_factor
        self.center = center
        self.z = z
        self.depth = depth
        self.radius = radius
        self.stepdown = stepdown
        # self.comment = comment
        self.side = side
        self.start_angle = start_angle
        self.end_angle = end_angle

        if self.start_angle == 0 and self.end_angle == 360:
            self.full_circle = True
        else:
            self.full_circle = False

    def generate(self):

        self.set_tool(self._tool)

        #if self.comment is None:
        #    self.comment = "Cutting CircleProfile, center=%r, rad=%0.3f, depth=%0.3f" % (self.center, self.radius, self.depth)
        self.write("( %s )" % self.comment)
        self.write("G17")

        x, y = self.center
        z1 = self.z
        z2 = self.z-self.depth

        clearZ = z1 + .25
        R = self.tool.diameter/2.0
        if self.side == "inner":
            rad = self.radius - R
        elif self.side == "outer":
            rad = self.radius + R
        elif self.side == "center":
            rad = self.radius
        else:
            rad = 1

        bx = x + math.sin(math.radians(-1*self.start_angle))*rad
        by = y + math.cos(math.radians(-1*self.start_angle))*rad

        bx2 = x + math.sin(math.radians(-1*self.end_angle))*rad
        by2 = y + math.cos(math.radians(-1*self.end_angle))*rad

        first = True
        for Z in self.zstep(z1, z2, self.calc_stepdown(), auto=False):
            if first or not self.full_circle:
                self.goto(z=clearZ)
                self.goto(x=bx, y=by)
                first = False

            self.cut(z=Z, rate=self.tool.drill_speed)
            self.set_speed(self.tool.rough_speed)
            self.cut_arc(bx2, by2, x - bx, y - by)


class RectPocketCornerRelief(CAM):
    def __init__(self, tool, p1, p2, z, depth, stepdown=None):
        super(RectPocketCornerRelief, self).__init__(None)
        self._tool = tool
        self.p1 = p1
        self.p2 = p2
        self.z = z
        self.depth = depth
        self.stepdown = stepdown if stepdown else tool.diameter

    def generate(self):

        self.set_tool(self._tool)

        px1, py1 = self.p1
        px2, py2 = self.p2
        r = 1.1 * self.tool.diameter / 2.0
        off = r / (2 * math.sqrt(2))

        px1, px2 = min(px1, px2), max(px1, px2)
        py1, py2 = min(py1, py2), max(py1, py2)
        px1 += r
        py1 += r
        px2 -= r
        py2 -= r

        clearZ = self.z + 0.25

        stepdown = self.calc_stepdown()
        z1 = self.z
        z2 = self.z - self.depth
        self.goto(z=self.z)
        for z in self.zstep(z1, z2, stepdown, auto=False):
            self.goto(x=px1, y=py1)
            self.cut(z=z)
            self.cut(x=px1-off, y=py1-off)
            self.goto(x=px1, y=py1)

        self.goto(z=self.z)
        for z in self.zstep(z1, z2, stepdown, auto=False):
            self.goto(x=px1, y=py2)
            self.cut(z=z)
            self.cut(x=px1-off, y=py2+off)
            self.goto(x=px1, y=py2)

        self.goto(z=self.z)
        for z in self.zstep(z1, z2, stepdown, auto=False):
            self.goto(x=px2, y=py2)
            self.cut(z=z)
            self.cut(x=px2+off, y=py2+off)
            self.goto(x=px2, y=py2)

        self.goto(z=self.z)
        for z in self.zstep(z1, z2, stepdown, auto=False):
            self.goto(x=px2, y=py1)
            self.cut(z=z)
            self.cut(x=px2+off, y=py1-off)
            self.goto(x=px2, y=py1)


# type is x (movement parallel to x axis) or y (y axis)
# probably needs to stop short of boundaries and then trim
class RectPocket(CAM):
    def __init__(self, tool, p1, p2, z, depth, stepover=.5, type='x', stepdown=None, rough_margin=0, auto_clear=True):
        super(RectPocket, self).__init__(tool=None)
        self._tool = tool
        self.depth = depth
        self.stepover = stepover
        self.type = type
        self.stepdown = stepdown if stepdown else tool.diameter/2.0
        self.z = z
        self.p1 = p1
        self.p2 = p2
        self.rough_margin = rough_margin # FIXME not used yet
        self.auto_clear = auto_clear

    def generate(self):


        self.set_tool(self._tool)

        R = self.tool.diameter/2.0

        x1p, y1p = self.p1
        x2p, y2p = self.p2

        if x1p < x2p:
            x1 = x1p + R
            x2 = x2p - R
        else:
            x1 = x1p - R
            x2 = x2p + R

        if y1p < y2p:
            y1 = y1p + R
            y2 = y2p - R
        else:
            y1 = y1p - R
            y2 = y2p + R

        #width = x2 - x1
        #height = y2 - y1
        
        step = self.tool.diameter*self.stepover

        self.set_speed(self.tool.rough_speed)

        clearZ = self.z + .25


        for Z in self.zstep(0, -1*self.depth, auto=False, stepdown=self.stepdown):
            # Don't actually need to go very far up
            if self.auto_clear:
                self.goto(z=clearZ)

            self.goto(x=x1, y=y1)

            self.cut(z=self.z+Z, rate=self.tool.drill_speed)
            self.set_speed(self.tool.rough_speed)

            plus = True
            if self.type == "x":
                for y in frange(y1, y2, step, True):
                    self.cut(y=y)
                    if plus:
                        self.cut(x=x2)
                    else:
                        self.cut(x=x1)

                    plus = not plus

            else:
                for x in frange(x1, x2, step, True):
                    self.cut(x=x)
                    if plus:
                        self.cut(y=y2)
                    else:
                        self.cut(y=y1)

                    plus = not plus
                
        if self.auto_clear:
            self.goto(z=clearZ)
                    

class CirclePocket(CAM):
    def __init__(self, tool, center, inner_rad, outer_rad, depth, stepover=0.5, stepdown=None, comment=None, clockwise=True):
        super(CirclePocket, self).__init__(tool=None)
        self._tool = tool

        # self.center = center
        # self.inner_rad = inner_rad
        # self.outer_rad=outer_rad
        # self.depth = depth
        # self.stepover = stepover
        # self.stepdown = stepdown
        # self.comment_message = comment
        # self.clockwise = clockwise

        if self._comment is None:
            self._comment = "Cutting CirclePocket at %r, from %.3f to %.3f, depth=%.3f" % (list(self.center), self.inner_rad, self.outer_rad, self.depth)

    def generate(self):
        # self.set_tool(self._tool)

        outty = True


        # self.comment(self.comment_message)
        self.write("G17")

        R = self.tool.diameter/2.0
        x1, y1, z1 = self.center
        z2 = z1 - self.depth

        clearZ = z1 + 0.25
        self.goto(z=clearZ)

        for Z in self.zstep(z1, z2, self.stepdown, auto=False):
            if outty:
                rad1 = self.inner_rad+R
                rad2 = self.outer_rad-R
            else:
                rad1 = self.outer_rad-R
                rad2 = self.inner_rad+R

            # if rad2 > rad1:
            #    rad2 = rad1

            bx = x1 + math.sin(0)*rad1
            by = y1 + math.cos(0)*rad1
            self.goto(z=clearZ)
            self.goto(x=bx, y=by)
            self.cut(z=Z)
            for rad in frange(rad1, rad2, self.stepover*self.tool.diameter, True):
                bx = x1 + math.sin(0)*rad
                by = y1 + math.cos(0)*rad
                self.cut(x=bx, y=by)
                self.cut_arc(bx, by, x1-bx, y1-by, clockwise=self.clockwise)

            outty = not outty


# This will make a helical arc with the outter radius = outter-rad
# it only operates at one radius
# with outter_rad = 1*r to 2*r this is essentially a drilling procedure
# otherwise it'll be making a groove with a width of the diameter of the bit
class HelicalDrill(CAM):
    def __init__(self, tool, center, outer_rad, depth, z=None, stepdown=None, clockwise=True, comment=None, speed=None):
        super(HelicalDrill, self).__init__(tool=None)

        self._tool = tool
        self.center = center
        self.outer_rad = outer_rad
        self.depth = depth
        self.comment_message = comment
        self.stepdown = stepdown if stepdown else tool.diameter/2.0
        self.clockwise = clockwise
        self._speed = speed or tool.drill_speed
        self.z = z

    def generate(self):

        self.set_tool(self._tool)

        # FIXME - make this a context manager
        self.push_speed(self._speed)
        self.generate_internal()
        self.pop_speed()
 
    def generate_internal(self):
        R = self.tool.diameter/2.0
        x1, y1 = self.center
        z1 = self.z
        z2 = z1 - self.depth
        clearZ = z1 + 0.25

        if self.depth == 0:
            return

        if self.comment_message is None:
            self.comment_message = "Cutting HelicalDrill at %r, outter_rad=%.3f, depth=%.3f" % (
                list(self.center), self.outer_rad, self.depth
            )
        self.comment(self.comment_message)

        if self.outer_rad <= R:
            self.goto(z=clearZ)
            self.goto(x1, y1)

        self.write("G17")

        rad = self.outer_rad-R

        start, end = self.arc_start_end(x1, y1, rad, 0, 0, clockwise=self.clockwise)
        self.goto(x=start[0], y=start[1])
        self.goto(z=z1)

        for Z in self.zstep(z1, z2, self.stepdown, auto=False):
            self.cut_arc2(x1, y1, rad, start_angle=0, end_angle=0, z=Z, clockwise=self.clockwise, cut_to=True)

        self.cut_arc2(x1, y1, rad, start_angle=0, end_angle=0, z=z2, clockwise=self.clockwise, cut_to=True)


class Screw(CAM):
    def __init__(self, length, outer_rad, inner_rad, rough_rad, rough_depth=1/8., fine_depth=1/16.):
        super(Screw, self).__init__(tool=tools['1/4in spiral upcut'])
        self.length = 2

        self.length = length
        self.outer_rad = outer_rad
        self.inner_rad = inner_rad
        self.rough_rad = rough_rad
        self.rough_depth=rough_depth
        self.fine_depth=fine_depth

    def generate(self):


        self.write("G0 X0.0 Y0.0 Z%.3f" % (self.rough_rad+.25))

        rotations = self.length/0.125

        # roughing to cylinder - last pass or 2 is fine cut
        rad = self.rough_rad
        dir_plus = True
        increment = self.rough_depth
        fine = False
        while rad >= self.outer_rad:
            self.write("(%s to cylinder radius=%.3f)" % ('Fine-tuning' if fine else 'Roughing', rad))

            if dir_plus:
                x = self.length
                rot = 360*rotations
                dir_plus=False
            else:
                x = 0
                rot = 0
                dir_plus=True

                
            self.write("G1 Z%.3f F%.3f" % (rad, self.tool.drill_speed))
            self.write("G1 X%.3f A%.3f F%.3f" % (x, rot, self.tool.fine_rotate_speed if fine else self.tool.rough_rotate_speed))

            if rad - self.rough_rad < self.rough_depth:
                fine = True

            if rad <= self.outer_rad: break

            rad -= (self.fine_depth if fine else self.rough_depth)
            if rad < self.outer_rad: rad = self.outer_rad


        # screw cutting
        rad = self.outer_rad
        while rad > self.inner_rad:
            rad -= self.fine_depth
            if rad < self.inner_rad: rad = self.inner_rad

            self.write("(Screw cutting radius = %.3f)" % rad)
            self.write("G0 Z%.3f" % (self.outer_rad+.25))
            self.write("G0 X%.3f A0" % (0))
            self.write("G1 Z%.3f F%.3f" % (rad, self.tool.drill_speed))
            self.write("G1 X%.3f A%.3f F%.3f" % (self.length, 360*5, self.tool.fine_rotate_speed))
        

class BoltCircle(CAM):
    def __init__(self, tool, center, z, depth, radius, bolts, bolt_size, first_angle=0, stepdown=None):
        super(BoltCircle, self).__init__(tool=None)
        self._tool = tool
        self.center = center
        self.z = z
        self.depth = depth
        self.radius = radius
        self.bolts = bolts
        self.bolt_size = bolt_size
        self.stepdown = stepdown
        self.first_angle = first_angle
        self.clearZ = self.z + 0.25

    def generate(self):

        self.set_tool(self._tool)

        bolt_rad = HoleSize.screw(screw=self.bolt_size, type='clearance', subtype='standard')
        for b in range(self.bolts):
            angle = math.radians(self.first_angle + b*360./self.bolts)
            bx = self.center[0] + math.sin(angle) * self.radius
            by = self.center[1] + math.cos(angle) * self.radius

            self.goto(z=self.clearZ)
            self.camtain(HelicalDrill(tool=self.tool, center=(bx, by), outer_rad=bolt_rad, depth=self.depth, z=self.z))


# assumes 1/4" bolt, want to fight about it?
class Ring(CAM):
    def __init__(self, tool, center, rad1, rad2, depth, stepdown, bolts=None, boltrad=0):
        super(Ring, self).__init__(tool=tool)

        self.center = center
        self.rad1 = rad1
        self.rad2 = rad2
        self.depth = depth
        self.stepdown = stepdown
        self.bolts = bolts
        self.boltrad = boltrad

    def generate(self):

        clearZ = self.center[2] + 0.25

        brad = .27/2

        if self.bolts is not None:
            for b in range(self.bolts):
                angle = math.radians(b*360./self.bolts)
                bx = self.center[0] + math.sin(angle)*self.boltrad
                by = self.center[1] + math.cos(angle)*self.boltrad
                self.goto(z=clearZ)
                self.goto(x=bx, y=by)
                self.add(CirclePocket(self.tool, center=(bx, by, self.center[2]), inner_rad=0, outer_rad=brad, depth=self.depth, stepdown=self.stepdown, comment="Bolt hole %d, diam=%f" % (b, brad*2)))

        self.goto(z=clearZ)
        CircleProfile(tool, self.center, self.rad1, self.depth, self.stepdown, side='inner', comment="Inner et of ring %f" % self.rad1).generate(self.f)
        self.goto(z=clearZ)
        CircleProfile(tool, self.center, self.rad2, self.depth, self.stepdown, side='outer', comment="Outer circle of ring %f" % self.rad2).generate(self.f)
   

# The *only* point of this is to cut a concentric pocket.  To do 3d roughing, I'll make another class (maybe)
# curve needs to be clockwise
# also it is expecting a geometry.Line object because of reasons
class PolyPocketConcentric(CAM):
    def __init__(self, tool, zstart, depth, curve, stepover=None, stepdown=None, material_factor=1, clearZ=None):
        super(PolyPocketConcentric, self).__init__(tool)
        self.set_speed(self.tool.rough_speed)

        self.zstart = zstart
        self.depth = depth
        self.curve = curve
        self.stepdown = stepdown or self.tool.diameter*2. # This combo is for HSM
        self.stepover = stepover or self.tool.diameter/4.
        self.material_factor = material_factor
        self.clearZ = clearZ or self.zstart + 0.25

    def generate(self):


        self.goto(z=self.clearZ)
        R = self.tool.diameter/2.

        #from matplotlib import pyplot
        #fig = pyplot.figure()
        #sp = fig.add_subplot(111)
        max_offset = self.curve.find_max_offset(self.stepover, plot=None)
        #max_offset = R
        #pyplot.show()


        # print "offset from", max_offset, R
        gotoZ = True
        for offset in frange(max_offset - self.stepover, R, self.stepover):
            this_curve = self.curve.parallel_offset(offset, 'right')
            coords = this_curve.coords
            if not len(coords): continue

            if gotoZ:
                self.goto(*(coords[0]))
                self.cut(z=self.zstart - self.depth)

            for c in reversed(coords):
                self.cut(*c)


class Voronoi(CAM):
    def __init__(self, tool):
        super(Voronoi, self).__init__(tool)

    # this function inserts point-sites into vd
    def insert_polygon_points(self, vd, polygon):
        pts = []
        for p in polygon:
            pts.append( ovd.Point( p[0], p[1] ) )
        id_list = []

        m=0
        for p in pts:
            id_list.append(vd.addVertexSite(p))
            m=m+1

        return id_list

    # this function inserts line-segments into vd
    def insert_polygon_segments(self, vd, id_list):
        j=0
        for n in range(len(id_list)):
            n_nxt = n+1
            if n==(len(id_list)-1):
                n_nxt=0
            vd.addLineSite(id_list[n], id_list[n_nxt])
            j=j+1

    # this function takes all segments from ttt and inserts them into vd
    def insert_many_polygons(self, vd, segs):
        polygon_ids =[]
        for poly in segs.lines:
            poly_id = self.insert_polygon_points(vd, poly.coords)
            polygon_ids.append(poly_id)

        for ids in polygon_ids:
            self.insert_polygon_segments(vd, ids)

    def get_scaled_segs(self, segs=None, offset=None):
        segs = segs or self.segs
        if offset:
            segs = segs.enforce_direction(clockwise=True).parallel_offset(offset, side='left').enforce_direction(clockwise=True)

        minx, miny, maxx, maxy = segs.bounds()
        current_length = maxx-minx
        current_height = maxy-miny
        scale = 0.6 / max(current_length, current_height)

        offset = minx, miny
        segs = segs.translate(-offset[0], -offset[1])
        segs = segs.scale(x=scale, y=scale, origin=(0, 0, 0)).unclose()
        return [segs, scale, offset]

    def vd(self, segs=None):
        # if True or self.vdobj is None:
        segs = segs or self.scaled_segs
        # print segs.lines[0].coords

        # float r  = radius within which all geometry is located. it is best to use 1 (unit-circle) for now.
        # int bins = number of bins for grid-search (affects performance, should not affect correctness)
        self.vdobj = ovd.VoronoiDiagram(1, 120)  # parameters: (r,bins)
        self.vdobj.set_silent(True)  # suppress Warnings!

        self.insert_many_polygons(self.vdobj, segs)  # insert segments into vd

        return self.vdobj


class VCarve(Voronoi):
    def __init__(self, tool):
        super(VCarve, self).__init__(tool)

    def z_from_rad(self, rad):
        return rad/math.tan(math.radians(self.tool.included_angle/2.0))

    def rad_from_z(self, depth):
        return depth*math.tan(math.radians(self.vtool.included_angle/2.0))

    def cutloops(self, loops, depth, do_clear=True):
        # draw loops
        for lop in loops:

            p = lop[0]
            if do_clear:
                self.goto(z=self.clearZ)
            self.goto(p[0].x*self.print_scale, p[0].y*self.print_scale)
            if do_clear:
                self.cut(z=-depth)
            lastp = p[0]

            for p in lop[1:]:
                # p[0] is the Point
                # p[1] is -1 for lines, and r for arcs
                cw = p[3]
                cen = p[2]
                r = p[1]
                p = p[0]


                if r == -1:  # this offset element is a line
                    self.cut(x=self.print_scale*p.x, y=self.print_scale*p.y)
                else:        # this offset element is an arc
                    offset = cen - lastp
                    I = offset.x*self.print_scale
                    J = offset.y*self.print_scale
                    self.cut_arc(x=p.x*self.print_scale, y=p.y*self.print_scale, I=I, J=J, clockwise=not cw)

                lastp = p

    def loops_to_linestrings(self, loops, enforce_direction=None):
        lines = self.loops_to_lineset(loops, enforce_direction=enforce_direction)
        return [LineString(x.coords) for x in lines]

    def loops_to_lineset(self, loops, enforce_direction=None):
        # rotate by cos/sin. from emc2 gcodemodule.cc
        def rotate(x, y,  c,  s):
            tx = x * c - y * s
            y = x * s + y * c
            x = tx
            return [x, y]

        lines = LineSet()
        for lop in loops:
            coords = []
            lcoords = []

            p = lop[0]
            coords.append(['point', p[0].x, p[0].y])
            lastp = p[0]

            for p in lop[1:]:
                # p[0] is the Point
                # p[1] is -1 for lines, and r for arcs
                cw = p[3]
                cen = p[2]
                r = p[1]
                pp = p[0]

                if r == -1:  # this offset element is a line
                    coords.append(['line', pp.x, pp.y])
                    # print['line', pp.x, pp.y]
                    lcoords.append([pp.x, pp.y])
                else:        # this offset element is an arc
                    start = lastp - cen
                    end = pp - cen
                    theta1 = math.atan2(start.x, start.y)
                    theta2 = math.atan2(end.x, end.y)
                    CIRCLE_FUZZ = 1e-9
                    # idea from emc2 / cutsim g-code interp G2/G3
                    if (cw == False):
                        while ( (theta2 - theta1) > -CIRCLE_FUZZ):
                            theta2 -= 2*math.pi
                    else:
                        while( (theta2 - theta1) < CIRCLE_FUZZ):
                            theta2 += 2*math.pi

                    dtheta = theta2-theta1
                    arclength = r*dtheta
                    dlength = min(0.01, arclength/10)
                    steps = int( float(arclength) / float(dlength))
                    rsteps = float(1)/float(steps)
                    dc = math.cos(-dtheta*rsteps) # delta-cos
                    ds = math.sin(-dtheta*rsteps) # delta-sin

                    tr = [start.x, start.y]
                    for i in range(steps):
                        #f = (i+1) * rsteps #; // varies from 1/rsteps..1 (?)
                        #theta = theta1 + i* dtheta
                        tr = rotate(tr[0], tr[1], dc, ds) #; // rotate center-start vector by a small amount
                        x = cen.x + tr[0]
                        y = cen.y + tr[1]
                        current = ovd.Point(x,y)
                        lcoords.append((current.x, current.y))
                        #myscreen.addActor( ovdvtk.Line(p1=(previous.x,previous.y,0),p2=(current.x,current.y,0),color=arcColor) )

                lastp = pp

            if enforce_direction:
                lines.add(Line(lcoords).enforce_direction(enforce_direction == 'counter-clockwise'))
            else:
                lines.add(Line(lcoords))

        return lines


class VCarveInlay(VCarve):
    def __init__(self, vtool, flat_tool, segs, pocket_depth, inlay_depth=None, inlay_fudge=None,
                 stepover=None, material_factor=1, female=True):
        super(VCarveInlay, self).__init__(tool=None)

        self.vtool = vtool
        self.flat_tool = flat_tool
        self.pocket_depth = pocket_depth
        self.inlay_depth = inlay_depth or (pocket_depth - 0.1)
        self.inlay_fudge = inlay_fudge or (self.inlay_depth*1.0)
        self.stepover = stepover or self.flat_tool.diameter/4.
        self.material_factor = material_factor
        self.female = female

        self.vdobj = None

        self.segs = segs
        # self.segs.graph()

        self.segs = self.segs.enforce_direction(clockwise=True)

        self.scaled_segs, self.scale, self.offset = self.get_scaled_segs()
        # self.scaled_segs.graph()
        self.print_scale = 1.0/self.scale

        self.clearZ = 1/16.

        # if this is the male side, we actually need to inset so it'll fit
        if not female:
            self.male_scaled_segs = self.scaled_segs.parallel_offset(
                self.rad_from_z(self.inlay_depth + self.inlay_fudge)/self.print_scale,
                side='left', join_style=2, mitre_limit=10
            ).unclose()
            # self.male_scaled_segs.graph()

        # self.set_speed(self.tool.rough_speed)

    def clear_depth(self):
        if self.female:
            return self.pocket_depth
        else:
            return self.inlay_fudge + self.inlay_depth

    def inlay_offset(self):
        return self.rad_from_z(self.pocket_depth) if self.female else 0.0001

    def cut_linestring(self, ls, last=None):
        coords = ls.coords

        this = coords[0][0]*self.print_scale, coords[0][1]*self.print_scale
        if _dist(this, last) > 0.0001:
            self.goto(z=self.clearZ)
            self.goto(*this)
            self.cut(z=-self.z_from_rad(coords[0][2]*self.print_scale))
        else:
            self.cut(this[0], this[1], -self.z_from_rad(coords[0][2]*self.print_scale))

        last = this

        for c in coords[1:]:
            this = c[0]*self.print_scale, c[1]*self.print_scale
            self.cut(this[0], this[1], z=-self.z_from_rad(c[2]*self.print_scale))
            last = this

        return last

    def generate_outline(self, segs=None):
        segs = segs or self.scaled_segs

        self.set_tool(self.vtool)
        self.vdobj = None

        vd = self.vd(segs)
        pi = ovd.PolygonInterior(self.female)
        vd.filter_graph(pi)

        of = ovd.Offset(vd.getGraph())

        stepover = (self.vtool.diameter/10.)/self.print_scale
        offto = (self.flat_tool.diameter/2.)/self.print_scale
        if offto > 0:
            for o in frange(0, offto, stepover):
                offset = o + (self.inlay_offset()/self.print_scale)
                ofs = of.offset(offset)
                self.cutloops(ofs, self.clear_depth())

    def generate_carve(self, segs):
        self.set_tool(self.vtool)
        self.vdobj = None

        vd = self.vd(segs)
        pi = ovd.PolygonInterior(self.female)
        vd.filter_graph(pi)

        of = ovd.Offset(vd.getGraph())
        ofs1 = of.offset(0.0001)
        ofs2 = of.offset(self.rad_from_z(self.clear_depth())/self.print_scale)

        if self.female:
            ls1 = LineString(self.loops_to_lineset(ofs1).lines[0].enforce_direction(clockwise=True).coords)
            ls2 = []
            for el in self.loops_to_lineset(ofs2).lines:
                coords = el.enforce_direction(clockwise=False).coords
                lr = LinearRing(coords)
                # print "lr is valid?", lr.is_valid
                ls2.append(lr)
        else:
            ls1 = LineString(self.loops_to_lineset(ofs2).lines[0].enforce_direction(clockwise=True).coords)
            ls2 = [LineString(self.loops_to_lineset(ofs1).lines[0].enforce_direction(clockwise=False).coords)]

        cutarea = Polygon(ls1, ls2)

        if True or self.female:
            ma = ovd.MedialAxis()  # filter so that only medial axis remains
            vd.filter_graph(ma)

            maw = ovd.MedialAxisWalk(vd.getGraph())
            toolpath = maw.walk()

            last = None
            for chain in toolpath:
                for move in chain:
                    if not len(move): continue

                    tmp = LineString([(x[0].x, x[0].y, x[1]) for x in move])

                    try:
                        i = cutarea.intersection(tmp)
                    except shapely.geos.TopologicalError:
                        print "TOPO ERROR!!"
                        continue

                    if i.is_empty:
                        continue

                    if isinstance(i, MultiLineString):
                        for l in list(i):
                            last = self.cut_linestring(l, last)
                    elif isinstance(i, LineString):
                        last = self.cut_linestring(i, last)
                    else:
                        print "FUCK IF I KNOW"

    def generate(self):


        self.generate_outline()

        for seg in self.scaled_segs.lines if self.female else self.male_scaled_segs.lines:
            self.generate_carve(LineSet([seg]))


def segments_to_drawable(filename, segments, colors=[], close=True, mode="a"):
    if close:
        segments.append(segments[0])

    colors = colors + [None]*(len(segments) - len(colors))

    with open(filename, mode) as f:
        last = segments[0]
        for p, col in zip(segments[1:], colors):
            if col is None:
                col = (0, 0, 0)
            r, g, b = col

            try:
                a1, b1, c1 = last
                a2, b2, c2 = p
            except ValueError:
                a1, b1 = last
                a2, b2 = p
                c1 = c2 = 0

            print >> f, "line,%f,%f,%f,%f,%f,%f,%f,%f,%f" % (a1, b1, c1, a2, b2, c2, r, g, b)
            last = p



tools = {}
tools['1/8in spiral upcut'] = StraightRouterBit(diameter=1/8.)
tools['1/16in spiral upcut'] = StraightRouterBit(diameter=1/16., rough_speed=20, drill_speed=10)
tools['1/4in spiral upcut'] = StraightRouterBit(diameter=1/4.)
tools['3/8in spiral upcut'] = StraightRouterBit(diameter=3/8.)
tools['1/2in spiral upcut'] = StraightRouterBit(diameter=1/2.)

tools['1/2in 4-flute endmill'] = StraightRouterBit(diameter=1/2.)
tools['1/4in 4-flute endmill'] = StraightRouterBit(diameter=1/4.)
tools['1/8in 4-flute endmill'] = StraightRouterBit(diameter=1/8.)

tools['1/8in spiral ball'] = BallRouterBit(diameter=1/8.)
tools['1/4in spiral ball'] = BallRouterBit(diameter=1/4.)
tools['3/8in spiral upcut'] = StraightRouterBit(diameter=3/8.)
tools['1/2in spiral ball'] = BallRouterBit(diameter=1/2.)

tools['1 1/2in straight bit'] = StraightRouterBit(diameter=1.5)
tools['1/2in dovetail'] = DovetailRouterBit(minor_diameter=5/8., major_diameter=1/2., height=7/8.)
tools['30degV'] = VRouterBit(included_angle=30.0, diameter=1/4., drill_speed=20, rough_speed=30)
tools['laser'] = Laser()

if __name__ == '__main__':
    if not os.path.exists("./test"):
        os.mkdir("./test")

    """
    tool = tools['1/4in spiral upcut']

    segments = []
    for deg in frange(0, 360, 1):
        segments.append(
            (
                math.sin(math.radians(deg)) + 1.2,
                math.cos(math.radians(deg)) + 1.2,
                math.sin(math.radians(deg*6))/4 + 1
            )
        )
    c = Camtainer("test/3dprofile.ngc", [
        RectStock(2.4, 2.4, 1),
        ThreeDProfile(segments, tool, .25),
    ])

    #
    c = Camtainer("test/circle_profile.ngc", [
        RectStock(2, 2, 1),
        CircleProfile(tool=tool, center=(1,1,1), radius=1.0, depth=.3, ),
    ])

    c = Camtainer("test/circle_profile2.ngc", [
        RectStock(2, 2, 1),
        CircleProfile(tool=tool, center=(1,1,1), radius=1.0, depth=.3, start_angle=0, end_angle=180),
    ])

    c = Camtainer("test/rect_pocket_x.ngc", [
        RectStock(3, 3, 1),
        RectPocket(tool, (.5, .5), (2.5, 1.5), z=1, depth=.25, type='x')
    ])

    c = Camtainer("test/rect_pocket_y.ngc", [
        RectStock(3, 3, 1),
        RectPocket(tool, (.5, .5), (2.5, 1.5), z=1, depth=.25, type='y')
    ])
    c = Camtainer("test/circle_pocket.ngc", [
        RectStock(4, 4, 1),
        CirclePocket(tool, (2, 2, 1), 2, 1, .25, clockwise=True)
    ])
    c = Camtainer("test/circle_pocket_ccw.ngc", [
        RectStock(4, 4, 1),
        CirclePocket(tool, (2, 2, 1), 2, 1, depth=.25, clockwise=False)
    ])
    c = Camtainer("test/ring.ngc")

    """

