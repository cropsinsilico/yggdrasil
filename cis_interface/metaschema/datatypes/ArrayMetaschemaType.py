import numpy as np
from cis_interface.metaschema.datatypes import register_type
from cis_interface.metaschema.datatypes.ScalarMetaschemaType import (
    ScalarMetaschemaType)


@register_type
class OneDArrayMetaschemaType(ScalarMetaschemaType):
    r"""Type associated with a scalar."""

    name = '1darray'
    description = 'A 1D array with or without units.'
    properties = ScalarMetaschemaType.properties + ['length']
    metadata_properties = ScalarMetaschemaType.metadata_properties + ['length']
    python_types = (np.ndarray, )

    @classmethod
    def validate(cls, obj):
        r"""Validate an object to check if it could be of this type.

        Args:
            obj (object): Object to validate.

        Returns:
            bool: True if the object could be of this type, False otherwise.

        """
        if not super(OneDArrayMetaschemaType, cls).validate(obj):
            return False
        if obj.ndim != 1:
            return False
        return True


@register_type
class NDArrayMetaschemaType(ScalarMetaschemaType):
    r"""Type associated with a scalar."""

    name = 'ndarray'
    description = 'An ND array with or without units.'
    properties = ScalarMetaschemaType.properties + ['shape']
    metadata_properties = ScalarMetaschemaType.metadata_properties + ['shape']
    python_types = (np.ndarray, )

    @classmethod
    def validate(cls, obj):
        r"""Validate an object to check if it could be of this type.

        Args:
            obj (object): Object to validate.

        Returns:
            bool: True if the object could be of this type, False otherwise.

        """
        if not super(NDArrayMetaschemaType, cls).validate(obj):
            return False
        if obj.ndim <= 1:
            return False
        return True
