from cis_interface import backwards
from cis_interface.schema import register_component, inherit_schema
from cis_interface.types.CisBaseType import CisBaseType


@register_component
class CisBytesType(CisBaseType):
    r"""Type associated with bytes."""

    _datatype = 'bytes'
    _schema = inherit_schema(CisBaseType._schema, 'datatype', _datatype)
    _python_type = backwards.bytes_type
    _type_string = 'B'
    _empty_msg = backwards.unicode2bytes('')

    def to_json(self, obj):
        r"""Return the JSON serializable form of the object.

        Args:
            obj (object): Object to be serialized.

        Returns:
            object: JSON serializable representation of the object.

        """
        return backwards.bytes2unicode(obj)

    def from_json(self, obj):
        r"""Return the deserialized form of the JSON serialized object.
        
        Args:
            obj (object): Object to be deserialized.

        Returns:
            object: Deserialized object.

        """
        return backwards.unicode2bytes(obj)
