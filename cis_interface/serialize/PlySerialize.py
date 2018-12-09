from cis_interface import backwards, serialize
from cis_interface.serialize import register_serializer
from cis_interface.serialize.DefaultSerialize import DefaultSerialize
from cis_interface.metaschema.datatypes.PlyMetaschemaType import PlyDict


@register_serializer
class PlySerialize(DefaultSerialize):
    r"""Class for serializing/deserializing .ply file formats.

    Args:
        write_header (bool, optional): If True, headers will be added to
            serialized output. Defaults to True.
        newline (str, optional): String that should be used for new lines.
            Defaults to '\n'.

    Attributes:
        write_header (bool): If True, headers will be added to serialized
            output.
        newline (str): String that should be used for new lines.
        default_rgb (list): Default color in RGB that should be used for
            missing colors.

    """
    
    _seritype = 'ply'
    _schema_properties = dict(
        newline={'type': 'unicode',
                 'default': backwards.bytes2unicode(serialize._default_newline)})
    _default_type = {'type': 'ply'}

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
        return PlyDict(self.datatype.decode_data(backwards.bytes2unicode(msg),
                                                 self.typedef))
