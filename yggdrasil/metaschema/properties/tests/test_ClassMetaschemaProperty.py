from yggdrasil.metaschema.properties.tests import (
    test_MetaschemaProperty as parent)


class TestClassMetaschemaProperty(parent.TestMetaschemaProperty):
    r"""Test class for ClassMetaschemaProperty class."""
    
    _mod = 'ClassMetaschemaProperty'
    _cls = 'ClassMetaschemaProperty'
    
    def __init__(self, *args, **kwargs):
        super(TestClassMetaschemaProperty, self).__init__(*args, **kwargs)
        self._valid = [(int(1), int), (dict(), dict)]
        self._invalid = [(int(1), dict), (dict(), int)]
        self._encode_errors = []
        self._valid_compare = [(int, int), (int, (int, float)),
                               ([int, float], int),
                               ([int, float], (dict, float))]
        self._invalid_compare = [(int, float), (int, (dict, float)),
                                 ((int, dict), float),
                                 ((int, float), (dict, list))]
