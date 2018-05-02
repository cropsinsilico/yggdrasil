import sys
import numpy as np
from openalea.lpy import Lsystem
from openalea.plantgl.all import Tesselator
from cis_interface.interface.CisInterface import (
    CisInput, CisAsciiArrayOutput)
from cis_interface.serialize.PlySerialize import PlySerialize

# Parse input
error_code = 0
usage = """Run an LPy model from an lpy input file
  usage: {} FILE."""
if len(sys.argv) != 2:
    print(usage.format(__name__))
fname = sys.argv[1]
ply_format = './Output/output_%d.ply'
sply = PlySerialize()

# Connect to I/O channels
in1 = CisInput('LPy_time')
out = CisAsciiArrayOutput('LPy_mesh', '%f\t%f\t%f\t%f\t%f\t%f\t%f\t%f\t%f\n')

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
    ply_dict = dict(vertices=[], vertex_colors=[], faces=[])
    mesh = []
    mins = 1e6 * np.ones(3, 'float')
    maxs = -1e6 * np.ones(3, 'float')
    nvert = 0
    for k, shapes in scene.todict().items():
        for shape in shapes:
            d.process(shape)
            if d.result is None:
                continue
            c = shape.appearance.ambient
            for p in d.result.pointList:
                ply_dict['vertices'].append([mm_to_cm * p.x,
                                             mm_to_cm * p.z,
                                             mm_to_cm * p.y])
                ply_dict['vertex_colors'].append([c.red, c.green, c.blue])
            for i3 in d.result.indexList:
                imesh = []
                for i in range(3):
                    _i3 = i3[i]
                    # if _i3 == len(d.result.pointList):
                    #     # TODO: sometimes the index is equal to the length of
                    #     # the points list. Should this be some special vertex?
                    #     # _i3 = 0
                    #     print(_i3, len(d.result.pointList))
                    #     imesh = []
                    #     break
                    _iv3 = d.result.pointList[_i3]
                    _iv3_cm = [mm_to_cm * _iv3.x, mm_to_cm * _iv3.z, mm_to_cm * _iv3.y]
                    imesh += _iv3_cm
                    mins = np.minimum(mins, np.array(_iv3_cm))
                    maxs = np.maximum(maxs, np.array(_iv3_cm))
                if imesh:
                    mesh.append(imesh)
                ply_dict['faces'].append([i3[0] + nvert, i3[1] + nvert, i3[2] + nvert])
            nvert += len(d.result.pointList)
            # Clear descretizer to ensure no hold over verts/faces
            d.clear()

    # Send output as just verts in each face
    flag = out.send(mesh)
    if not flag:
        print('LPy: Failed to send mesh.')
        error_code = -1
        break
    print('LPy: Sent mesh with %d triangles.' % len(mesh))
    print('LPy: \tmins: %f %f %f' % (mins[0], mins[1], mins[2]))
    print('LPy: \tmaxs: %f %f %f' % (maxs[0], maxs[1], maxs[2]))

    # Write output in ply format
    iply = ply_format % niter
    with open(iply, 'wb') as fd:
        fd.write(sply.serialize(ply_dict))
    print('LPy: Wrote %s' % iply)


print('LPy: Exiting with code %d' % error_code)
sys.exit(error_code)
