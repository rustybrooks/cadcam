import base64
from gerber.render.cairo_backend import GerberCairoContext
import json
import tempfile
from lib.api_framework import api_register, Api, FileResponse, api_bool, api_list, api_int, api_float
from lib.campy import *
import shutil
import time

from . import queries, projects

logger = logging.getLogger(__name__)

from lib import cache


@cache.PickleCache(
    prefix='render_svg', timeout=60 * 60 * 24 * 7, basedir='/srv/data/file_cache'
)
def render_svg_generator(
    project_id=None, date_modified=None, layers=None, encode=True, max_height=None, max_width=None, side=None,
    theme_name=None
):
    pcb = PCBProject()

    files = queries.project_files(project_id=project_id, is_deleted=False)
    if not files:
        return PCBApi._empty_svg(encode=encode)

    fmap = {}
    for frow in files:
        file_type = PCBProject.identify_file(frow['file_name'])
        if not file_type:
            continue

        fmap[file_type] = frow

    try:
        pcb.load_layer(fmap[('both', 'outline')]['file_name'],
                       projects.project_files.get_fobj(project_file=fmap['both', 'outline']))
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

        pcb.load_layer(fmap[mapkey]['file_name'], projects.project_files.get_fobj(project_file=fmap[mapkey]))

        render_layers.append(mapkey)

    with tempfile.NamedTemporaryFile(delete=True) as tf:
        ctx = GerberSVGContext(svg_file=tf.name, width=max_width, height=max_height, flipx=side == 'bottom')
        ctx.render_layers([pcb.get_layer(x) for x in render_layers], theme=theme.THEMES[theme_name])
        ctx.save()

        if encode:
            data = base64.b64encode(open(tf.name).read())
            return data
        else:
            return FileResponse(
                content=open(tf.name),
                content_type='image/svg+xml',
            )


@cache.PickleCache(
    prefix='pcb_load_and_process', timeout=60*60*24*7, basedir='/srv/data/file_cache',
    keyfn=cache.arg_hash_gen(skip=['files'])
)
def pcb_load_and_process(project_id=None, date_modified=None, files=None):
    pcb = PCBProject()

    fmap = {}
    for frow in files:
        file_type = PCBProject.identify_file(frow['file_name'])
        if not file_type:
            continue

        fmap[file_type] = frow

    keys = [
        ('both', 'outline'),
        ('both', 'drill'),
        ('top', 'copper'),
        ('bottom', 'copper'),
    ]

    for mapkey in keys:
        if mapkey not in fmap:
            logger.warn("Not found: %r", mapkey)
            continue

        logger.warn("loading %r", mapkey)
        pcb.load_layer(fmap[mapkey]['file_name'], projects.project_files.get_fobj(project_file=fmap[mapkey]))

    pcb.process_layers()
    return pcb





@api_register(None, require_login=True)
class PCBApi(Api):
    '''
    @classmethod
    @Api.config(file_keys=['file'], require_login=False)
    def generate_from_zip(
        cls, file=None,
        depth=0.005, separation=0.020, border=0, thickness=1.7*constants.MM, panelx=1, panely=1, zprobe_type='auto',
        posts='x'
    ):
        with tempfile.NamedTemporaryFile(mode="w+b", suffix=os.path.splitext(file.name)[-1]) as tf:
            for chunk in file.chunks():
                tf.write(chunk)
            tf.flush()

            logger.warn("file = %r, size = %r", tf.name, file.size)

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
            cutout='top',
            # iso_bit='engrave-0.01in-15',
            iso_bit='engrave-0.1mm-30',
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

            logger.warn("returning zip")
            return FileResponse(
                response_object=send_file(tf.name, mimetype='application/zip'),
                # content_type='application/zip'
            )

    @classmethod
    @Api.config(file_keys=['file'], require_login=False)
    def generate(
        cls, project_key=None, username=None,
        depth=0.005, separation=0.020, border=0, thickness=1.7*constants.MM, panelx=1, panely=1, zprobe_type='auto',
        posts='x',
        _user=None,
    ):
        depth = api_float(depth)
        separation = api_float(separation)
        border = api_float(border)
        thickness = api_float(thickness)
        panelx = api_int(panelx)
        panely = api_int(panely)

        if project_key is None:
            raise cls.BadRequest("project_key is a required field")

        p = queries.project(
            project_key=project_key,
            username=username,
            viewing_user_id=_user.user_id,
            allow_public=True,
        )
        if not p:
            raise cls.NotFound()

        files = queries.project_files(project_id=p.project_id)

        pcb = PCBProject(
            gerber_input=[(f['file_name'], projects.project_files.get_fobj(project_file=f)) for f in files],
            border=border,
            auto_zero=True if zprobe_type == 'auto' else False,
            thickness=thickness,
            posts=posts,
        )

        machine = set_machine('k2cnc')
        machine.set_material('fr4-1oz')
        machine.max_rpm = machine.min_rpm = 15000

        if zprobe_type is None or zprobe_type == 'none':
            zprobe_radius = None
        elif zprobe_type == 'auto':
            zprobe_radius = 'auto'
        else:
            zprobe_radius = float(zprobe)

        outdir = tempfile.mkdtemp()

        pcb.pcb_job(
            drill='top',
            cutout='top',
            # iso_bit='engrave-0.01in-15',
            iso_bit='engrave-0.1mm-30',
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

            logger.warn("returning zip")
            return FileResponse(
                response_object=send_file(tf.name, mimetype='application/zip'),
                # content_type='application/zip'
            )
    '''

    @classmethod
    @Api.config(require_login=False)
    def render(cls, username=None, project_key=None, layers=None, side='top', encode=True, _user=None):
        if project_key is None:
            raise cls.BadRequest("project_key is a required field")

        rtheme = theme.THEMES['OSH Park']
        layers = api_list(layers) if layers else [
            'copper', 'solder-mask', 'drill', 'outline'
        ]
        encode = api_bool(encode)
        p = queries.project(
            project_key=project_key,
            username=username,
            viewing_user_id=_user.user_id,
            allow_public=True,
        )
        if not p:
            raise cls.NotFound()

        ctx = GerberCairoContext()

        files = queries.project_files(project_id=p['project_id'], is_deleted=False)

        fmap = {}
        for frow in files:
            file_type = PCBProject.identify_file(frow['file_name'])
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
            file_name = projects.project_files.get(project_file=frow)
            layer = gerber.load_layer(file_name)
            rendered = True
            ctx.render_layer(
                layer,
                settings=rtheme.get(layer.layer_class, RenderSettings()), bgsettings=rtheme['background']
            )

        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tf:
            ctx.dump(tf.name)

            if encode:
                data = base64.b64encode(open(tf.name).read()) if rendered else None
                return data
            else:
                return FileResponse(
                    content=open(tf.name, 'rb+'),
                    content_type='image/png'
                )


    @classmethod
    @Api.config(require_login=False)
    def render_svg(
        cls, project_key=None, username=None, side='top', encode=True, layers=None, max_width=700, max_height=700, _user=None,
        theme_name='OSH Park'
    ):
        if project_key is None:
            raise cls.BadRequest("project_key is a required field")

        encode = api_bool(encode)
        layers = list(set(api_list(layers) or [])) + ['outline']

        p = queries.project(
            project_key=project_key,
            username=username,
            viewing_user_id=_user.user_id,
            allow_public=True,
        )
        if not p:
            raise cls.NotFound()

        return render_svg_generator(
            project_id=p['project_id'],
            side=side,
            encode=encode,
            layers=layers,
            max_width=max_width,
            max_height=max_height,
            theme_name=theme_name,
            date_modified=p['date_modified'],
        )

    @classmethod
    def _empty_svg(cls, encode=False):
        with tempfile.NamedTemporaryFile(delete=True) as tf:
            dwg = geometry.shapely_get_dwg(
                svg_file=tf.name,
                bounds={'box_width': 1, 'box_height': 1, 'minx': 0, 'miny': 0, 'maxx': 0, 'maxy': 0},
                marginpct=0, width=1, height=1,
            )

            # goto
            geometry.shapely_add_to_dwg(
                 dwg, geoms=[
                    shapely.geometry.Polygon([
                        [0, 0], [0, 1], [1, 1], [1, 0],
                    ])
                ],
                foreground='green', background='black',
            )

            dwg.save()

            if encode:
                data = base64.b64encode(open(tf.name).read())
                return data
            else:
                return FileResponse(
                    content=open(tf.name),
                    content_type='image/svg+xml',
                )

    @classmethod
    @Api.config(require_login=False)
    def render_cam(
        cls, project_key=None, username=None, side='top',
        depth=0.005, separation=0.020, border=0, thickness=1.7*constants.MM, panelx=1, panely=1, zprobe_type='auto',
        posts='x', drill='top', cutout='top', iso_bit=None, drill_bit='tiny-1.0mm',
        cutout_bit=None, post_bit='1/8in spiral upcut',
        max_width=800, max_height=800, _user=None,
    ):
        depth = api_float(depth)
        separation = api_float(separation)
        border = api_float(border)
        thickness = api_float(thickness)
        panelx = api_int(panelx)
        panely = api_int(panely)
        max_width = api_int(max_width)
        max_height = api_int(max_height)

        if project_key is None:
            raise cls.BadRequest("project_key is a required field")

        p = queries.project(
            project_key=project_key,
            username=username,
            viewing_user_id=_user.user_id,
            allow_public=True,
        )
        if not p:
            raise cls.NotFound()

        if zprobe_type is None or zprobe_type == 'none':
            zprobe_radius = None
        elif zprobe_type == 'auto':
            zprobe_radius = 'auto'
        else:
            zprobe_radius = float(zprobe)

        job_kwargs = {
            'drill': drill,
            'cutout': cutout,
            # iso_bit='engrave-0.01in-15',
            'iso_bit': iso_bit,
            'drill_bit': drill_bit,
            'cutout_bit': cutout_bit,
            'post_bit': post_bit,
            'file_per_operation': True,
            'outline_depth': depth,
            'outline_separation': separation,
            'panelx': panelx,
            'panely': panely,
            'flip': 'x',
            'zprobe_radius': zprobe_radius,
            'border': border,
            'thickness': thickness,
            'posts': posts,
        }

        job_hash = cache.arg_hash(**job_kwargs)
        job = queries.project_job(project_id=p['project_id'], job_hash=job_hash)
        logger.warn("looking for job, id=%r, hash=%r job=%r", p['project_id'], job_hash, job)
        if False or not job:
            job_id = cls._render_cam_internal(
                side=side, project=p, job_kwargs=job_kwargs, max_width=max_width, max_height=max_height, job=job
            )
            job = queries.project_job(project_job_id=job_id)
        else:
            job_id = job['project_job_id'] if job else None

        job['files'] = queries.project_files(project_job_id=job_id, sort='file_name')
        return job

    @classmethod
    def _render_cam_internal(cls, side=None, project=None, job_kwargs=None, max_width=None, max_height=None, job=None):
        if job:
            job_id = job['project_job_id']
        else:
            job_id = queries.add_project_job(project['project_id'], cache.arg_hash(**job_kwargs))

        files = queries.project_files(project_id=project['project_id'])

        machine = set_machine('k2cnc')
        machine.set_material('fr4-1oz')
        machine.max_rpm = machine.min_rpm = 1000

        logger.warn("before geom=%r", len(machine.geometry))

        pcb = pcb_load_and_process(
            project_id=project['project_id'], date_modified=project['date_modified'],
            files=files
        )

        if side == 'both':
            sides = ['top', 'bottom']
        else:
            sides = [side]

        for side in sides:
            outdir = tempfile.mkdtemp()
            machine.set_save_geoms(True)
            pcb.pcb_job(output_directory=outdir, side=side, **job_kwargs)

            with tempfile.NamedTemporaryFile(delete=True) as tf:
                bounds = geometry.shapely_svg_bounds([x[0] for x in machine.geometry])

                dwg = geometry.shapely_get_dwg(svg_file=tf.name, bounds=bounds, marginpct=0, width=max_width,
                                               height=max_height)

                # goto
                geometry.shapely_add_to_dwg(
                    dwg, geoms=[x[0] for x in machine.geometry if x[1] == 'goto'], foreground='green'
                )

                # cut
                geometry.shapely_add_to_dwg(
                    dwg, geoms=[x[0] for x in machine.geometry if x[1] == 'cut'], foreground='blue'
                )

                dwg.save()

                projects.project_files.add(
                    project=project, project_job_id=job_id, fobj=open(tf.name, 'rb+'), file_name='{}_cam.svg'.format(side)
                )

            for fname in os.listdir(outdir):
                projects.project_files.add(
                    project=project, project_job_id=job_id, fobj=open(os.path.join(outdir, fname), 'rb+'), file_name=fname
                )

            shutil.rmtree(outdir)

        projects.project_files.add(
            project=project, project_job_id=job_id, contents=json.dumps(job_kwargs), file_name='params.json'
        )

        queries.update_project_job(
            project_job_id=job_id, status='succeeded'
        )

        return job_id