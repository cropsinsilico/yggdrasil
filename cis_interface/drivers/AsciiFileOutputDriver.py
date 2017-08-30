import sys
from logging import *
import os
import time
from scanf import scanf
from cis_interface.interface.PsiInterface import PSI_MSG_EOF
from cis_interface.drivers.FileOutputDriver import FileOutputDriver
from cis_interface.dataio.AsciiFile import AsciiFile


class AsciiFileOutputDriver(FileOutputDriver):
    r"""Class to handle output line by line to an ASCII file.

    Args:
        name (str): Name of the output queue to receive messages from.
        args (str or dict): Path to the file that messages should be written to
            or dictionary containing the filepath and other keyword arguments
            to be passed to the created AsciiFile object. 
        skip_AsciiFile (bool, optional): If True, the AsciiFile instance is not
            created. Defaults to False. 
        \*\*kwargs: Additional keyword arguments are passed to parent class's 
            __init__ method. 

    Attributes (in addition to parent class's): 
        file_kwargs (dict): Arguments used to create AsciiFile instance. 
        file (:class:`AsciiFile.AsciiFile`): Associated special class for ASCII
            file.

    """
    
    def __init__(self, name, args, skip_AsciiFile=False, **kwargs):
        filepath = None
        self.args_ignored = []
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
                    self.args_ignored.append(a)
            args = args_new
        elif not isinstance(args, dict):  # pragma: debug
            raise TypeError("args is incorrect type, check the yaml.")
        if filepath is None:
            filepath = args.pop('filename', None)
            filepath = args.pop('filepath', filepath) 
        super(AsciiFileOutputDriver, self).__init__(name, filepath, **kwargs)
        self.debug('(%s)', filepath)
        for a in self.args_ignored:
            self.info(": Ignoring argument '%s'", str(a))
        self.file_kwargs = args
        self.file_kwargs['format_str'] = ''
        if skip_AsciiFile:
            self.file = None
        else:
            self.file = AsciiFile(filepath, 'w', **self.file_kwargs)
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
        r"""Run the driver. The driver will open the file and write receieved
        messages to the file as they are received until the file is closed.
        """
        self.debug(':run in %s', os.getcwd())
        try:
            with self.lock:
                self.file.open()
        except:  # pragma: debug
            self.exception('Could not open file.')
            return
        while self.file.is_open:
            data = self.ipc_recv()
            if data is None:
                self.debug(':recv: closed')
                break
            self.debug(':recvd %s bytes', len(data))
            if data == self.eof_msg:
                self.debug(':recv: end of file')
                break
            elif len(data) > 0:
                with self.lock:
                    if self.file.is_open:
                        self.file.writeline_full(data)
                    else:  # pragma: debug
                        break
            else:
                self.debug(':recv: no data')
                self.sleep()
        self.debug(':run returned')


