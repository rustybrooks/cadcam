#!/usr/bin/env python

from descartes import PolygonPatch
import math
#from matplotlib.collections import PatchCollection
#from matplotlib import pyplot
import ocl
import shapely.affinity
from shapely.coords import CoordinateSequence
from shapely.geometry import Point, LineString, MultiLineString, Polygon, LinearRing
import svg
# import stl


def make_vector(p1, p2):
    return [x - y for x, y in zip(p2, p1)]


def distance(p1, p2):
    return math.sqrt((p1[0]-p2[0])**2 + (p1[1]-p2[1])**2)


def dotproduct(v1, v2):
    return sum((a*b) for a, b in zip(v1, v2))


def crossproduct(a, b):
    c = [
        a[1]*b[2] - a[2]*b[1],
        a[2]*b[0] - a[0]*b[2],
        a[0]*b[1] - a[1]*b[0],
    ]

    return c


def length(v):
    return math.sqrt(dotproduct(v, v))


def bisect(v1, v2):
    return [(x+y)/2.0 for x, y in zip(v1, v2)]


def unit(v):
    l = length(v)
    return [x/l if l else 1 for x in v]


def angle_between(v1, v2):
    foo = min(1,(dotproduct(v1, v2) / (length(v1) * length(v2))))
    angle = math.acos(foo)

    cross = crossproduct(list(v1) + [0], list(v2) + [0]);
    if dotproduct([0, 0, 1], cross) < 0:
        angle = -angle

    return angle


def lengthen(v1, factor):
    return [x*factor for x in v1]


def frange(start, stop, step, include_end=True):
    if start < stop:
        while start < stop:
            yield start
            start += step
    else:
        while start > stop:
            yield start
            start -= step

    if include_end:
        yield stop


def polar_parameterize(curve, numpts):
    newcurve = []
    for i in range(numpts):
        angle = math.radians(360.*i/numpts)
        test_line = LineString([(0, 0), (1000*math.sin(angle), 1000*math.cos(angle))])
        inter = curve.intersection(test_line)
        newcurve.append(inter)
    newcurve.append(newcurve[0])
    return [length(x.coords[0]) for x in newcurve]


# def intersect_segments(seg1, seg2):
#     A, B = seg1
#     C, D = seg2
#
#     Bx_Ax = B[0] - A[0]
#     By_Ay = B[1] - A[1]
#     Dx_Cx = D[0] - C[0]
#     Dy_Cy = D[1] - C[1]
#     determinant = (-Dx_Cx * By_Ay + Bx_Ax * Dy_Cy)
#     if abs(determinant) < 1e-20:
#         return None
#
#     #s = (-By_Ay * (A[0] - C[0]) + Bx_Ax * (A[1] - C[1])) / determinant
#     t = ( Dx_Cx * (A[1] - C[1]) - Dy_Cy * (A[0] - C[0])) / determinant
#     res1 = (A[0] + (t * Bx_Ax), A[1] + (t * By_Ay))
#     #res2 = (C[0] + (s * Dx_Cx), C[1] + (s * Dy_Cy))
#
#     #if s >= 0 and s <= 1 and t >= 0 and t <= 1:
#     return res1
#
#     #return None

class Line():
    def __init__(self, coords=None, close=False):
        if not isinstance(coords, (tuple, list, CoordinateSequence)):
            raise Exception("Expecting coords to be a list or tuple, but it's a %r" % coords.__class__)
        self.coords = list(coords)
        self.close = close

    def unclose(self, epsilon=0.0001):
        if not self.coords:
            return self

        if distance(self.coords[0], self.coords[-1]) < epsilon:
            self.coords.pop()

        return Line(self.coords, close=self.close)

    def bounds(self):
        return LineString(self.coords).bounds

    def parallel_offset(self, dist, side='right', use_ring=True, join_style=1, mitre_limit=1):
        if not self.coords:
            return self

        coords = self.unclose().coords
        coords.append(coords[0])

        sline1 = LinearRing(coords[1:]) if use_ring else LineString(coords)
        sline2 = LinearRing(coords[:-1]) if use_ring else LineString(coords)
        offsline1 = sline1.parallel_offset(dist, side=side, join_style=join_style, mitre_limit=mitre_limit)
        offsline2 = sline2.parallel_offset(dist, side=side, join_style=join_style, mitre_limit=mitre_limit)

        if distance(offsline1.coords[0], offsline1.coords[-1]) < 0.0001:
            coords = offsline1.coords
        elif distance(offsline2.coords[0], offsline2.coords[-1]) < 0.0001:
            coords = offsline2.coords
        else:
            poly = Polygon(offsline1)
            poly = poly.union(Polygon(offsline2))
            coords = poly.exterior.coords

        #Line(coords).graph()
        try:
            return Line(coords).unclose()
        except Exception:
            return Line([])

    def intersection(self, l):
        coords = self.unclose().coords
        #coords.append(coords[0])
        p = Polygon(coords)
        #print len(l.coords), l.coords
        #lp = Polygon(l.coords)
        try:
            lp = l.linestring()
        except:
            lp = l

        return p.intersection(lp)  # FIXME should return Line or Lineset...?

    def difference(self, l):
        coords = self.unclose().coords
        p = Polygon(coords)
        try:
            lp = l.linestring()
        except:
            lp = l

        return p.difference(Polygon(lp))

    def graph(self, fig=None, color="red", show=True):
        from matplotlib import pyplot
        dograph = False
        if not fig:
            dograph = True
            foo = pyplot.figure()
            fig = foo.add_subplot(111)

        x = [el[0] for el in self.coords]
        y = [el[1] for el in self.coords]

        if self.close:
            x.append(x[0])
            y.append(y[0])

        fig.plot(x, y, color, alpha=0.9, linewidth=1, solid_capstyle='round')

        if dograph and show:
            pyplot.show()

    def area(self):
        if not len(self.coords): return 0
        poly = Polygon(self.coords)
        return poly.area

    def is_clockwise(self):
        sum = 0
        for p1, p2 in zip(self.coords[:-1], self.coords[1:]):
            #sum += (p2[0] - p2[1])*(p2[1] + p1[1])
            sum += p1[0]*p2[1] - p2[0]*p1[1]
        iscw = sum > 0
        return iscw

    def enforce_direction(self, clockwise=True):
        if not len(self.coords):
            return self

        coords = self.coords
        if coords[0] != coords[-1]:
            print "noeq", coords[0], coords[-1]
            coords.append(coords[0])

        sum = 0
        for p1, p2 in zip(coords[:-1], coords[1:]):
            #sum += (p2[0] - p2[1])*(p2[1] + p1[1])
            sum += p1[0]*p2[1] - p2[0]*p1[1]
        iscw = sum > 0
        # print iscw, sum


        #v1 = make_vector(self.coords[0], self.coords[1])
        #v2 = make_vector(self.coords[1], self.coords[2])
        #c = unit(crossproduct(v1 + [0], v2 + [0]))
        #print v1, v2
        #print "cross = ", c

        #iscw = True if c[2] == -1 else False

        if clockwise and not iscw:
            self.coords.reverse()
        elif not clockwise and iscw:
            self.coords.reverse()

        return Line(self.coords, close=self.close)

    def find_max_offset(self, offset, start=0, depth=0, maxdepth=4, plot=None):
        #print "find_max", offset, start, depth, maxdepth
        trial_offset = start
        lastarea = self.parallel_offset(trial_offset).area()
        if plot:
            self.graph(plot)

        #print "----"
        while True:
            trial_offset += offset
            o = self.parallel_offset(trial_offset, 'right')
            area = o.area()
            #print o.coords
            #if area == 0:
            #    print "Short circuit"
            #    #return trial_offset
            #    break
            #print trial_offset, area, lastarea
            if plot and area > 0:
                o.graph(plot)
            if area > lastarea or area == 0:
                break

            lastarea = area

        if depth < maxdepth:
            return self.find_max_offset(offset/4.0, trial_offset-offset*2, depth+1, maxdepth, plot=plot)
        else:
            return trial_offset - offset

    def linestring(self):
        return LineString(self.coords)

    def polygon(self):
        return Polygon(self.coords)

    def scale(self, x=1, y=1, z=1, origin='center'):
        return Line(shapely.affinity.scale(LineString(self.coords), xfact=x, yfact=y, zfact=z, origin=origin).coords, close=self.close)

    def translate(self, x=0, y=0, z=0):
        return Line(
            shapely.affinity.translate(LineString(self.coords), xoff=x, yoff=y, zoff=z).coords,
            close=self.close
        )

    def normal(self):
        p1 = make_vector(self.coords[0], self.coords[1])
        p2 = make_vector(self.coords[1], self.coords[2])
        cross = crossproduct(p1, p2)
        return tuple(unit(cross))

    def angle_to(self, axis):
        n = self.normal()
        return math.degrees(abs(dotproduct(n, axis) / length(n)*length(axis)))


class LineSet(object):
    def __init__(self, lines=None):
        self.lines = lines or []

    def add(self, line):
        self.lines.append(line)

    def load_from_svg(self, svgfile, max_width=None, max_height=None):
        l = LineSet()
        l.from_svg(svgfile, max_width, max_height)
        return l

    def from_svg(self, svgfile, max_width=None, max_height=None):
        svgf = svg.parse(svgfile)
        a, b = svgf.bbox()
        width, height = (b - a).coord()

        if max_width:
            svgf = svgf.translate(a).scale(max_width/width)

        if max_height:
            svgf = svgf.translate(a).scale(max_height/height)

        a, b = svgf.bbox()

        for el in svgf.flatten():
            foo = []
            for segment in el.segments(.01):
                last = None
                for el in segment:
                    el = el.coord()
                    if last is None or el[0] != last[0] or el[1] != last[1]:
                        foo.append([f - g for f, g in zip(el, a.coord())])
                    last = el

            self.add(Line(foo))

    def bounds(self):
        def reduce_bounds(bounds1, bounds2):
            return (
                min(bounds1[0], bounds2[0]),
                min(bounds1[1], bounds2[1]),
                max(bounds1[2], bounds2[2]),
                max(bounds1[3], bounds2[3])
            )

        return reduce(reduce_bounds, map(lambda x: x.bounds(), self.lines))

    def center(self):
        minx, miny, maxx, maxy = self.bounds()
        return (maxx+minx)/2.0, (maxy+miny)/2.0, 0

    def scale(self, x=1, y=1, z=1, origin='center'):
        if origin == 'center':
            origin = self.center()
            # print "set origin to", origin

        return LineSet(map(lambda foo: foo.scale(x=x, y=y, z=z, origin=origin), self.lines))

    def enforce_direction(self, clockwise=True):
        return LineSet(map(lambda x: x.enforce_direction(clockwise=clockwise), self.lines))

    def translate(self, x=0, y=0, z=0):
        return LineSet(map(lambda foo: foo.translate(x=x, y=y, z=z), self.lines))

    def unclose(self):
        return LineSet(map(lambda x: x.unclose(), self.lines))

    def parallel_offset(self, offset, use_ring=True, side='right', join_style=1, mitre_limit=1):
        return LineSet(map(lambda x: x.parallel_offset(offset, use_ring=use_ring, side=side, join_style=join_style, mitre_limit=mitre_limit), self.lines))

    def union_poly(self):
        return reduce(lambda x, y: x.union(y), map(lambda x: Polygon(x.coords), self.lines))

    def graph(self, fig=None):
        from matplotlib import pyplot
        dograph = False
        if not fig:
            dograph = True
            fig = pyplot.figure()
            ax = fig.add_subplot(111)

        for line in self.lines:
            line.graph(ax)

        if dograph:
            pyplot.show()

        #graph_poly(self.union_poly())


def generate_polygon(sides=3, diameter=1, rotation=None, offset=(0,0)):
    geom = []

    def point(angle):
        return [
            (diameter/2.0)*math.sin(math.radians(angle)) + offset[0],
            (diameter/2.0)*math.cos(math.radians(angle)) + offset[1],
        ]

    angle_incr = 360.0/sides
    if rotation is None:
        rotation = -angle_incr/2.0

    for side in range(sides):
        geom.append(point(rotation + side*angle_incr))
    geom.append(geom[0])

    return geom


class PolySurface(object):
    def __init__(self, polys=None, default=None):
        self.polys = []
        self.zvals = {}
        self.default = default
        self.misses = 0
        self.hits = 0

        self.range = [[1e12, -1e12], [1e12, -1e12], [1e12, -1e12]]

        if polys:
            for p in polys:
                self.append(p)

        # print "poly count", len(self.polys)

    @staticmethod
    def _distance(self, p1, p2):
        p1 = p1.coords[0]
        return math.sqrt((p1[0] - p2[0])**2 + (p1[1] - p2[1])**2)

    def append(self, poly):
        self.polys.append(poly)

        for i in (0, 1, 2):
            #print min([x[i] for x in poly.exterior.coords]
            self.range[i][0] = min(self.range[i][0], min([x[i] for x in poly.coords]))
            self.range[i][1] = max(self.range[i][1], max([x[i] for x in poly.coords]))

    def interpolate(self, point, poly):
        poly = list(poly.coords)
        point = point.coords[0]
        v0 = poly[0]

        p0 = (point[0], point[1], self.range[2][0] - 1)
        p1 = (point[0], point[1], self.range[2][1] + 1)

        n = crossproduct(
            make_vector(poly[0], poly[1]),
            make_vector(poly[1], poly[2]),
        )

        num = dotproduct(n, make_vector(v0, p0))
        denom = dotproduct(n, make_vector(p0, p1))

        r1 = -1 * num/denom if denom != 0 else 0
        inter = self.range[2][0] - 1 + (2 + self.range[2][1] - self.range[2][0])*r1
        #print r1, inter
        return inter

    def get(self, x, y):
        thisp = Point(x, y)
        key = (x, y)
        if key not in self.zvals:
            results = []
            for poly in self.polys:
                if poly.contains(thisp):
                    results.append(self.interpolate(thisp, poly))

            #print results
            self.zvals[key] = max(results) if results else self.default
            self.misses += 1
        else:
            self.hits += 1

        return self.zvals[key]

    def graph(self, extra_poly=None, show=True, color='zangle'):
        def _get_color(line):
            if color == 'zangle':
                angle = line.angle_to([0, 0, 1])
                pct = angle / 90.0
                pct = int(pct/10)*10
                val = int(256*pct)[-2:]
                return "#{v}{v}{v}".format(v=val)

        fig = pyplot.figure()
        sp = fig.add_subplot(211)

        sp.add_collection(PatchCollection(
            [PolygonPatch(x, alpha=1, fc=_get_color(x), zorder=2) for x in self.polys], match_original=True)
        )

        if extra_poly:
            sp.add_collection(PatchCollection(
                [PolygonPatch(x, alpha=1, fc='#0000ff', zorder=2) for x in extra_poly], match_original=True)
            )

        sp.set_xlim(*self.range[0])
        sp.set_ylim(*self.range[1])
        #sp.set_aspect(1.0)
        if show:
            pyplot.show()

        return fig, sp

    def write_obj(self, file):
        vertice_map = {}
        vertices = []

        verticen_map = {}
        verticens = []

        polygons = []

        for poly in self.polys:
            newpoly = []

            coords = [(x[0], x[2], x[1]) for x in list(poly.coords)]
            p1 = make_vector(coords[0], coords[1])
            p2 = make_vector(coords[0], coords[2])
            cross = crossproduct(p1, p2)
            normal = tuple(unit(cross))

            if normal not in verticen_map:
                verticens.append(normal)
                verticen_map[normal] = len(verticens)

            #print p1, p2, normal, vertice_map[normal]

            for point in coords:
                if point not in vertice_map:
                    vertices.append(point)
                    vertice_map[point] = len(vertices)

                newpoly.append("%d//%d" % (vertice_map[point], verticen_map[normal]))

            polygons.append(newpoly)

        with open(file, 'w') as f:
            f.write("# OBJ file\n")
            for v in vertices:
                f.write("v %.4f %.4f %.4f\n" % v)
            for v in verticens:
                f.write("vn %.4f %.4f %.4f\n" % v)
            for p in polygons:
                f.write("f %s\n" % (' '.join(p), ))

    @classmethod
    def from_stl(cls, filename):
        mesh = stl.mesh.Mesh.from_file(filename)
        polys = [Line(v) for v in mesh.vectors]
        return PolySurface(polys=polys)

    def get_ocl_stl_surf(self):
        s = ocl.STLSurf()
        count = 0
        for poly in self.polys:
            p1 = ocl.Point(*poly.coords[0])
            p2 = ocl.Point(*poly.coords[1])
            p3 = ocl.Point(*poly.coords[2])
            t = ocl.Triangle(p1, p2, p3)
            s.addTriangle(t)
            count += 1
        print "Surface with {} triangles!!".format(count)
        return s


def graph_poly(all_poly, fig=None):
    if isinstance(all_poly, Polygon):
        all_poly = [all_poly]

    COLOR = {
         True:  '#6699cc',
         False: '#ff3333'
    }

    def v_color(ob):
        return COLOR[ob.is_valid]

    def plot_coords(ax, ob):
        x, y = ob.xy
        ax.plot(x, y, 'o', color='#999999', zorder=1)

    dograph = False
    if not fig:
        dograph = True
        fig = pyplot.figure()
        ax = fig.add_subplot(111)

    for poly in all_poly:
        for i in poly.interiors:
            plot_coords(ax, i)

        plot_coords(ax, poly.exterior)

        patch = PolygonPatch(poly, facecolor=v_color(poly), edgecolor=v_color(poly), alpha=0.5, zorder=2)
        ax.add_patch(patch)

    if dograph:
        pyplot.show()

def graph_lines():
    pass


