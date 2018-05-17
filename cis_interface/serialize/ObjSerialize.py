import copy
import getpass
from cis_interface import backwards
from cis_interface.serialize.PlySerialize import PlySerialize


class ObjSerialize(PlySerialize):
    r"""Class for serializing/deserializing .obj file formats. Reader
    adapted from https://www.pygame.org/wiki/OBJFileLoader."""

    @property
    def serializer_type(self):
        r"""int: Type of serializer."""
        return 9

    def standardize(self, args):
        r"""Put the file in the standard format with face information split
        into separate fields.

        Args:
            args (dict): Dictionary of obj information. Fields include:
                material (str): Material to use for faces.
                vertices (list): 3D vertices comprising the object.
                vertex_colors (list): RGB values for each of the vertices.
                    If not provided, all vertices will be black.
                normals (list): 3D normals for vertices.
                texcoords (list): 3D texture coordinates for vertices.
                faces (list): Indices of 3 or more vertices making up faces or a
                    tuple containing the indices for the position, texture
                    coordinate, and normal for each vertex in the face. This
                    information can also be provided in their own lists, but
                    there must be an entry for every face.
                face_texcoords (list): Indices of texture coordinates for each
                    vertex in the face. Entries of None are ignored.
                face_normals (list): Indices of normals for each vertex in the
                    face. Entries of None are ignored.
               
        Returns:
            dict: Standardized obj information.

        """
        out = copy.deepcopy(args)
        # Convert face tuples to lists
        face_keys = {'faces': 0, 'face_texcoords': 1, 'face_normals': 2}
        for k in ['face_texcoords', 'face_normals']:
            if not out.get(k, []):
                out[k] = [[None for v in f] for f in args['faces']]
        for i, f in enumerate(args['faces']):
            for k in ['face_texcoords', 'face_normals']:
                if out[k][i] is None:
                    out[k][i] = [None for v in f]
            for j, v in enumerate(f):
                if issubclass(v.__class__, (int, float)):
                    out['faces'][i][j] = v
                else:
                    for k, kindex in face_keys.items():
                        out[k][i][j] = v[kindex]
        return out

    def func_serialize(self, args, zero_indexed=True):
        r"""Serialize a message.

        Args:
            args (dict): Dictionary of obj information. Fields include:
                material (str): Material to use for faces.
                vertices (list): 3D vertices comprising the object.
                vertex_colors (list): RGB values for each of the vertices.
                    If not provided, all vertices will be black.
                normals (list): 3D normals for vertices.
                texcoords (list): 3D texture coordinates for vertices.
                faces (list): Indices of 3 or more vertices making up faces or a
                    tuple containing the indices for the position, texture
                    coordinate, and normal for each vertex in the face. This
                    information can also be provided in their own lists, but
                    there must be an entry for every face.
                face_texcoords (list): Indices of texture coordinates for each
                    vertex in the face. Entries of None are ignored.
                face_normals (list): Indices of normals for each vertex in the
                    face. Entries of None are ignored.
            zero_indexed (bool, optional): If True, the input indices are assumed
                to start at zero and they will be adjusted to start at one and
                conform with .obj format. If False, the input indices are assumed
                to start at one and they will not be adjusted. Defaults to True.
               
        Returns:
            bytes, str: Serialized message.

        """
        lines = []
        fkey_order = ['faces', 'face_texcoords', 'face_normals']
        # Standardize
        sargs = self.standardize(args)
        # Header
        if self.write_header:
            lines += ['# Author %s' % getpass.getuser(),
                      '# Generated by cis_interface', '']
        if sargs.get('material', None) is not None:
            lines.append('usemtl %s' % sargs['material'])
        if 'vertices' in sargs:
            if not sargs.get('vertex_colors', []):
                for v in sargs['vertices']:
                    lines.append('v %f %f %f' % tuple(v))
            else:
                for i in range(len(sargs['vertices'])):
                    line = 'v'
                    line += ' %f %f %f' % tuple(sargs['vertices'][i])
                    line += ' %d %d %d' % tuple(sargs['vertex_colors'][i])
                    lines.append(line)
        if 'normals' in sargs:
            for v in sargs['normals']:
                lines.append('vn %f %f %f' % tuple(v))
        if 'texcoords' in sargs:
            for v in sargs['texcoords']:
                lines.append('vt %f %f' % tuple(v))
        if 'faces' in sargs:
            add_ind = 0
            if zero_indexed:
                add_ind = 1
            for i in range(len(sargs['faces'])):
                iline = 'f'
                for j in range(len(sargs['faces'][i])):
                    v = [sargs[k][i][j] for k in fkey_order]
                    iline += ' %d/' % (v[0] + add_ind)
                    if v[1] is not None:
                        iline += '%d' % (v[1] + add_ind)
                    iline += '/'
                    if v[2] is not None:
                        iline += '%d' % (v[2] + add_ind)
                lines.append(iline)
        out = self.newline.join(lines)
        return backwards.unicode2bytes(out)

    def func_deserialize(self, msg, zero_indexed=True):
        r"""Deserialize a message.

        Args:
            msg (str, bytes): Message to be deserialized.
            zero_indexed (bool, optional): If True, the parsed indices are adjusted
                to start at zero. If False, the indices will not be adjusted and
                will start at one as per .obj format. Defaults to True.

        Returns:
            dict: Deserialized .obj information. The faces are zero indexed.

        """
        if len(msg) == 0:
            out = self.empty_msg
        else:
            lines = backwards.bytes2unicode(msg).split(self.newline)
            out = dict(vertices=[], material=None, normals=[], texcoords=[],
                       faces=[], face_texcoords=[], face_normals=[])
            nvert = 0
            for line in lines:
                if line.startswith('#'):
                    continue
                values = line.split()
                if not values:
                    continue
                if values[0] == 'v':
                    out['vertices'].append([x for x in map(float, values[1:4])])
                    if len(values) == 7:
                        if 'vertex_colors' not in out:
                            out['vertex_colors'] = [self.default_rgb for
                                                    _ in range(nvert)]
                        out['vertex_colors'].append([x for x in map(int, values[4:7])])
                    else:
                        if 'vertex_colors' in out:
                            out['vertex_colors'].append(self.default_rgb)
                    nvert += 1
                elif values[0] == 'vn':
                    out['normals'].append([x for x in map(float, values[1:4])])
                elif values[0] == 'vt':
                    out['texcoords'].append([x for x in map(float, values[1:3])])
                elif values[0] in ('usemtl', 'usemat'):
                    out['material'] = values[1]
                elif values[0] == 'f':
                    sub_ind = 0
                    if zero_indexed:
                        sub_ind = 1
                    face = []
                    texcoords = []
                    norms = []
                    for v in values[1:]:
                        w = v.split('/')
                        face.append(int(w[0]) - sub_ind)
                        itexc = None
                        inorm = None
                        if len(w) >= 2 and len(w[1]) > 0:
                            itexc = int(w[1]) - sub_ind
                        texcoords.append(itexc)
                        if len(w) >= 3 and len(w[2]) > 0:
                            inorm = int(w[2]) - sub_ind
                        norms.append(inorm)
                    out['faces'].append(face)
                    out['face_texcoords'].append(texcoords)
                    out['face_normals'].append(norms)
                    for x in out['faces'][-1]:
                        assert(x <= (len(out['vertices']) - sub_ind))
        return out

    def merge(self, obj_list):
        r"""Merge a list of obj dictionaries.

        Args:
            obj_list (list): Obj dictionaries.

        Returns:
            dict: Merged obj dictionary.

        """
        sobj_list = [self.standardize(x) for x in obj_list]
        out = super(ObjSerialize, self).merge(sobj_list)
        # Merge material using first in list
        material = None
        for x in sobj_list:
            if x.get('material', None) is not None:
                material = x['material']
                break
        out['material'] = material
        # Merge vertex things
        for k in ['normals', 'texcoords']:
            fk = 'face_' + k
            out[k] = []
            out[fk] = []
            nprev = 0
            for x in sobj_list:
                if k not in x:
                    continue
                out[k] += x[k]
                if fk in x:
                    for f in x[fk]:
                        fnew = []
                        for v in f:
                            if v is None:
                                fnew.append(v)
                            else:
                                fnew.append(v + nprev)
                        out[fk].append(fnew)
                nprev += len(x[k])
        return out
