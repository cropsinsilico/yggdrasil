import os
import copy
import warnings
import numpy as np
from yggdrasil import tools
from yggdrasil.metaschema.encoder import encode_json, decode_json
from yggdrasil.metaschema.datatypes import _schema_dir
from yggdrasil.metaschema.datatypes.JSONObjectMetaschemaType import (
    JSONObjectMetaschemaType)


_schema_file = os.path.join(_schema_dir, 'ply.json')
_index_type = ('int', 'uint')
_color_type = ('int', 'uint')
_coord_type = 'float'
_index_fmt = '%d'
_color_fmt = '%d'
_coord_fmt = '%6.4f'
_index_conv = np.int32
_color_conv = np.uint8
_coord_conv = np.float32
_map_ply2py = {'char': 'int8', 'uchar': 'uint8',
               'short': 'int16', 'ushort': 'uint16',
               'int': 'int32', 'uint': 'uint32',
               'float': 'float32', 'double': 'float64'}
_map_py2ply = {v: k for k, v in _map_ply2py.items()}
_default_element_order = ['material', 'vertices', 'faces', 'edges']
_default_property_order = {'vertices': ['x', 'y', 'z', 'red', 'green', 'blue'],
                           'faces': [],
                           'edges': ['vertex1', 'vertex2', 'red', 'green', 'blue']}
# 'materials': ['ambient_red', 'ambient_green',
#               'ambient_blue', 'ambient_coeff',
#               'diffuse_red', 'diffuse_green',
#               'diffuse_blue', 'diffuse_coeff',
#               'specular_red', 'specular_green',
#               'specular_blue', 'specular_coeff',
#               'specular_power']}


def create_schema(overwrite=False):
    r"""Creates a file containing the Ply schema.

    Args:
        overwrite (bool, optional): If True and a file already exists, the
            existing file will be replaced. If False, an error will be raised
            if the file already exists.

    """
    if (not overwrite) and os.path.isfile(_schema_file):
        raise RuntimeError("Schema file already exists.")
    schema = {
        'title': 'ply',
        'description': 'A mapping container for Ply 3D data.',
        'type': 'object',
        'required': ['vertices', 'faces'],
        'definitions': {
            'index': {'type': ('int', 'uint')},
            'color': {'type': ('int', 'uint')},
            'coord': {'type': 'float'},
            'vertex': {
                'description': 'Map describing a single vertex.',
                'type': 'object', 'required': ['x', 'y', 'z'],
                'additionalProperties': False,
                'properties': {'x': {'type': _coord_type},
                               'y': {'type': _coord_type},
                               'z': {'type': _coord_type},
                               'red': {'type': _color_type},
                               'blue': {'type': _color_type},
                               'green': {'type': _color_type}}},
            'face': {
                'description': 'Map describing a single face.',
                'type': 'object', 'required': ['vertex_index'],
                'additionalProperties': False,
                'properties': {
                    'vertex_index': {
                        'type': 'array', 'minItems': 3,
                        'items': {'type': _index_type}}}},
            'edge': {
                'description': 'Vertex indices describing an edge.',
                'type': 'object', 'required': ['vertex1', 'vertex2'],
                'additionalProperties': False,
                'properties': {
                    'vertex1': {'type': _index_type},
                    'vertex2': {'type': _index_type},
                    'red': {'type': _color_type},
                    'green': {'type': _color_type},
                    'blue': {'type': _color_type}}}
            # 'material': {
            #     'description': 'Map of material parameters.',
            #     'type': 'object',
            #     'required': ['ambient_red', 'ambient_green',
            #                  'ambient_blue', 'ambient_coeff',
            #                  'diffuse_red', 'diffuse_green',
            #                  'diffuse_blue', 'diffuse_coeff',
            #                  'specular_red', 'specular_green',
            #                  'specular_blue', 'specular_coeff',
            #                  'specular_power'],
            #     'properties': {'ambient_red': {'type': _color_type},
            #                    'ambient_green': {'type': _color_type},
            #                    'ambient_blue': {'type': _color_type},
            #                    'ambient_coeff': {'type': _coord_type},
            #                    'diffuse_red': {'type': _color_type},
            #                    'diffuse_green': {'type': _color_type},
            #                    'diffuse_blue': {'type': _color_type},
            #                    'diffuse_coeff': {'type': _coord_type},
            #                    'specular_red': {'type': _color_type},
            #                    'specular_green': {'type': _color_type},
            #                    'specular_blue': {'type': _color_type},
            #                    'specular_coeff': {'type': _coord_type},
            #                    'specular_power': {'type': _coord_type}}}},
        },
        'properties': {
            'material': {
                'description': 'Name of the material to use.',
                'type': ['unicode', 'string']},
            # 'materials': {
            #     'description': 'Array of materials.',
            #     'type': 'array', 'items': {'$ref': '#/definitions/material'}},
            'vertices': {
                'description': 'Array of vertices.',
                'type': 'array', 'items': {'$ref': '#/definitions/vertex'}},
            'edges': {
                'description': 'Array of edges.',
                'type': 'array', 'items': {'$ref': '#/definitions/edge'}},
            'faces': {
                'description': 'Array of faces.',
                'type': 'array', 'items': {'$ref': '#/definitions/face'}}},
        'dependencies': {
            'edges': ['vertices'],
            'faces': ['vertices']}}
    with open(_schema_file, 'w') as fd:
        encode_json(schema, fd, indent='\t')


def get_schema():
    r"""Return the Ply schema, initializing it if necessary.

    Returns:
        dict: Ply schema.
    
    """
    if not os.path.isfile(_schema_file):
        create_schema()
    with open(_schema_file, 'r') as fd:
        out = decode_json(fd)
    return out


if not os.path.isfile(_schema_file):  # pragma: debug
    create_schema()
    

def translate_ply2fmt(type_ply):
    r"""Get the corresponding type string for a Ply type string.

    Args:
        type_ply (str): Ply type string.
    
    Returns:
        str: C-style format string.
    
    """
    if type_ply in ['char', 'uchar', 'short', 'ushort', 'int', 'uint']:
        out = '%d '
    elif type_ply in ['float', 'double']:
        out = '%6.4f '
    else:
        raise ValueError("Could not get format string for type '%s'" % type_ply)
    return out


def translate_ply2py(type_ply):
    r"""Get the corresponding Python type for the Ply type string.

    Args:
        type_ply (str): Ply type string.

    Returns:
        type: Python type.

    Raises:
        ValueError: If the type string does not have a match.

    """
    if type_ply not in _map_ply2py:
        raise ValueError("Could not find type for ply type string '%s'." % type_ply)
    return np.dtype(_map_ply2py[type_ply]).type


def translate_py2ply(py_obj):
    r"""Get the correpsonding Ply type string for the provided Python object.

    Args:
        py_obj (object): Python object.

    Returns:
        str: Ply type string.

    """
    type_py = np.array([py_obj]).dtype
    type_np = np.dtype(type_py).name
    if type_np == 'int64':
        warnings.warn("Ply dosn't support long. Precision will be lost.")
        return _map_py2ply['int32']
    if type_np not in _map_py2ply:
        raise ValueError("Could not find ply type string for numpy type '%s'." % type_np)
    return _map_py2ply[type_np]


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

    @classmethod
    def from_dict(cls, in_dict):
        r"""Get a version of the object from a dictionary."""
        out = cls(**in_dict)
        return out

    def as_dict(self):
        r"""Get a version of the object as a pure dictionary."""
        out = dict(**self)
        return out
    
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


def get_key_order(all_keys, default_order):
    r"""Determine the order of keys based on the keys and default order. Keys
    are added first in the default order and then alphabetically.

    Args:
        all_keys (list): List of all keys that should be present in the returned
            list.
        default_order (list): Default order for keys that may or may not be in
            all_keys.

    Returns:
        list: Key order.

    """

    def sort_key(x):
        if x in default_order:
            return str(default_order.index(x))
        else:
            return x

    out = sorted(all_keys, key=sort_key)
    return out

   
# The base class could be anything since it is discarded during registration,
# but is set to JSONObjectMetaschemaType here for transparancy since this is
# what the base class is determined to be on loading the schema
class PlyMetaschemaType(JSONObjectMetaschemaType):
    r"""Ply 3D structure map."""

    _empty_msg = {'vertices': [], 'faces': []}
    python_types = (dict, PlyDict)
    schema_file = _schema_file
    _replaces_existing = False

    @classmethod
    def encode_data(cls, obj, typedef, element_order=None, property_order=None,
                    default_rgb=[0, 0, 0], comments=[], newline='\n',
                    plyformat='ascii 1.0'):
        r"""Encode an object's data.

        Args:
            obj (object): Object to encode.
            typedef (dict): Type definition that should be used to encode the
                object.
            element_order (list, optional): Order that elements should be written
                to the file. If not provided, the order is determined based on
                typical ply files with remaining elements output in sorted order.
            property_order (dict, optional): Dictionary of property order for
                each element determining the order that they properties should
                be written to the file. If not provided, the orders are determined
                based on typical ply files with remaining elements output in sorted
                order.
            default_rgb (list, optional): Default color in RGB that should be
                used for missing colors. Defaults to [0, 0, 0].
            comments (list, optional): List of comments that should be included in
                the file header. Defaults to lines describing the automated origin
                of the file.
            newline (str, optional): String that should be used to delineated end
                of lines. Defaults to '\n'.
            plyformat (str, optional): String describing the ply format and version.
                Defaults to 'ascii 1.0'.

        Returns:
            bytes, str: Serialized message.

        """
        # Add comments to identify generated files
        default_comments = ['author ygg_auto', 'File generated by yggdrasil']
        for c in default_comments:
            if c not in comments:
                comments.append(c)
        # Default order to allow user definited elements
        if element_order is None:
            element_order = get_key_order(obj.keys(), _default_element_order)
        if property_order is None:
            property_order = {}
            for e in element_order:
                if e == 'material':
                    continue
                assert(isinstance(obj[e], (list, tuple)))
                if len(obj[e]) == 0:
                    continue
                property_order[e] = get_key_order(obj[e][0].keys(),
                                                  _default_property_order.get(e, []))
        # Get information needed
        size_map = {}
        type_map = {}
        for e in element_order:
            if e == 'material':
                continue
            assert(isinstance(obj[e], (list, tuple)))
            type_map[e] = {}
            size_map[e] = len(obj[e])
            if size_map[e] == 0:
                continue
            for p in property_order[e]:
                if isinstance(obj[e][0][p], list):
                    subtype = translate_py2ply(obj[e][0][p][0])
                    type_map[e][p] = 'list uchar %s' % subtype
                else:
                    type_map[e][p] = translate_py2ply(obj[e][0][p])
        # Encode header
        header = ['ply', 'format %s' % plyformat]
        header += ['comment ' + c for c in comments]
        for e in element_order:
            if e == 'material':
                header += ['comment material: %s' % obj[e]]
            else:
                e_sing = plural2singular(e)
                header.append('element %s %d' % (e_sing, size_map[e]))
                if size_map[e] > 0:
                    for p in property_order[e]:
                        header.append('property %s %s' % (type_map[e][p], p))
        header.append('end_header')
        # Encode body
        body = []
        for e in element_order:
            if (e not in obj) or (e == 'material'):
                continue
            for x in obj[e]:
                iline = ''
                for p in property_order[e]:
                    if type_map[e][p].startswith('list'):
                        vars = type_map[e][p].split()
                        ientry = x[p]
                        ifmt = translate_ply2fmt(vars[2])
                        iline += translate_ply2fmt(vars[1]) % len(ientry)
                        for ix in ientry:
                            iline += ifmt % ix
                    else:
                        # if p not in x:
                        #     if p in ['red', 'green', 'blue']:
                        #         rgb_index = ['red', 'green', 'blue'].index(p)
                        #         x[p] = default_rgb[rgb_index]
                        iline += translate_ply2fmt(type_map[e][p]) % x[p]
                body.append(iline.strip())  # Ensure trailing spaces are removed
        return newline.join(header + body) + newline
        
    @classmethod
    def encode_data_readable(cls, obj, typedef):
        r"""Encode an object's data in a readable format.

        Args:
            obj (object): Object to encode.
            typedef (dict): Type definition that should be used to encode the
                object.

        Returns:
            string: Encoded object.

        """
        return cls.encode_data(obj, typedef)
    
    @classmethod
    def decode_data(cls, msg, typedef):
        r"""Decode an object.

        Args:
            msg (string): Encoded object to decode.
            typedef (dict): Type definition that should be used to decode the
                object.

        Returns:
            object: Decoded object.

        """
        msg = tools.bytes2str(msg)
        lines = msg.splitlines()
        metadata = {'comments': [], 'element_order': [], 'property_order': {}}
        if lines[0] != 'ply':
            raise ValueError("The first line must be 'ply'")
        # Parse header
        e = None
        p = None
        type_map = {}
        size_map = {}
        obj = {}
        for i, line in enumerate(lines):
            if line.startswith('format'):
                metadata['plyformat'] = line.split(None, 1)[-1]
            elif line.startswith('comment'):
                out = line.split(None, 1)[-1]
                if out.startswith('material:'):
                    metadata['element_order'].append('material')
                    obj['material'] = out.split(None, 1)[-1]
                metadata['comments'].append(out)
            elif line.startswith('element'):
                vars = line.split()
                e_sing = vars[1]
                e = singular2plural(e_sing)
                size_map[e] = int(float(vars[2]))
                type_map[e] = {}
                metadata['element_order'].append(e)
                metadata['property_order'][e] = []
                obj[e] = []
            elif line.startswith('property'):
                vars = line.split()
                p = vars[-1]
                type_map[e][p] = ' '.join(vars[1:-1])
                metadata['property_order'][e].append(p)
            elif 'end_header' in line:
                headline = i + 1
                break
        # Parse body
        i = headline
        for e in metadata['element_order']:
            if e == 'material':
                continue
            for ie in range(size_map[e]):
                vars = lines[i].split()
                iv = 0
                new = {}
                for p in metadata['property_order'][e]:
                    if type_map[e][p].startswith('list'):
                        type_vars = type_map[e][p].split()
                        count_type = translate_ply2py(type_vars[1])
                        plist_type = translate_ply2py(type_vars[2])
                        count = count_type(vars[iv])
                        plist = []
                        iv += 1
                        for ip in range(count):
                            plist.append(plist_type(vars[iv]))
                            iv += 1
                        new[p] = plist
                    else:
                        prop_type = translate_ply2py(type_map[e][p])
                        new[p] = prop_type(vars[iv])
                        iv += 1
                assert(iv == len(vars))
                obj[e].append(new)
                i += 1
        # Check that all properties filled in
        for e in metadata['element_order']:
            if e not in metadata['property_order']:
                continue
            for p in metadata['property_order'][e]:
                assert(len(obj[e]) == size_map[e])
        # Return
        return PlyDict(obj)

    @classmethod
    def updated_fixed_properties(cls, obj):
        r"""Get a version of the fixed properties schema that includes information
        from the object.

        Args:
            obj (object): Object to use to put constraints on the fixed properties
                schema.

        Returns:
            dict: Fixed properties schema with object dependent constraints.

        """
        out = super(PlyMetaschemaType, cls).updated_fixed_properties(obj)
        # Constrain indices on number of elements they refer to
        if isinstance(obj, dict) and ('vertices' in obj):
            nvert = len(obj['vertices'])
            out['definitions']['face']['properties']['vertex_index']['items'][
                'maximum'] = nvert - 1
            for k in ['vertex1', 'vertex2']:
                out['definitions']['edge']['properties'][k][
                    'maximum'] = nvert - 1
        return out


PlyDict._type_class = PlyMetaschemaType
