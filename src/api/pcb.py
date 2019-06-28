import boto3
from flask import send_file
import logging
import tempfile
import zipfile

from lib.api_framework import api_register, Api, FileResponse
from lib.campy import *

from . import login

logger = logging.getLogger(__name__)


@api_register(None, require_login=login.is_logged_in)
class PCBApi(Api):
    @classmethod
    @Api.config(file_keys=['file'])
    def upload(cls, project_key=None, file=None, file_key=None):
        bucket = "rustybrooks-cadcam"
        file_key = "{}".format(project_key)
        storage_key = '{}/{}'.format(project_key, file_key)

        s3 = boto3.client('s3')
        s3.upload_file(file, bucket, storage_key)

    @classmethod
    @Api.config(file_keys=['file'])
    def generate(
        cls, file=None,
        depth=0.005, separation=0.020, border=0, thickness=1.7*constants.MM, panelx=1, panely=1, zprobe_type='auto',
        posts='x'
    ):
        with tempfile.NamedTemporaryFile(mode="w+b", suffix=os.path.splitext(file.name)[-1]) as tf:
            logger.warn("fil = %r", file)
            for chunk in file.chunks():
                tf.write(chunk)
            tf.flush()
            logger.warn("step 1a")

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

        outdir = tempfile.mkdtemp()

        pcb.pcb_job(
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
            output_directory=outdir,
        )

        with tempfile.NamedTemporaryFile(suffix='.zip', delete=False) as tf:
            with zipfile.ZipFile(tf.name, 'w') as zip:
                for filename in os.listdir(outdir):
                    zip.write(
                        os.path.join(outdir, filename),
                        arcname=os.path.split(filename)[-1]
                    )

            logger.warn("step 5")
            return FileResponse(content=send_file(tf.name, mimetype='application/zip'), content_type='application/zip')

