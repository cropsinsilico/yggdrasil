from cis_interface import serialize, backwards
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
    _schema = inherit_schema(FileComm._schema, 'filetype', _filetype,
                             comment={'type': 'string', 'required': False})

    def _init_before_open(self, comment=serialize._default_comment, **kwargs):
        r"""Get absolute path and set attributes."""
        self.comment = backwards.unicode2bytes(comment)
        kwargs.setdefault('read_meth', 'readline')
        super(AsciiFileComm, self)._init_before_open(**kwargs)

    def opp_comm_kwargs(self):
        r"""Get keyword arguments to initialize communication with opposite
        comm object.

        Returns:
            dict: Keyword arguments for opposite comm object.

        """
        kwargs = super(AsciiFileComm, self).opp_comm_kwargs()
        kwargs['comment'] = self.comment
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
            while flag and msg.startswith(self.comment):
                flag, msg = super(AsciiFileComm, self)._recv()
        return flag, msg
