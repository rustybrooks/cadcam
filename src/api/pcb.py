import base64
import boto3
from flask import send_file
from gerber import PCB
from gerber import load_layer
from gerber.render import RenderSettings, theme
from gerber.render.cairo_backend import GerberCairoContext
import logging
import tempfile
import zipfile
from lib.api_framework import api_register, Api, FileResponse, api_bool
from lib.campy import *

from . import login, queries, projects

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

    def open_remote_file(self, ):
        pass

    @classmethod
    def render(cls, project_key=None, side='top', encode=True, _user=None):
        encode = api_bool(encode)
        p = queries.project(project_key=project_key, user_id=_user.user_id)
        if not p:
            raise cls.NotFound()

        ctx = GerberCairoContext()

        files = queries.project_files(project_id=p.project_id)

        fmap = {}
        for frow in files:
            file_type = PCBProject.identify_file(frow.file_name)
            if not file_type:
                continue

            fmap[file_type] = frow

        settings_map = {
            (side, 'silk-screen'): RenderSettings(color=theme.COLORS['white'], alpha=0.85)
        }

        for mapkey in [
            (side, 'copper'),
            (side, 'solder-mask'),
            (side, 'silk-screen'),
            ('both', 'drill'),
            ('both', 'outline'),
        ]:
            if mapkey not in fmap:
                continue

            frow = fmap[mapkey]
            with tempfile.NamedTemporaryFile(delete=False) as tf:
                tf.close()
                projects.s3.download_file(projects.bucket, frow.s3_key, tf.name)
            ctx.render_layer(gerber.load_layer(tf.name), settings=settings_map.get(mapkey))
            os.unlink(tf.name)

        with tempfile.NamedTemporaryFile(suffix='.png', delete=True) as tf:
            ctx.dump(tf.name)

            if encode:
                data = base64.b64encode(open(tf.name).read())
                return data
            else:
                return FileResponse(
                    content=send_file(tf.name, mimetype='application/png'),
                    # content_type='application/png'
                )

    @classmethod
    def render2(cls, project_key=None, side='top', max_width=400, max_height=400, encode=True, _user=None):
        encode = api_bool(encode)

        p = queries.project(project_key=project_key, user_id=_user.user_id)
        if not p:
            raise cls.NotFound()

        GERBER_FOLDER = tempfile.mkdtemp()

        for frow in queries.project_files(project_id=p.project_id):
            fname = os.path.join(GERBER_FOLDER, frow.file_name)
            projects.s3.download_file(projects.bucket, frow.s3_key, fname)

        # Create a new drawing context
        ctx = GerberCairoContext()

        # Create a new PCB instance
        pcb = PCB.from_directory(GERBER_FOLDER)

        with tempfile.NamedTemporaryFile(suffix='.png', delete=True) as tf:
            if side == 'top':
                # Render PCB top view
                ctx.render_layers(
                    pcb.top_layers, tf.name,
                    theme.THEMES['OSH Park'], max_width=max_width, max_height=max_height
                )
            else:
                # Render PCB bottom view
                ctx.render_layers(
                    pcb.bottom_layers, tf.name,
                    theme.THEMES['OSH Park'], max_width=max_width, max_height=max_height
                )

            if encode:
                data = base64.b64encode(open(tf.name).read())
                return data
            else:
                return FileResponse(
                    content=send_file(tf.name, mimetype='application/png'),
                    # content_type='application/png'
                )


