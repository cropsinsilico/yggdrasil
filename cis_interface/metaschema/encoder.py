import json
from cis_interface.metaschema.datatypes import get_registered_types


_json_encoder = None


class JSONReadableEncoder(json.JSONEncoder):
    r"""Encoder class for CiS messages."""

    def default(self, o):  # pragma: no cover
        r"""Encoder that allows for expansion types."""
        for cls in get_registered_types().values():
            if (not cls._replaces_existing) and cls.validate(o):
                new_o = cls.encode_data_readable(o, None)
                return new_o
        return json.JSONEncoder.default(self, o)


# class JSONEncoder(json.JSONEncoder):
#     r"""Encoder class for CiS messages."""

#     def default(self, o):
#         r"""Encoder that allows for expansion types."""
#         for cls in get_registered_types():
#             if cls.validate(o):
#                 new_o = cls.encode_data(o, None)
#                 return new_o
#         return json.JSONEncoder.default(self, o)

    
# class JSONDecoder(json.JSONDecoder):
#     r"""Decoder class for CiS messages."""
#
#     def raw_decode(self, s, idx=0):
#         r"""Decoder that further decodes objects."""
