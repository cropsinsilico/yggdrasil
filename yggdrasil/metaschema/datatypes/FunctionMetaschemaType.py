import types
from yggdrasil.metaschema.datatypes.ClassMetaschemaType import (
    ClassMetaschemaType)


class FunctionMetaschemaType(ClassMetaschemaType):
    r"""Type for evaluating functions."""

    name = 'function'
    description = 'Type for callable Python functions.'
    python_types = (types.BuiltinFunctionType, types.FunctionType,
                    types.BuiltinMethodType, types.MethodType)

    @classmethod
    def _generate_data(cls, typedef):
        r"""Generate mock data for the specified type.

        Args:
            typedef (dict): Type definition.

        Returns:
            object: Python object of the specified type.

        """
        def example_func(x):  # pragma: debug
            return x
        return example_func
