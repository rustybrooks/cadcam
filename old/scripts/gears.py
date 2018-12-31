#!/usr/bin/env python

from campy import *
import shapely
import shapely.geometry

def xfrange(start, stop, step):
    if start < stop:
        while start < stop:
            yield start
            start += step
    else:
        while start > stop:
            yield start
            start -= step

    if start != stop:
        yield stop

def dist(x1, y1, x2, y2):
    return math.sqrt( (x1 - x2)**2 + (y1 - y2)**2 )


def unit(p):
    x, y = p
    len = dist(0, 0, x, y)
    return (x/len, y/len)

def angle(x, y):
    return normalize_angle(math.degrees(math.atan2(y, x)), 360)


def normalize_angle(a, norm_by):
    while a >= norm_by: a -= norm_by
    while a < 0:  a += norm_by
    return a


def rotate(x, y, angle):
    sa = math.sin(math.radians(angle))
    ca = math.cos(math.radians(angle))

    newx = x*ca - y*sa
    newy = x*sa + y*ca
    
    return (newx, newy)


class Gear(CAM):
    # hub is (diameter, thickness)
    def __init__(self, tool, thickness, pitch_diameter, num_teeth, shaft_size, flat=True, hub=None):
        super(Gear, self).__init__(tool=None)

        self._tool = tool
        self.thickness = thickness
        self.pitch_diameter = pitch_diameter
        self.num_teeth = num_teeth
        self.flat = flat
        self.shaft_size = shaft_size
        self.hub=hub

        pressure_angle = 20
        self.PD = self.pitch_diameter 
        diam_pitch = num_teeth/self.PD
        self.OD = (num_teeth + 2.0)/diam_pitch ; # (outside diameter)
        self.BD = self.PD*math.cos(math.radians(pressure_angle)) ; # (base diameter)

        print "Outside diam = ", self.OD

    def find_pitch_point(self, t1, t2):
        t12 = (t1 + t2)/2.0
        p = self.point(t12)
    
        if p[0] is None:
            mydist = self.PD
        else:
            mydist = dist(0, 0, p[0], p[1])
    
    
        pr = self.PD/2.0
        if abs(mydist - pr) / pr < 0.00001:
            return t12
        elif mydist < pr:
            return self.find_pitch_point(t12, t2)
        else:
            return self.find_pitch_point(t1, t12)
    
    def point(self, t):
    
        r = self.BD/2.0
        angle = t*math.pi/2.0
        s = math.pi*r*t/2.0
        
        xc = r*math.cos(angle)
        yc = r*math.sin(angle)
        x = xc + s*math.sin(angle)
        y = yc - s*math.cos(angle)
    
        mydist = dist(0, 0, x, y)
        if mydist > self.OD/2.0:
            x = None
            y = None
        
        return (x, y)


    def make_single_tooth_curve(self):
        
        step = 0.001
        
        leading = []
        for t in xfrange(0, 1, step):
        
            p = self.point(t)
            if p[0] is None: break
                    
            leading.append(p)

        return leading

    def make_poly(self):
        astep = .25

        pp = self.find_pitch_point(0.0, 1.0)
        x, y = self.point(pp)
        pitch_angle = angle(x, y)
        
        tooth_angle = 360.0/self.num_teeth

        leading = self.make_single_tooth_curve()
        all = leading
        
        start_angle = angle(leading[-1][0], leading[-1][1])
        lead_angle = pitch_angle*2 + tooth_angle/2.0
        
        end_angle = None
        tailing = []
        for el in reversed(leading):
            x, y = el
            y = y*-1
            x, y = rotate(x, y, lead_angle)
        
            if end_angle is None: end_angle = angle(x, y)
            tailing.append((x,y))
        
        new_start_angle = angle(x, y)
        
        for a in xfrange(start_angle, end_angle, astep):
            x = self.OD/2.0*math.cos(math.radians(a))
            y = self.OD/2.0*math.sin(math.radians(a))
                    
            all.append((x, y))
        
        all.extend(tailing)
        
        for a in xfrange(new_start_angle, tooth_angle, astep):
            x = self.BD/2.0*math.cos(math.radians(a))
            y = self.BD/2.0*math.sin(math.radians(a))
                    
            all.append((x, y))
        
        print len(all), tooth_angle
        
        segments = []
        for base_rot in xfrange(0, 360, tooth_angle):
        
            lastx = None; lasty = None
            for el in all:
                xx, yy = el
                x, y = rotate(xx, yy, base_rot)
        
                segments.append((x, y))
        
                lastx = x
                lasty = y
        
        self.poly = shapely.geometry.LineString(segments)



    def generate_flat(self):

        R = self.tool.diameter/2.0


        self.make_poly()
        print "Before", len(self.poly.coords)
        offset = self.poly.simplify(0.01).parallel_offset(R, 'right')
        print "After", len(offset.coords)
        segments = offset.coords

        if self.hub:
            hub_diam, hub_thickness = self.hub
            comment = "Cutting hub diam=%0.3f, thickness=%0.3f" % (hub_diam, hub_thickness)
            Z = self.thickness + hub_thickness
            
            astep = .25
            rstep = R/2.0*astep/360

            self.camtain(
                    CirclePocket(tool=self.tool, center=(0, 0, self.thickness+hub_thickness), inner_rad=hub_diam/2.0, outer_rad=self.OD/2.0+R, depth=hub_thickness, comment=comment)
            )


#         Z = self.thickness
#         clearZ = Z + 0.25

#         last = segments[0]
#         self.goto(z=clearZ)
#         self.goto(x=last[0], y=last[1])

#         while Z > 0.001:
#             self.write("( Cutting gears, Z=%0.3f )" % Z)
#             Z -= self.tool.zstep_pass_rough if (Z>self.tool.zstep_depth_finish) else self.tool.zstep_pass_finish

#             if Z <= 0: Z = 0.001;
#             print "Z=", Z
            
#             self.cut(z=Z, rate=self.tool.drill_speed)

#             self.set_speed(50)
#             for p in segments[1:]:
#                 x,y = p

#                 self.cut(x,y)
            
#                 last = p


#         self.cut(z=clearZ, rate=self.tool.drill_speed)

        

    def generate_rotated(self):
        R = self.tool.diameter/2.0

        self.make_poly()

        self.set_speed(50)

        Z = math.sqrt(2)*self.PD/2
        clearZ = Z + 0.25

        self.goto(z=clearZ)
        self.goto(x=0, y=0)

        if self.hub:
            hub_diam, hub_thickness = self.hub
        else:
            hub_thickness = 0
            hub_diam = 0

        length = self.thickness + hub_thickness
        maxangle = 360*length/(R/4)
        print maxangle
        #maxangle = 360

        while Z > self.OD/2:
            Z -= self.tool.zstep_pass_rough 
            if Z < self.OD/2: Z = self.OD/2
            self.write("( facing to %0.3f )" % Z)

            self.cut(z=Z, rate=self.tool.drill_speed)
            self.set_speed(50)

            self.cut(x=length, a=maxangle)

            Z -= self.tool.zstep_pass_rough 
            if Z < self.OD/2: Z = self.OD/2

            self.cut(z=Z, rate=self.tool.drill_speed)
            self.set_speed(50)

            self.cut(x=0, a=maxangle*2)

        self.goto(z=Z+.25)
        self.goto(x=self.thickness+R)
        self.goto(z=Z)

        if hub:
            maxangle = 360*hub_thickness/(R/4)
            print maxangle
            while Z > hub_diam/2:
                Z -= self.tool.zstep_pass_rough 
                if Z < hub_diam/2: Z = hub_diam/2
                self.write("( facing hub to %0.3f )" % Z)
    
                self.cut(z=Z, rate=self.tool.drill_speed)
                self.set_speed(50)
    
                self.cut(x=length, a=maxangle)
    
                Z -= self.tool.zstep_pass_rough 
                if Z < hub_diam/2: Z = hub_diam/2
    
                self.cut(z=Z, rate=self.tool.drill_speed)
                self.set_speed(50)
    
                self.cut(x=self.thickness+R, a=maxangle*2)


        tooth_angle = 360.0/self.num_teeth

        pp = self.find_pitch_point(0.0, 1.0)
        x, y = self.point(pp)
        pitch_angle = angle(x, y)

        curve = self.make_single_tooth_curve()
        #curve2 = [ (x[0], -1*x[1]) for x in curve1 ]

        start_angle = angle(curve[-1][0], curve[-1][1])
        lead_angle = pitch_angle*2 + tooth_angle/2.0
        x , y = curve[0]
        x, y = rotate(x, y, lead_angle)
        new_start_angle = angle(x, y)

        xxx = (tooth_angle-new_start_angle)/2.0
        curve2 = [rotate(a[0], a[1], xxx) for a in curve]

        new_start_angle = angle(x, y)

        print "nsa=", new_start_angle, (tooth_angle-new_start_angle)/2.0




        #print curve
        # basic curve
        #print curve2
        for base_rot in xfrange(0, 360, tooth_angle):
            Z = self.OD/2
            self.goto(z=Z + 0.25)
            self.goto(x=0, y=-R*1.5)
            self.goto(a=base_rot)

            stepover = R*2.0/4.0
            while Z > self.BD/2.0:
                #print "----------------------------------------"
                Z -= .05
                self.write("( roughing gear to %0.3f )" % Z)
                if Z < self.BD/2.0: Z = self.BD/2.0
    
                near_dist = 1e12
                near_point = None
                for el in curve2:
                    d = abs(Z - el[0])
                    if d < near_dist:
                        #print "set d to", d, Z, el[0]
                        near_dist = d
                        near_point = el
   
                p1 = -1*near_point[1]  +R
                p2 = near_point[1]     -R
                #print Z, d, p1, p2, near_point, near_dist

                self.goto(x=-R*1.5, y=p1)
                self.goto(z=Z)
                self.set_speed(50)
   
                plus = True
                for y in xfrange(p1, p2, stepover):
                    #print "y=", y
                    self.goto(y=y)
                    if plus:
                        self.cut(x=self.thickness+R*1.5)
                    else:
                        self.cut(x=-R*1.5)
    
                    plus = not plus

        # refined curve
        curve_simple = shapely.geometry.LineString(curve).simplify(0.001)
        #curve_simple = curve_simple.parallel_offset(R, 'right')
        #curve_simple = shapely.geometry.LineString(curve)

        lastw=None
        lasth=0
        for base_rot in xfrange(0, 360, tooth_angle):
            self.goto(z=self.OD/2+0.25)
            #self.goto(a=base_rot)
            self.goto(x=-R*1.5)
            
            lastp = None
            plus = True
            for p in curve_simple.coords:
                #print p

                if lastp is not None:
                    x, y = p
                    lastx, lasty = lastp
                    poff = (x-lastx, y-lasty)
                    a = math.sqrt(2)*angle(poff[0], poff[1])
                    ar = math.radians(a)

                    nx, ny = unit(rotate(lastx, lasty, a))
                                 
                    xp = lasty*math.tan(ar)
                    h = math.cos(ar)*(lastx + xp)
                    w = dist(nx*h, ny*h, lastx, lasty)

#                    print "p=%r, lastp=%r, poff=%r, angle=%f, xp=%f, h=%f, w=%f" % (p, lastp, poff, a, xp, h, w)

                    yoff = w+R
                    zoff = h

                    #if lastw:
                    #    print >> f, "line,%f,%f,%f,%f,%f,%f,1.0,0.0,0.0" % (-0.01, w, h, -0.01, lastw, lasth)

                    lastw = w
                    lasth = h

                    self.goto(y=yoff, z=zoff, a=base_rot+a+xxx)

                    if plus:
                        self.cut(x=self.thickness+R*1.5)
                    else:
                        self.cut(x=-R*1.5)

                    plus = not plus

                lastp=p

        f = open("gear.draw", "w")
        rot_coords = [rotate(a[0], a[1], xxx) for a in self.poly.coords]
        #rot_coords = [a for a in self.poly.coords]
        last = rot_coords[0]
        for p in rot_coords[1:]:
            a1, b1 = last
            a2, b2 = p

            print >> f, "line,%f,%f,%f,%f,%f,%f,0.0,0.0,0.0" % (-0.000, a1, -b1, -0.000, a2, -b2)
            print >> f, "line,%f,%f,%f,%f,%f,%f,0.0,0.0,0.0" % (self.thickness, a1, -b1, self.thickness, a2, -b2)

            last = p
        f.close()


    def generate(self):

        self.set_tool(self._tool)

        self.write("%")
        self.write("G17 G20 G40 G90")


        if self.flat: 
            self.generate_flat()
        else:
            self.generate_rotated()

        self.end_program()


hub = (.5, .25)
tool=tools['1/4in spiral upcut']
Camtainer('./test/gear_6_20.ngc', [
     Gear(tool=tool, thickness=.5, pitch_diameter=2, num_teeth=32, shaft_size=0.25, hub=hub, flat=True)
])
