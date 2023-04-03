import os
import uuid
from collections import OrderedDict
from yggdrasil.serialize.YAMLSerialize import encode_yaml, decode_yaml


def test_encode_yaml():
    r"""Test encode_yaml to/from file."""
    fname = f"{uuid.uuid4()}.yaml"
    assert not os.path.isfile(fname)
    x = {'a': 1, 'b': 2}
    try:
        with open(fname, 'w') as fd:
            encode_yaml(x, fd=fd, sorted_dict_type=OrderedDict)
        assert os.path.isfile(fname)
        with open(fname, 'r') as fd:
            y = decode_yaml(fd)
        assert y == x
    finally:
        if os.path.isfile(fname):
            os.remove(fname)
