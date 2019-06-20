import logging
import tempfile

from lib.api_framework import api_register, Api
from lib.campy import *

logger = logging.getLogger(__name__)


@api_register(None, require_login=False)
class PCBApi(Api):
    @classmethod
    @Api.config(file_keys=['file'])
    def index(
        cls, file=None,
        depth=0.005, separation=0.020, border=0, thickness=1.7*constants.MM, panelx=1, panely=1, zprobe_type='auto',
        posts='x'
    ):
        with tempfile.NamedTemporaryFile(mode="w+b") as tf:
            for chunk in file.chunks():
                tf.write(chunk)
            tf.flush()

        pcb = PCBProject(
            gerber_input=tf.name,
            border=border,
            auto_zero=True,
            thickness=thickness,
            posts=posts,
            # fixture_width=fixture_width,
        )

        machine = set_machine('k2cnc')
        machine.set_material('fr4-1oz')
        machine.max_rpm = machine.min_rpm = 15000

        if zprobe_type is None:
            zprobe_radius = None
        elif zprobe_type == 'auto':
            zprobe_radius = 'auto'
        else:
            zprobe_radius = float(zprobe)

        pcb.pcb_job(
            # output_directory=output,
            drill='top',
            cutout='bottom',
            iso_bit='engrave-0.01in-15',
            drill_bit='tiny-0.9mm',
            cutout_bit='1/16in spiral upcut',
            post_bit='1/8in spiral upcut',
            # file_per_operation=not one_file,
            outline_depth=depth,
            outline_separation=separation,
            panelx=panelx,
            panely=panely,
            flip='x',
            zprobe_radius=zprobe_radius,
        )

        return "hi"
