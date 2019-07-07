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
from lib.api_framework import api_register, Api, FileResponse, api_bool, api_list
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
    def render(cls, username=None, project_key=None, layers=None, side='top', encode=True, _user=None):
        rtheme = theme.THEMES['OSH Park']
        layers = api_list(layers) if layers else [
            'copper', 'solder-mask', 'drill', 'outline'
        ]

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

        rendered = False
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

            if mapkey[1] not in layers:
                continue

            frow = fmap[mapkey]
            file_name = projects.s3cache.get(project_file=frow)
            layer = gerber.load_layer(file_name)
            rendered = True
            ctx.render_layer(
                layer,
                settings=rtheme.get(layer.layer_class, RenderSettings()), bgsettings=rtheme['background']
            )

        with tempfile.NamedTemporaryFile(suffix='.png', delete=True) as tf:
            ctx.dump(tf.name)

            if encode:
                data = base64.b64encode(open(tf.name).read()) if rendered else None
                return data
            else:
                return FileResponse(
                    content=send_file(tf.name, mimetype='application/png'),
                    # content_type='application/png'
                )

    @classmethod
    def _flip(cls, g, bounds):
        minx, miny, maxx, maxy = bounds
        g = shapely.affinity.scale(g, xfact=-1, origin=(0, 0))
        g = shapely.affinity.translate(g, xoff=maxx+minx)
        return g

    @classmethod
    @Api.config(require_login=False)
    def render_svg(
        cls, project_key=None, username=None, side='top', encode=True, layers=None, max_width=600, max_height=600, _user=None,
    ):
        encode = api_bool(encode)
        layers = set(api_list(layers) or [])
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

        fmap = {}
        for frow in files:
            file_type = PCBProject.identify_file(frow.file_name)
            if not file_type:
                continue

            fmap[file_type] = frow

        try:
            pcb.load_layer(fmap[('both', 'outline')].file_name, projects.s3cache.get_fobj(project_file=fmap['both', 'outline']))
        except KeyError:
            pass

        render_layers = []
        for mapkey in [
            ('both', 'outline'),
            (side, 'copper'),
            (side, 'solder-mask'),
            (side, 'silk-screen'),
            ('both', 'drill'),
        ]:
            if mapkey not in fmap:
                logger.warn("Not found: %r", mapkey)
                continue

            if mapkey[1] not in layers:
                continue

            if mapkey[0] not in [side, 'both']:
                continue

            pcb.load_layer(fmap[mapkey].file_name, projects.s3cache.get_fobj(project_file=fmap[mapkey]))
            render_layers.append(mapkey)

        pcb.process_layers(union=False)

        try:
            outline = pcb.layers[('both', 'outline')]['geometry']
        except KeyError:
            logger.warn("NO OUTLINE")
            outline = None

        bgmap = {
            'solder-mask': '#cfb797',
            'drill': '#cccccc',
        }

        fgmap = {
            'copper': '#cfb797',
            'outline': 'black',
            'solder-mask': '#4e2a87',
            'silk-screen': 'white',
            'drill': '#444444',
        }

        bgalphamap = {
            'silk-screen': 1,
            'solder-mask': 1,
        }

        fgalphamap = {
            'solder-mask': .75,
            'silk-screen': 1,
        }

        if outline:
            geoms = list(outline)
        else:
            geoms = []
        for l in render_layers:
            g = pcb.layers[l]['geometry']
            geoms.extend(g)

        bounds = geometry.shapely_svg_bounds(geoms)
        logger.warn("bounds = %r", bounds)
        fbounds = [bounds['minx'], bounds['miny'], bounds['maxx'], bounds['maxy']]

        if not outline:
            bounds2 = geometry.shapely_svg_bounds(geoms, flip=False)
            outline = shapely.geometry.Polygon([
                [bounds2['minx'], bounds2['miny']],
                [bounds2['minx'], bounds2['maxy']],
                [bounds2['maxx'], bounds2['maxy']],
                [bounds2['maxx'], bounds2['miny']],
            ])
        else:
            bounds2 = geometry.shapely_svg_bounds(geoms, flip=False)
            gout = shapely.ops.unary_union(outline)
            outline = shapely.geometry.Polygon(gout.exterior).simplify(0.005)


            # logger.warn("before %r %r", list(gout.exterior.coords), gout.interiors)
            # outline = shapely.geometry.Polygon([
            #    [bounds2['minx'], bounds2['miny']],
            #    [bounds2['minx'], bounds2['maxy']],
            #    [bounds2['maxx'], bounds2['maxy']],
            #    [bounds2['maxx'], bounds2['miny']],
            # ])
            # logger.warn("after %r %r", list(outline.exterior.coords), outline.interiors)

        with tempfile.NamedTemporaryFile(delete=False) as tf:
            dwg = geometry.shapely_get_dwg(
                svg_file=tf.name,
                bounds=bounds,
                marginpct=0,
                width=max_width, height=max_height
            )

            geometry.shapely_add_to_dwg(
                dwg, geoms=outline,
                # bounds=bounds, fill_box=True,
                background=bgmap.get('outline', '#4e2a87'),
                foreground=fgmap.get('outline', 'green'),
                foreground_alpha=fgalphamap.get('outline', 1),
                background_alpha=bgalphamap.get('outline', 1),
            )

            for l in render_layers:
                geom = pcb.layers[l]['geometry']
                if not isinstance(geom, (list, tuple)):
                    geom = [geom]

                if side == 'bottom':
                    geom = [cls._flip(g, fbounds) for g in geom]

                if l[1] == 'solder-mask':
                    gout = shapely.ops.unary_union(outline)
                    if not isinstance(gout, (shapely.geometry.LineString, shapely.geometry.Polygon)):
                        gout = gout[0]
                    gout = shapely.geometry.Polygon(gout)
                    geom = gout.difference(shapely.ops.unary_union(geom))

                geometry.shapely_add_to_dwg(
                    dwg, geoms=geom,
                    background=bgmap.get(l[1], '#4e2a87'),
                    foreground=fgmap.get(l[1], 'green'),
                    foreground_alpha=fgalphamap.get(l[1], 1),
                    background_alpha=bgalphamap.get(l[1], 1),
                )

            dwg.save()

            if encode:
                data = base64.b64encode(open(tf.name).read())
                return data
            else:
                return FileResponse(
                    # content=send_file(tf.name, mimetype='image/svg+xml'),
                    content=open(tf.name),
                    content_type='image/svg+xml',
                )

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


