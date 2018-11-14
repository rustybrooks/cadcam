#!/usr/bin/env python

import logging
import optparse
from os import sys, path
sys.path.append(path.dirname(path.dirname(path.abspath(__file__))))

from campy import *


logging.basicConfig()


if __name__ == '__main__':
    parser = optparse.OptionParser()
    parser.add_option('-v', '--vbit', help='VBit engraving tool', type=str, default='engrave-0.1-30')
    parser.add_option('-d', '--depth', help="Engraving depth", type=float, default=0.010)
    parser.add_option('-s', '--stepovers', help='# of isolation paths to engrave', type=int, default=2)
    parser.add_option('-b', '--border', help='Width of border for PCB', type=float, default=0.1)
    parser.add_option('-t', '--thickness', help="Thickness of PCB (for drill/cutout)", type=float, default=1.6*constants.MM)
    options, args = parser.parse_args()

    drill_file = None
    gerber_top = None
    gerber_bottom = None
    flipx = False
    for fname in args:
        ext = os.path.splitext(fname)[-1].lower()
        if ext == ".gbl":
            gerber_bottom = fname
            flipx = True
        elif ext == '.gtl':
            gerber_top = fname
        elif ext == '.drl':
            drill_file = fname
        else:
            raise Exception("only drill files and gerber top and bottom copper layer supported: {}".format(gerber_file))

    if not gerber_bottom and not gerber_top:
        raise Exception("Must supply at least one gerber")

    machine = set_machine('k2cnc')
    machine.max_rpm = 15000
    machine.min_rpm = 15000
    machine.set_material('fr4-1oz')
    machine.set_file('ngc/pcb/pcb.gcode')

    machine.set_tool(options.vbit)
    bounds=None
    if gerber_top:
        bounds, geoms = pcb_isolation_mill(
            gerber_file=gerber_top,
            stepovers=options.stepovers,
            depth=options.depth,
            border=options.border,
        )

        minx, miny, maxx, maxy = bounds
        width = maxx - minx
        height = maxy - miny
        rect_stock(width, height, options.thickness, origin=(0, -options.thickness, 0))

    if gerber_bottom:
        bounds, geoms = pcb_isolation_mill(
            gerber_file=gerber_bottom,
            stepovers=options.stepovers,
            depth=options.depth,
            border=options.border,
        )

        minx, miny, maxx, maxy = bounds
        width = maxx - minx
        height = maxy - miny
        rect_stock(width, height, options.thickness, origin=(0, -options.thickness, 0))

    if drill_file:
        machine.set_tool('tiny-0.8mm')
        pcb_drill(
            drill_file=drill_file,
            depth=options.thickness,
            xoff=options.border, yoff=options.border, flipx=flipx
        )

    machine.set_tool('1/16in spiral upcut')
    print "...... bounds", bounds
    pcb_cutout(bounds=bounds, depth=options.thickness)

