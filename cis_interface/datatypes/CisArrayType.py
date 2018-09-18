from cis_interface.datatypes import register_type
from cis_interface.datatypes.CisScalarType import CisScalarType


@register_type
class Cis1DArrayType(CisScalarType):
    r"""Type associated with a scalar."""

    name = '1darray'
    description = 'A 1D array with or without units.'
    properties = dict(CisScalarType.properties,
                      length={
                          'description': 'Number of elements in the 1D array.',
                          'type': 'number',
                          'minimum': 1})
    metadata_properties = CisScalarType.metadata_properties + ['length']

    @classmethod
    def encode_type(cls, obj):
        r"""Encode an object's type definition.

        Args:
            obj (object): Object to encode.

        Returns:
            dict: Encoded type definition.

        """
        out = super(Cis1DArrayType, cls).encode_type(obj)
        out['length'] = len(obj)
        return out


@register_type
class CisNDArrayType(CisScalarType):
    r"""Type associated with a scalar."""

    name = 'ndarray'
    description = 'An ND array with or without units.'
    properties = dict(CisScalarType.properties,
                      shape={
                          'description': 'Shape of the ND array in each dimension.',
                          'type': 'array',
                          'items': {
                              'type': 'integer',
                              'minimum': 1}})
    metadata_properties = CisScalarType.metadata_properties + ['shape']

    @classmethod
    def encode_type(cls, obj):
        r"""Encode an object's type definition.

        Args:
            obj (object): Object to encode.

        Returns:
            dict: Encoded type definition.

        """
        out = super(CisNDArrayType, cls).encode_type(obj)
        out['shape'] = list(obj.shape)
        return out
