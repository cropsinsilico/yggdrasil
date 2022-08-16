import copy
import numpy as np
from yggdrasil import constants
from yggdrasil.serialize.SerializeBase import SerializeBase
try:
    import trimesh
except ImportError:
    trimesh = None


def singular2plural(e_sing):
    r"""Get the plural version of a singular element name. If the singular
    version ends with the suffix 'ex' it is replaced with the plural suffix
    'ices'. Otherwise, an 's' is appended to the singular name to make it
    plural.

    Args:
        e_sing (str): Singular version of an element name.

    Returns:
        str: Plural version of the singular element name e_sing.

    """
    if e_sing.endswith('ex'):
        e_plur = e_sing.rsplit('ex', 1)[0]
        e_plur += 'ices'
    else:
        e_plur = e_sing + 's'
    return e_plur


def plural2singular(e_plur):
    r"""Get the singular version of a plural element name. If the plural version
    ends with the suffix 'ices', it is replaced with the singular suffix 'ex'.
    If the plural version ends with an 's', it is removed.

    Args:
        e_plur (str): Plural version of an element name.

    Returns:
        str: Singular version of the plural element name e_plur.

    Raises:
        ValueError: If a singular version cannot be determined.

    """
    if e_plur.endswith('ices'):
        e_sing = e_plur.rsplit('ices', 1)[0]
        e_sing += 'ex'
    elif e_plur.endswith('s'):
        e_sing = e_plur[:-1]
    else:
        raise ValueError("Cannot determine singular version of '%s'." % e_plur)
    return e_sing


class PlyDict(dict):
    r"""Enhanced dictionary class for storing Ply information."""

    def __init__(self, *args, **kwargs):
        super(PlyDict, self).__init__(*args, **kwargs)
        self.setdefault('vertices', [])
        self.setdefault('faces', [])
        self._type_class.validate(self)

    def convert_arrays(self):
        r"""Check fields and convert arrays to nested structures."""

    @classmethod
    def from_dict(cls, in_dict):
        r"""Get a version of the object from a dictionary."""
        out = cls(**in_dict)
        return out

    def as_dict(self):
        r"""Get a version of the object as a pure dictionary."""
        out = dict(**self)
        return out

    @classmethod
    def from_array_dict(cls, in_dict):
        r"""Get a version of the object from a dictionary of arrays."""
        kws = {}
        for k in ['material', 'vertices', 'edges', 'faces']:
            if k in in_dict:
                kws[k] = copy.deepcopy(in_dict[k])
        if isinstance(kws.get('vertices', None), np.ndarray):
            old_vert = kws.pop('vertices')
            assert(old_vert.shape[1] == 3)
            kws['vertices'] = [
                {k: old_vert[i, j] for j, k in enumerate('xyz')}
                for i in range(old_vert.shape[0])]
        if isinstance(in_dict.get('vertex_colors', None), np.ndarray):
            old_colr = in_dict['vertex_colors']
            assert(old_colr.shape == (len(kws['vertices']), 3))
            for i in range(old_colr.shape[0]):
                for j, k in enumerate(['red', 'green', 'blue']):
                    if not np.isnan(old_colr[i, j]):
                        kws['vertices'][i][k] = np.int32(old_colr[i, j])
        if isinstance(kws.get('edges', None), np.ndarray):
            old_edge = kws.pop('edges')
            assert(old_edge.shape[1] == 2)
            kws['edges'] = [
                {k: np.int32(old_edge[i, j]) for j, k
                 in enumerate(['vertex1', 'vertex2'])}
                for i in range(old_edge.shape[0])]
        if isinstance(in_dict.get('edge_colors', None), np.ndarray):
            old_colr = in_dict['edge_colors']
            assert(old_colr.shape == (len(kws['edges']), 3))
            for i in range(old_colr.shape[0]):
                for j, k in enumerate(['red', 'green', 'blue']):
                    if not np.isnan(old_colr[i, j]):
                        kws['edges'][i][k] = np.int32(old_colr[i, j])
        if isinstance(kws.get('faces', None), np.ndarray):
            old_face = kws.pop('faces')
            assert(old_face.shape[1] >= 3)
            kws['faces'] = [
                {'vertex_index': [
                    np.int32(old_face[i, j]) for j
                    in range(old_face.shape[1])
                    if (not np.isnan(old_face[i, j]))]}
                for i in range(old_face.shape[0])]
        if isinstance(in_dict.get('face_colors', None), np.ndarray):
            old_colr = in_dict['face_colors']
            assert(old_colr.shape == (len(kws['faces']), 3))
            for i in range(old_colr.shape[0]):
                for j, k in enumerate(['red', 'green', 'blue']):
                    if not np.isnan(old_colr[i, j]):
                        kws['faces'][i][k] = np.int32(old_colr[i, j])
        return cls.from_dict(kws)

    def as_array_dict(self):
        r"""Get a version of the object as a dictionary of arrays."""
        out = {}
        if self.get('material', None):
            out['material'] = self['material']
        if self.get('vertices', None):
            out['vertices'] = np.asarray(
                [[v[k] for k in 'xyz'] for v in self['vertices']])
            out['vertex_colors'] = np.NaN * np.ones(out['vertices'].shape,
                                                    dtype='int32')
            for i, v in enumerate(self['vertices']):
                for j, k in enumerate(['red', 'green', 'blue']):
                    out['vertex_colors'][i, j] = v.get(k, np.NaN)
            if np.all(np.isnan(out['vertex_colors'])):
                out.pop('vertex_colors')
        if self.get('faces', None):
            def fkey(x):
                return len(x['vertex_index'])
            face_shp = (len(self['faces']),
                        len(max(self['faces'], key=fkey)['vertex_index']))
            out['faces'] = np.NaN * np.ones(face_shp, dtype='int32')
            out['face_colors'] = np.NaN * np.ones(
                (face_shp[0], 3), dtype='int32')
            for i, f in enumerate(self['faces']):
                out['faces'][i, :fkey(f)] = f['vertex_index']
                for j, k in enumerate(['red', 'green', 'blue']):
                    out['face_colors'][i, j] = f.get(k, np.NaN)
            if np.all(np.isnan(out['face_colors'])):
                out.pop('face_colors')
        if self.get('edges', None):
            out['edges'] = np.asarray(
                [[v[k] for k in ['vertex1', 'vertex2']]
                 for v in self['edges']])
            out['edge_colors'] = np.NaN * np.ones(
                (out['edges'].shape[0], 3), dtype='int32')
            for i, f in enumerate(self['edges']):
                for j, k in enumerate(['red', 'green', 'blue']):
                    out['edge_colors'][i, j] = f.get(k, np.NaN)
            if np.all(np.isnan(out['edge_colors'])):
                out.pop('edge_colors')
        return out

    @classmethod
    def from_trimesh(cls, in_mesh):
        r"""Get a version of the object from a trimesh class."""
        kws = dict(vertices=in_mesh.vertices,
                   vertex_colors=in_mesh.visual.vertex_colors,
                   faces=in_mesh.faces.astype('int32'))
        kws['vertex_colors'] = kws['vertex_colors'][:, :3]
        return cls.from_array_dict(kws)

    def as_trimesh(self, **kwargs):
        r"""Get a version of the object as a trimesh class."""
        kws0 = self.as_array_dict()
        kws = {'vertices': kws0.get('vertices', None),
               'vertex_colors': kws0.get('vertex_colors', None),
               'faces': kws0.get('faces', None)}
        kws.update(kwargs, process=False)
        return trimesh.base.Trimesh(**kws)
    
    def count_elements(self, element_name):
        r"""Get the count of a certain element in the dictionary.

        Args:
            element_name (str): Name of the element to count.

        Returns:
            int: Number of the provided element.

        """
        if element_name in self:
            return len(self[element_name])
        elif singular2plural(element_name) in self:
            return len(self[singular2plural(element_name)])
        else:
            raise ValueError("'%s' is not a valid property." % element_name)

    @property
    def nvert(self):
        r"""int: Number of vertices."""
        return self.count_elements('vertices')

    @property
    def nface(self):
        r"""int: Number of faces."""
        return self.count_elements('faces')

    @property
    def bounds(self):
        r"""tuple: Mins/maxs of vertices in each dimension."""
        mins = np.empty(3, 'float64')
        maxs = np.empty(3, 'float64')
        for i, x in enumerate('xyz'):
            mins[i] = min([v[x] for v in self['vertices']])
            maxs[i] = max([v[x] for v in self['vertices']])
        return mins, maxs

    @property
    def mesh(self):
        r"""list: Vertices for each face in the structure."""
        mesh = []
        for i in range(self.count_elements('faces')):
            imesh = []
            for f in self['faces']:
                for v in f['vertex_index']:
                    imesh += [self['vertices'][v][k] for k in ['x', 'y', 'z']]
            mesh.append(imesh)
        return mesh

    @classmethod
    def from_shape(cls, shape, d, conversion=1.0, _as_obj=False):  # pragma: lpy
        r"""Create a ply dictionary from a PlantGL shape and descritizer.

        Args:
            scene (openalea.plantgl.scene): Scene that should be descritized.
            d (openalea.plantgl.descritizer): Descritizer.
            conversion (float, optional): Conversion factor that should be
                applied to the vertex positions. Defaults to 1.0.

        """
        out = None
        d.process(shape)
        if d.result is not None:
            out = cls()
            # Vertices
            for p in d.result.pointList:
                new_vert = {}
                for k in ['x', 'y', 'z']:
                    new_vert[k] = conversion * getattr(p, k)
                out['vertices'].append(new_vert)
            # Colors
            if d.result.colorPerVertex and d.result.colorList:
                if d.result.isColorIndexListToDefault():
                    for i, c in enumerate(d.result.colorList):
                        for k in ['red', 'green', 'blue']:
                            out['vertices'][i][k] = getattr(c, k)
                else:  # pragma: debug
                    raise Exception("Indexed vertex colors not supported.")
            # elif not shape.appearance.isAmbientToDefault():
            #     c = shape.appearance.ambient
            #     for k in ['red', 'green', 'blue']:
            #         for v in out['vertices']:
            #             v[k] = getattr(c, k)
            # Material
            if (shape.appearance.name != shape.appearance.DEFAULT_MATERIAL.name):
                out['material'] = shape.appearance.name
            # Faces
            if _as_obj:
                for i3 in d.result.indexList:
                    out['faces'].append([{'vertex_index': i3[j]}
                                         for j in range(len(i3))])
            else:
                for i3 in d.result.indexList:
                    out['faces'].append({'vertex_index': [i3[j] for j in
                                                          range(len(i3))]})
        return out

    @classmethod
    def from_scene(cls, scene, d=None, conversion=1.0):  # pragma: lpy
        r"""Create a ply dictionary from a PlantGL scene and descritizer.

        Args:
            scene (openalea.plantgl.scene): Scene that should be descritized.
            d (openalea.plantgl.descritizer, optional): Descritizer. Defaults
                to openalea.plantgl.all.Tesselator.
            conversion (float, optional): Conversion factor that should be
                applied to the vertex positions. Defaults to 1.0.

        """
        if d is None:
            from openalea.plantgl.all import Tesselator
            d = Tesselator()
        out = cls()
        for k, shapes in scene.todict().items():
            for shape in shapes:
                d.clear()
                iply = cls.from_shape(shape, d, conversion=conversion)
                if iply is not None:
                    out.append(iply)
                d.clear()
        return out

    def to_scene(self, conversion=1.0, name=None):  # pragma: lpy
        r"""Create a PlantGL scene from a Ply dictionary.

        Args:
            conversion (float, optional): Conversion factor that should be
                applied to the vertices. Defaults to 1.0.
            name (str, optional): Name that should be given to the created
                PlantGL symbol. Defaults to None and is ignored.

        Returns:
        

        """
        import openalea.plantgl.all as pgl
        smb_class, args, kwargs = self.to_geom_args(conversion=conversion,
                                                    name=name)
        smb = smb_class(*args, **kwargs)
        if name is not None:
            smb.setName(name)
        if self.get('material', None) is not None:
            mat = pgl.Material(self['material'])
            shp = pgl.Shape(smb, mat)
        else:
            shp = pgl.Shape(smb)
        if name is not None:
            shp.setName(name)
        scn = pgl.Scene([shp])
        return scn

    def to_geom_args(self, conversion=1.0, name=None, _as_obj=False):  # pragma: lpy
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
        kwargs = dict()
        # Add vertices
        obj_points = []
        obj_colors = []
        for v in self['vertices']:
            xarr = conversion * np.array([v[k] for k in ['x', 'y', 'z']])
            obj_points.append(pgl.Vector3(np.float64(xarr[0]),
                                          np.float64(xarr[1]),
                                          np.float64(xarr[2])))
            c = [v.get(k, None) for k in ['red', 'green', 'blue']]
            if None not in c:
                cast_type = int
                obj_colors.append(pgl.Color4(cast_type(c[0]),
                                             cast_type(c[1]),
                                             cast_type(c[2]),
                                             cast_type(1)))
        points = pgl.Point3Array(obj_points)
        if obj_colors:
            colors = pgl.Color4Array(obj_colors)
            kwargs['colorList'] = colors
            kwargs['colorPerVertex'] = True
        # Add indices
        obj_indices = []
        index_class = pgl.Index
        array_class = pgl.IndexArray
        smb_class = pgl.FaceSet
        # index_class = pgl.Index3
        # array_class = pgl.Index3Array
        # smb_class = pgl.TriangleSet
        for f in self['faces']:
            if _as_obj:
                f_int = [int(_f['vertex_index']) for _f in f]
            else:
                f_int = [int(_f) for _f in f['vertex_index']]
            obj_indices.append(index_class(*f_int))
        indices = array_class(obj_indices)
        args = (points, indices)
        return smb_class, args, kwargs

    def append(self, solf):
        r"""Append new ply information to this dictionary.

        Args:
            solf (PlyDict): Another ply to append to this one.

        """
        nvert = self.count_elements('vertices')
        # Vertex fields
        self['vertices'] += solf['vertices']
        # Face fields
        for f in solf['faces']:
            self['faces'].append({'vertex_index': [v + nvert for v in
                                                   f['vertex_index']]})
        # Edge fields
        if 'edges' in solf:
            if 'edges' not in self:
                self['edges'] = []
            for e in solf['edges']:
                iedge = {'vertex1': e['vertex1'] + nvert,
                         'vertex2': e['vertex2'] + nvert}
                for k in ['red', 'green', 'blue']:
                    if k in e:
                        iedge[k] = e[k]
                self['edges'].append(iedge)

    def merge(self, ply_list, no_copy=False):
        r"""Merge a list of ply dictionaries.

        Args:
            ply_list (list): Ply dictionaries.
            no_copy (bool, optional): If True, the current dictionary will be
                updated, otherwise a copy will be returned with the update.
                Defaults to False.

        Returns:
            dict: Merged ply dictionary.

        """
        if not isinstance(ply_list, list):
            ply_list = [ply_list]
        # Merge fields
        if no_copy:
            out = self
        else:
            out = copy.deepcopy(self)
        for x in ply_list:
            out.append(x)
        return out

    def apply_scalar_map(self, scalar_arr, color_map=None,
                         vmin=None, vmax=None, scaling='linear',
                         scale_by_area=False, no_copy=False, _as_obj=False):
        r"""Set the color of faces in a 3D object based on a scalar map.
        This creates a copy unless no_copy is True.

        Args:
            scalar_arr (arr): Scalar values that should be mapped to colors
                for each face.
            color_map (str, optional): The name of the color map that should
                be used. Defaults to 'plasma'.
            vmin (float, optional): Value that should map to the minimum of the
                colormap. Defaults to min(scalar_arr).
            vmax (float, optional): Value that should map to the maximum of the
                colormap. Defaults to max(scalar_arr).
            scaling (str, optional): Scaling that should be used to map the scalar
                array onto the colormap. Defaults to 'linear'.
            scale_by_area (bool, optional): If True, the elements of the scalar
                array will be multiplied by the area of the corresponding face.
                If True, vmin and vmax should be in terms of the scaled array.
                Defaults to False.
            no_copy (bool, optional): If True, the returned object will not be a
                copy. Defaults to False.

        Returns:
            dict: Ply with updated vertex colors.

        """
        from matplotlib import cm
        from matplotlib import colors as mpl_colors
        # Scale by area
        if scale_by_area:
            scalar_arr = copy.deepcopy(scalar_arr)
            for i, f in enumerate(self['faces']):
                if _as_obj:
                    fv = [_f['vertex_index'] for _f in f]
                else:
                    fv = f['vertex_index']
                if len(fv) > 3:
                    raise NotImplementedError("Area calc not implemented "
                                              + "for faces above triangle.")
                v0 = np.array([self['vertices'][fv[0]][k] for k in 'xyz'])
                v1 = np.array([self['vertices'][fv[1]][k] for k in 'xyz'])
                v2 = np.array([self['vertices'][fv[2]][k] for k in 'xyz'])
                a = np.sqrt(np.sum((v0 - v1)**2))
                b = np.sqrt(np.sum((v1 - v2)**2))
                c = np.sqrt(np.sum((v2 - v0)**2))
                s = (a + b + c) / 2.0
                area = np.sqrt(s * (s - a) * (s - b) * (s - c))
                scalar_arr[i] = area * scalar_arr[i]
        # Map vertices onto faces
        vertex_scalar = [[] for x in self['vertices']]
        if _as_obj:
            for i in range(len(self['faces'])):
                for v in self['faces'][i]:
                    vertex_scalar[v['vertex_index']].append(scalar_arr[i])
        else:
            for i in range(len(self['faces'])):
                for v in self['faces'][i]['vertex_index']:
                    vertex_scalar[v].append(scalar_arr[i])
        for i in range(len(vertex_scalar)):
            if len(vertex_scalar[i]) == 0:
                vertex_scalar[i] = 0
            else:
                vertex_scalar[i] = np.mean(vertex_scalar[i])
        vertex_scalar = np.array(vertex_scalar)
        if scaling == 'log':
            vertex_scalar = np.ma.MaskedArray(vertex_scalar, vertex_scalar <= 0)
        # Get color scaling
        if color_map is None:
            # color_map = 'summer'
            color_map = 'plasma'
        if vmin is None:
            vmin = vertex_scalar.min()
        if vmax is None:
            vmax = vertex_scalar.max()
        cmap = cm.get_cmap(color_map)
        if scaling == 'log':
            norm = mpl_colors.LogNorm(vmin=vmin, vmax=vmax)
        elif scaling == 'linear':
            norm = mpl_colors.Normalize(vmin=vmin, vmax=vmax)
        else:  # pragma: debug
            raise Exception("Scaling must be 'linear' or 'log'.")
        m = cm.ScalarMappable(norm=norm, cmap=cmap)
        # Scale colors
        vertex_colors = (255 * m.to_rgba(vertex_scalar)).astype('int')[:, :3].tolist()
        if no_copy:
            out = self
        else:
            out = copy.deepcopy(self)
        for i, c in enumerate(vertex_colors):
            for j, k in enumerate(['red', 'green', 'blue']):
                out['vertices'][i][k] = c[j]
        return out


class PlySerialize(SerializeBase):
    r"""Class for serializing/deserializing .ply file formats.

    Args:
        write_header (bool, optional): If True, headers will be added to
            serialized output. Defaults to True.
        newline (str, optional): String that should be used for new lines.
            Defaults to '\n'.

    Attributes:
        write_header (bool): If True, headers will be added to serialized
            output.
        newline (str): String that should be used for new lines.
        default_rgb (list): Default color in RGB that should be used for
            missing colors.

    """
    
    _seritype = 'ply'
    _schema_subtype_description = ('Serialize 3D structures using Ply format.')
    _schema_properties = {
        'newline': {'type': 'string',
                    'default': constants.DEFAULT_NEWLINE_STR}}
    default_datatype = {'type': 'ply'}
    concats_as_str = False

    def __init__(self, *args, **kwargs):
        r"""Initialize immediately as default is only type."""
        super(PlySerialize, self).__init__(*args, **kwargs)
        self.initialized = True

    def func_serialize(self, args):
        r"""Serialize a message.

        Args:
            args: List of arguments to be formatted or numpy array to be
                serialized.

        Returns:
            bytes: Serialized message.

        """
        return self.datatype.encode_data(args, self.typedef).encode("utf-8")

    def func_deserialize(self, msg):
        r"""Deserialize a message.

        Args:
            msg (bytes): Message to be deserialized.

        Returns:
            obj: Deserialized message.

        """
        return PlyDict(self.datatype.decode_data(msg, self.typedef))

    @classmethod
    def concatenate(cls, objects, **kwargs):
        r"""Concatenate objects to get object that would be recieved if
        the concatenated serialization were deserialized.

        Args:
            objects (list): Objects to be concatenated.
            **kwargs: Additional keyword arguments are ignored.

        Returns:
            list: Set of objects that results from concatenating those provided.

        """
        if len(objects) == 0:
            return []
        total = objects[0]
        for x in objects[1:]:
            total = total.merge(x)
        return [total]
        
    @classmethod
    def get_testing_options(cls):
        r"""Method to return a dictionary of testing options for this class.

        Returns:
            dict: Dictionary of variables to use for testing.

        """
        out = super(PlySerialize, cls).get_testing_options()
        obj = PlyDict({'vertices': [{'x': float(0), 'y': float(0), 'z': float(0)},
                                    {'x': float(0), 'y': float(0), 'z': float(1)},
                                    {'x': float(0), 'y': float(1), 'z': float(1)}],
                       'faces': [{'vertex_index': [int(0), int(1), int(2)]}]})
        out.update(objects=[obj, obj],
                   empty=dict(vertices=[], faces=[]),
                   contents=(b'ply\n'
                             + b'format ascii 1.0\n'
                             + b'comment author ygg_auto\n'
                             + b'comment File generated by yggdrasil\n'
                             + b'element vertex 6\n'
                             + b'property double x\n'
                             + b'property double y\n'
                             + b'property double z\n'
                             + b'element face 2\nproperty list uchar int vertex_index\n'
                             + b'end_header\n'
                             + b'0.0000 0.0000 0.0000\n'
                             + b'0.0000 0.0000 1.0000\n'
                             + b'0.0000 1.0000 1.0000\n'
                             + b'0.0000 0.0000 0.0000\n'
                             + b'0.0000 0.0000 1.0000\n'
                             + b'0.0000 1.0000 1.0000\n'
                             + b'3 0 1 2\n'
                             + b'3 3 4 5\n'))
        out['concatenate'] = [([], [])]
        return out
