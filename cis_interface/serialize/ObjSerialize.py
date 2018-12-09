from cis_interface.serialize import register_serializer
from cis_interface.serialize.PlySerialize import PlySerialize


@register_serializer
class ObjSerialize(PlySerialize):
    r"""Class for serializing/deserializing .obj file formats. Reader
    adapted from https://www.pygame.org/wiki/OBJFileLoader."""

    _seritype = 'obj'
    _default_type = {'type': 'obj'}
