from yggdrasil.metaschema.properties.tests import (
    test_MetaschemaProperty as parent)


class TestPropertiesMetaschemaProperty(parent.TestMetaschemaProperty):
    r"""Test class for PropertiesMetaschemaProperty class."""
    
    _mod = 'JSONObjectMetaschemaProperties'
    _cls = 'PropertiesMetaschemaProperty'
    
    def __init__(self, *args, **kwargs):
        super(TestPropertiesMetaschemaProperty, self).__init__(*args, **kwargs)
        ele = 'abc'
        valid_value = {x: int(i) for i, x in enumerate(ele)}
        valid = {x: {'type': 'int'} for x in ele}
        invalid_type = {x: {'type': 'float'} for x in ele}
        invalid_keys = {x: {'type': 'int'} for x in ele[:-1]}
        self._valid = [(valid_value, valid)]
        self._invalid = [({x: float(i) for i, x in enumerate(ele)}, valid)]
        # ({x: int(i) for i, x in enumerate(ele[:-1])}, valid)]
        self._valid_compare = [(valid, valid),
                               (valid, invalid_keys)]
        self._invalid_compare = [(invalid_type, valid),
                                 (invalid_keys, valid)]
