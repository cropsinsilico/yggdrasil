from yggdrasil.communication import FileComm
from yggdrasil.schema import register_component, inherit_schema
from yggdrasil.serialize.JSONSerialize import JSONSerialize


@register_component
class JSONFileComm(FileComm.FileComm):
    r"""Class for handling I/O from/to a JSON file on disk.

    Args:
        name (str): The environment variable where file path is stored.
        **kwargs: Additional keywords arguments are passed to parent class.

    """

    _filetype = 'json'
    _schema_properties = inherit_schema(
        FileComm.FileComm._schema_properties,
        **JSONSerialize._schema_properties)
    _default_serializer = JSONSerialize

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
        out = super(JSONFileComm, cls).get_testing_options()
        out['recv'] = out['send']
        return out
