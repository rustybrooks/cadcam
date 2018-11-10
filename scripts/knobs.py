#!/usr/bin/env python

from campy import *
from hsm import *

class Knob(CAM):
    def __init__(
            self, tool, center, diameter=2.0, boss_diameter=1.0, thickness=.75, boss_thickness=.25,
            divots=7, divot_rad=.25, bore=None, nut=None
    ):
        super(Knob, self).__init__()
        # self.tool = tool
        # self.center = center
        # self.diameter = diameter
        # self.thickness = thickness
        # self.boss_diameter = boss_diameter
        # self.boss_thickness = boss_thickness
        # self.divots = divots
        # self.divot_rad = divot_rad
        # self.bore = bore
        # self.nut = nut
        pass

    def generate(self):
        # self.set_speed(self.tool.rough_speed)

        block = [self.diameter, self.diameter, self.thickness]
        # self.camtain(RectStock(*block, origin=(-block[0]/2.0, 0, -block[1]/2.0)))

        cx, cy = self.center
        R = self.tool.diameter/2.0
        clearZ = self.thickness + .5
        self.goto(z=clearZ)

        # self.set_speed(self.tool.rough_speed)

        # bore center if required
        c = self.center 
        if self.bore:
            self.camtain(HelicalDrill(tool=self.tool, center=c, z=self.thickness, outer_rad=self.bore/2.0, depth=self.thickness))

        if self.nut:
            self.camtain([
                HelicalDrill(tool=self.tool, center=c, z=self.thickness, outer_rad=self.nut['minor_dia']/2.0*.99, depth=self.thickness, stepdown=2*R),
                Goto(z=clearZ),
                HelicalDrill(tool=self.tool, center=c, z=self.thickness, outer_rad=self.nut['major_dia']/2.0, depth=self.nut['major_length'], stepdown=2*R),
            ])

        # bore circular cutouts on edges
        for div in range(self.divots):
            angle = 360.0/self.divots
            x = cx + self.diameter/2.0*math.sin(math.radians(div*angle))
            y = cy + self.diameter/2.0*math.cos(math.radians(div*angle))

            self.goto(z=clearZ)
            self.camtain(HelicalDrill(tool=self.tool, center=(x, y), z=self.thickness, outer_rad=self.divot_rad, depth=self.thickness, stepdown=2*R, speed=50))

        self.goto(z=clearZ)

        if self.boss_diameter is not None:
            self.goto(z=clearZ)
            self.camtain(
                HSMCirclePocket(
                    tool=tool,
                    center=c,
                    z=self.thickness,
                    inner_rad=self.boss_diameter/2.0,
                    outer_rad=self.diameter/2.0 + R,
                    depth=self.boss_thickness,
                   # clockwise=True,
                    speed=self.tool.rough_speed
                ),
            )

        # cut exterior
        self.goto(z=clearZ)
        self.camtain(HelicalDrill(tool=self.tool, center=c, z=self.thickness, outer_rad=self.diameter/2.0+2*R, depth=self.thickness, speed=100))

        self.goto(z=clearZ)


class KnobGrid(CAM):
    def __init__(
            self, tool, rows=1, cols=1,
            diameter=2.0, boss_diameter=1.0, thickness=.75, boss_thickness=.25,
            divots=7, divot_rad=.25, bore=None, nut=None
    ):
        super(KnobGrid, self).__init__()
        pass
        # self.tool = None
        # self.rows = rows
        # self.cols = cols
        # self._tool = tool
        # self.diameter = diameter
        # self.thickness = thickness
        # self.boss_diameter = boss_diameter
        # self.boss_thickness = boss_thickness
        # self.divots = divots
        # self.divot_rad = divot_rad
        # self.bore = bore
        # self.nut = nut

        # self.set_tool(self._tool)
        # self.set_speed(self.tool.rough_speed)

    def generate(self):
        R = self.tool.diameter/2.0
        clearZ = self.thickness + 0.5

        # first cut holes for rivnuts
        for row in range(self.rows):
            for col in range(self.cols):
                cent = [(col+0.5)*(self.diameter+2*R), (row+0.5)*(self.diameter+2*R)]
                self.goto(z=clearZ)
                c = cent

                if self.nut:
                    self.camtain([
                        HelicalDrill(tool=self.tool, center=c, z=self.thickness, outer_rad=self.nut['minor_dia']/2.0, depth=self.thickness, stepdown=2*R),
                        Goto(z=clearZ),
                        HelicalDrill(tool=self.tool, center=c, z=self.thickness, outer_rad=self.nut['major_dia']/2.0, depth=self.nut['major_length'], stepdown=2*R),
                    ])
                 
                if self.bore:
                    self.camtain([
                        HelicalDrill(tool=self.tool, center=c, z=self.thickness, outer_rad=self.bore/2.0, depth=self.thickness, stepdown=2*R),
                    ])

        self.goto(z=clearZ)
        # self.end_program()
        # self.f.next_part()

        for row in range(self.rows):
            for col in range(self.cols):
                self.goto(z=clearZ)
                cent = [(col+0.5)*(self.diameter+2*R), (row+0.5)*(self.diameter+2*R)]
                self.camtain(Knob(
                    tool=tool, center=cent, diameter=self.diameter,
                    boss_diameter=self.boss_diameter, boss_thickness=self.boss_thickness,
                    thickness=self.thickness, divots=self.divots, divot_rad=self.divot_rad,
                ))


if __name__ == '__main__':
    tool = tools['1/4in spiral upcut']
    Camtainer('test/knob_2.ngc', [
        RectStock(5, 5, 0.688+0.005),
        KnobGrid(
            tool=tool, rows=1, cols=2, diameter=1.5,
            boss_diameter=1.0, boss_thickness=.25,
            thickness=.688+.005, divots=5, divot_rad=tool.diameter*1,
            bore=HoleSize.nuts['rivnut-M5']['minor_dia'],
        )
        ]
    )

    #Camtainer('test/knob_1.ngc', Knob(
    #    tool=tool, center=[0, 0], diameter=1.0,
    #    boss_diameter=0.5, boss_thickness=.125,
    #    thickness=0.5, divots=7, divot_rad=tool.diameter/2.0*1.5,
    #    nut=HoleSize.nuts['rivnut-1/4-20'],
    #))
