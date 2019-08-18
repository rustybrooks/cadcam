_machine = None

import copy


def set_machine(m):
    global _machine
    if isinstance(m, (unicode, str)):
        m = machines[m]

    _machine = copy.deepcopy(m)
    return _machine


def machine():
    return _machine


import geometry
import constants

from cammath import *
from environment import tools, materials, machines, holes
from operations import *
from operations.pcb import *
from operations.probe import *
