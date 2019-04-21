import types
from yggdrasil.metaschema.datatypes import register_type
from yggdrasil.metaschema.datatypes.ClassMetaschemaType import (
    ClassMetaschemaType)


@register_type
class FunctionMetaschemaType(ClassMetaschemaType):
    r"""Type for evaluating functions."""

    name = 'function'
    description = 'Type for callable Python functions.'
    python_types = (types.BuiltinFunctionType, types.FunctionType,
                    types.BuiltinMethodType, types.MethodType)
