import yaml
from cis_interface import backwards
from cis_interface.serialize import register_serializer
from cis_interface.serialize.DefaultSerialize import DefaultSerialize


@register_serializer
class YAMLSerialize(DefaultSerialize):
    r"""Class for serializing a python object into a bytes message using YAML."""

    _seritype = 'yaml'
    _schema_properties = dict(
        DefaultSerialize._schema_properties,
        indent={'type': 'int', 'default': 4},
        encoding={'type': 'string', 'default': 'utf-8'},
        default_flow_style={'type': 'boolean', 'default': False})
    _default_type = {'type': 'object'}

    def func_serialize(self, args):
        r"""Serialize a message.

        Args:
            args (obj): Python object to be serialized.

        Returns:
            bytes, str: Serialized message.

        """
        # Convert bytes to str because JSON cannot serialize bytes by default
        if not backwards.PY2:  # pragma: Python 3
            args = backwards.as_str(args, recurse=True,
                                    convert_types=(backwards.bytes_type,),
                                    allow_pass=True)
        out = yaml.dump(args, indent=self.indent, encoding=self.encoding,
                        default_flow_style=self.default_flow_style)
        return out

    def func_deserialize(self, msg):
        r"""Deserialize a message.

        Args:
            msg (str, bytes): Message to be deserialized.

        Returns:
            obj: Deserialized Python object.

        """
        out = yaml.safe_load(msg)
        return out

    @classmethod
    def get_testing_options(cls, **kwargs):
        r"""Method to return a dictionary of testing options for this class.

        Returns:
            dict: Dictionary of variables to use for testing. Key/value pairs:
                kwargs (dict): Keyword arguments for comms tested with the
                    provided content.
                empty (object): Object produced from deserializing an empty
                    message.
                objects (list): List of objects to be serialized/deserialized.
                extra_kwargs (dict): Extra keyword arguments not used to
                    construct type definition.
                typedef (dict): Type definition resulting from the supplied
                    kwargs.
                dtype (np.dtype): Numpy data types that is consistent with the
                    determined type definition.

        """
        iobj = {'a': ['b', int(1), float(1.0)], 'c': {'z': 'hello'}}
        out = {'kwargs': {},
               'empty': {}, 'dtype': None,
               'extra_kwargs': {},
               'objects': [iobj],
               'typedef': {'type': 'object'}}
        out['contents'] = b'a:\n- b\n- 1\n- 1.0\nc:\n    z: hello\n'
        return out
