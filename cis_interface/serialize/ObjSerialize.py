import copy
from cis_interface import backwards
from cis_interface.serialize.PlySerialize import PlyDict, PlySerialize


class ObjDict(PlyDict):
    r"""Class for storing obj information.

    Args:
        vertices (list, optional): 3D positions of vertices comprising the
            3D object. Defaults to [].
        faces (list, optional): Indices of 3 or more vertices making up faces
            or a tuple containing the indices for the position, texture
            coordinate, and normal for each vertex in the face. This
            information can also be provided in their own lists, but
            there must be an entry for every face. Defaults to [].
        vertex_colors (list, optional): RGB values for each of the vertices.
            If not provided, all vertices will be black. Defaults to [].
        material (str, optional): Material to use for faces. Defaults to None.
        normals (list, optional): 3D normals for vertices. Defaults to [].
        texcoords (list, optional): 3D texture coordinates for vertices.
            Defaults to [].
        face_texcoords (list, optional): Indices of texture coordinates for each
            vertex in the face. Entries of None are ignored. Defaults to [].
        face_normals (list, optional): Indices of normals for each vertex in the
            face. Entries of None are ignored. Defaults to [].

    """
    def __init__(self, **kwargs):
        list_keys = ['vertices', 'faces', 'vertex_colors',
                     'normals', 'texcoords', 'face_texcoords', 'face_normals']
        for k in list_keys:
            if kwargs.get(k, None) is None:
                kwargs.setdefault(k, [])
        kwargs.setdefault('material', None)
        super(ObjDict, self).__init__(**kwargs)
        self.update(**self.standardize())

    def standardize(self, no_copy=False):
        r"""Put the dictionary in the standard format with face information
        split into separate fields.

        Args:
            no_copy (bool, optional): If True, the current dictionary will be
                updated. Otherwise a copy will be returned. Defaults to False.
               
        Returns:
            ObjDict: Standardized obj information.

        """
        if no_copy:
            out = self
        else:
            out = copy.deepcopy(self)
        # Convert face tuples to lists
        face_keys = {'faces': 0, 'face_texcoords': 1, 'face_normals': 2}
        for k in ['face_texcoords', 'face_normals']:
            if not out.get(k, []):
                out[k] = [[None for v in f] for f in self['faces']]
        for i, f in enumerate(self['faces']):
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

    @classmethod
    def from_shape(cls, shape, d, conversion=1.0):
        r"""Create a ply dictionary from a PlantGL shape and descritizer.

        Args:
            scene (openalea.plantgl.scene): Scene that should be descritized.
            d (openalea.plantgl.descritizer): Descritizer.
            conversion (float, optional): Conversion factor that should be
                applied to the vertex positions. Defaults to 1.0.

        """
        iobj = super(ObjDict, cls).from_shape(shape, d, conversion=conversion)
        if iobj is not None:
            # Texcoords
            if d.result.texCoordList:
                for t in d.result.texCoordList:
                    # TODO: Should the coords be scaled?
                    iobj['texcoords'].append([t.x, t.y])
                if d.result.texCoordIndexList:
                    for t in d.result.texCoordIndexList:
                        if t[0] < len(iobj['texcoords']):
                            iobj['face_texcoords'].append([t[0], t[1], t[2]])
                        else:
                            iobj['face_texcoords'].append([None, None, None])
            # Normals
            if d.result.normalList:
                for n in d.result.normalList:
                    iobj['normals'].append([n.x, n.y, n.z])
                if d.result.texCoordIndexList:
                    for n in d.result.texCoordIndexList:
                        if n[0] < len(iobj['normals']):
                            iobj['face_normals'].append([n[0], n[1], n[2]])
                        else:
                            iobj['face_normals'].append([None, None, None])
        return iobj

    def to_geom_args(self, conversion=1.0, name=None):
        r"""Get arguments for creating a PlantGL geometry.

        Args:
            conversion (float, optional): Conversion factor that should be
                applied to the vertices. Defaults to 1.0.
            name (str, optional): Name that should be given to the created
                PlantGL symbol. Defaults to None and is ignored.

        Returns:
            tuple: Class, arguments and keyword arguments for PlantGL geometry.

        """
        import openalea.plantgl.all as pgl
        smb_class, args, kwargs = super(ObjDict, self).to_geom_args(
            conversion=conversion, name=name)
        index_class = pgl.Index3
        array_class = pgl.Index3Array
        # Texture coords
        if self.get('texcoords', []):
            obj_texcoords = []
            for t in self['texcoords']:
                obj_texcoords.append(pgl.Vector2(t[0], t[1]))
            kwargs['texCoordList'] = pgl.Point2Array(obj_texcoords)
            if self.get('face_texcoords', []):
                obj_ftexcoords = []
                for t in self['face_texcoords']:
                    if (t is not None) and (t[0] is not None):
                        entry = [int(_t) for _t in t]
                    else:
                        entry = [len(self['texcoords']) for _ in range(3)]
                    obj_ftexcoords.append(index_class(*entry))
                kwargs['texCoordIndexList'] = array_class(obj_ftexcoords)
        # Normals
        if self.get('normals', []):
            obj_normals = []
            for n in self['normals']:
                obj_normals.append(pgl.Vector3(n[0], n[1], n[2]))
            kwargs['normalList'] = pgl.Point3Array(obj_normals)
            if self.get('face_normals', []):
                obj_fnormals = []
                for n in self['face_normals']:
                    if (n is not None) and (n[0] is not None):
                        entry = [int(_n) for _n in n]
                    else:
                        entry = [len(self['normals']) for _ in range(3)]
                    obj_fnormals.append(index_class(*entry))
                kwargs['normalIndexList'] = array_class(obj_fnormals)
        return smb_class, args, kwargs

    def append(self, solf, default_rgb=None):
        r"""Append new ply information to this dictionary.

        Args:
            solf (ObjDict): Another ply to append to this one.
            default_rgb (list, optional): Default color in RGB that should be
                used for missing colors. Defaults to [0, 0, 0].

        """
        super(ObjDict, self).append(solf, default_rgb=default_rgb)
        # Merge material using first in list
        material = None
        for x in [self, solf]:
            if x['material'] is not None:
                material = x['material']
                break
        self['material'] = material
        # Merge vertex things
        for k in ['normals', 'texcoords']:
            fk = 'face_' + k
            nprev = len(self[k])
            self[k] += solf[k]
            for f in solf[fk]:
                fnew = []
                for v in f:
                    if v is None:
                        fnew.append(v)
                    else:
                        fnew.append(v + nprev)
                self[fk].append(fnew)
        return self


class ObjSerialize(PlySerialize):
    r"""Class for serializing/deserializing .obj file formats. Reader
    adapted from https://www.pygame.org/wiki/OBJFileLoader."""

    @property
    def serializer_type(self):
        r"""int: Type of serializer."""
        return 9

    def func_serialize(self, args, zero_indexed=True):
        r"""Serialize a message.

        Args:
            args (ObjDict): Dictionary of obj information.
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
        if isinstance(args, dict):
            args = ObjDict(**args)
        sargs = args.standardize()
        # Header
        if self.write_header:
            lines += ['# Author cis_auto',
                      '# Generated by cis_interface', '']
        if sargs.get('material', None) is not None:
            lines.append('usemtl %s' % sargs['material'])
        if 'vertices' in sargs:
            if not sargs.get('vertex_colors', []):
                for v in sargs['vertices']:
                    lines.append('v %6.4f %6.4f %6.4f' % tuple(v))
            else:
                for i in range(len(sargs['vertices'])):
                    line = 'v'
                    line += ' %6.4f %6.4f %6.4f' % tuple(sargs['vertices'][i])
                    line += ' %d %d %d' % tuple(sargs['vertex_colors'][i])
                    lines.append(line)
        for v in sargs['normals']:
            lines.append('vn %6.4f %6.4f %6.4f' % tuple(v))
        for v in sargs['texcoords']:
            lines.append('vt %6.4f %6.4f' % tuple(v))
        # Faces
        add_ind = 0
        if zero_indexed:
            add_ind = 1
        for i in range(sargs.nface):
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
        out = self.newline.join(lines) + self.newline
        return backwards.unicode2bytes(out)

    def func_deserialize(self, msg, zero_indexed=True):
        r"""Deserialize a message.

        Args:
            msg (str, bytes): Message to be deserialized.
            zero_indexed (bool, optional): If True, the parsed indices are adjusted
                to start at zero. If False, the indices will not be adjusted and
                will start at one as per .obj format. Defaults to True.

        Returns:
            ObjDict: Deserialized .obj information. The faces are zero indexed.

        """
        if len(msg) == 0:
            out = self.empty_msg
        else:
            lines = backwards.bytes2unicode(msg).split(self.newline)
            out = ObjDict()
            nvert = 0
            for line in lines:
                if line.startswith('#'):
                    continue
                values = line.split()
                if not values:
                    continue
                if values[0] == 'v':
                    out['vertices'].append([x for x in map(float, values[1:4])])
                    iclr = self.default_rgb
                    if len(values) == 7:
                        if not out['vertex_colors']:
                            out['vertex_colors'] = [self.default_rgb for
                                                    _ in range(nvert)]
                        iclr = [x for x in map(int, values[4:7])]
                    if out['vertex_colors']:
                        out['vertex_colors'].append(iclr)
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
            out.standardize(no_copy=True)
        return out
