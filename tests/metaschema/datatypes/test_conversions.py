import pytest
from yggdrasil.metaschema.datatypes import conversions


def test_register_conversion_errors():
    r"""Test errors in register_conversion."""
    x = list(conversions._conversion_registry.keys())[0]
    with pytest.raises(ValueError):
        conversions.register_conversion(x[0], x[1])


def test_ply2obj(ply_test_value, obj_test_value):
    r"""Test conversion between ply and obj objects."""
    from yggdrasil.metaschema.datatypes import (
        ObjMetaschemaType, PlyMetaschemaType)
    obj_class = ObjMetaschemaType.ObjMetaschemaType
    ply_class = PlyMetaschemaType.PlyMetaschemaType
    # Start at ply
    obj = conversions.ply2obj(ply_test_value)
    obj_class.validate_instance(obj, {'type': 'obj'})
    ply = conversions.obj2ply(obj)
    ply_class.validate_instance(ply, {'type': 'ply'})
    # Start at obj
    ply = conversions.obj2ply(obj_test_value)
    ply_class.validate_instance(ply, {'type': 'ply'})
    obj = conversions.ply2obj(ply)
    obj_class.validate_instance(obj, {'type': 'obj'})
