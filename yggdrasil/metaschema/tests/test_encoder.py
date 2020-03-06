import io as sio
from collections import OrderedDict
from yggdrasil.metaschema import encoder
from yggdrasil.tests import assert_raises


class TestClass(object):  # pragma: no cover
    pass


def test_JSONEncoder():
    r"""Test JSONEncoder error."""
    x = TestClass()
    assert_raises(TypeError, encoder.encode_json, x)


def test_encode_yaml():
    r"""Test encode_yaml with dict representer and file."""
    x = OrderedDict([('a', 1), ('b', 2)])
    fd = sio.StringIO()
    encoder.encode_yaml(x, fd=fd, sorted_dict_type=OrderedDict)
    fd.close()
