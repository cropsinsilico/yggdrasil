from cis_interface.communication import FileComm
from cis_interface.schema import register_component, inherit_schema
from cis_interface.serialize.AsciiMapSerialize import AsciiMapSerialize


@register_component
class AsciiMapComm(FileComm.FileComm):
    r"""Class for handling I/O from/to a ASCII map on disk.

    Args:
        name (str): The environment variable where file path is stored.
        **kwargs: Additional keywords arguments are passed to parent class.

    """

    _filetype = 'map'
    _schema_properties = inherit_schema(
        FileComm.FileComm._schema_properties,
        **AsciiMapSerialize._schema_properties)
    _default_serializer = AsciiMapSerialize
    _attr_conv = FileComm.FileComm._attr_conv + ['delimiter']
