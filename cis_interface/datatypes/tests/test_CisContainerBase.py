import copy
import numpy as np
import nose.tools as nt
from cis_interface import backwards
from cis_interface.datatypes.CisContainerBase import CisContainerBase


_vallist = [np.float32(1),
            backwards.unicode2bytes('hello'),
            {'nested': np.int64(2)}]
_deflist = [{'typename': 'float',
             'precision': 32,
             'units': ''},
            {'typename': 'string',
             'precision': 40,
             'units': ''},
            {'typename': 'map',
             'contents': {'nested': {'typename': 'int',
                                     'precision': 64,
                                     'units': ''}}}]
_typedef = []
for v in _deflist:
    itypedef = {'typename': v['typename']}
    if v['typename'] in ['map', 'set']:
        itypedef['contents'] = copy.deepcopy(v['contents'])
    _typedef.append(itypedef)
_count = len(_vallist)


def test_container_errors():
    r"""Test implementation errors on bare container class."""
    nt.assert_raises(NotImplementedError, CisContainerBase._iterate, None)
    nt.assert_raises(NotImplementedError, CisContainerBase._assign, None, None, None)
    nt.assert_raises(NotImplementedError, CisContainerBase._has_element, None, None)
