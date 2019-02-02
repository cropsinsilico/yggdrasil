from yggdrasil.communication import FileComm
from yggdrasil.schema import register_component, inherit_schema
from yggdrasil.serialize.YAMLSerialize import YAMLSerialize


@register_component
class YAMLFileComm(FileComm.FileComm):
    r"""Class for handling I/O from/to a YAML file on disk.

    Args:
        name (str): The environment variable where file path is stored.
        **kwargs: Additional keywords arguments are passed to parent class.

    """

    _filetype = 'yaml'
    _schema_properties = inherit_schema(
        FileComm.FileComm._schema_properties,
        **YAMLSerialize._schema_properties)
    _default_serializer = YAMLSerialize

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
        out = super(YAMLFileComm, cls).get_testing_options()
        out['recv'] = out['send']
        return out
