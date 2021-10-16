from yggdrasil import units, constants
from yggdrasil.metaschema import data2dtype, MetaschemaTypeError
from yggdrasil.metaschema.properties.MetaschemaProperty import (
    MetaschemaProperty)


class SubtypeMetaschemaProperty(MetaschemaProperty):
    r"""Property class for 'subtype' property."""

    name = 'subtype'
    schema = {'description': 'The base type for each item.',
              'type': 'string',
              'enum': [k for k in sorted(constants.VALID_TYPES.keys())]}

    @classmethod
    def encode(cls, instance, typedef=None):
        r"""Encoder for the 'subtype' scalar property."""
        dtype = data2dtype(instance)
        out = None
        for k, v in constants.VALID_TYPES.items():
            if dtype.name.startswith(v):
                out = k
                break
        if out is None:
            raise MetaschemaTypeError('Cannot find subtype string for dtype %s'
                                      % dtype)
        return out

    @classmethod
    def normalize_in_schema(cls, schema):
        r"""Normalization for the 'subtype' scalar property in a schema."""
        if cls.name in schema:
            return schema
        if not units.is_null_unit(schema.get('units', '')):
            schema.setdefault(cls.name, 'float')
        return schema
    

class PrecisionMetaschemaProperty(MetaschemaProperty):
    r"""Property class for 'precision' property."""
    
    name = 'precision'
    schema = {'description': 'The size (in bits) of each item.',
              'type': 'number',
              'minimum': 1}

    @classmethod
    def encode(cls, instance, typedef=None):
        r"""Encoder for the 'precision' scalar property."""
        dtype = data2dtype(instance)
        out = dtype.itemsize * 8  # in bits
        return out

    @classmethod
    def compare(cls, prop1, prop2, root1=None, root2=None):
        r"""Comparison for the 'precision' scalar property."""
        if (prop1 > prop2):
            yield '%s is greater than %s' % (prop1, prop2)

    @classmethod
    def normalize_in_schema(cls, schema):
        r"""Normalization for the 'precision' scalar property in a schema."""
        if cls.name in schema:
            return schema
        subtype = schema.get('subtype', schema.get('type'))
        if subtype in ['float', 'int', 'uint']:
            schema.setdefault(cls.name, int(64))
        elif subtype in ['complex']:
            schema.setdefault(cls.name, int(128))
        return schema
            

class UnitsMetaschemaProperty(MetaschemaProperty):
    r"""Property class for 'units' property."""

    name = 'units'
    schema = {'description': 'Physical units.',
              'type': 'string'}

    @classmethod
    def encode(cls, instance, typedef=None):
        r"""Encoder for the 'units' scalar property."""
        out = units.get_units(instance)
        if (not out) and (typedef is not None):
            out = typedef
        return out

    @classmethod
    def compare(cls, prop1, prop2, root1=None, root2=None):
        r"""Comparision for the 'units' scalar property."""
        if not units.are_compatible(prop1, prop2):
            yield "Unit '%s' is not compatible with unit '%s'" % (prop1, prop2)
