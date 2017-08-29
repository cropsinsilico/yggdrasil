import sys
from logging import *
import os
import time
from scanf import scanf
from cis_interface.drivers.FileInputDriver import FileInputDriver
from cis_interface.io.AsciiFile import AsciiFile
from cis_interface.interface.PsiInterface import PSI_MSG_EOF


class AsciiFileInputDriver(FileInputDriver):
    r"""Class that sends lines from an ASCII file.

    Args:
        name (str): Name of the queue that messages should be sent to.  
        args (str or dict): Path to the file that messages should be read from
            or dictionary containing the filepath and other keyword arguments
            to be passed to the created AsciiFile object.
        skip_AsciiFile (bool, optional): If True, the AsciiFile instance is not
            created. Defaults to False.
        \*\*kwargs: Additional keyword arguments are passed to parent class's 
            __init__ method.

    Attributes (in additon to parent class's):
        file_kwargs (dict): Arguments used to create AsciiFile instance.
        file (:class:`AsciiFile.AsciiFile`): Associated special class for ASCII
            file.

    """
    def __init__(self, name, args, skip_AsciiFile=False, **kwargs):
        filepath = None
        if isinstance(args, str):
            filepath = args
            args = {}
        elif isinstance(args, list):
            if isinstance(args[0], str):
                filepath = args.pop(0)
            args_new = {}
            for a in args:
                if isinstance(a, dict):
                    args_new.update(**a)
                else:
                    self.info(": Ignoring argument '%s'", str(a))
            args = args_new
        elif isinstance(args, dict):
            pass
        else:  # pragma: debug
            raise TypeError("args is incorrect type, check the yaml.")
        if filepath is None:
            filepath = args.pop('filename', None)
            filepath = args.pop('filepath', filepath)
        super(AsciiFileInputDriver, self).__init__(name, filepath, **kwargs)
        self.debug('(%s)', filepath)
        self.file_kwargs = args
        if skip_AsciiFile:
            self.file = None
        else:
            self.file = AsciiFile(self.args, 'r', **args)
        self.debug('(%s): done with init', args)

    @property
    def eof_msg(self):
        r"""str: Message indicating end of file."""
        return PSI_MSG_EOF

    def close_file(self):
        r"""Close the file."""
        self.debug(':close_file()')
        with self.lock:
            self.file.close()
        
    def run(self):
        r"""Run the driver. The file is opened and then data is read from the
        file and sent to the message queue until eof is encountered or the file
        is closed.
        """
        self.debug(':run in %s', os.getcwd())
        with self.lock:
            self.file.open()
        nread = 0
        while self.file.is_open:
            with self.lock:
                if self.file.is_open:
                    eof, data = self.file.readline_full()
                else:  # pragma: debug
                    break
            if eof:
                self.debug(':run, End of file encountered')
                self.ipc_send(self.eof_msg)
                break
            if data is not None:
                self.debug(':run: read: %d bytes', len(data))
                self.ipc_send(data)
                nread += 1
        if nread == 0:  # pragma: debug
            self.debug(':run, no input')
        self.debug(':run returned')


