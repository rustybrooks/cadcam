from campy import *

tool=tools['1/4in spiral upcut']

tap_diam=7/16.
outter_diam = 5.75
groove_diam = 4.85
groove_depth=1/8.
thickness=.51

stepdown=(tool.diameter/4.)
print "stepdown=", stepdown

f = open("eric.ngc", "w")
f.write("%\n")
f.write("G17 G20 G40 G90\n")

#g = CirclePocket(tool, (0, 0, 0), 0, tap_diam/2., thickness, stepdown=stepdown, stepover=0.1)
#g.generate(f)

f.write("G0 Z0.25\n")

g = CircleProfile(tool, (0, 0, 0), .09375, thickness, side="center", stepdown=stepdown)
g.generate(f)

#g = CircleProfile(tool, (3, 3, 0), groove_diam/2., groove_depth, side="center", stepdown=stepdown)
#g.generate(f)

#g = CircleProfile(tool, (3, 3, 0), outter_diam/2., thickness, side="inner", stepdown=stepdown)
#g.generate(f)

g.end_program()
f.close()



