from cis_interface import backwards, serialize
from cis_interface.serialize import register_serializer
from cis_interface.serialize.DefaultSerialize import DefaultSerialize


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
