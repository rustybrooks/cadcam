import copy
import os

_machine = None

flask_storage = os.environ.get('FLASK_STORAGE', "0'") != "0"
if flask_storage:
    from flask import request

def set_machine(m):
    global _machine
    if isinstance(m, (unicode, str)):
        m = Environment(**machines[m])

    if flask_storage:
        request._machine = m
    else:
        _machine = m

    return m


def machine():
    if flask_storage:
        return request._machine
    else:
        return _machine



import geometry
import constants

from cammath import *
from environment import materials, machines, holes, Environment
from operations import *
from operations.pcb import *
from operations.probe import *
