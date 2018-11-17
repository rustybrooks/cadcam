#!/usr/bin/env python

import logging
import optparse
import os.path
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import zipfile

from campy import *


logging.basicConfig()


if __name__ == '__main__':
    parser = optparse.OptionParser()
    parser.add_option('-d', '--depth', help="Engraving depth", type=float, default=0.010)
    parser.add_option('-s', '--stepovers', help='# of isolation paths to engrave', type=int, default=2)
    parser.add_option('-b', '--border', help='Width of border for PCB', type=float, default=0.1)
    parser.add_option('-t', '--thickness', help="Thickness of PCB (for drill/cutout)", type=float, default=1.7*constants.MM)
    options, args = parser.parse_args()

    pcb = PCBProject(gerber_input=args[0], border=0.1, flip='y')

    machine = set_machine('k2cnc')
    machine.max_rpm = 15000
    machine.min_rpm = 15000
    machine.set_material('fr4-1oz')

    pcb.pcb_job(
        output_directory='/tmp/test/',
        drill='bottom',
        cutout='bottom',
        iso_bit='engrave-0.1-30',
        drill_bit='tiny-0.8mm',
        cutout_bit='1/16in spiral upcut',
        file_per_operation=False,
    )