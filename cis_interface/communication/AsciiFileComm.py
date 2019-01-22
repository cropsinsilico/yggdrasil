from cis_interface import serialize, backwards  # , platform
from cis_interface.communication.FileComm import FileComm
from cis_interface.schema import register_component, inherit_schema


@register_component
class AsciiFileComm(FileComm):
    r"""Class for handling I/O from/to a file on disk.

    Args:
        name (str): The environment variable where communication address is
            stored.
        comment (str, optional): String indicating a comment. If 'read_meth'
            is 'readline' and this is provided, lines starting with a comment
            will be skipped.
        **kwargs: Additional keywords arguments are passed to parent class.

    Attributes:
        comment (str): String indicating a comment.

    """

    _filetype = 'ascii'
    _schema_properties = inherit_schema(
        FileComm._schema_properties,
        {'comment': {'type': 'string',
                     'default': backwards.as_str(serialize._default_comment)}})
    _attr_conv = FileComm._attr_conv + ['comment']

    def _init_before_open(self, **kwargs):
        r"""Get absolute path and set attributes."""
        kwargs.setdefault('read_meth', 'readline')
        super(AsciiFileComm, self)._init_before_open(**kwargs)

    @classmethod
    def get_testing_options(cls, **kwargs):
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
        kwargs.setdefault('read_meth', 'readline')
        out = super(AsciiFileComm, cls).get_testing_options(**kwargs)
        comment = backwards.as_bytes(
            cls._schema_properties['comment']['default'] + 'Comment\n')
        out['send'].append(comment)
        out['contents'] = b''.join(out['send'])
        # out['contents'] = out['contents'].replace(b'\n', platform._newline)
        out['dict'] = {'f0': out['msg']}
        return out
    
    def opp_comm_kwargs(self):
        r"""Get keyword arguments to initialize communication with opposite
        comm object.

        Returns:
            dict: Keyword arguments for opposite comm object.

        """
        kwargs = super(AsciiFileComm, self).opp_comm_kwargs()
        kwargs['comment'] = self.serializer.comment
        return kwargs

    def _recv(self, timeout=0):
        r"""Reads message from a file.

        Args:
            timeout (float, optional): Time in seconds to wait for a message.
                Defaults to self.recv_timeout. Unused.

        Returns:
            tuple (bool, str): Success or failure of reading from the file and
                the read messages as bytes.

        """
        flag, msg = super(AsciiFileComm, self)._recv()
        if self.read_meth == 'readline':
            while flag and msg.startswith(backwards.as_bytes(self.comment)):
                flag, msg = super(AsciiFileComm, self)._recv()
        return flag, msg
