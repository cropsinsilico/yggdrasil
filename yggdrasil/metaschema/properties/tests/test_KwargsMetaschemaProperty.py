from yggdrasil.metaschema.properties.tests import (
    test_MetaschemaProperty as parent)
from yggdrasil.metaschema.properties.tests.test_ArgsMetaschemaProperty import (
    ValidArgsClass1, ValidArgsClass2, ValidArgsClass3,
    ValidArgsClass4, InvalidArgsClass)


class TestKwargsMetaschemaProperty(parent.TestMetaschemaProperty):
    r"""Test class for KwargsMetaschemaProperty class."""
    
    _mod = 'KwargsMetaschemaProperty'
    _cls = 'KwargsMetaschemaProperty'
    
    def __init__(self, *args, **kwargs):
        super(TestKwargsMetaschemaProperty, self).__init__(*args, **kwargs)
        self._valid = []
        self._invalid = []
        for cls in [ValidArgsClass1, ValidArgsClass2,
                    ValidArgsClass3, ValidArgsClass4]:
            cls_inst = cls(*(cls.test_args), **(cls.test_kwargs))
            self._valid.append((cls_inst, cls.valid_kwargs))
            self._invalid.append((cls_inst, cls.invalid_kwargs))
        valid_type = ValidArgsClass1.valid_kwargs
        invalid_type = ValidArgsClass1.invalid_kwargs
        self._encode_errors = [int(1), InvalidArgsClass]
        self._valid_compare = [(valid_type, valid_type)]
        self._invalid_compare = [(valid_type, invalid_type)]
