import sys
from openalea.lpy import Lsystem
from openalea.plantgl.all import Tesselator
from cis_interface.interface.CisInterface import (
    CisInput, CisAsciiArrayOutput)

# Parse input
error_code = 0
usage = """Run an LPy model from an lpy input file
  usage: {} FILE."""
if len(sys.argv) != 2:
    print(usage.format(__name__))
fname = sys.argv[1]
ply_format = './Output/output_%d.ply'

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
    # vertices = []
    # faces = []
    scene = lsys.sceneInterpretation(tree)
    nind = 0
    nvert = 0
    vert_part = ''
    ind_part = ''
    mesh = []
    for k, shapes in scene.todict().items():
        for shape in shapes:
            d.process(shape)
            c = shape.appearance.ambient
            for p in d.result.pointList:
                # vertices.append((p.x, p.y, p.z, c.red, c.green, c.blue))
                vert_part += "%f %f %f %i %i %i\n" % (
                    p.x, p.y, p.z, c.red, c.green, c.blue)
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
                # faces.append((3, i3[0] + nvert, i3[1] + nvert, i3[2] + nvert))
                ind_part += "3 %i %i %i\n" % (
                    i3[0] + nvert, i3[1] + nvert, i3[2] + nvert)
            nind += len(d.result.indexList)
            nvert += len(d.result.pointList)
            d.clear()

    # Send output as just verts in each face
    flag = out.send(mesh)
    if not flag:
        print('LPy: Failed to send mesh.')
        error_code = -1
        break

    # Write output in ply format
    # TODO: Create ply serializer
    header = """ply
    format ascii 1.0
    comment author Xarthisius
    comment File Generated with PlantGL API
    element vertex {nvert}
    property float x
    property float y
    property float z
    property uchar diffuse_red
    property uchar diffuse_green
    property uchar diffuse_blue
    element face {nind}
    property list uchar int vertex_indices
    end_header
    """
    iply = ply_format % niter
    with open(iply, 'w') as fd:
        fd.write(header.format(nvert=nvert, nind=nind))
        fd.write(vert_part)
        fd.write(ind_part)
    print('LPy: Wrote %s' % iply)


print('LPy: Exiting with code %d' % error_code)
sys.exit(error_code)
