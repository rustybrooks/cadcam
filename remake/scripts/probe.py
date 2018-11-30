#!/usr/bin/env python

import sys, os
if __name__ == '__main__' and __package__ is None:
    from os import sys, path
    sys.path.append(path.dirname(path.dirname(path.abspath(__file__))))
    from campy import *
else:
    from .campy import *

width = 1.5
height = 1.5
thickness = .75
offset = 0.25
step = .5
safe = 0.05
rate = 1
tries = 2


def doprobe():
    machine.write("(PROBEOPEN /tmp/probe.txt)")
    for x in frange(offset, width-offset, step):
        for y in frange(offset, height-offset, step):
            zprobe(center=(x, y), z=safe, depth=.5, rate=rate, tries=tries, backoff=.5)
#            machine.write("(LOG,X#5061 Y#5062 Z#5063)")

    machine.write("(PROBECLOSE)")

    machine.goto(z=safe)


machine = set_machine('k2cnc')
machine.set_material('none')
machine.set_tool('1/4in spiral ball')
machine.set_file('ngc/probe.ngc')
doprobe()

