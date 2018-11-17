#!/usr/bin/env python

import logging
import optparse
import os.path
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import zipfile

from campy import *


logging.basicConfig()


def identify_file(fname):
    ext = os.path.splitext(fname)[-1].lower()
    if ext == ".gbl":
        return 'bottom-copper'
    elif ext == '.gtl':
        return 'top-copper'
    elif ext == '.drl':
        return 'drill'
    else:
        return None


def flipx(geom, bounds):
    minx, miny, maxx, maxy = geom.bounds
    geom = shapely.affinity.scale(geom, xfact=-1, origin=(0, 0))
    return shapely.affinity.translate(geom, xoff=maxx + minx)


def flipy(geom, bounds):
    minx, miny, maxx, maxy = geom.bounds
    geom = shapely.affinity.scale(geom, yfact=-1, origin=(0, 0))
    return shapely.affinity.translate(geom, yoff=maxy+miny)


if __name__ == '__main__':
    parser = optparse.OptionParser()
    parser.add_option('-v', '--vbit', help='VBit engraving tool', type=str, default='engrave-0.1-30')
    parser.add_option('-d', '--depth', help="Engraving depth", type=float, default=0.010)
    parser.add_option('-s', '--stepovers', help='# of isolation paths to engrave', type=int, default=2)
    parser.add_option('-b', '--border', help='Width of border for PCB', type=float, default=0.1)
    parser.add_option('-t', '--thickness', help="Thickness of PCB (for drill/cutout)", type=float, default=1.6*constants.MM)
    options, args = parser.parse_args()

    layers = {
    }

    union_geom = shapely.geometry.MultiPolygon()
    if os.path.isdir(args[0]):
        for fname in os.listdir(args[0]):
            ftype = identify_file(fname)
            if ftype is None:
                continue

            layers[ftype] = (fname, open(fname).read())

    elif os.path.splitext(args[0])[-1].lower() == '.zip':
        z = zipfile.ZipFile(args[0])
        for i in z.infolist():
            ftype = identify_file(i.filename)
            if ftype is None:
                continue

            layers[ftype] = (i.filename, z.read(i.filename))
    else:
        print("Input not supported: supply either a directory or zip file containing gerber files")
        sys.exit(1)

    machine = set_machine('k2cnc')
    machine.max_rpm = 15000
    machine.min_rpm = 15000
    machine.set_material('fr4-1oz')
    machine.set_file('ngc/pcb/pcb.gcode')

    machine.set_tool(options.vbit)

    union_geom = shapely.geometry.GeometryCollection()
    for k, v in layers.items():
        fname, fdata = v
        if k == 'drill':
            g = pcb_drill_geometry(gerber_data=fdata, gerber_file=fname)
        else:
            g = pcb_trace_geometry(gerber_data=fdata, gerber_file=fname)

        union_geom = union_geom.union(g)

    bounds = union_geom.bounds

    bottom_trace_geom = None
    top_trace_geom = None
    drill_geom = None

    if 'top-copper' in layers:
        fname, fdata = layers['top-copper']
        top_trace_geom, top_iso_geoms = pcb_isolation_mill(
            gerber_data=fdata,
            gerber_file=fname,
            stepovers=options.stepovers,
            depth=options.depth,
            border=options.border,
        )

        # minx, miny, maxx, maxy = bounds
        # width = maxx - minx
        # height = maxy - miny
        # rect_stock(width, height, options.thickness, origin=(0, -options.thickness, 0))

    if 'bottom-copper' in layers:
        fname, fdata = layers['bottom-copper']

        bottom_trace_geom, bottom_iso_geoms = pcb_isolation_mill(
            gerber_data=fdata,
            gerber_file=fname,
            stepovers=options.stepovers,
            depth=options.depth,
            flipy=bounds,
            zprobe_radius=None,
        )

        # minx, miny, maxx, maxy = bounds
        # width = maxx - minx
        # height = maxy - miny
        # rect_stock(width, height, options.thickness, origin=(0, -options.thickness, 0))

    if 'drill' in layers:
        machine.set_tool('tiny-0.8mm')
        fname, fdata = layers['drill']
        drill_geom = pcb_drill(
            gerber_data=fdata,
            gerber_file=fname,
            depth=options.thickness,
            flipy=bounds
        )

    machine.set_tool('1/16in spiral upcut')
    # pcb_cutout(bounds=bounds, depth=options.thickness)

    geoms = [x for x in [
        bottom_trace_geom,
#        # top_trace_geom,
        drill_geom
    ] if x]
    geometry.shapely_to_svg('drill.svg', geoms, marginpct=0)
    geometry.shapely_to_svg('drill2.svg', list(reversed(bottom_iso_geoms))+[drill_geom], marginpct=0)
#    geometry.shapely_to_svg('drill.svg', union_geom, marginpct=0)
