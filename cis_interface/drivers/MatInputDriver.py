import os
from scipy.io import loadmat
from cis_interface.backwards import pickle
from cis_interface.drivers.FileInputDriver import FileInputDriver


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

    def file_read(self):
        r"""Returned pickled data read from the .mat file.
        
        Returns:
            str: Pickled .mat dictionary of read variables.

        """
        with self.lock:
            if self.fd.tell() == (os.fstat(self.fd.fileno()).st_size - 1):
                self.debug(':file_read: eof')
                return self.eof_msg
            self.debug(':file_read: reading .mat file')
            data_dict = loadmat(self.fd, squeeze_me=False)
        self.debug(':file_read: read %s from .mat file', str(data_dict.keys()))
        data = pickle.dumps(data_dict)
        self.debug(':file_read: pickled data (len = %d)', len(data))
        return data

    def file_send(self, data):
        r"""Send pickled data as a large message.

        Args:
            data (str): Message.

        """
        with self.lock:
            self.ipc_send_nolimit(data)
