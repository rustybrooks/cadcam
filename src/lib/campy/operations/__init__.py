from functools import wraps
import inspect
import math

from .. import machine
from ..cammath import frange

# center is always (x, y), z separate?
# if an operation goes straight down, then use depth rather then a stop center
# stepover is X% for a percentage of bit diameter, X for absolute
# stepdown is X% for a percentage of bit diameter, X for absolute


def operation(required=None, operation_feedrate=None, comment=None):
    required = required or []

    def wrapout(fn):
        names, varargs, keywords, defaults = inspect.getargspec(fn)

        @wraps(fn)
        def wrapper(*args, **kwargs):
            machine().push_level()

            foo = {}
            for name, default in zip(reversed(names), reversed(defaults)):
                foo[name] = default

            # I don't think this is right...
            for name, arg in list(zip(names, args)) + list(kwargs.items()):
                foo[name] = arg

            missing = []
            for r in required:
                if r not in kwargs:
                    missing += [r]

            if missing:
                raise Exception("Required parameters missing: {}".format(missing))

            if comment is not None:
                machine().comment(comment.format(**kwargs))
            elif '_comment' in foo and foo['_comment']:
                machine().comment(foo['_comment'])

            pop_speed = False

            if 'stepover' in foo:
                kwargs['stepover'] = machine().calc_stepover(foo['stepover'], depth=foo.get('depth', 0))

            if 'stepdown' in foo:
                kwargs['stepdown'] = machine().calc_stepover(foo['stepdown'], depth=foo.get('depth', 0))

            #if '_speed' in foo:
            #    machine().push_speed(foo['_speed'])
            #    pop_speed = True
            if operation_feedrate:
                pop_speed = True
                machine().push_speed(operation_feedrate)

            retval = fn(*args, **kwargs)

            machine().pop_level()
            if pop_speed:
                machine().pop_speed()

            return retval

        return wrapper

    return wrapout


def rect_stock(width, height, thickness, origin=(0, 0, 0)):
    machine().write("(RectSolid %f %f %f origin=%f %f %f)" % (width, height, thickness, origin[0], origin[1], origin[2]))


# G0 X0 Y0 Z0
# G38.2 Z-0.375 F5
# G10 L20 P0 Z0
# G0 Z0.125
# G38.2 Z-0.0625 F2.5
# G10 L20 P0 Z0
# G0 Z0.125
# G0 X0 Y0
# G38.2 Z-0.0625 F5
@operation(required=['center', 'z', 'depth'], operation_feedrate='probe')
def zprobe(
    center=None, z=None, zretract=0.025, depth=None, rate=None, toward=True, halt_on_error=True,
    tries=1, backoff=.5, setz=False, auto_clear=True, clearz=None, storez=False,
):
    clearz = clearz or 0.125

    x, y = center
    machine().goto(z=z)
    machine().goto(x, y)

    for i in range(tries):
        machine().probe(axis='Z', to=z-depth, rate=rate*(backoff**i), toward=toward, halt_on_error=halt_on_error)
        if i + 1 != tries:
            machine().goto(z="[#5063+{}]".format(zretract))
#        machine().probe(axis='Z', to=z, rate=rate, toward=not toward, halt_on_error=False)

    if setz:
        machine().write("G10 L20 P0 Z0")  # set Z

    if storez:
        machine().write("#{}=#5422".format(storez))

    if auto_clear:
        machine().goto(z=clearz)

@operation(
    required=['centers', 'z', 'depth', 'retract_distance'],
    operation_feedrate='plunge',
    comment='Peck drilling holes z={z:.3f}, depth={depth:.3f}, retract_distance={retract_distance:.3f}',
)
def drill_cycle(centers=None, z=None, retract_distance=None, depth=None, clearz=None, auto_clear=True):
    clearz = clearz or (z + 0.125)

    machine().drill_cycle_plain(centers=centers, z=z, depth=depth)

    if auto_clear:
        machine().goto(z=clearz)

# This will make a helical arc with the outter radius = outter-rad
# it only operates at one radius
# with outter_rad = 1*r to 2*r this is essentially a drilling procedure
# otherwise it'll be making a groove with a width of the diameter of the bit
# Used to be HelicalDrill
@operation(
    required=['center', 'z', 'outer_rad', 'depth', 'stepdown'],
    operation_feedrate='plunge',
    comment="Cutting HelicalDrill at {center}, outter_rad={outer_rad:.3f}, depth={depth:.3f}",
)
def helical_drill(center=None, z=None, outer_rad=None, depth=None, stepdown="25%", clockwise=True, clearz=None, auto_clear=True):
    R = machine().tool.diameter / 2.0
    x1, y1 = center
    z1 = z
    z2 = z1 - depth
    clearz = clearz or (z1 + 0.125)

    if depth == 0:
        return

    if outer_rad <= R:
        machine().goto(z=clearz)
        machine().goto(x1, y1)

    # machine().write("G17")  # plane selection

    rad = outer_rad - R

    start, end = machine().arc_start_end(x1, y1, rad, 0, 0, clockwise=clockwise)
    machine().goto(x=start[0], y=start[1])

    if outer_rad <= R:
        # print "Asked to helical drill, but just drilling", R, outer_rad
        machine().cut(z=z2)
    else:
        machine().goto(z=z1)
        for Z in machine().zstep(z1, z2, stepdown):
            machine().cut_arc_center_rad(x1, y1, rad, start_angle=0, end_angle=0, z=Z, clockwise=clockwise, cut_to=True)

        machine().cut_arc_center_rad(x1, y1, rad, start_angle=0, end_angle=0, z=z2, clockwise=clockwise, cut_to=True)

    if auto_clear:
        machine().goto(z=clearz)


@operation(required=['center', 'stepdown', 'stepover', 'inner_rad', 'outer_rad'], operation_feedrate='cut', comment='HSM Circle Pocket')
def hsm_circle_pocket(
    center=None, z=None, inner_rad=None, outer_rad=None, depth=None, stepover='50%', stepdown="50%", clearz=None, climb=True, auto_clear=True,
):
    depth = depth or 0
    xc, yc = center
    zc = z
    clearz = clearz or (zc + 0.125)

    R = machine().tool.diameter / 2.

    if inner_rad is not None and inner_rad > 0:
        startrad = inner_rad + R
    else:
        startrad = min(R, outer_rad)

    helical_drill(
        center=center, z=z, outer_rad=startrad, depth=depth,
        clockwise=climb, stepdown=stepdown,
    )

    for Z in machine().zstep(zc, zc - depth, stepdown):
        machine().goto(z=clearz)
        machine().goto(*center)
        machine().goto(z=Z)
        for rad in frange(startrad, outer_rad, stepover):
            machine().cut_arc_center_rad(
                xc, yc, radius=rad - R, start_angle=0, end_angle=0, clockwise=climb,
                cut_to=True, return_to=False
            )

    if auto_clear:
        machine().goto(z=clearz)


# type is x (movement parallel to x axis) or y (y axis)
# probably needs to stop short of boundaries and then trim
@operation(required=['stepdown', 'stepover'])
def rect_pocket(p1, p2, z, depth, stepover="50%", stepdown="50%", type='x', rough_margin=0, clearz=None, auto_clear=True, **kwargs):
    R = machine().tool.diameter / 2.

    x1p, y1p = p1
    x2p, y2p = p2

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

    # FIXME reset after?
    # machine().set_speed(machine().tool.rough_speed)

    clearz = clearz or (z + .125)

    for Z in machine().zstep(0, -1 * depth, stepdown=stepdown):
        # Don't actually need to go very far up
        if auto_clear:
            machine().goto(z=clearz)

        machine().goto(x=x1, y=y1)

        machine().cut(z=z + Z, rate=machine().tool.plunge_feedrate)
        # machine().set_speed(machine().tool.rough_speed)

        plus = True
        if type == "x":
            for y in frange(y1, y2, stepover, True):
                machine().cut(y=y)
                if plus:
                    machine().cut(x=x2)
                else:
                    machine().cut(x=x1)

                plus = not plus

        else:
            for x in frange(x1, x2, stepover, True):
                machine().cut(x=x)
                if plus:
                    machine().cut(y=y2)
                else:
                    machine().cut(y=y1)

                plus = not plus

    if auto_clear:
        machine().goto(z=clearz)


@operation(required=['stepdown'])
def rect_pocket_corner_relief(p1, p2, z, depth, stepdown="50%", auto_clear=True, clearz=None, **kwargs):
    px1, py1 = p1
    px2, py2 = p2
    r = 1.1 * machine().tool.diameter / 2.
    off = r / (2 * math.sqrt(2))

    px1, px2 = min(px1, px2), max(px1, px2)
    py1, py2 = min(py1, py2), max(py1, py2)
    px1 += r
    py1 += r
    px2 -= r
    py2 -= r

    clearz = clearz or (z + 0.125)

    z1 = z
    z2 = z - depth
    machine().goto(z=z)
    for zs in machine().zstep(z1, z2, stepdown):
        machine().goto(x=px1, y=py1)
        machine().cut(z=zs)
        machine().cut(x=px1-off, y=py1-off)
        machine().goto(x=px1, y=py1)

    machine().goto(z=z)
    for zs in machine().zstep(z1, z2, stepdown):
        machine().goto(x=px1, y=py2)
        machine().cut(z=zs)
        machine().cut(x=px1-off, y=py2+off)
        machine().goto(x=px1, y=py2)

    machine().goto(z=z)
    for zs in machine().zstep(z1, z2, stepdown):
        machine().goto(x=px2, y=py2)
        machine().cut(z=zs)
        machine().cut(x=px2+off, y=py2+off)
        machine().goto(x=px2, y=py2)

    machine().goto(z=z)
    for zs in machine().zstep(z1, z2, stepdown):
        machine().goto(x=px2, y=py1)
        machine().cut(z=zs)
        machine().cut(x=px2+off, y=py1-off)
        machine().goto(x=px2, y=py1)

    if auto_clear:
        machine().goto(z=clearz)


