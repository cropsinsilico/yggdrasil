import os
import json
import numpy as np
from cis_interface import backwards
from cis_interface.metaschema.datatypes import register_type_from_file, _schema_dir
from cis_interface.metaschema.datatypes.JSONObjectMetaschemaType import (
    JSONObjectMetaschemaType)


_schema_file = os.path.join(_schema_dir, 'ply.json')
_map_ply2py = {'char': 'int8', 'uchar': 'uint8',
               'short': 'int16', 'ushort': 'uint16',
               'int': 'int32', 'uint': 'uint32',
               'float': 'float32', 'double': 'float64'}
_map_py2ply = {v: k for k, v in _map_ply2py.items()}
_default_element_order = ['vertex', 'face', 'edge', 'material']
_default_property_order = {'vertex': ['x', 'y', 'z', 'red', 'green', 'blue'],
                           'face': ['vertex_index'],
                           'edge': ['vertex1', 'vertex2', 'red', 'green', 'blue'],
                           'material': ['ambient_red', 'ambient_green',
                                        'ambient_blue', 'ambient_coeff',
                                        'diffuse_red', 'diffuse_green',
                                        'diffuse_blue', 'diffuse_coeff',
                                        'specular_red', 'specular_green',
                                        'specular_blue', 'specular_coeff',
                                        'specular_power']}


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
        'required': ['vertex', 'face', 'edge'],  # 'material'],
        'definitions': {'indexes': {'type': '1darray',
                                    'subtype': 'int',
                                    'precision': 32},
                        'colors': {'type': '1darray',
                                   'subtype': 'uint',
                                   'precision': 8},
                        'coords': {'type': '1darray',
                                   'subtype': 'float',
                                   'precision': 32}},
        'properties': {
            'vertex': {
                'description': 'Map of vertex properties.',
                'type': 'object', 'properties': {},
                'required': ['x', 'y', 'z']},
            'face': {
                'description': 'Map of face properties.',
                'type': 'object',
                'properties': {
                    'vertex_indices': {'type': 'array',
                                       'items': {"$ref": "#/definitions/indexes"}}},
                'required': ['vertex_indices']},
            'edge': {
                'description': 'Map of edge properties.',
                'type': 'object', 'properties': {},
                'required': ['vertex1', 'vertex2']},
            'material': {
                'description': 'Map of material properties.',
                'type': 'object', 'properties': {}}}}
    for x in ['x', 'y', 'z']:
        schema['properties']['vertex']['properties'][x] = {
            "$ref": "#/definitions/coords"}
    for x in ['red', 'green', 'blue']:
        schema['properties']['vertex']['properties'][x] = {
            "$ref": "#/definitions/colors"}
    for x in ['vertex1', 'vertex2']:
        schema['properties']['edge']['properties'][x] = {
            "$ref": "#/definitions/indexes"}
    for x in ['red', 'green', 'blue']:
        schema['properties']['edge']['properties'][x] = {
            "$ref": "#/definitions/colors"}
    with open(_schema_file, 'w') as fd:
        json.dump(schema, fd, sort_keys=True, indent="\t")


if not os.path.isfile(_schema_file):
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


def translate_py2ply(type_py):
    r"""Get the correpsonding Ply type string for the provided Python type.

    Args:
        type_py (type): Python type.

    Returns:
        str: Ply type string.

    """
    type_np = np.dtype(type_py).name
    if type_np not in _map_py2ply:
        raise ValueError("Could not find ply type string for numpy type '%s'." % type_np)
    return _map_py2ply[type_np]


# The base class could be anything since it is discarded during registration,
# but is set to JSONObjectMetaschemaType here for transparancy since this is
# what the base class is determined to be on loading the schema
@register_type_from_file(_schema_file)
class PlyMetaschemaType(JSONObjectMetaschemaType):
    r"""Ply 3D structure map."""

    @classmethod
    def encode_data(cls, obj, typedef, element_order=[], property_order={},
                    comments=[], newline='\n', plyformat='ascii 1.0'):
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
        # Default order
        if not element_order:
            for k in _default_element_order:
                if k in obj:
                    element_order.append(k)
            for k in sorted(obj.keys()):
                if k not in element_order:
                    element_order.append(k)
        if not property_order:
            for e in element_order:
                property_order[e] = []
                for k in _default_property_order[e]:
                    if k in obj[e]:
                        property_order[e].append(k)
                for k in sorted(obj[e].keys()):
                    if k not in property_order[e]:
                        property_order[e].append(k)
        # TODO: validate & set defaults
        # metadata, data = self.encode(obj, self._typedef)
        # Get information needed
        size_map = {}
        type_map = {}
        for e in element_order:
            type_map[e] = {}
            for p in property_order[e]:
                if e not in size_map:
                    size_map[e] = len(obj[e][p])
                assert(len(obj[e][p]) == size_map[e])
                if isinstance(obj[e][p], np.ndarray):
                    type_map[e][p] = translate_py2ply(obj[e][p].dtype)
                elif isinstance(obj[e][p], list):
                    subtype = translate_py2ply(type(obj[e][p][0][0]))
                    type_map[e][p] = 'list uchar %s' % subtype
                else:
                    raise ValueError("Cannot determine Ply type for Python type '%s'"
                                     % type(obj[e][p]))
        # Encode header
        header = ['ply', 'format %s' % plyformat]
        header += ['comment ' + c for c in comments]
        for e in element_order:
            header.append('element %s %d' % (e, size_map[e]))
            for p in property_order[e]:
                header.append('property %s %s' % (type_map[e][p], p))
        header.append('end_header')
        # Encode body
        body = []
        for e in element_order:
            for i in range(size_map[e]):
                iline = ''
                for p in property_order[e]:
                    if type_map[e][p].startswith('list'):
                        vars = type_map[e][p].split()
                        ientry = obj[e][p][i]
                        ifmt = translate_ply2fmt(vars[2])
                        iline += translate_ply2fmt(vars[1]) % len(ientry)
                        for x in ientry:
                            iline += ifmt % x
                    else:
                        iline += translate_ply2fmt(type_map[e][p]) % obj[e][p][i]
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
                metadata['plyformat'] = line.split(maxsplit=1)
            elif line.startswith('comment'):
                metadata['comments'].append(line.split(maxsplit=1))
            elif line.startswith('element'):
                vars = line.split()
                e = vars[1]
                size_map[e] = int(float(vars[2]))
                type_map[e] = {}
                metadata['element_order'].append(e)
                metadata['property_order'][e] = []
                obj[e] = {}
            elif line.startswith('property'):
                vars = line.split()
                p = vars[-1]
                type_map[e][p] = ' '.join(vars[1:-1])
                metadata['property_order'][e].append(p)
                if vars[1] == 'list':
                    obj[e][p] = []
                else:
                    obj[e][p] = np.empty(size_map[e], dtype=translate_ply2py(vars[1]))
            elif 'end_header' in line:
                headline = i + 1
                break
        # Parse body
        i = headline
        for e in metadata['element_order']:
            for ie in range(size_map[e]):
                vars = lines[i].split()
                iv = 0
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
                        obj[e][p].append(np.array(plist, dtype=plist_type))
                    else:
                        prop_type = translate_ply2py(type_map[e][p])
                        obj[e][p][ie] = prop_type(vars[iv])
                        iv += 1
                assert(iv == len(vars))
                i += 1
        # Check that all properties filled in
        for e in metadata['element_order']:
            for p in metadata['property_order'][e]:
                assert(len(obj[e][p]) == size_map[e])
        # Return
        return obj
