from yggdrasil.metaschema.properties.tests import (
    test_MetaschemaProperty as parent)


class TestItemsMetaschemaProperty(parent.TestMetaschemaProperty):
    r"""Test class for ItemsMetaschemaProperty class."""
    
    _mod = 'JSONArrayMetaschemaProperties'
    _cls = 'ItemsMetaschemaProperty'
    
    def __init__(self, *args, **kwargs):
        super(TestItemsMetaschemaProperty, self).__init__(*args, **kwargs)
        nele = 3
        valid_value = [int(i) for i in range(nele)]
        valid_sing = {'type': 'int'}
        valid_mult = [{'type': 'int'} for i in range(nele)]
        invalid_sing = {'type': 'float'}
        invalid_mult = [{'type': 'float'} for i in range(nele)]
        self._valid = [(valid_value, valid_sing),
                       (valid_value, valid_mult),
                       ([int(i) for i in range(nele - 1)], valid_sing)]
        self._invalid = [([float(i) for i in range(nele)], valid_sing),
                         ([float(i) for i in range(nele)], valid_mult)]
        # ([int(i) for i in range(nele - 1)], valid_mult)]
        self._valid_compare = [(valid_sing, valid_sing),
                               (valid_sing, valid_mult),
                               (valid_mult, valid_sing),
                               (valid_mult, valid_mult)]
        self._invalid_compare = [(valid_sing, invalid_sing),
                                 (valid_sing, invalid_mult),
                                 (valid_mult, invalid_sing),
                                 (valid_mult, invalid_mult),
                                 (1, 1),
                                 (valid_mult, valid_mult[:-1])]
