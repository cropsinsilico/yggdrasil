import os
import json
from cis_interface import backwards
from cis_interface.metaschema.datatypes import register_type_from_file, _schema_dir
from cis_interface.metaschema.datatypes.JSONObjectMetaschemaType import (
    JSONObjectMetaschemaType)


_index_type = ('int', 'uint')
_color_type = ('int', 'uint')
_coord_type = 'float'
_index_fmt = '%d'
_float_fmt = '%6.4f'
_schema_file = os.path.join(_schema_dir, 'obj.json')
_map_obj2py = {'char': 'int8', 'uchar': 'uint8',
               'short': 'int16', 'ushort': 'uint16',
               'int': 'int32', 'uint': 'uint32',
               'float': 'float32', 'double': 'float64'}
_map_py2obj = {v: k for k, v in _map_obj2py.items()}
_default_element_order = ['vertices', 'params', 'normals', 'texcoords',
                          'lines', 'faces', 'curves', 'curve2Ds', 'surfaces']
# TODO: Unclear what standard puts colors after coords and how that is
# reconciled with the weight (i.e. do colors go before or after weight)
_default_property_order = {
    'vertices': ['x', 'y', 'z', 'red', 'green', 'blue', 'w'],
    'params': ['u', 'v', 'w'],
    'normals': ['i', 'j', 'k'],
    'texcoords': ['u', 'v', 'w'],
    'lines': ['vertex_index', 'texcoord_index'],
    'faces': ['vertex_index', 'texcoord_index', 'normal_index'],
    'curves': ['starting_param', 'ending_param', 'vertex_indices'],
    'curve2Ds': ['param_indices'],
    'surfaces': ['starting_param_u', 'ending_param_u',
                 'starting_param_v', 'ending_param_v',
                 {'vertex_indices': ['vertex_index', 'texcoord_index', 'normal_index']}]}
# TODO: ['vertex_index', 'texcoord_index', 'normal_index']
_map_element2code = {'vertices': 'v', 'params': 'vp', 'normals': 'vn', 'texcoords': 'vt',
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
                                + 'describing a line'),
                'type': 'array', 'minItems': 2,
                'items': {'type': 'object', 'required': ['vertex_index'],
                          'additionalProperties': False,
                          'properties':
                              {'vertex_index': {'type': _index_type},
                               'texcoord_index': {'type': _index_type}}}},
            'face': {
                'description': ('Array of vertex, texture, and normal indices '
                                + 'describing a line'),
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
                                  'vertex_index': {'type': _index_type},
                                  'texcoord_index': {'type': _index_type},
                                  'normal_index': {'type': _index_type}}}}}},
        'properties': {
            'material': {
                'description': 'Name of the material to use.',
                'type': 'unicode'},
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
                'type': 'array', 'items': {'$ref': '#/definitions/surface'}}}}
    with open(_schema_file, 'w') as fd:
        json.dump(schema, fd, sort_keys=True, indent="\t")


if not os.path.isfile(_schema_file):
    create_schema()


# The base class could be anything since it is discarded during registration,
# but is set to JSONObjectMetaschemaType here for transparancy since this is
# what the base class is determined to be on loading the schema
@register_type_from_file(_schema_file)
class ObjMetaschemaType(JSONObjectMetaschemaType):
    r"""Obj 3D structure map."""

    @classmethod
    def from_ply(cls, ply):
        r"""Convert a Ply object to an Obj object.

        Args:
            ply (dict): Ply type object.

        Returns:
            dict: Obj data container.

        """
        out = {}
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
        # Encode header
        header = ['# Author cis_auto',
                  '# Generated by cis_interface']
        header += ['# ' + c for c in comments]
        header += ['']
        if 'material' in obj:
            header.append('usemtl %s' % obj['material'])
        # Encode body
        body = []
        for e in _default_element_order:
            if (e in ['material']) or (e not in obj):
                continue
            for ie in obj[e]:
                plist = []
                fmtlist = []
                if e in ['vertices', 'params', 'normals', 'texcoords']:
                    for p in _default_property_order[e]:
                        if p in ie:
                            plist.append(ie[p])
                            if p in ['red', 'blue', 'green']:
                                fmtlist.append(_index_fmt)
                            else:
                                fmtlist.append(_float_fmt)
                elif e in ['lines', 'faces']:
                    for iie in ie:
                        vfmtlist = []
                        for p in _default_property_order[e]:
                            if p in iie:
                                plist.append(iie[p])
                                vfmtlist.append(_index_fmt)
                            else:
                                vfmtlist.append('')
                        fmtlist.append('/'.join(vfmtlist))
                elif e in ['curves']:
                    for p in _default_property_order[e]:
                        if p in ie:
                            if p == 'vertex_indices':
                                plist += [x for x in ie[p]]
                                fmtlist += [_index_fmt for x in ie[p]]
                            else:
                                plist.append(ie[p])
                                fmtlist.append(_float_fmt)
                elif e in ['curve2Ds']:
                    plist += [x for x in ie]
                    fmtlist += [_index_fmt for x in ie]
                elif e in ['surface']:
                    for p in _default_property_order[e]:
                        if p in ie:
                            if isinstance(p, dict):
                                assert('vertex_indices' in p)
                                for iie in ie['vertex_indices']:
                                    vfmtlist = []
                                    for vp in p['vertex_indices']:
                                        if vp in iie:
                                            plist.append(iie[vp])
                                            vfmtlist.append(_index_fmt)
                                        else:
                                            vfmtlist.append('')
                                    fmtlist.append('/'.join(vfmtlist))
                            else:
                                plist.append(ie[p])
                                fmtlist.append(_float_fmt)
                else:
                    raise ValueError("Unsupported element '%s'" % e)
                iline = _map_element2code[e] + ' ' + ' '.join(fmtlist) % tuple(plist)
                body.append(iline.strip())  # Ensure trailing spaces are removed
        return newline.join(header + body)

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
        lines = backwards.bytes2unicode(msg).splitlines()
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
                                 % values[0], line_count)
            e = _map_code2element[values[0]]
            if e not in out:
                out[e] = []
            if e in ['material']:
                out[e] = values[1]
                continue
            elif e in ['vertices', 'params', 'normals', 'texcoords']:
                new = {}
                for v, p in zip(values[1:], _default_property_order[e]):
                    new[p] = float(v)
                    if p in ['red', 'green', 'blue']:
                        new[p] = int(new[p])
            elif e in ['lines', 'faces']:
                new = []
                for v in values[1:]:
                    vnew = {}
                    for vv, p in zip(v.split('/'), _default_property_order[e]):
                        if vv:
                            vnew[p] = int(float(vv))
                    new.append(vnew)
            elif e in ['curves']:
                new = {}
                for i, (v, p) in enumerate(zip(values[1:], _default_property_order[e])):
                    if p == 'vertex_indices':
                        new[p] = [int(float(vv)) for vv in values[1:][i:]]
                        break
                    else:
                        new[p] = float(v)
            elif e in ['curve2Ds']:
                new = [int(float(v)) for v in values[1:]]
            elif e in ['surface']:
                new = {}
                for i, (v, p) in enumerate(zip(values[1:], _default_property_order[e])):
                    if isinstance(p, dict):
                        assert('vertex_indices' in p)
                        new['vertex_indices'] = []
                        for v in values[1:][i:]:
                            inew = {}
                            for vv, vp in zip(v.split('/'), p['vertex_indices']):
                                if vv:
                                    inew[vp] = int(float(vv))
                            new['vertex_indices'].append(inew)
                        break
                    else:
                        new[p] = float(v)
            out[e].append(new)
        # Return
        # out.update(**metadata)
        return out
