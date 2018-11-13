#!/usr/bin/env python

import sys, os
if __name__ == '__main__' and __package__ is None:
    from os import sys, path
    sys.path.append(path.dirname(path.dirname(path.abspath(__file__))))
    from campy import *
else:
    from .campy import *

width = 2
height = 2
thickness = .75
offset = 0.25
step = .5


def doprobe():
    machine.write("(probeopen /tmp/probe.txt)")
    for x in frange(offset, width-offset, step):
        for y in frange(offset, height-offset, step):
            zprobe(center=(x, y), z=.25, depth=.5, rate=1, tries=2, backoff=.5)
            machine.write("(LOG,#5061 #5062 #5063)")

    machine.write("(probeclose)")


machine = set_machine('k2cnc')
machine.set_material('none')
machine.set_tool('1/4in spiral ball')
machine.set_file('ngc/probe.ngc')
doprobe()

