from cis_interface import backwards
from cis_interface.schema import register_component, inherit_schema
from cis_interface.types.CisBaseType import CisBaseType


@register_component
class CisStringType(CisBaseType):
    r"""Type associated with strings."""

    _datatype = 'string'
    _schema = inherit_schema(CisBaseType._schema, 'datatype', _datatype)
    _python_type = backwards.string_type
    _type_string = 'S'
    _empty_msg = backwards.bytes2unicode('')
