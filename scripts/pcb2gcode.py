#!/usr/bin/env python

import logging
import optparse
import os.path
import sys

basedir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'src')
print basedir
sys.path.append(basedir)
# import zipfile

# from campy import *
# from lib.campy import constants

from lib.api_framework import client
from lib import config
import tempfile
import zipfile

logging.basicConfig()


if __name__ == '__main__':
    if config.get_config_key('ENVIRONMENT') == 'dev':
        url = 'http://localhost:5000'
    else:
        url = 'http://cadcam.rustybrooks.com'

    cadcam = client.Frameworks(
        base_url=url,
        framework_endpoint='api/framework/endpoints',
        framework_key='cadcam',
    )

    parser = optparse.OptionParser()
    parser.add_option('-d', '--depth',     help="Engraving depth", type=float, default=0.005)
    parser.add_option('-s', '--separation', help='Trace separation', type=int, default=0.020)
    parser.add_option('-b', '--border',    help='Width of border for PCB', type=float, default=0)
    parser.add_option('-t', '--thickness', help="Thickness of PCB (for drill/cutout)", type=float, default=1.7/25.4)
    parser.add_option('-o', '--output',    help='output directory, will be created if it doesn\'t exist', type=str)
    parser.add_option('--one-file',        help='if passed, will put each layer in one file', action='store_true')
    # parser.add_option('--side',            help='For one sided boards, which side to use', type='str', default='bottom')
    parser.add_option('--panelx',          help='Number of times to repeat pcb in x direction', type=int, default=1)
    parser.add_option('--panely',          help='Number of times to repeat pcb in y direction', type=int, default=1)
    parser.add_option('--zprobe',          help='zprobe radius interval, use a number or "auto" or "none"', type=str, default='auto')
    parser.add_option('--posts',           help='cut 1/8" post holes for alignment (x or y or none)', type='str', default='x')
    parser.add_option('--fixture_width',   help='width of 2-side fixture', type=float, default=None)
    options, args = parser.parse_args()

    with tempfile.NamedTemporaryFile(suffix='.zip') as tf:
        with open(tf.name, 'w+b') as f:
            f.write(cadcam.PCBApi.generate_from_zip(
                file=args[0],
                depth=options.depth, separation=options.separation, border=options.border, thickness=options.thickness, 
                panelx=options.panelx, panely=options.panely, zprobe=options.zprobe, posts=options.posts,
            ))

        with zipfile.ZipFile(tf.name) as z:
            z.extractall(path=options.output)

