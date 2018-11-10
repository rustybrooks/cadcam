#!/usr/bin/env python

# from campy import *
from hsm import *
# from digital_joints import *

base = '.'

tool = tools['1/4in spiral upcut']
tool.rough_speed = 90
margin = 3/4.
w = 3. + 0.005
h = 8. + 0.005
depth = 1/4.
thickness = .75
stepover = 0.5
stepdown = 1.5

x1 = margin+(margin+w)*0
x2 = margin+(margin+w)*1
x3 = margin+(margin+w)*2

xoffs = [x1, x2, x3]
xoffs = [x1]
pockets = [
    HSMRectPocket(
        tool=tool, p1=(xoff, margin), p2=(xoff+w, margin + h), z=0, depth=depth, stepover=stepover,
        stepdown=stepdown, corner_relief=1, finish_offset=.1, finish_passes=1,
    ) for xoff in xoffs
]


def slatsegs(xoff, yoff):
    p1 = [xoff, margin]
    p2 = [xoff+w, margin+h]
    bounds = [
        [p1[0]-.15, p1[1]],
        [p1[0]-.15, p2[1]],
        [p2[0]+.15, p2[1]],
        [p2[0]+.15, p1[1]],
        [p1[0]-.15, p1[1]]
    ]

    a = math.radians(30)
    s1 = [xoff-1, yoff]
    s2 = [xoff+w+1, yoff+w*math.sin(a)]
    foo = .25
    slat = [
        [s1[0], s1[1]-foo],
        [s1[0], s1[1]+foo],
        [s2[0], s2[1]+foo],
        [s2[0], s2[1]-foo],
        [s1[0], s1[1]-foo],
    ]

    p1 = Polygon(bounds)
    p2 = Polygon(slat)
    inter = p1.intersection(p2)
    # inter = bounds.intersection(slat)
    if inter.is_empty:
        return []
    res = Line(inter.exterior.coords).enforce_direction(clockwise=True)
    # print res.coords
    # res = res.parallel_offset(0.125, side='right')
    return LineSet([res])


def slatargs():
    args = []
    for xo in xoffs:
        args.extend([(xo, yo) for yo in frange(-1, h+1, 1.25)])

    return args`


pocket_slats = [
    HSMPocket(
        tool=tool, segs=slatsegs(*a), stepover=stepover, z=0, depth=thickness, stepdown=stepdown, material_factor=1,
        finish_passes=1, finish_offset=0.04
    ) for a in slatargs() if slatsegs(*a)
]

Camtainer(
    "{}/test/sharpen.nc".format(base),
    [RectStock(3*w + 4*margin, h+2*margin, thickness, origin=(0, -thickness, 0))]
    + pockets + pocket_slats
    + [Goto(z=.25)]
)
