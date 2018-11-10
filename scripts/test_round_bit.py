#!/usr/bin/env python

from campy import *

Camtainer("./test/test_round_bit.ngc", [
    RectStock(4, 4, 1, origin=(0, -1, 0)),
    Goto(x=2, y=2),
    Goto(z=-1/4.),
    Goto(x=4, y=4),
    Goto(z=-1/2.),
    Goto(x=3, y=1),
])