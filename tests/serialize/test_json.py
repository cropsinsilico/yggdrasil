import os
import uuid
from yggdrasil.serialize.JSONSerialize import encode_json, decode_json


def test_encode_json():
    r"""Test encode_json to/from file."""
    fname = f"{uuid.uuid4()}.json"
    assert not os.path.isfile(fname)
    x = {'a': 1, 'b': 2}

    class DefaultSerialize(object):
        def default(self, x):
            return str(x)
    
    try:
        with open(fname, 'w') as fd:
            encode_json(x, fd=fd, cls=DefaultSerialize)
        assert os.path.isfile(fname)
        with open(fname, 'r') as fd:
            y = decode_json(fd)
        assert y == x
    finally:
        if os.path.isfile(fname):
            os.remove(fname)
