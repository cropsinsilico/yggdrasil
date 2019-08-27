from yggdrasil.schema import get_schema
from yggdrasil.communication.filters.tests.test_FilterBase import TestFilterBase


_schema = get_schema()
for filter_name in _schema['filter'].subtypes:
    filter_cls = _schema['filter'].subtype2class[filter_name]
    cls_attr = {'filter': filter_cls}
    new_cls = type('Test%s' % filter_cls, (TestFilterBase, ), cls_attr)
    globals()[new_cls.__name__] = new_cls
    del new_cls


__all__ = []
