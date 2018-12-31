#!/usr/bin/env python

from campy import *
basedir = os.path.dirname(os.path.realpath(__file__))

if __name__ == "__main__":
    tool1 = tools['30degV']
    tool2 = tools['1/8in spiral upcut']

    ### Bowtie
    segs = LineSet([Line([
        [0.0, 0.0],
        [0.5, .35],
        [1.0, 0.0],
        [1.0, 1.0],
        [0.5, .65],
        [0.0, 1.0],
        [0.0, 0.0],
    ])])

    segs = segs.scale(x=2, y=2, origin=(0, 0, 0))
    Camtainer("./test/vcarve_bowtie_fem.ngc", [
                RectStock(3.4, 3.4, .5, origin=(-.5, -0.5, -.5)),
                VCarveInlay(vtool=tool1, flat_tool=tool2, segs=segs, pocket_depth=0.3, female=True),
    ])
    Camtainer("./test/vcarve_bowtie_male.ngc", [
                RectStock(3.4, 3.4, .5, origin=(-.5, -0.5, -.5)),
                VCarveInlay(vtool=tool1, flat_tool=tool2, segs=segs, pocket_depth=0.3, female=False),
    ])

    """

    ### Empire Star Wars logo
    segs = LineSet()
    segs.from_svg(os.path.join(basedir, '%s/../images/empire_mod.svg' % basedir), max_width=3.0)

    Camtainer("./test/vcarve_empire_fem.ngc", [
                RectStock(4.5, 4.5, .35, origin=(-.5, -0.35, -.5)),
                VCarveInlay(vtool=tool1, flat_tool=tool2, segs=segs, pocket_depth=0.3, female=True),
    ])

    Camtainer("./test/vcarve_empire_male.ngc", [
                RectStock(4.5, 4.5, .35, origin=(-.5, -0.35, -.5)),
                VCarveInlay(vtool=tool1, flat_tool=tool2, segs=segs, pocket_depth=0.3, female=False, material_factor=1),
    ])
    """