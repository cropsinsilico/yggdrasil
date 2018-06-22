import json
from cis_interface import backwards
from cis_interface.schema import register_component


@register_component
class CisBaseType(object):
    r"""Base type."""

    _datatype = 'null'
    _schema_type = 'type'
    _schema = dict(datatype={'type': 'string', 'required': True})
    _python_type = type(None)
    _type_string = 'N'
    _empty_msg = None

    def __repr__(self):
        return self.type_json

    @classmethod
    def from_type_info(cls, obj, *args, **kwargs):
        r"""Construct type instance from data structure."""
        assert(obj == cls._type_string)
        return cls(*args, **kwargs)

    @property
    def type_info(self):
        r"""obj: Python object containing information about the data type."""
        return self._type_string

    @property
    def type_json(self):
        r"""str: JSON representation of the type."""
        return json.dumps(self.type_info, sort_keys=True)

    @property
    def empty_msg(self):
        r"""str: Empty message."""
        return self._empty_msg

    def __eq__(self, other):
        if hasattr(other, 'type_json'):
            return (self.type_json == other.type_json)
        else:
            return False

    def is_type(self, obj):
        r"""Check that object is the desired type type.

        Args:
            obj (object): Python objected to be tested.

        Returns:
            bool: Truth of if the provided object is the correct type.

        """
        return isinstance(obj, self._python_type)

    def to_json(self, obj):
        r"""Return the JSON serializable form of the object.

        Args:
            obj (object): Object to be serialized.

        Returns:
            object: JSON serializable representation of the object.

        """
        return obj

    def from_json(self, obj):
        r"""Return the deserialized form of the JSON serialized object.
        
        Args:
            obj (object): Object to be deserialized.

        Returns:
            object: Deserialized object.

        """
        return obj

    def serialize(self, obj):
        r"""Serialize a message.

        Args:
            obj (object): Python object to be formatted.

        Returns:
            bytes, str: Serialized message.

        Raises:
            TypeError: If the provided argument is not the correct type.
            TypeError: If returned msg is not bytes type (str on Python 2).


        """
        if not self.is_type(obj):
            raise TypeError("Input object is not the correct type.")
        msg = backwards.unicode2bytes(json.dumps(self.to_json(obj),
                                                 sort_keys=True))
        if not isinstance(msg, backwards.bytes_type):  # pragma: debug
            raise TypeError("Serialization function did not yield bytes type.")
        return msg
    
    def deserialize(self, msg):
        r"""Deserialize a message.

        Args:
            msg (str, bytes): Message to be deserialized.

        Returns:
            tuple(obj, dict): Deserialized message and header information.

        Raises:
            TypeError: If msg is not bytes type (str on Python 2).
            TypeError: If deserialized object is not correct type.

        """
        if not isinstance(msg, backwards.bytes_type):
            raise TypeError("Message to be deserialized is not bytes type.")
        if len(msg) == 0:
            obj = self._empty_msg
        else:
            obj = self.from_json(json.loads(backwards.bytes2unicode(msg)))
            if not self.is_type(obj):  # pragma: debug
                raise TypeError("Deserialized object is not the correct type.")
        return obj
