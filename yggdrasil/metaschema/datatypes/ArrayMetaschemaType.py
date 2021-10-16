from yggdrasil import units
from yggdrasil.metaschema.datatypes.ScalarMetaschemaType import (
    ScalarMetaschemaType)


class OneDArrayMetaschemaType(ScalarMetaschemaType):
    r"""Type associated with a scalar."""

    name = '1darray'
    description = 'A 1D array with or without units.'
    properties = ['length']
    metadata_properties = ['length']
    python_types = units.ALL_PYTHON_ARRAYS_WITH_UNITS

    @classmethod
    def validate(cls, obj, raise_errors=False):
        r"""Validate an object to check if it could be of this type.

        Args:
            obj (object): Object to validate.
            raise_errors (bool, optional): If True, errors will be raised when
                the object fails to be validated. Defaults to False.

        Returns:
            bool: True if the object could be of this type, False otherwise.

        """
        if not super(OneDArrayMetaschemaType, cls).validate(obj,
                                                            raise_errors=raise_errors):
            return False
        if units.get_data(obj).ndim != 1:
            if raise_errors:
                raise ValueError("The array has more than one dimension.")
            return False
        return True


class NDArrayMetaschemaType(ScalarMetaschemaType):
    r"""Type associated with a scalar."""

    name = 'ndarray'
    description = 'An ND array with or without units.'
    properties = ['shape']
    metadata_properties = ['shape']
    python_types = units.ALL_PYTHON_ARRAYS_WITH_UNITS

    @classmethod
    def validate(cls, obj, raise_errors=False):
        r"""Validate an object to check if it could be of this type.

        Args:
            obj (object): Object to validate.
            raise_errors (bool, optional): If True, errors will be raised when
                the object fails to be validated. Defaults to False.

        Returns:
            bool: True if the object could be of this type, False otherwise.

        """
        if not super(NDArrayMetaschemaType, cls).validate(obj,
                                                          raise_errors=raise_errors):
            return False
        if units.get_data(obj).ndim <= 1:
            if raise_errors:
                raise ValueError("The array does not have more than one dimension.")
            return False
        return True
