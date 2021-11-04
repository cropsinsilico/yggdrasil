import os
import copy
import numpy as np
import warnings
from yggdrasil import tools
from yggdrasil.metaschema.encoder import encode_json, decode_json
from yggdrasil.metaschema.datatypes import _schema_dir
from yggdrasil.metaschema.datatypes.JSONObjectMetaschemaType import (
    JSONObjectMetaschemaType)
from yggdrasil.metaschema.datatypes.PlyMetaschemaType import (
    trimesh, PlyDict,
    _index_type, _color_type, _coord_type,
    _index_conv, _color_conv, _coord_conv,
    _index_fmt, _color_fmt, _coord_fmt)


# TODO: Add support for groups
    

_schema_file = os.path.join(_schema_dir, 'obj.json')
_default_element_order = ['material', 'vertices', 'params', 'normals', 'texcoords',
                          'points', 'lines', 'faces', 'curves', 'curve2Ds', 'surfaces']
# TODO: Unclear what standard puts colors after coords and how that is
# reconciled with the weight (i.e. do colors go before or after weight)
_default_property_order = {
    'vertices': ['x', 'y', 'z', 'red', 'green', 'blue', 'w'],
    'params': ['u', 'v', 'w'],
    'normals': ['i', 'j', 'k'],
    'texcoords': ['u', 'v', 'w'],
    'points': 'vertex_indices',
    'lines': ('vertex_index', 'texcoord_index'),
    'faces': ('vertex_index', 'texcoord_index', 'normal_index'),
    'curves': ['starting_param', 'ending_param', ['vertex_indices']],
    'curve2Ds': 'param_indices',
    'surfaces': ['starting_param_u', 'ending_param_u',
                 'starting_param_v', 'ending_param_v',
                 {'vertex_indices': ('vertex_index', 'texcoord_index', 'normal_index')}]}
_index_properties = ['vertex_indices', 'vertex_index', 'texcoord_index',
                     'normal_index', 'param_indices']
_default_property_formats = {}
_default_property_converters = {}
for k in ['x', 'y', 'z', 'u', 'v', 'w', 'i', 'j', 'k',
          'starting_param', 'ending_param',
          'starting_param_u', 'ending_param_u',
          'starting_param_v', 'ending_param_v']:
    _default_property_formats[k] = _coord_fmt
    _default_property_converters[k] = _coord_conv
for k in ['red', 'green', 'blue']:
    _default_property_formats[k] = _color_fmt
    _default_property_converters[k] = _color_conv
for k in ['vertex_index', 'texcoord_index', 'normal_index', 'param_index',
          'vertex_indices', 'param_indices']:
    _default_property_formats[k] = _index_fmt
    _default_property_converters[k] = _index_conv
_map_element2code = {'material': 'usemtl', 'vertices': 'v',
                     'params': 'vp', 'normals': 'vn', 'texcoords': 'vt',
                     'points': 'p', 'lines': 'l', 'faces': 'f',
                     'curves': 'curv', 'curve2Ds': 'curv2', 'surfaces': 'surf'}
_map_code2element = {v: k for k, v in _map_element2code.items()}


def create_schema(overwrite=False):
    r"""Creates a file containing the Obj schema.

    Args:
        overwrite (bool, optional): If True and a file already exists, the
            existing file will be replaced. If False, an error will be raised
            if the file already exists.

    """
    if (not overwrite) and os.path.isfile(_schema_file):
        raise RuntimeError("Schema file already exists.")
    schema = {
        'title': 'obj',
        'description': 'A mapping container for Obj 3D data.',
        'type': 'object',
        'required': ['vertices', 'faces'],
        'definitions': {
            'vertex': {
                'description': 'Map describing a single vertex.',
                'type': 'object', 'required': ['x', 'y', 'z'],
                'additionalProperties': False,
                'properties': {'x': {'type': _coord_type},
                               'y': {'type': _coord_type},
                               'z': {'type': _coord_type},
                               'red': {'type': _color_type},
                               'blue': {'type': _color_type},
                               'green': {'type': _color_type},
                               'w': {'type': _coord_type, 'default': 1.0}}},
            'param': {
                'description': 'Map describing a single parameter space point.',
                'type': 'object', 'required': ['u', 'v'],
                'additionalProperties': False,
                'properties': {'u': {'type': _coord_type},
                               'v': {'type': _coord_type},
                               'w': {'type': _coord_type, 'default': 1.0}}},
            'normal': {
                'description': 'Map describing a single normal.',
                'type': 'object', 'required': ['i', 'j', 'k'],
                'additionalProperties': False,
                'properties': {'i': {'type': _coord_type},
                               'j': {'type': _coord_type},
                               'k': {'type': _coord_type}}},
            'texcoord': {
                'description': 'Map describing a single texture vertex.',
                'type': 'object', 'required': ['u'],
                'additionalProperties': False,
                'properties': {'u': {'type': _coord_type},
                               'v': {'type': _coord_type, 'default': 0.0},
                               'w': {'type': _coord_type, 'default': 0.0}}},
            'point': {
                'description': 'Array of vertex indices describing a set of points.',
                'type': 'array', 'minItems': 1,
                'items': {'type': _index_type}},
            'line': {
                'description': ('Array of vertex indices and texture indices '
                                + 'describing a line.'),
                'type': 'array', 'minItems': 2,
                'items': {'type': 'object', 'required': ['vertex_index'],
                          'additionalProperties': False,
                          'properties':
                              {'vertex_index': {'type': _index_type},
                               'texcoord_index': {'type': _index_type}}}},
            'face': {
                'description': ('Array of vertex, texture, and normal indices '
                                + 'describing a face.'),
                'type': 'array', 'minItems': 3,
                'items': {'type': 'object', 'required': ['vertex_index'],
                          'additionalProperties': False,
                          'properties':
                              {'vertex_index': {'type': _index_type},
                               'texcoord_index': {'type': _index_type},
                               'normal_index': {'type': _index_type}}}},
            'curve': {
                'description': 'Properties of describing a curve.',
                'type': 'object', 'required': ['starting_param', 'ending_param',
                                               'vertex_indices'],
                'additionalProperties': False,
                'properties': {
                    'starting_param': {'type': _coord_type},
                    'ending_param': {'type': _coord_type},
                    'vertex_indices': {
                        'type': 'array', 'minItems': 2,
                        'items': {'type': _index_type}}}},
            'curve2D': {
                'description': ('Array of parameter indices describine a 2D curve on '
                                + 'a surface.'),
                'type': 'array', 'minItems': 2,
                'items': {'type': _index_type}},
            'surface': {
                'description': 'Properties describing a surface.',
                'type': 'object', 'required': ['starting_param_u', 'ending_param_u',
                                               'starting_param_v', 'ending_param_v',
                                               'vertex_indices'],
                'additionalProperties': False,
                'properties': {
                    'starting_param_u': {'type': _coord_type},
                    'ending_param_u': {'type': _coord_type},
                    'starting_param_v': {'type': _coord_type},
                    'ending_param_v': {'type': _coord_type},
                    'vertex_indices': {
                        'type': 'array', 'minItems': 2,
                        'items': {'type': 'object', 'required': ['vertex_index'],
                                  'additionalProperties': False,
                                  'properties': {
                                      'vertex_index': {'type': _index_type},
                                      'texcoord_index': {'type': _index_type},
                                      'normal_index': {'type': _index_type}}}}}}},
        'properties': {
            'material': {
                'description': 'Name of the material to use.',
                'type': ['unicode', 'string']},
            'vertices': {
                'description': 'Array of vertices.',
                'type': 'array', 'items': {'$ref': '#/definitions/vertex'}},
            'params': {
                'description': 'Array of parameter coordinates.',
                'type': 'array', 'items': {'$ref': '#/definitions/param'}},
            'normals': {
                'description': 'Array of normals.',
                'type': 'array', 'items': {'$ref': '#/definitions/normal'}},
            'texcoords': {
                'description': 'Array of texture vertices.',
                'type': 'array', 'items': {'$ref': '#/definitions/texcoord'}},
            'points': {
                'description': 'Array of points.',
                'type': 'array', 'items': {'$ref': '#/definitions/point'}},
            'lines': {
                'description': 'Array of lines.',
                'type': 'array', 'items': {'$ref': '#/definitions/line'}},
            'faces': {
                'description': 'Array of faces.',
                'type': 'array', 'items': {'$ref': '#/definitions/face'}},
            'curves': {
                'description': 'Array of curves.',
                'type': 'array', 'items': {'$ref': '#/definitions/curve'}},
            'curve2Ds': {
                'description': 'Array of curve2Ds.',
                'type': 'array', 'items': {'$ref': '#/definitions/curve2D'}},
            'surfaces': {
                'description': 'Array of surfaces.',
                'type': 'array', 'items': {'$ref': '#/definitions/surface'}}},
        'dependencies': {
            'lines': ['vertices'],
            'faces': ['vertices'],
            'curves': ['vertices'],
            'curve2Ds': ['params'],
            'surfaces': ['vertices']}}
    with open(_schema_file, 'w') as fd:
        encode_json(schema, fd, indent='\t')


def get_schema():
    r"""Return the Obj schema, initializing it if necessary.

    Returns:
        dict: Obj schema.
    
    """
    if not os.path.isfile(_schema_file):
        create_schema()
    with open(_schema_file, 'r') as fd:
        out = decode_json(fd)
    return out


if not os.path.isfile(_schema_file):  # pragma: debug
    create_schema()


class ObjDict(PlyDict):
    r"""Enhanced dictionary class for storing Obj information."""

    @classmethod
    def from_array_dict(cls, in_dict):
        r"""Get a version of the object from a dictionary of arrays."""
        kws = {}
        for k in ['material', 'vertices', 'params', 'normals', 'texcoords',
                  'lines', 'faces', 'points', 'curves', 'curve2Ds',
                  'surfaces']:
            if k in in_dict:
                kws[k] = copy.deepcopy(in_dict[k])
        if isinstance(kws.get('vertices', None), np.ndarray):
            old_vert = kws['vertices']
            nvert = old_vert.shape[1]
            assert(nvert in (3, 4))
            kws['vertices'] = [
                {k: old_vert[i, j] for j, k in enumerate('xyzw'[:nvert])
                 if ((j < 3) or (not np.isnan(old_vert[i, j])))}
                for i in range(old_vert.shape[0])]
        if isinstance(in_dict.get('vertex_colors', None), np.ndarray):
            old_colr = in_dict['vertex_colors']
            assert(old_colr.shape == (len(kws['vertices']), 3))
            for i in range(old_colr.shape[0]):
                for j, k in enumerate(['red', 'green', 'blue']):
                    kws['vertices'][i][k] = old_colr[i, j]
        if isinstance(kws.get('params', None), np.ndarray):
            old_parm = kws['params']
            nparm = old_parm.shape[1]
            assert(nparm in [2, 3])
            kws['params'] = [
                {k: old_parm[i, j] for j, k in enumerate('uvw'[:nparm])
                 if ((j < 2) or (not np.isnan(old_parm[i, j])))}
                for i in range(old_parm.shape[0])]
        if isinstance(kws.get('normals', None), np.ndarray):
            old_norm = kws['normals']
            assert(old_norm.shape[1] == 3)
            kws['normals'] = [
                {k: old_norm[i, j] for j, k in enumerate('ijk')}
                for i in range(old_norm.shape[0])]
        if isinstance(kws.get('texcoords', None), np.ndarray):
            old_texc = kws['texcoords']
            ntexc = old_texc.shape[1]
            assert(ntexc in [1, 2, 3])
            kws['texcoords'] = [
                {k: old_texc[i, j] for j, k in enumerate('uvw'[:ntexc])
                 if ((j < 1) or (not np.isnan(old_texc[i, j])))}
                for i in range(old_texc.shape[0])]
        # Composites of above
        if isinstance(kws.get('lines', None), np.ndarray):
            old_edge = kws['lines']
            assert(old_edge.shape[1] == 2)
            kws['lines'] = [
                [{'vertex_index': np.int32(old_edge[i, j])}
                 for j in range(old_edge.shape[1])
                 if (not np.isnan(old_edge[i, j]))]
                for i in range(old_edge.shape[0])]
        if isinstance(kws.get('faces', None), np.ndarray):
            old_face = kws['faces']
            assert(old_face.shape[1] >= 3)
            kws['faces'] = [
                [{'vertex_index': np.int32(old_face[i, j])}
                 for j in range(old_face.shape[1])
                 if (not np.isnan(old_face[i, j]))]
                for i in range(old_face.shape[0])]
        if isinstance(in_dict.get('face_texcoords', None), np.ndarray):
            old_texc = in_dict['face_texcoords']
            assert(old_texc.shape[0] == len(kws.get('faces', [])))
            for i in range(old_texc.shape[0]):
                for j in range(old_texc.shape[1]):
                    if not np.isnan(old_texc[i, j]):
                        kws['faces'][i][j]['texcoord_index'] = np.int32(
                            old_texc[i, j])
        if isinstance(in_dict.get('face_normals', None), np.ndarray):
            old_norm = in_dict['face_normals']
            assert(old_norm.shape[0] == len(kws.get('faces', [])))
            for i in range(old_norm.shape[0]):
                for j in range(old_norm.shape[1]):
                    if not np.isnan(old_norm[i, j]):
                        kws['faces'][i][j]['normal_index'] = np.int32(
                            old_norm[i, j])
        if isinstance(kws.get('points', None), np.ndarray):
            old_pnts = kws['points']
            kws['points'] = [
                [np.int32(old_pnts[i, j]) for j in range(old_pnts.shape[1])
                 if (not np.isnan(old_pnts[i, j]))]
                for i in range(old_pnts.shape[0])]
        if isinstance(kws.get('curves', None), np.ndarray):
            old_curv = kws['curves']
            kws['curves'] = [
                {'vertex_indices': [
                    np.int32(old_curv[i, j]) for j in range(old_curv.shape[1])
                    if (not np.isnan(old_curv[i, j]))]}
                for i in range(old_curv.shape[0])]
            assert('curve_params' in in_dict)
            if isinstance(in_dict['curve_params'], np.ndarray):
                old_parm = in_dict['curve_params']
                assert(old_parm.shape == (len(kws['curves']), 2))
                for i in range(old_parm.shape[0]):
                    kws['curves'][i]['starting_param'] = old_parm[i, 0]
                    kws['curves'][i]['ending_param'] = old_parm[i, 1]
        if isinstance(kws.get('curve2Ds', None), np.ndarray):
            old_curv = kws['curve2Ds']
            kws['curve2Ds'] = [
                [np.int32(old_curv[i, j]) for j in range(old_curv.shape[1])
                 if (not np.isnan(old_curv[i, j]))]
                for i in range(old_curv.shape[0])]
        if isinstance(kws.get('surfaces', None), np.ndarray):
            old_surf = kws['surfaces']
            kws['surfaces'] = [
                {'vertex_indices': [
                    {'vertex_index': np.int32(old_surf[i, j])}
                    for j in range(old_surf.shape[1])
                    if (not np.isnan(old_surf[i, j]))]}
                for i in range(old_surf.shape[0])]
            assert('surface_params' in in_dict)
            if isinstance(in_dict['surface_params'], np.ndarray):
                old_parm = in_dict['surface_params']
                assert(old_parm.shape == (len(kws['surfaces']), 4))
                for i in range(old_parm.shape[0]):
                    kws['surfaces'][i]['starting_param_u'] = old_parm[i, 0]
                    kws['surfaces'][i]['ending_param_u'] = old_parm[i, 1]
                    kws['surfaces'][i]['starting_param_v'] = old_parm[i, 2]
                    kws['surfaces'][i]['ending_param_v'] = old_parm[i, 3]
        if isinstance(in_dict.get('surface_texcoords', None), np.ndarray):
            old_texc = in_dict['surface_texcoords']
            assert(old_texc.shape[0] == len(kws['surfaces']))
            for i in range(old_texc.shape[0]):
                for j in range(old_texc.shape[1]):
                    if not np.isnan(old_texc[i, j]):
                        kws['surfaces'][i]['vertex_indices'][j][
                            'texcoord_index'] = np.int32(old_texc[i, j])
        if isinstance(in_dict.get('surface_normals', None), np.ndarray):
            old_norm = in_dict['surface_normals']
            assert(old_norm.shape[0] == len(kws['surfaces']))
            for i in range(old_norm.shape[0]):
                for j in range(old_norm.shape[1]):
                    if not np.isnan(old_norm[i, j]):
                        kws['surfaces'][i]['vertex_indices'][j][
                            'normal_index'] = np.int32(old_norm[i, j])
        return cls.from_dict(kws)
        
    def as_array_dict(self):
        r"""Get a version of the object as a dictionary of arrays."""
        out = {}
        if self.get('material', None):
            out['material'] = self['material']
        if self.get('vertices', None):
            out['vertices'] = np.asarray(
                [[v.get(k, np.NaN) for k in 'xyzw']
                 for v in self['vertices']])
            out['vertex_colors'] = np.asarray(
                [[v.get(k, np.NaN) for k in ['red', 'green', 'blue']]
                 for v in self['vertices']])
            if np.all(np.isnan(out['vertices'][:, 3])):
                out['vertices'] = out['vertices'][:, :3]
            if np.all(np.isnan(out['vertex_colors'])):
                out.pop('vertex_colors')
        if self.get('params', None):
            out['params'] = np.asarray(
                [[v.get(k, np.NaN) for k in 'uvw']
                 for v in self['params']])
            if np.all(np.isnan(out['params'][:, 2])):
                out['params'] = out['params'][:, :2]
        if self.get('normals', None):
            out['normals'] = np.asarray(
                [[v[k] for k in 'ijk'] for v in self['normals']])
        if self.get('texcoords', None):
            out['texcoords'] = np.asarray(
                [[v.get(k, np.NaN) for k in 'uvw']
                 for v in self['texcoords']])
            if np.all(np.isnan(out['texcoords'][:, 1:])):
                out['texcoords'] = out['texcoords'][:, :1]
            elif np.all(np.isnan(out['texcoords'][:, 2])):
                out['texcoords'] = out['texcoords'][:, :2]
        if self.get('lines', None):
            out['lines'] = np.NaN * np.ones(
                (len(self['lines']), len(max(self['lines'], key=len))),
                dtype='int32')
            for i, vlist in enumerate(self['lines']):
                for j, v in enumerate(vlist):
                    out['lines'][i, j] = v['vertex_index']
        if self.get('faces', None):
            face_shp = (len(self['faces']), len(max(self['faces'], key=len)))
            out['faces'] = np.NaN * np.ones(face_shp, dtype='int32')
            out['face_texcoords'] = np.NaN * np.ones(face_shp, dtype='int32')
            out['face_normals'] = np.NaN * np.ones(face_shp, dtype='int32')
            for i, vlist in enumerate(self['faces']):
                for j, v in enumerate(vlist):
                    out['faces'][i, j] = v['vertex_index']
                    out['face_texcoords'][i, j] = v.get(
                        'texcoord_index', np.NaN)
                    out['face_normals'][i, j] = v.get('normal_index', np.NaN)
            if np.all(np.isnan(out['face_texcoords'])):
                out.pop('face_texcoords')
            if np.all(np.isnan(out['face_normals'])):
                out.pop('face_normals')
        if self.get('points', None):
            out['points'] = np.NaN * np.ones(
                (len(self['points']), len(max(self['points'], key=len))),
                dtype='int32')
            for i, vlist in enumerate(self['points']):
                out['points'][i, :len(vlist)] = vlist
        if self.get('curves', None):
            def fkey(x):
                return len(x['vertex_indices'])
            out['curves'] = np.NaN * np.ones(
                (len(self['curves']), len(max(self['curves'], key=fkey))),
                dtype='int32')
            out['curve_params'] = np.zeros((out['curves'].shape[0], 2))
            for i, curv in enumerate(self['curves']):
                out['curve_params'][i, :] = [curv['starting_param'],
                                             curv['ending_param']]
                out['curves'][i, :fkey(curv)] = curv['vertex_indices']
        if self.get('curve2Ds', None):
            out['curve2Ds'] = np.NaN * np.ones(
                (len(self['curve2Ds']), len(max(self['curve2Ds'], key=len))),
                dtype='int32')
            for i, vlist in enumerate(self['curve2Ds']):
                out['curve2Ds'][i, :len(vlist)] = vlist
        if self.get('surfaces', None):
            def fkey(x):
                return len(x['vertex_indices'])
            surf_shp = (len(self['surfaces']), len(max(self['surfaces'], key=fkey)))
            out['surfaces'] = np.NaN * np.ones(surf_shp, dtype='int32')
            out['surface_params'] = np.zeros((surf_shp[0], 4))
            out['surface_texcoords'] = np.NaN * np.ones(surf_shp, dtype='int32')
            out['surface_normals'] = np.NaN * np.ones(surf_shp, dtype='int32')
            for i, surf in enumerate(self['surfaces']):
                out['surface_params'][i, :] = [surf['starting_param_u'],
                                               surf['ending_param_u'],
                                               surf['starting_param_v'],
                                               surf['ending_param_v']]
                for j, v in enumerate(surf['vertex_indices']):
                    out['surfaces'][i, j] = v['vertex_index']
                    out['surface_texcoords'][i, j] = v.get(
                        'texcoord_index', np.NaN)
                    out['surface_normals'][i, j] = v.get(
                        'normal_index', np.NaN)
            if np.all(np.isnan(out['surface_texcoords'])):
                out.pop('surface_texcoords')
            if np.all(np.isnan(out['surface_normals'])):
                out.pop('surface_normals')
        return out
    
    @classmethod
    def from_trimesh(cls, in_mesh):
        r"""Get a version of the object from a trimesh class."""
        kws = dict(vertices=in_mesh.vertices,
                   vertex_colors=in_mesh.visual.vertex_colors,
                   faces=in_mesh.faces.astype('int32'))
        weights = (kws['vertex_colors'][:, 3].astype('float32') + 1.0) / 256
        weights[weights == 1.0] = np.NaN
        kws['vertex_colors'] = kws['vertex_colors'][:, :3]
        kws['vertices'] = np.hstack([kws['vertices'], weights[..., None]])
        return cls.from_array_dict(kws)

    def as_trimesh(self, **kwargs):
        r"""Get a version of the object as a trimesh class."""
        kws0 = self.as_array_dict()
        kws = {'vertices': kws0.get('vertices', None),
               'vertex_colors': kws0.get('vertex_colors', None),
               'faces': kws0.get('faces', None)}
        if (kws['vertices'] is not None) and (kws['vertices'].shape[1] == 4):
            weights = kws['vertices'][:, 3] * 256 - 1.0
            weights[np.isnan(weights)] = 255
            kws['vertices'] = kws['vertices'][:, :3]
            if kws['vertex_colors'] is not None:
                kws['vertex_colors'] = np.hstack(
                    [kws['vertex_colors'], weights[..., None]])
        kws.update(kwargs, process=False)
        return trimesh.base.Trimesh(**kws)
    
    @property
    def mesh(self):
        r"""list: Vertices for each face in the structure."""
        mesh = []
        for f in self['faces']:
            imesh = []
            for v in f:
                imesh.append([self['vertices'][v['vertex_index']][k]
                              for k in ['x', 'y', 'z']])
            mesh.append(imesh)
        return mesh

    @property
    def vertex_normals(self):
        mesh = None
        if 'normals' in self:
            mesh = []
            for f in self['faces']:
                imesh = []
                for v in f:
                    imesh.append([self['normals'][v['normal_index']][k]
                                  for k in ['i', 'j', 'k']])
                mesh.append(imesh)
        return mesh

    @classmethod
    def from_shape(cls, shape, d, conversion=1.0):  # pragma: lpy
        r"""Create a ply dictionary from a PlantGL shape and descritizer.

        Args:
            scene (openalea.plantgl.scene): Scene that should be descritized.
            d (openalea.plantgl.descritizer): Descritizer.
            conversion (float, optional): Conversion factor that should be
                applied to the vertex positions. Defaults to 1.0.

        """
        iobj = super(ObjDict, cls).from_shape(shape, d, conversion=conversion,
                                              _as_obj=True)
        if iobj is not None:
            # Texcoords
            if d.result.texCoordList:
                iobj.setdefault('texcoords', [])
                for t in d.result.texCoordList:
                    # TODO: Should the coords be scaled?
                    iobj['texcoords'].append({'u': t.x, 'v': t.y})
                if d.result.texCoordIndexList:
                    for i, t in enumerate(d.result.texCoordIndexList):
                        if t[0] < len(iobj['texcoords']):
                            for j in range(3):
                                iobj['faces'][i][j]['texcoord_index'] = t[j]
            # Normals
            if d.result.normalList:
                iobj.setdefault('normals', [])
                for n in d.result.normalList:
                    iobj['normals'].append({'i': n.x, 'j': n.y, 'k': n.z})
                if d.result.normalIndexList:
                    for i, n in enumerate(d.result.normalIndexList):
                        if n[0] < len(iobj['normals']):
                            for j in range(3):
                                iobj['faces'][i][j]['normal_index'] = n[j]
        return iobj

    def to_geom_args(self, conversion=1.0, name=None):  # pragma: lpy
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
            conversion=conversion, name=name, _as_obj=True)
        index_class = pgl.Index
        array_class = pgl.IndexArray
        # Texture coords
        if self.get('texcoords', []):
            obj_texcoords = []
            for t in self['texcoords']:
                obj_texcoords.append(pgl.Vector2(np.float64(t['u']),
                                                 np.float64(t.get('v', 0.0))))
            kwargs['texCoordList'] = pgl.Point2Array(obj_texcoords)
            obj_ftexcoords = []
            for i, f in enumerate(self['faces']):
                entry = []
                for _f in f:
                    if 'texcoord_index' not in _f:
                        if i > 0:  # pragma: debug
                            warnings.warn(("'texcoord_index' missing from face"
                                           + "%d, texcoord indices will be "
                                           + "ignored.") % i)
                        obj_ftexcoords = []
                        entry = []
                        break
                    entry.append(int(_f['texcoord_index']))
                if not entry:
                    break
                obj_ftexcoords.append(index_class(*entry))
            if obj_ftexcoords:
                kwargs['texCoordIndexList'] = array_class(obj_ftexcoords)
        # Normals
        if self.get('normals', []):
            obj_normals = []
            for n in self['normals']:
                obj_normals.append(pgl.Vector3(np.float64(n['i']),
                                               np.float64(n['j']),
                                               np.float64(n['k'])))
            kwargs['normalList'] = pgl.Point3Array(obj_normals)
            obj_fnormals = []
            for i, f in enumerate(self['faces']):
                entry = []
                for _f in f:
                    if 'normal_index' not in _f:
                        if i > 0:  # pragma: debug
                            warnings.warn(("'normal_index' missing from face"
                                           + "%d, normal indices will be "
                                           + "ignored.") % i)
                        obj_fnormals = []
                        entry = []
                        break
                    entry.append(int(_f['normal_index']))
                if not entry:
                    break
                obj_fnormals.append(index_class(*entry))
            if obj_fnormals:
                kwargs['normalIndexList'] = array_class(obj_fnormals)
        return smb_class, args, kwargs

    def append(self, solf):
        r"""Append new ply information to this dictionary.

        Args:
            solf (ObjDict): Another ply to append to this one.

        """
        exist_map = {'vertex_index': len(self.get('vertices', [])),
                     'texcoord_index': len(self.get('texcoords', [])),
                     'normal_index': len(self.get('normals', [])),
                     'param_index': len(self.get('params', []))}
        exist_map.update(points=exist_map['vertex_index'],
                         curve2Ds=exist_map['param_index'])
        # Vertex fields
        for k in ['vertices', 'texcoords', 'normals', 'params']:
            if k in solf:
                if k not in self:
                    self[k] = []
                self[k] += solf[k]
        # Points/2D curves
        for k in ['points', 'curve2Ds']:
            if k in solf:
                if k not in self:
                    self[k] = []
                for x in solf[k]:
                    self[k].append([v + exist_map[k] for v in x])
        # Face/line fields
        for k in ['lines', 'faces']:
            if k in solf:
                if k not in self:
                    self[k] = []
                for x in solf[k]:
                    iele = [{ik: v[ik] + exist_map[ik] for ik in v.keys()} for v in x]
                    self[k].append(iele)
        # Curves
        k = 'curves'
        if k in solf:
            if k not in self:
                self[k] = []
            for x in solf[k]:
                iele = copy.deepcopy(x)
                iele['vertex_indices'] = [v + exist_map['vertex_index']
                                          for v in x['vertex_indices']]
        # Surfaces
        k = 'surfaces'
        if k in solf:
            if k not in self:
                self[k] = []
            for x in solf[k]:
                iele = copy.deepcopy(x)
                iele['vertex_indices'] = [{ik: v[ik] + exist_map[ik] for ik in v.keys()}
                                          for v in x['vertex_indices']]
        # Merge material using first in list
        material = None
        for x in [self, solf]:
            if x.get('material', None) is not None:
                material = x['material']
                break
        if material is not None:
            self['material'] = material
        return self

    def apply_scalar_map(self, *args, **kwargs):
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
            dict: Obj with updated vertex colors.

        """
        kwargs['_as_obj'] = True
        return super(ObjDict, self).apply_scalar_map(*args, **kwargs)
    

if trimesh:
    python_types = (dict, ObjDict, trimesh.base.Trimesh)
else:
    python_types = (dict, ObjDict)

   
# The base class could be anything since it is discarded during registration,
# but is set to JSONObjectMetaschemaType here for transparancy since this is
# what the base class is determined to be on loading the schema
class ObjMetaschemaType(JSONObjectMetaschemaType):
    r"""Obj 3D structure map."""

    _empty_msg = {'vertices': [], 'faces': []}
    python_types = python_types
    schema_file = _schema_file
    _replaces_existing = False

    @classmethod
    def _encode_object_property(cls, obj, order, req_keys=False):
        if req_keys:
            sep = '/'
        else:
            sep = ' '
        plist = []
        if isinstance(obj, (list, tuple)):
            for x in obj:
                plist.append(cls._encode_object_property(x, order, req_keys=True))
            return sep.join(plist)
        elif isinstance(obj, dict):
            for i, k in enumerate(order):
                if isinstance(k, dict):
                    assert(len(k) == 1)
                    ksub = list(k.keys())[0]
                    if ksub in obj:
                        plist.append(cls._encode_object_property(obj[ksub], k[ksub]))
                elif isinstance(k, (list, tuple)):
                    assert(len(k) == 1)
                    ksub = k[0]
                    if ksub in obj:
                        plist.append(cls._encode_object_property(obj[ksub], ksub))
                else:
                    if k in obj:
                        plist.append(cls._encode_object_property(obj[k], k))
                    elif req_keys:
                        plist.append('')
            return sep.join(plist)
        else:
            if order in _index_properties:
                # Add one at write to indexes as .obj is not zero indexed
                return _default_property_formats[order] % (obj + 1)
            else:
                return _default_property_formats[order] % obj

    @classmethod
    def _decode_object_property(cls, values, order):
        if isinstance(values, (list, tuple)):
            if not isinstance(order, (list, tuple)):
                out = [cls._decode_object_property(v, order) for v in values]
            elif (len(values) > 0) and ('/' in values[0]) or isinstance(order, tuple):
                out = [cls._decode_object_property(v, order) for v in values]
            else:
                out = {}
                for i, (o, v) in enumerate(zip(order, values)):
                    if not v:
                        continue
                    if isinstance(o, dict):
                        assert(len(o) == 1)
                        osub = list(o.keys())[0]
                        out[osub] = cls._decode_object_property(values[i:], o[osub])
                        break
                    elif isinstance(o, (list, tuple)):
                        assert(len(o) == 1)
                        osub = o[0]
                        out[osub] = cls._decode_object_property(values[i:], osub)
                    else:
                        out[o] = cls._decode_object_property(v, o)
        else:
            if not isinstance(order, (list, tuple)):
                ftranslate = _default_property_converters[order]
                out = ftranslate(values)
                if order in _index_properties:
                    # Subtract 1 from indexes because .obj is not zero indexed
                    out -= 1
            elif '/' in values:
                subvalues = values.split('/')
                assert(isinstance(order, tuple))
                assert(len(order) == len(subvalues))
                out = cls._decode_object_property(subvalues, list(order))
            else:
                out = cls._decode_object_property([values], [order[0]])
        return out

    @classmethod
    def encode_data(cls, obj, typedef, comments=[], newline='\n'):
        r"""Encode an object's data.

        Args:
            obj (object): Object to encode.
            typedef (dict): Type definition that should be used to encode the
                object.
            comments (list, optional): List of comments that should be included in
                the file header. Defaults to lines describing the automated origin
                of the file.
            newline (str, optional): String that should be used to delineated end
                of lines. Defaults to '\n'.

        Returns:
            bytes, str: Serialized message.

        """
        if trimesh and isinstance(obj, trimesh.base.Trimesh):
            obj = ObjDict.from_trimesh(obj)
        # Encode header
        header = ['# Author ygg_auto',
                  '# Generated by yggdrasil']
        header += ['# ' + c for c in comments]
        header += ['']
        # Encode body
        body = []
        for e in _default_element_order:
            if (e not in obj):
                continue
            if (e == 'material'):
                body.append('%s %s' % (_map_element2code[e], obj['material']))
                continue
            for ie in obj[e]:
                ivalue = cls._encode_object_property(ie, _default_property_order[e])
                iline = '%s %s' % (_map_element2code[e], ivalue)
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
        metadata = {'comments': []}
        out = {}
        # Parse
        for line_count, line in enumerate(lines):
            if line.startswith('#'):
                metadata['comments'].append(line)
                continue
            values = line.split()
            if not values:
                continue
            if values[0] not in _map_code2element:
                raise ValueError("Type code '%s' on line %d not understood"
                                 % (values[0], line_count))
            e = _map_code2element[values[0]]
            if e not in out:
                out[e] = []
            if e in ['material']:
                out[e] = values[1]
                continue
            else:
                out[e].append(
                    cls._decode_object_property(values[1:], _default_property_order[e]))
        # Return
        # out.update(**metadata)
        return ObjDict(out)

    @classmethod
    def coerce_type(cls, obj, typedef=None, **kwargs):
        r"""Coerce objects of specific types to match the data type.

        Args:
            obj (object): Object to be coerced.
            typedef (dict, optional): Type defintion that object should be
                coerced to. Defaults to None.
            **kwargs: Additional keyword arguments are metadata entries that may
                aid in coercing the type.

        Returns:
            object: Coerced object.

        """
        if trimesh and isinstance(obj, trimesh.base.Trimesh):
            obj = ObjDict.from_trimesh(obj)
        if isinstance(obj, dict) and ('material' in obj):
            obj['material'] = tools.bytes2str(obj['material'])
        return super(ObjMetaschemaType, cls).coerce_type(
            obj, typedef=typedef, **kwargs)

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
        out = super(ObjMetaschemaType, cls).updated_fixed_properties(obj)
        # Constrain dependencies for indexes into other elements
        depend_map = {'vertex_index': 'vertices', 'vertex_indices': 'vertices',
                      'texcoord_index': 'texcoords',
                      'normal_index': 'normals'}
        check_depends = {'lines': ['texcoord_index'],
                         'faces': ['texcoord_index', 'normal_index'],
                         'surfaces:vertex_indices': ['texcoord_index', 'normal_index']}
        for e, props in check_depends.items():
            sube = None
            if ':' in e:
                e, sube = e.split(':')
            if not ((e in obj) and isinstance(obj[e], (list, tuple))):
                continue
            req_flags = {k: False for k in props}
            for o in obj[e]:
                if sum(req_flags.values()) == len(props):
                    break
                if isinstance(o, dict):
                    assert(sube)
                    if (((sube not in o) or (not isinstance(o[sube], (list, tuple)))
                         or (len(o[sube]) == 0) or (not isinstance(o[sube][0], dict)))):
                        continue
                    for p in props:
                        if p in o[sube][0]:
                            req_flags[p] = True
                elif isinstance(o, (list, tuple)):
                    if (len(o) == 0) or (not isinstance(o[0], dict)):
                        continue
                    for p in props:
                        if p in o[0]:
                            req_flags[p] = True
            # Set dependencies
            for p in req_flags.keys():
                if not req_flags[p]:
                    continue
                if depend_map[p] not in out['dependencies'][e]:
                    out['dependencies'][e].append(depend_map[p])
        # Contrain indices on number of elements refered to
        if ('vertices' in obj) and isinstance(obj['vertices'], (list, tuple)):
            out['definitions']['curve']['properties']['vertex_indices']['items'][
                'maximum'] = len(obj['vertices']) - 1
        if ('params' in obj) and isinstance(obj['params'], (list, tuple)):
            out['definitions']['curve2D']['items']['maximum'] = len(obj['params']) - 1
        for e in ['line', 'face', 'surface']:
            if e == 'surface':
                iprop = out['definitions'][e]['properties']['vertex_indices'][
                    'items']['properties']
            else:
                iprop = out['definitions'][e]['items']['properties']
            for k, e_depends in depend_map.items():
                if k in iprop:
                    if (e_depends in obj) and isinstance(obj[e_depends], (list, tuple)):
                        iprop[k]['maximum'] = len(obj[e_depends]) - 1
        return out

    @classmethod
    def _generate_data(cls, typedef, **kwargs):
        r"""Generate mock data for the specified type.

        Args:
            typedef (dict): Type definition.

        Returns:
            object: Python object of the specified type.

        """
        kwargs.setdefault('numeric_value', 0)
        out = super(ObjMetaschemaType, cls)._generate_data(typedef, **kwargs)
        out['texcoords'][0].update(v=1.0, w=1.0)
        return out


ObjDict._type_class = ObjMetaschemaType
