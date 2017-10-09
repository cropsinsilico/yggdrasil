# from logging import debug, error, exception
import os
from cis_interface.communication.FileComm import _N_FILES, FileComm
from cis_interface.dataio.AsciiFile import AsciiFile


class AsciiFileComm(FileComm):
    r"""Class for handling I/O from/to a file on disk.

    Args:
        name (str): The environment variable where communication address is
            stored.
        **kwargs: Additional keywords arguments are passed to parent class.

    Attributes:
        file_kwargs (dict): Keyword arguments for the AsciiFile instance.
        file (AsciiFile): Instance for read/writing to/from file.

    """
    def __init__(self, name, dont_open=False, skip_AsciiFile=False, **kwargs):
        file_keys = ['comment', 'newline']
        file_kwargs = {}
        for k in file_keys:
            if k in kwargs:
                file_kwargs[k] = kwargs.pop(k)
        self.file_kwargs = file_kwargs
        self.file = None
        super(AsciiFileComm, self).__init__(name, dont_open=True, **kwargs)
        if not skip_AsciiFile:
            if self.direction == 'recv':
                self.file = AsciiFile(self.address, 'r', **self.file_kwargs)
            else:
                if self.append:
                    self.file = AsciiFile(self.address, 'a', **self.file_kwargs)
                else:
                    self.file = AsciiFile(self.address, 'w', **self.file_kwargs)
            if not dont_open:
                self.open()
        else:
            self.file = None

    def opp_comm_kwargs(self):
        r"""Get keyword arguments to initialize communication with opposite
        comm object.

        Returns:
            dict: Keyword arguments for opposite comm object.

        """
        kwargs = super(AsciiFileComm, self).opp_comm_kwargs()
        kwargs['comment'] = self.file.comment
        kwargs['newline'] = self.file.newline
        kwargs['open_as_binary'] = self.file.open_as_binary
        return kwargs

    def open(self):
        r"""Open the file."""
        global _N_FILES
        self.file.open()
        _N_FILES += 1

    def close(self):
        r"""Close the file."""
        self.file.close()

    @property
    def is_open(self):
        r"""bool: True if the connection is open."""
        return self.file.is_open

    @property
    def fd(self):
        r"""Associated file identifier."""
        if self.file is None:
            return None
        else:
            return self.file.fd

    def _send(self, msg):
        r"""Write message to a file.

        Args:
            msg (bytes, str): Data to write to the file.

        Returns:
            bool: Success or failure of writing to the file.

        """
        self.file.writeline_full(msg)
        self.file.fd.flush()
        return True

    def _recv(self, timeout=0, **kwargs):
        r"""Reads message from a file.

        Returns:
            tuple(bool, str): Success or failure of reading from the file.

        """
        eof, data = self.file.readline(**kwargs)
        if eof:
            data = self.eof_msg
        return (True, data)
