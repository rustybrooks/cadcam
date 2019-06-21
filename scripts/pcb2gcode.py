#!/usr/bin/env python

import logging
import optparse
import os.path
import sys

sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'src/lib'))
import zipfile

from campy import *

logging.basicConfig()


if __name__ == '__main__':
    parser = optparse.OptionParser()
    parser.add_option('-d', '--depth',     help="Engraving depth", type=float, default=0.005)
    parser.add_option('-s', '--separation', help='Trace separation', type=int, default=0.020)
    parser.add_option('-b', '--border',    help='Width of border for PCB', type=float, default=0)
    parser.add_option('-t', '--thickness', help="Thickness of PCB (for drill/cutout)", type=float, default=1.7*constants.MM)
    parser.add_option('-o', '--output',    help='output directory, will be created if it doesn\'t exist', type=str)
    parser.add_option('--one-file',        help='if passed, will put each layer in one file', action='store_true')
    # parser.add_option('--side',            help='For one sided boards, which side to use', type='str', default='bottom')
    parser.add_option('--panelx',          help='Number of times to repeat pcb in x direction', type=int, default=1)
    parser.add_option('--panely',          help='Number of times to repeat pcb in y direction', type=int, default=1)
    parser.add_option('--zprobe',          help='zprobe radius interval, use a number or "auto" or "none"', type=str, default='auto')
    parser.add_option('--posts',           help='cut 1/8" post holes for alignment (x or y or none)', type='str', default='x')
    parser.add_option('--fixture_width',   help='width of 2-side fixture', type=float, default=None)
    options, args = parser.parse_args()

    pcb = PCBProject(
        gerber_input=args[0],
        border=options.border,
        auto_zero=True,
        thickness=options.thickness,
        posts=options.posts,
        fixture_width=options.fixture_width,
    )

    machine = set_machine('k2cnc')
    machine.set_material('fr4-1oz')
    machine.max_rpm = machine.min_rpm = 15000

    if options.zprobe == 'none':
        zprobe_radius = None
    elif options.zprobe == 'auto':
        zprobe_radius = 'auto'
    else:
        zprobe_radius = float(options.zprobe)

    pcb.pcb_job(
        output_directory=options.output,
        drill='top',
        cutout='bottom',
        iso_bit='engrave-0.01in-15',
        drill_bit='tiny-0.9mm',
        cutout_bit='1/16in spiral upcut',
        post_bit='1/8in spiral upcut',
        file_per_operation=not options.one_file,
        outline_depth=options.depth,
        outline_separation=options.separation,
        panelx=options.panelx,
        panely=options.panely,
        flip='x',
        zprobe_radius=zprobe_radius,
    )

