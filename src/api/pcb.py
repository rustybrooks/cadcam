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

from . import queries, projects

logger = logging.getLogger(__name__)


@api_register(None, require_login=True)
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

            return FileResponse(content=send_file(tf.name, mimetype='application/zip'), content_type='application/zip')

    def open_remote_file(self, ):
        pass

    @classmethod
    @Api.config(require_login=False)
    def render(cls, username=None, project_key=None, side='top', encode=True, _user=None):
        rtheme = theme.THEMES['OSH Park']

        encode = api_bool(encode)
        p = queries.project(
            project_key=project_key,
            username=_user.username if username == 'me' else username,
            viewing_user_id=_user.user_id,
            allow_public=True,
        )
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

        for mapkey in [
            (side, 'copper'),
            (side, 'solder-mask'),
            (side, 'silk-screen'),
            ('both', 'drill'),
            ('both', 'outline'),
        ]:
            if mapkey not in fmap:
                logger.warn("Not found: %r", mapkey)
                continue

            frow = fmap[mapkey]
            file_name = projects.s3cache.get(project_file=frow)
            layer = gerber.load_layer(file_name)
            ctx.render_layer(
                layer,
                settings=rtheme.get(layer.layer_class, RenderSettings()), bgsettings=rtheme['background']
            )

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
    @Api.config(require_login=False)
    def render2(cls, project_key=None, username=None, side='top', max_width=600, max_height=600, encode=True, _user=None, union=True):
        encode = api_bool(encode)
        union = api_bool(union)
        p = queries.project(
            project_key=project_key,
            username=_user.username if username == 'me' else username,
            viewing_user_id=_user.user_id,
            allow_public=True,
        )
        if not p:
            raise cls.NotFound()

        pcb = PCBProject(
            border=0,
            auto_zero=True,
            thickness=1.7*constants.MM,
            posts=False,
        )

        files = queries.project_files(project_id=p.project_id)
        for f in files:
            file_type = PCBProject.identify_file(f.file_name)
            if not file_type:
                continue

            if file_type != ('top', 'copper'):
                continue

            pcb.load_layer(f.file_name, projects.s3cache.get_fobj(project_file=f))

        pcb.process_layers(union=union)

        with tempfile.NamedTemporaryFile(delete=False) as tf:
            pcb.layer_to_svg(('top', 'copper'), tf.name, width=max_width, height=max_height)

            return FileResponse(
                # content=send_file(tf.name, mimetype='image/svg+xml'),
                content=open(tf.name),
                content_type='image/svg+xml',
            )

    @classmethod
    def render3(cls, union=True):
        union = api_bool(union)
        import shapely.geometry
        import shapely.ops
        from lib.campy import geometry

        p1 = shapely.geometry.Polygon([[0, 0], [1, 0], [1, .2], [0, .2]])
        p2 = shapely.geometry.Polygon([[0, 1], [1, 1], [1, .8], [0, .8]])
        p3 = shapely.geometry.Polygon([[0, 0], [.2, 0], [.2, 1], [0, 1]])
        p4 = shapely.geometry.Polygon([[1, 1], [.8, 1], [.8, 0], [1, 0]])
        p5 = shapely.geometry.Polygon([[.4, .4], [.4, .6], [.6, .6], [.6, .4]])
        # polys = [p1, p2, p3, p4, p5]
        polys = [p5, p1, p2, p3, p4]
        if union:
            geoms = [shapely.ops.unary_union(polys)]
        else:
            geoms = polys

        with tempfile.NamedTemporaryFile(delete=False) as tf:
            geometry.shapely_to_svg(geoms=geoms, svg_file=tf.name)

            return FileResponse(content=open(tf.name), content_type='image/svg+xml')


    # @classmethod
    # def render2(cls, project_key=None, side='top', max_width=600, max_height=600, encode=True, _user=None):
    #     encode = api_bool(encode)
    #
    #     p = queries.project(project_key=project_key, user_id=_user.user_id, allow_public=True)
    #     if not p:
    #         raise cls.NotFound()
    #
    #     GERBER_FOLDER = tempfile.mkdtemp()
    #
    #     for frow in queries.project_files(project_id=p.project_id):
    #         fname = os.path.join(GERBER_FOLDER, frow.file_name)
    #         projects.s3.download_file(projects.bucket, frow.s3_key, fname)
    #
    #     # Create a new drawing context
    #     ctx = GerberCairoContext()
    #
    #     # Create a new PCB instance
    #     pcb = PCB.from_directory(GERBER_FOLDER)
    #
    #     with tempfile.NamedTemporaryFile(suffix='.png', delete=True) as tf:
    #         if side == 'top':
    #             # Render PCB top view
    #             ctx.render_layers(
    #                 pcb.top_layers, tf.name,
    #                 theme.THEMES['OSH Park'], max_width=max_width, max_height=max_height
    #             )
    #         else:
    #             # Render PCB bottom view
    #             ctx.render_layers(
    #                 pcb.bottom_layers, tf.name,
    #                 theme.THEMES['OSH Park'], max_width=max_width, max_height=max_height
    #             )
    #
    #         if encode:
    #             data = base64.b64encode(open(tf.name).read())
    #             return data
    #         else:
    #             return FileResponse(
    #                 content=send_file(tf.name, mimetype='application/png'),
    #                 # content_type='application/png'
    #             )


