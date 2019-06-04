import sys
from openalea.lpy import Lsystem
from openalea.plantgl.all import Tesselator
from yggdrasil.interface.YggInterface import (
    YggInput, YggPlyOutput, YggObjOutput, YggAsciiArrayOutput)
from yggdrasil.serialize.PlySerialize import PlyDict
from yggdrasil.serialize.ObjSerialize import ObjDict


# Parse input
error_code = 0
usage = """Run an LPy model from an lpy input file
  usage: {} FILE [output method]."""
if len(sys.argv) not in [2, 3]:
    print(usage.format(__name__))
fname = sys.argv[1]
if len(sys.argv) == 2:
    out_meth = 'ply'
else:
    out_meth = sys.argv[2]

# Connect to I/O channels
in1 = YggInput('LPy_time')
if out_meth == 'ply':
    out = YggPlyOutput('LPy_mesh')
elif out_meth == 'obj':
    out = YggObjOutput('LPy_mesh')
else:
    out = YggAsciiArrayOutput('LPy_mesh', '%f\t%f\t%f\t%f\t%f\t%f\t%f\t%f\t%f\n')

# Create lsystem & discretizer
lsys = Lsystem(fname)
d = Tesselator()

# Continue looping until no more input times
# TODO: Automated unit conversion
mm_to_cm = 0.1
flag = True
while (flag):

    # Receive next step
    flag, result = in1.recv()
    if not flag:
        print("LPy: End of input.")
        break
    niter = result[0]
    print("LPy: Received request for step %d" % niter)

    # Iterate over tree, rewriting rules
    tree = lsys.axiom
    for i in range(niter):
        tree = lsys.iterate(tree, 1)

    # Discretize the scene
    scene = lsys.sceneInterpretation(tree)
    ply_dict = PlyDict.from_scene(scene, d=d, conversion=mm_to_cm)
    mins, maxs = ply_dict.bounds

    # Send output as just verts in each face
    if out_meth == 'ply':
        flag = out.send(ply_dict)
        nface = ply_dict.nface
    elif out_meth == 'obj':
        obj_dict = ObjDict.from_ply(ply_dict)
        flag = out.send(obj_dict)
        nface = ply_dict.nface
    else:
        mesh = ply_dict.mesh
        flag = out.send(mesh)
        nface = len(mesh)
    if not flag:
        print('LPy: Failed to send mesh.')
        error_code = -1
        break
    print('LPy: Sent mesh with %d faces.' % nface)
    print('LPy: \tmins: %f %f %f' % (mins[0], mins[1], mins[2]))
    print('LPy: \tmaxs: %f %f %f' % (maxs[0], maxs[1], maxs[2]))


print('LPy: Exiting with code %d' % error_code)
sys.exit(error_code)
