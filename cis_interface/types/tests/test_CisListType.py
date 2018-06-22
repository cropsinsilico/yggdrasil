import copy
from cis_interface import backwards
from cis_interface.types.tests import test_CisBaseType as parent


class TestCisListType(parent.TestCisBaseType):
    r"""Test class for CisListType class."""

    def __init__(self, *args, **kwargs):
        super(TestCisListType, self).__init__(*args, **kwargs)
        self._cls = 'CisListType'
        self._objects = [[backwards.unicode2bytes(l) for l in self.file_lines]]
        _typ_map = {'L': ['S', 'B'], 'M': {'a': 'S', 'b': 'B'}}
        _obj_map = {'S': 'hello', 'B': backwards.unicode2bytes('hello')}
        _typ_ord = ['S', 'B', 'L', 'M']
        self._type_info = []
        self._objects = [[]]
        for t in _typ_ord:
            tinfo = _typ_map.get(t, t)
            if isinstance(tinfo, list):
                _obj_map[t] = [_obj_map[it] for it in tinfo]
            elif isinstance(tinfo, dict):
                _obj_map[t] = {k: _obj_map[v] for k, v in tinfo.items()}
            self._type_info.append(tinfo)
            self._objects[0].append(_obj_map[t])
        # self._objects.append(tuple(self._objects[0]))

    def test_is_type_contents(self):
        r"""Test is_type in cause where a field is incorrect."""
        assert(not self.instance.is_type([]))
        obj = copy.deepcopy(self._objects[0])
        obj[0] = None
        assert(not self.instance.is_type(obj))
