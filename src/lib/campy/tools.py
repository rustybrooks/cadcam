import math

from .cammath import frange


class Tool(object):
    index_counter = 0

    def __init__(self, tool_material, effective_diameter, flutes=None, edge_radius=0):
        self.index_counter += 1
        self.index = self.index_counter

        self.effective_diameter = effective_diameter


        self.flutes = flutes
        self.edge_radius = edge_radius
        self.feeds = {
            'cut': None,
            'raster_engrave': None,
            'vector_engrave': None,
            'plunge': None,
            'leadin': None,
            'leadout': None,
            'ramp': None,
            'probe': None,
        }

        self.spindle_speed = None
        self.ramp_speed = None

        self.tool_material = tool_material

    def to_json(self):
        return self.to_db()


    """
    DEPTH OF CUT: 1 x D Use recommended chip load
    2 x D Reduce chip load by 25%
    3 x D Reduce chip load by 50%
    """
    # rpm = sfm/(dp/12)
    # ips = rpm*fpt/flutes

    def sfm(self, material):
        if self.tool_material == 'hss':
            sfm_list = material.sfm_hss
        elif self.tool_material == 'carbide':
            sfm_list = material.sfm_carbide
        else:
            raise Exception("Unsupported tool material: %r", self.tool_material)

        return sfm_list

    def fpt(self, material):
        if self.tool_material == 'hss':
            fpt_list = material.fpt_hss
        elif self.tool_material == 'carbide':
            fpt_list = material.fpt_carbide
        else:
            raise Exception("Unsupported tool material: %r", self.tool_material)

        diams = [1., 1/2., 1/4., 1/8., 1/16., 1/32.]
        data = zip(diams, fpt_list)
        fpt_low, fpt_high = fpt_list[-1]
        for el in reversed(data):
            fpt_low, fpt_high = el[1]
            if el[0] >= self.effective_diameter:
                break

        return fpt_low, fpt_high

    def base_feedrate(self, material, machine, effective_depth=None, feed_class=None):
        # print "calculate_feedrate", material, base_feedrate

        def _fpt(rpm, ipm):
            return (self.flutes*ipm)/rpm

        def _ipm(rpm, fpt):
            return rpm*fpt/self.flutes

        def _rpm(sfm):
            return sfm / (self.effective_diameter*math.pi/12)

        def _pair(sfm, fpt):
            return _ipm(_rpm(sfm), fpt), _rpm(sfm)

        if feed_class in ['high', 'low', 'average']:
            sfm_low, sfm_high = self.sfm(material)
            fpt_low, fpt_high = self.fpt(material)

            rpm_low = max(_rpm(sfm_low), machine.min_rpm)
            rpm_high = min(_rpm(sfm_high), machine.max_rpm)

            feedrate_low = _ipm(rpm_low, fpt_low)
            feedrate_high = _ipm(rpm_high, fpt_high)
            if feedrate_high > machine.peak_feedrate:
                feedrate_high = machine.peak_feedrate
                rpm_high = feedrate_high * self.flutes / fpt_high

            if feed_class == 'high':
                feedrate = feedrate_high
                rpm = rpm_high
            elif feed_class == 'low':
                feedrate = feedrate_low
                rpm = rpm_low
            elif feed_class == 'average':
                feedrate = (feedrate_low + feedrate_high) / 2.
            else:
                raise Exception("Unknown feed_class value: %r", feed_class)
        else:
            feedrate = feed_class

        return feedrate

    # def calculate_feedrates(self, material, machine, feed_class=None):
    #     base = self.base_feedrate(material, machine, feed_class=feed_class)
    #
    #     self.feeds['cut'] = feedrate
    #     self.feeds['plunge'] = feedrate*0.40  # FIXME?
    #     self.feeds['raster_engrave'] = 0  # FIXME?
    #     self.feeds['vector_engrave'] = 0  # FIXME?
    #     self.feeds['leadin'] = 0
    #     self.feeds['leadout'] = 0
    #     self.feeds['ramp'] = 0
    #     self.feeds['probe'] = 1
    #     self.spindle_speed = rpm

    # z = #flutes!
    # rpm*d*pi/12 = sfm
    # sfm*(pi/12)/d = rpm
    # ipm*z=ipr
    # rpm*ipr=ipm
    # ipm/rpm/z = ipt
    def drill_feedrate(self, material, machine, feed_class=None):
        def _rpm(sfm):
            return sfm / (self.effective_diameter*math.pi/12)

        def _ipm(rpm, fpt):
            return fpt*rpm*self.flutes

        if feed_class in ['high', 'low', 'average']:
            sfm_low, sfm_high = self.sfm(material)
            fpt_low, fpt_high = self.fpt(material)  # FIXME not sure this is valid for drill operations

            rpm_low = max(_rpm(sfm_low), machine.min_rpm)
            rpm_high = min(_rpm(sfm_high), machine.max_rpm)

            feedrate_low = _ipm(rpm_low, fpt_low)
            feedrate_high = _ipm(rpm_high, fpt_high)
            if feedrate_high > machine.peak_feedrate:
                feedrate_high = machine.peak_feedrate
                rpm_high = feedrate_high * self.flutes / fpt_high

            if feed_class == 'high':
                feedrate = feedrate_high
                rpm = rpm_high
            elif feed_class == 'low':
                feedrate = feedrate_low
                rpm = rpm_low
            elif feed_class == 'average':
                feedrate = (feedrate_low + feedrate_high) / 2.
            else:
                raise Exception("Unknown feed_class value: %r", feed_class)

            # print "!!!!!", feedrate
            feedrate = feedrate / 10.  # This is entirely pulled out of my ass, but intuitively we can't plunge
                                      # or drill at the same x-y feed rate?
        else:
            feedrate = feed_class

        return feedrate

    def engrave_feedrate(self, material, machine, feed_class=None):
        return 5  # FIXME lol

    def calculate_feedrate(self, material=None, machine=None, feed_type=None, feed_class=None):
        if feed_type in ['cut']:
            base = self.base_feedrate(material, machine, feed_class=feed_class)
        elif feed_type in ['plunge', 'drill']:
            base = self.drill_feedrate(material, machine, feed_class=feed_class)
        elif feed_type in ['vector_engrave']:
            base = self.engrave_feedrate(material, machine, feed_class=feed_class)
        elif feed_type in ['probe']:
            base = 5
        else:
            raise Exception("Unsupported feed type: {}".format(feed_type))

        # print feed_type, feed_class, "returning", base
        return base

    def comment(self, cam):
        pass

    def diameter_at_depth(self, depth=0):
        return self.effective_diameter

    @classmethod
    def from_db(cls, data):
        raise Exception("not defined")

    def to_db(self):
        raise Exception("not defined")


class StraightRouterBit(Tool):
    def __init__(self, diameter, tool_material, flutes=None, edge_radius=0, cutting_length=5):
        super(StraightRouterBit, self).__init__(
            effective_diameter=diameter, tool_material=tool_material, flutes=flutes, edge_radius=edge_radius,
        )

        self.diameter = diameter
        self.cutting_length = cutting_length

    def comment(self, cam):
        cam.comment("FlatMill %f %f" % (self.cutting_length, self.diameter/2.0))

    def to_db(self):
        return {
            'type': 'straight',
            'material': self.tool_material,
            'flutes': self.flutes,
            'diameter': self.diameter,
            'edge_radius': self.edge_radius,
            'cutting_length': self.cutting_length,
        }

    @classmethod
    def from_db(cls, data):
        return StraightRouterBit(
            diameter=data['diameter'],
            tool_material=data['material'],
            flutes=data['flutes'],
            edge_radius=data['edge_radius'],
            cutting_length=data['cutting_length'],
        )


class BallRouterBit(StraightRouterBit):
    def comment(self, cam):
        cam.comment("BallMill %f %f" % (self.cutting_length, self.diameter/2.0))

    def to_db(self):
        return {
            'type': 'straight',
            'material': self.tool_material,
            'flutes': self.flutes,
            'diameter': self.diameter,
            'edge_radius': self.edge_radius,
            'cutting_length': self.cutting_length,
        }


class DovetailRouterBit(Tool):
    def __init__(self, minor_diameter=None, major_diameter=None, height=None, tool_material=None, flutes=None, edge_radius=0):
        super(DovetailRouterBit, self).__init__(
            effective_diameter=major_diameter, tool_material=tool_material, flutes=flutes, edge_radius=edge_radius,
        )

        self.major_diameter = major_diameter
        self.minor_diameter = minor_diameter
        self.height = height

    def to_db(self):
        return {
            'type': 'dovetail',
            'material': self.tool_material,
            'flutes': self.flutes,
            'diameter': self.major_diameter,
            'minor_diameter': self.major_diameter,
            'edge_radius': self.edge_radius,
            'cutting_length': self.height,
        }

    @classmethod
    def from_db(cls, data):
        return DovetailRouterBit(
            major_diameter=data['diameter'],
            minor_diameter=data['minor_diameter'],
            tool_material=data['material'],
            flutes=data['flutes'],
            edge_radius=data['edge_radius'],
            height=data['cutting_length'],
        )


class VRouterBit(Tool):
    def __init__(self, included_angle, diameter=None, tip_diameter=None, tool_material=None, flutes=None, edge_radius=0, cutting_length=5):
        super(VRouterBit, self).__init__(
            effective_diameter=diameter/2., tool_material=tool_material, flutes=flutes, edge_radius=edge_radius,
        )

        self.included_angle = included_angle
        self.diameter = diameter
        self.tip_diameter = tip_diameter
        self.edge_radius = edge_radius
        self.cutting_length = cutting_length

    def comment(self, cam):
        cam.comment("VMill %f %f %f %f" % (1, self.tip_diameter/2.0, self.diameter/2.0, self.included_angle))  # FIXME fixed cutting length

    def diameter_at_depth(self, depth=0):
        return self.tip_diameter + math.tan(math.radians(self.included_angle/2.))*depth*2

    def to_db(self):
        return {
            'type': 'vee',
            'material': self.tool_material,
            'flutes': self.flutes,
            'diameter': self.diameter,
            'minor_diameter': self.tip_diameter,
            'edge_radius': self.edge_radius,
            'cutting_length': self.cutting_length,
            'included_angle': self.included_angle,
        }

    @classmethod
    def from_db(cls, data):
        return VRouterBit(
            included_angle=data['included_angle'],
            diameter=data['diameter'],
            tip_diameter=data['minor_diameter'],
            tool_material=data['material'],
            flutes=data['flutes'],
            edge_radius=data['edge_radius'],
            cutting_length=data['cutting_length'],
        )



class Laser(Tool):
    def __init__(self, focused_beam_width):
        self.focused_beam_width = focused_beam_width

    def diameter_at_depth(self, depth=0):
        return self.focused_beam_width


class HoleSize(object):
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

    pvc = {
        '1/2':   0.840,
        '3/4':   1.040,
        '1':     1.315,
        '1-1/4': 1.660,
        '1-1/2': 1.900,
        '2':     2.375,
    }

    # all measurements in mm
    # list is
    # http://www.littlemachineshop.com/reference/tapdrillsizes.pdf
    screws = {
        # inch thread
        "1/4-20": [.1887, "7", .2010, "7/32", .2188, "F", .2570, "H", .2660],
        "1/4-28": [.2062, "3", .2130, "1", .2280, "F", .2570, "H", .2660],
        "1/4-32": [.2117, "7/32", .2188, "1", .2280, "F", .2570, "H", .2660],

        # metric thread
        "M1.5-.35": [1.15, "56", 1.25, "55", 1.60, "1/16", 1.65, "52"],
        "M1.6-.35": [1.25, "55", 1.35, "54", 1.70, "51", 1.75, "50"],
        "M1.8-.35": [1.45, "53", 1.55, "1/16", 1.90, "49", 2.00, "5/64"],
        "M2-.45": [1.55, "1/16", 1.70, "51", 2.210, "45", 2.20, "44"],
        "M2-.40": [1.60, "52", 1.75, "50", 2.10, "45", 2.20, "44"],
        "M2.2-.45": [1.75, "50", 1.90, "48", 2.30, "3/32", 2.40, "41"],
        "M2.5-.45": [2.05, "46", 2.20, "44", 2.65, "37", 2.75, "7/64"],
        "M3-.60": [2.40, "41", 2.60, "37", 3.15, "1/8", 3.30, "30"],
        "M3-.50": [2.50, "39", 2.70, "36", 3.15, "1/8", 3.30, "30"],
        "M3.5-.60": [2.90, "32", 3.10, "31", 3.70, "27", 3.85, "24"],
        "M4-.75": [3.25, "30", 3.50, "28", 4.20, "19", 4.40, "17"],
        "M4-.70": [3.30, "30", 3.50, "28", 4.20, "19", 4.40, "17"],
        "M4.5-.75": [3.75, "25", 4.00, "22", 4.75, "13", 5.00, "9"],
        "M5-1.00": [4.00, "21", 4.40, "11/64", 5.25, "5", 5.50, "7/32"],
        "M5-.90": [4.10, "20", 4.40, "17", 5.25, "5", 5.50, "7/32"],
        "M5-.80": [4.20, "19", 4.50, "16", 5.25, "5", 5.50, "7/32"],
        "M5.5-.90": [4.60, "14", 4.90, "10", 5.80, "1", 6.10, "B"],
        "M6-1.00": [5.00, "8", 5.40, "4", 6.30, "E", 6.60, "G"],
        "M6-0.75": [5.25, "4", 5.50, "7/32", 6.30, "E", 6.60, "G"],
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


