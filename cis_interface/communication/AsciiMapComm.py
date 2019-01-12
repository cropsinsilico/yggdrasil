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

    @classmethod
    def get_testing_options(cls):
        r"""Method to return a dictionary of testing options for this class.

        Returns:
            dict: Dictionary of variables to use for testing. Key/value pairs:
                kwargs (dict): Keyword arguments for comms tested with the
                    provided content.
                send (list): List of objects to send to test file.
                recv (list): List of objects that will be received from a test
                    file that was sent the messages in 'send'.
                contents (bytes): Bytes contents of test file created by sending
                    the messages in 'send'.

        """
        out = {'kwargs': {},
               'send': [{'args1': int(1), 'args2': 'this'},
                        {'args3': float(1), 'args4': [int(1), int(2)]}],
               'recv': [{'args1': int(1), 'args2': 'this',
                         'args3': float(1), 'args4': [int(1), int(2)]}],
               'contents': (b'args1\t1\n'
                            + b'args2\t"this"\n'
                            + b'args3\t1.0\n'
                            + b'args4\t[1, 2]\n')}
        out['msg'] = out['send'][0]
        out['dict'] = {'f0': out['msg']}
        return out

