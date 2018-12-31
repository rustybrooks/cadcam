#!/usr/bin/env python

import sys
from shapely.geometry import LineString, MultiLineString, Polygon, GeometryCollection
import shapely.affinity, shapely.geometry, shapely

from campy import *
from geometry import PolySurface, Line

import ocl  # https://github.com/aewallin/opencamlib
import camvtk  # ocl helper library


# this could be any source of triangles
# as long as it produces an ocl.STLSurf() we can work with
def STLSurfaceSource(filename):
    stl = camvtk.STLSurf(filename)
    polydata = stl.src.GetOutput()
    s = ocl.STLSurf()
    camvtk.vtkPolyData2OCLSTL(polydata, s)
    return s


# maybe fold this into CAM
class OCLCAM(CAM):
    def ocl_cutter(self):
        # choose a cutter for the operation:
        # http://www.anderswallin.net/2011/08/opencamlib-cutter-shapes/
        diameter = self.tool.diameter
        length = 5
        # cutter = ocl.BallCutter(diameter, length)
        if isinstance(self.tool, StraightRouterBit):
            cutter = ocl.CylCutter(self.tool.diameter, self.tool.cutting_length)
        elif isinstance(self.tool, BallRouterBit):
            cutter = ocl.BullCutter(diameter, self.tool.diameter/2.0, self.tool.cutting_length)

        # cutter = ocl.ConeCutter(diameter, angle, length)
        # cutter = cutter.offsetCutter( 0.4 )

        return cutter

    @classmethod
    def filter_path(cls, path, tolerance):
        f = ocl.LineCLFilter()
        f.setTolerance(tolerance)
        for p in path:
            p2 = ocl.CLPoint(p.x, p.y, p.z)
            f.addCLPoint(p2)
        f.run()
        return f.getCLPoints()

    # run the actual drop-cutter algorithm
    @classmethod
    def adaptive_path_drop_cutter(cls, surface, cutter, paths, sampling_size=0.04, min_sampling_size=0.01):
        apdc = ocl.AdaptivePathDropCutter()
        apdc.setSTL(surface)
        apdc.setCutter(cutter)

        # maximum sampling or "step-forward" distance
        # should be set so that we don't loose any detail of the STL model
        # i.e. this number should be similar or smaller than the smallest triangle
        apdc.setSampling(sampling_size)

        # minimum sampling or step-forward distance
        # the algorithm subdivides "steep" portions of the toolpath
        # until we reach this limit.
        # 0.0008
        apdc.setMinSampling(min_sampling_size)

        cl_paths = []
        n_points = 0
        for path in paths:
            apdc.setPath(path)
            apdc.run()
            cl_points = apdc.getCLPoints()
            n_points += len(cl_points)
            cl_paths.append(apdc.getCLPoints())
        return cl_paths

    def get_boundary(self):
        boundary = self.boundary
        if boundary is None:
            xr, yr, zr = self.surface.range
            boundary = xr[0], yr[0], xr[1], yr[1]

        if isinstance(boundary, (tuple, list)):
            minx, miny, maxx, maxy = boundary
            boundary = Line((
                (minx, miny),
                (minx, maxy),
                (maxx, maxy),
                (maxx, miny),
            ))

        #return boundary.parallel_offset(self.tool.diameter/2.)
        return boundary

    def points_to_ocl_path(self, pts):
        path = ocl.Path()
        for p1, p2 in zip(pts[:-1], pts[1:]):
            path.append(ocl.Line(ocl.Point(*p1), ocl.Point(*p2)))

        return path


class ParallelSurfacing(OCLCAM):
    def __init__(
            self, tool, surface, stepover=0.25, stepdown=0.5, tolerance=0.001, roughZ=0.0,
            material_factor=1.0, direction='y', boundary=None,
            clearZ=None, minZ=None, maxZ=None,
    ):
        super(ParallelSurfacing, self).__init__(tool=None)

        self._tool = tool
        self.surface = surface
        self.stepover = stepover
        self.stepdown = stepdown
        self.tolerance = tolerance
        self.material_factor = material_factor
        self.direction = direction
        self.boundary = boundary
        self.clearZ = clearZ
        self.minZ = minZ
        self.maxZ = maxZ
        self.roughZ = roughZ

    def generate(self):

        self.set_tool(tool=self._tool)

        minz = self.minZ if self.minZ is not None else self.surface.range[2][0]
        maxz = self.maxZ if self.maxZ is not None else self.surface.range[2][1]
        clearZ = self.clearZ or self.surface.range[2][1] + 0.25
        cutter = self.ocl_cutter()
        roughZ = self.roughZ*self.tool.diameter

        boundary = self.get_boundary()

        minx, miny, maxx, maxy = boundary.bounds()
        stepover = self.tool.diameter * min(self.stepover * self.material_factor, 1)
        stepdown = self.tool.diameter * min(self.stepover * self.material_factor, 4)

        # let's stay within tool radius from the edges of the curve and then clean up
        if self.direction == 'x':
            vector = shapely.geometry.LineString(((minx, 0), (maxx, 0)))
        elif self.direction == 'y':
            vector = shapely.geometry.LineString(((0, miny), (0, maxy)))
        else:
            vector = shapely.geometry.LineString((0, 0), self.direction)
            scale = 2*max(maxx-minx, maxy-miny)
            vector = shapely.affinity.scale(vector, scale, scale, 1, origin=(0, 0))

        lines = []
        if self.direction == 'x':
            for y in frange(miny, maxy, stepover):
                trial_vector = shapely.affinity.translate(vector, 0, y, 0)
                lines.append(trial_vector)
        elif self.direction == 'y':
            for x in frange(minx, maxx, stepover):
                trial_vector = shapely.affinity.translate(vector, x, 0, 0)
                lines.append(trial_vector)
        else:
            for y in frange(maxy, miny, stepover):  # should be modified by angle
                trial_vector = shapely.affinity.translate(vector, 0, y, 0)
                lines.append(trial_vector)

            for x in frange(minx, maxx, stepover):
                trial_vector = shapely.affinity.translate(vector, x, 0, 0)
                lines.append(trial_vector)

        def _filter_z(p):
            tpz = p.z + roughZ
            return [p.x, p.y, tpz if tpz > zh else zh]

        def _order(p):
            if inter.coords[0][0] < inter.coords[1][0]:
                these = list(p)
            else:
                these = list(reversed(p))

            if forward:
                these.reverse()

            path = ocl.Path()
            path.append(ocl.Line(ocl.Point(*these[0]), ocl.Point(*these[1])))
            return path

        paths = []
        forward = True
        for line in lines:
            inter = boundary.intersection(line)
            if isinstance(inter, LineString):
                path = _order(inter.coords)
                paths.append(path)
            elif isinstance(inter, MultiLineString):
                for ls in inter:
                    path = _order(ls.coords)
                    paths.append(path)
            else:
                print "Weird intersection", inter
                continue

            forward = not forward

        # now project onto the STL surface
        toolpaths = {
            True: self.adaptive_path_drop_cutter(self.surface.get_ocl_stl_surf(), cutter, paths),
            False: self.adaptive_path_drop_cutter(self.surface.get_ocl_stl_surf(), cutter, reversed(paths)),
        }

        # output a g-code file
        forward = True
        lastz = None
        for zh in frange(max(minz, maxz-stepdown), minz, stepdown):
            print "MINZ level", zh, roughZ, roughZ
            self.goto(z=clearZ)

            for path in toolpaths[forward]:
                fpath = self.filter_path(path, self.tolerance)
                first_pt = _filter_z(fpath[0])

                if not lastz or lastz > first_pt[2]:
                    self.cut(x=first_pt[0], y=first_pt[1])
                    self.cut(z=first_pt[2])
                else:
                    self.cut(z=first_pt[2])
                    self.cut(x=first_pt[0], y=first_pt[1])

                for p in fpath[1:]:
                    self.cut(*_filter_z(p))

                lastz = _filter_z(p)[2]

            forward = not forward


# This is only intended as a finishing method.  No stepdown.
class PathSurfacing(OCLCAM):
    def __init__(
            self, tool, surface, paths, seperate_paths=False, tolerance=0.001, clearZ=None,
    ):
        super(PathSurfacing, self).__init__(tool)

    def generate(self):

        self.set_tool(tool=self._tool)

        clearZ = self.clearZ or self.surface.range[2][1] + 0.25
        cutter = self.ocl_cutter()

        adaptive_paths = self.adaptive_path_drop_cutter(
                self.surface.get_ocl_stl_surf(),
                cutter,
                [self.points_to_ocl_path(x) for x in self.paths]
        )

        first = True
        for path in adaptive_paths:
            fpath = self.filter_path(path, self.tolerance)
            first_pt = fpath[0]

            if self.seperate_paths or first:
                self.goto(z=clearZ)
                self.goto(x=first_pt.x, y=first_pt.y)
                self.cut(z=first_pt.z)
                first = False
            else:
                self.cut(x=first_pt.x, y=first_pt.y, z=first_pt.z)

            for p in fpath[1:]:
                self.cut(x=p.x, y=p.y, z=p.z)


class SpiralPathSurfacing(OCLCAM):
    def __init__(
            self, tool, surface, minrad, maxrad, anglestep=0.5, tolerance=0.001, clearZ=None, stepover=0.25,
    ):
        super(SpiralPathSurfacing, self).__init__(tool)

    def generate(self):

        self.set_tool(self._tool)

        stepover = min(.9, self.stepover) * self.tool.diameter

        path = []
        rad = self.minrad
        angle = 0
        radstep = stepover / (360./self.anglestep)
        while rad <= self.maxrad:
            x = rad*math.cos(math.radians(angle))
            y = rad*math.sin(math.radians(angle))
            path.append((x, y))

            rad += radstep
            angle += self.anglestep

        self.camtain(PathSurfacing(
            tool=self.tool,
            surface=self.surface,
            paths=[path],
            tolerance=self.tolerance,
            clearZ=self.clearZ,
        ))


class WaterlineSurfacing(OCLCAM):
    def __init__(
            self, tool, surface, stepdown=0.2, tolerance=0.001, material_factor=1.0,
            boundary=None, clearZ=None, minZ=None, maxZ=None, adaptive=False,

    ):
        super(WaterlineSurfacing, self).__init__(tool=None)
        self._tool = tool
        self.surface = surface
        self.stepdown = stepdown
        self.tolerance = tolerance
        self.material_factor = material_factor
        self.boundary = None
        self.clearZ = clearZ
        self.minZ = minZ
        self.maxZ = maxZ
        self.adaptive = adaptive
        self.boundary = boundary

    def generate(self):

        self.set_tool(tool=self._tool)

        stepdown = min(self.stepdown*self.material_factor, 2)*self.tool.diameter
        boundary = self.get_boundary()

        if isinstance(self.boundary, (tuple, list)):
            minx, miny, maxx, maxy = self.boundary
            self.boundary = Polygon((
                (minx, miny),
                (minx, maxy),
                (maxx, maxy),
                (maxy, miny),
            ))

        cutter = self.ocl_cutter()
        minz = self.minZ if self.minZ is not None else self.surface.range[2][0]
        maxz = self.maxZ if self.maxZ is not None else self.surface.range[2][1]
        clearz = self.clearZ or maxz

        if self.adaptive:
            wl = ocl.AdaptiveWaterline()  # this is slower, ca 60 seconds on i7 CPU
            wl.setMinSampling(0.01)
        else:
            wl = ocl.Waterline()  # total time 14 seconds on i7 CPU

        surf = self.surface.get_ocl_stl_surf()
        wl.setSTL(surf)  # surface MUST be saved in a variable first
        wl.setCutter(cutter)
        wl.setSampling(0.0314)  # this should be smaller than the smallest details in the STL file

        for zh in frange(maxz, minz, stepdown):
            wl.reset()
            wl.setZ(zh)  # height for this waterline
            wl.run()

            for path in wl.getLoops():
                fpath = self.filter_path(path, self.tolerance)

                coords = [(a.x, a.y, a.z) for a in fpath]
                coords.append(coords[0])
                ls = LineString(coords)
                inter = boundary.intersection(ls)
                if isinstance(inter, MultiLineString):
                    print "MULTI"
                    for lx in inter:
                        self.cut_linestring(lx, zh, clearz=clearz)
                        #Line(lx.coords).graph(fig=fig)
                elif isinstance(inter, LineString):
                    print "SINGLE"
                    self.cut_linestring(inter, zh, clearz=clearz)
                    #Line(inter.coords).graph(fig=fig)
                elif isinstance(inter, GeometryCollection):
                    for foo in inter:
                        print "COLLECTION", foo.__class__
                        sys.exit(0)
                else:
                    print "WEIRD", inter.__class__
                    sys.exit(0)


class RadialSurfacing(OCLCAM):
    pass


class SpiralSurfacing(OCLCAM):
    pass


if __name__ == '__main__':
    tool = tools['1/4in spiral ball']

    stlfile = "stl/gnu_tux_mod.stl"
    surface = PolySurface.from_stl(stlfile)

    Camtainer("test/parallel_surfacing.ngc", [
        RectStock(8, 12, 3),

        ParallelSurfacing(
            tool=tool,
            surface=surface,
            #boundary=(0, 0, 10, 12),
            material_factor=10,
            direction='x',
            #minZ=2.2
        ),
    ])
    """
    Camtainer("test/waterline_surfacing.ngc", [
        RectStock(8, 12, 3),

        WaterlineSurfacing(
            tool=tool,
            surface=surface,
            boundary=(0, 0, 10, 12),
            material_factor=10,
        ),
    ])
    """
