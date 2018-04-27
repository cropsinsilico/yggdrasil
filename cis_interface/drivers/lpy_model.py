import sys
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
    for k, shapes in scene.todict().items():
        for shape in shapes:
            d.process(shape)
            c = shape.appearance.ambient
            for p in d.result.pointList:
                ply_dict['vertices'].append([p.x, p.y, p.z])
                ply_dict['vertex_colors'].append([c.red, c.green, c.blue])
            for i3 in d.result.indexList:
                imesh = []
                for i in range(3):
                    _i3 = i3[i]
                    if _i3 == len(d.result.pointList):
                        # TODO: sometimes the index is equal to the length of
                        # the points list. Should this be some special vertex?
                        # print(_i3, len(d.result.pointList))
                        _i3 = 0
                    _iv3 = d.result.pointList[_i3]
                    imesh += [_iv3.x, _iv3.y, _iv3.z]
                if imesh:
                    mesh.append(imesh)
                nvert = len(ply_dict['vertices'])
                ply_dict['faces'].append([i3[0] + nvert, i3[1] + nvert, i3[2] + nvert])
            # Clear descretizer to ensure no hold over verts/faces
            d.clear()

    # Send output as just verts in each face
    flag = out.send(mesh)
    if not flag:
        print('LPy: Failed to send mesh.')
        error_code = -1
        break

    # Write output in ply format
    iply = ply_format % niter
    with open(iply, 'wb') as fd:
        fd.write(sply.serialize(ply_dict))
    print('LPy: Wrote %s' % iply)


print('LPy: Exiting with code %d' % error_code)
sys.exit(error_code)
