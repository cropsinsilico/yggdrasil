from cis_interface import backwards
from cis_interface.serialize import register_serializer
from cis_interface.serialize.PlySerialize import PlySerialize
from cis_interface.metaschema.datatypes.ObjMetaschemaType import ObjDict


@register_serializer
class ObjSerialize(PlySerialize):
    r"""Class for serializing/deserializing .obj file formats. Reader
    adapted from https://www.pygame.org/wiki/OBJFileLoader."""

    _seritype = 'obj'
    _default_type = {'type': 'obj'}

    def func_serialize(self, args):
        r"""Serialize a message.

        Args:
            args: List of arguments to be formatted or numpy array to be
                serialized.

        Returns:
            bytes, str: Serialized message.

        """
        return backwards.unicode2bytes(self.datatype.encode_data(args, self.typedef))

    def func_deserialize(self, msg):
        r"""Deserialize a message.

        Args:
            msg: Message to be deserialized.

        Returns:
            obj: Deserialized message.

        """
        return ObjDict(self.datatype.decode_data(backwards.bytes2unicode(msg),
                                                 self.typedef))
