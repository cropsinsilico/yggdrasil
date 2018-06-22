from cis_interface.schema import register_component, inherit_schema
from cis_interface.types import from_type_info
from cis_interface.types.CisBaseType import CisBaseType


@register_component
class CisListType(CisBaseType):
    r"""Type associated with sequencies of other types.

    Args:
        type_list (list): A list of the types that are in a list of this type.

    Attributes:
        type_list (list): A list of the types that are in a list of this type.

    """

    _datatype = 'list'
    _schema = inherit_schema(CisBaseType._schema, 'datatype', _datatype,
                             subtypes={'type': 'list', 'required': False,
                                       'schema': {'type': 'dict',
                                                  'schema': 'type'}})
    _python_type = (list, tuple)
    _type_string = 'L'
    _empty_msg = []

    def __init__(self, type_list, *args, **kwargs):
        self.type_list = type_list
        super(CisListType, self).__init__(*args, **kwargs)

    @classmethod
    def from_type_info(cls, obj, *args, **kwargs):
        r"""Construct type instance from data structure."""
        assert(isinstance(obj, list))
        type_list = [from_type_info(o) for o in obj]
        return cls(type_list, *args, **kwargs)
        
    @property
    def type_info(self):
        r"""obj: Python object containing information about the data type."""
        return [t.type_info for t in self.type_list]

    def is_type(self, obj):
        r"""Check that object is a list type.

        Args:
            obj (object): Python objected to be tested.

        Returns:
            bool: Truth of if the provided object is a stirng.

        """
        if not isinstance(obj, self._python_type):
            return False
        if len(obj) != len(self.type_list):
            return False
        for t, o in zip(self.type_list, obj):
            if not t.is_type(o):
                return False
        return True

    def to_json(self, obj):
        r"""Return the JSON serializable form of the object.

        Args:
            obj (object): Object to be serialized.

        Returns:
            object: JSON serializable representation of the object.

        """
        out = []
        for io, it in zip(obj, self.type_list):
            out.append(it.to_json(io))
        return out

    def from_json(self, obj):
        r"""Return the deserialized form of the JSON serialized object.
        
        Args:
            obj (object): Object to be deserialized.

        Returns:
            object: Deserialized object.

        """
        out = []
        for io, it in zip(obj, self.type_list):
            out.append(it.from_json(io))
        return out
