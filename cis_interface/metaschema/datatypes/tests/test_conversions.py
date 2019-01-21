from yggdrasil.tests import assert_raises
from yggdrasil.metaschema.datatypes import conversions


def test_register_conversion_errors():
    r"""Test errors in register_conversion."""
    x = list(conversions._conversion_registry.keys())[0]
    assert_raises(ValueError, conversions.register_conversion, x[0], x[1])


def test_ply2obj():
    r"""Test conversion between ply and obj objects."""
    from yggdrasil.metaschema.datatypes import (
        ObjMetaschemaType, PlyMetaschemaType)
    from yggdrasil.metaschema.datatypes.tests import (
        test_ObjMetaschemaType, test_PlyMetaschemaType)
    obj_class = ObjMetaschemaType.ObjMetaschemaType
    ply_class = PlyMetaschemaType.PlyMetaschemaType
    obj_test = test_ObjMetaschemaType._test_value
    ply_test = test_PlyMetaschemaType._test_value
    # Start at ply
    obj = conversions.ply2obj(ply_test)
    obj_class.validate_instance(obj, {'type': 'obj'})
    ply = conversions.obj2ply(obj)
    ply_class.validate_instance(ply, {'type': 'ply'})
    # Start at obj
    ply = conversions.obj2ply(obj_test)
    ply_class.validate_instance(ply, {'type': 'ply'})
    obj = conversions.ply2obj(ply)
    obj_class.validate_instance(obj, {'type': 'obj'})
