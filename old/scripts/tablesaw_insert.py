#!/usr/bin/env python
from matplotlib import pyplot
import matplotlib.image as mpimg
from campy import *
import shapely.geometry
import cv2
#from figures import SIZE

from campy import *

COLOR = {
    True:  '#6699cc',
    False: '#ffcc33'
    }

def v_color(ob):
    return COLOR[ob.is_simple]

def plot_coords(ax, ob):
    x, y = ob.xy
    ax.plot(x, y, 'o', color='#999999', zorder=1)

def plot_bounds(ax, ob):
    print ob.boundary
    x, y = zip(*list((p.x, p.y) for p in ob.boundary))
    ax.plot(x, y, 'o', color='#000000', zorder=1)

def plot_line(ax, ob):
    x, y = ob.xy
    ax.plot(x, y, color=v_color(ob), alpha=0.7, linewidth=1, solid_capstyle='round', zorder=2)

class PowermaticTSInsert(CAM):
    def __init__(self, tool):
        super(PowermaticTSInsert, self).__init__()

        self.tool = tool
        self.width = 4.0
        self.square_height = 8.0  # This is the height minus the half-circle ends


    def generate(self):

        Camtainer(f, [
            HelicalDrill(tool, (2, 2, .5), outer_rad=.2, depth=.5*tool.diameter/2.0, stepdown=tool.diameter/2.0),
        ], self_contained=False)


def halftone():
    #import PIL
    with open("test.draw", "w"):
        pass

    from PIL import Image
    im = Image.open("images/biohazard.png")
    w = 30
    h = 30
    im = im.resize((w*2, h*2), Image.ANTIALIAS)

    segments = []

    for y in range(h):
        for x in range(w):
            offset = y % 2
            print im.getpixel((x*2, y*2))
            pixels = [
                im.getpixel((x*2, y*2))[3],
                im.getpixel((x*2+1, y*2))[3],
                im.getpixel((x*2, y*2+1))[3],
                im.getpixel((x*2+1, y*2+1))[3],
            ]
            p = sum(pixels)/4.0
            if p < .2*256: continue
            #p = 255
            segments = []
            add_poly(segments, (.1*x + offset*.05, .1*y, 0), p/256.0*0.05, 6)
            segments_to_drawable('test.draw', segments, close=False)

def img_to_segments(filename, threshold=20, height=1, invert=False):
    img = cv2.imread(filename, cv2.IMREAD_GRAYSCALE)
    img_orig = cv2.imread(filename)

    resize = 2
    img = cv2.resize(img, None, fx=resize, fy=resize, interpolation=cv2.INTER_CUBIC)
    img_orig = cv2.resize(img_orig, None, fx=resize, fy=resize, interpolation=cv2.INTER_CUBIC)

    th, img2 = cv2.threshold(img, threshold, 255, cv2.THRESH_BINARY_INV if invert else cv2.THRESH_BINARY);

    img3, contours, hierarchy = cv2.findContours(img2, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)

    scale = float(height)/img.shape[1]
    scale = 1
    #print scale

    #print len(contours)
    count = 0

    open("test.draw", "w").close()

    all_segments = []
    for c in contours:
        count += 1

        segments = [(x[0][0]*scale, x[0][1]*scale) for x in c]
        segments.append(segments[0])
        all_segments.append(segments)

    return img_orig, all_segments

# man, rename this to something else
# make all the parts below "threshold" disappear, optionally invert first
# height is the number of inches for the image height
def cutout_image(filename, tool, depth, threshold=20, invert=False, height=1):
    profiles = [RectStock(height, height, depth)]

    for segments in img_to_segments(filename, threshold=threshold, height=height, invert=invert):
        profiles.append(ThreeDProfile(segments, tool, depth=depth, side='right'))


    Camtainer("./tablesaw_insert.ngc", profiles, self_contained=True)
    #cv2.drawContours(img_orig, contours, -1, (0, 255, 0), 1)

def vcarve_image(filename, tool, depth, threshold=20, invert=False, height=1):
    fig = pyplot.figure()
    ax = fig.add_subplot(111)

    image, all_segments = img_to_segments(filename, threshold=threshold, height=height, invert=invert)

    pyplot.imshow(image, alpha=1)

    for s in all_segments:
        line = shapely.geometry.LineString(s).simplify(.005)
        x, y = line.xy
        ax.plot(x, y, color=v_color(line), alpha=0.9, linewidth=1, solid_capstyle='round', zorder=2)

    pyplot.show()

def add_poly(segments, center, radius, sides):
    angle = 360/sides
    for i in range(sides+1):
        segments.append((
            center[0] + math.sin(math.radians(angle*i))*radius,
            center[1] + math.cos(math.radians(angle*i))*radius,
            center[2]
    ))

#halftone()
tool = tools['1/16in spiral upcut']
#cutout_image("images/biohazard.png", tools, depth=.025, threshold=65, height=5, invert=True)
#cutout_image("images/teardrop_tree.jpg", tool, depth=.025, threshold=65, height=10)
vcarve_image("images/teardrop_tree.jpg", tool, depth=.025, threshold=65, height=10)




#tool = tools['1/4in spiral upcut']
#thickness = 0.5

#Camtainer("powermatic_insert.ngc", [
#    RectStock(4, 4, thickness, origin=(0, 0, 0)),
#    PowermaticTSInsert(tool),
#], self_contained=True)
