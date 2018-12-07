import json
from cis_interface.datatypes import get_registered_types


_json_encoder = None


class CisJSONEncoder(json.JSONEncoder):
    r"""Encoder class for CiS messages."""

    def default(self, o):
        r"""Encoder that allows for expansion types."""
        for cls in get_registered_types():
            if cls.validate(o):
                return json.JSONEncoder.default(self, cls.encode_data(o, None))
        return json.JSONEncoder.default(self, o)


# class CisJSONDecoder(json.JSONDecoder):
#     r"""Decoder class for CiS messages."""
#
#     def raw_decode(self, s, idx=0):
#         r"""Decoder that further decodes objects."""
