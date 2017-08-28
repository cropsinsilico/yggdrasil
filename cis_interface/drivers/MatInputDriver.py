import sys
from logging import *
import os
import time
from scanf import scanf
from scipy.io import loadmat
from cis_interface.backwards import pickle
from FileInputDriver import FileInputDriver


class MatInputDriver(FileInputDriver):
    r"""Class that sends pickled dictionaries of matricies read from a .mat 
    file.

    Args:
        name (str): Name of the queue that messages should be sent to.
        args (str): Path to the .mat file that messages should be read from.
        \*\*kwargs: Additional keyword arguments are passed to parent class's
            __init__ method. 

    Attributes (in addition to parent class's):
        -

    """

    def get(self):
        r"""Returned pickled data read from the .mat file.
        
        Returns:
            data (str): Pickled .mat dictionary of read variables.

        """
        if self.fd.tell() == (os.fstat(self.fd.fileno()).st_size-1):
            self.debug(':get: eof')
            return ''
        self.debug(':get: reading .mat file')
        data_dict = loadmat(self.fd, squeeze_me=False)
        self.debug(':get: read %s from .mat file', str(data_dict.keys()))
        data = pickle.dumps(data_dict)
        self.debug(':get: pickled data (len = %d)', len(data))
        return data

    def run(self):
        r"""Run the driver. The .mat file is opened and contents are read 
        and then sent to the message queue until EOF is encountered or the file
        is closed.
        """
        self.debug(':run in %s', os.getcwd())
        try:
            with self.lock:
                self.fd = open(self.args, 'rb')
        except:
            self.exception('Could not open file.')
            return
        while self.fd is not None:
            with self.lock:
                if self.fd is None:
                    self.debug(':run: file closed')
                    return
                else:
                    data = self.get()
            self.debug(':run: read: %d bytes', len(data))
            if len(data) == 0:
                self.debug(':run: end of file')
                break
            else:
                self.ipc_send_nolimit(data)
        self.debug(':run returned')
        
