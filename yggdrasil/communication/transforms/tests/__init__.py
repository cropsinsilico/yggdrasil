from yggdrasil.schema import get_schema
from yggdrasil.communication.transforms.tests.test_TransformBase import TestTransformBase


_schema = get_schema()
for transform_name in _schema['transform'].subtypes:
    transform_cls = _schema['transform'].subtype2class[transform_name]
    cls_attr = {'transform': transform_cls}
    new_cls = type('Test%s' % transform_cls, (TestTransformBase, ), cls_attr)
    globals()[new_cls.__name__] = new_cls
    del new_cls


__all__ = []
