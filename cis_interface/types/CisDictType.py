from cis_interface.schema import register_component, inherit_schema
from cis_interface.types import from_type_info
from cis_interface.types.CisBaseType import CisBaseType


@register_component
class CisDictType(CisBaseType):
    r"""Type associated with mappings from keys to other types.

    Args:
        type_dict (dict): A dictionary of the key/type pairs that are in a
            dict of this type.

    Attributes:
        type_dict (dict): A dict of the types that are in a dict of this type.

    """

    _datatype = 'dict'
    _schema = inherit_schema(CisBaseType._schema, 'datatype', _datatype,
                             type_dict={'type': 'dict', 'required': False,
                                        'valueschema': {'type': 'dict',
                                                        'schema': 'type'}})
    _python_type = dict
    _type_string = 'M'
    _empty_msg = {}

    def __init__(self, type_dict, *args, **kwargs):
        self.type_dict = type_dict
        super(CisDictType, self).__init__(*args, **kwargs)

    @classmethod
    def from_type_info(cls, obj, *args, **kwargs):
        r"""Construct type instance from data structure."""
        assert(isinstance(obj, dict))
        type_dict = {k: from_type_info(v) for k, v in obj.items()}
        return cls(type_dict, *args, **kwargs)
        
    @property
    def type_info(self):
        r"""obj: Python object containing information about the data type."""
        return {k: v.type_info for k, v in self.type_dict.items()}

    def is_type(self, obj):
        r"""Check that object is a dict type.

        Args:
            obj (object): Python objected to be tested.

        Returns:
            bool: Truth of if the provided object is a stirng.

        """
        if not isinstance(obj, self._python_type):
            return False
        if len(obj) != len(self.type_dict):
            return False
        for k, v in self.type_dict.items():
            if (k not in obj) or (not v.is_type(obj[k])):
                return False
        return True

    def to_json(self, obj):
        r"""Return the JSON serializable form of the object.

        Args:
            obj (object): Object to be serialized.

        Returns:
            object: JSON serializable representation of the object.

        """
        out = {k: v.to_json(obj[k]) for k, v in self.type_dict.items()}
        return out

    def from_json(self, obj):
        r"""Return the deserialized form of the JSON serialized object.
        
        Args:
            obj (object): Object to be deserialized.

        Returns:
            object: Deserialized object.

        """
        out = {k: v.from_json(obj[k]) for k, v in self.type_dict.items()}
        return out
