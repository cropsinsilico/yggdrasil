from scipy.io import savemat
from cis_interface.backwards import pickle
from cis_interface.drivers.FileOutputDriver import FileOutputDriver


class MatOutputDriver(FileOutputDriver):
    r"""Class to handle output to .mat Matlab files.

    Args:
        name (str): Name of the output queue to receive messages from.
        args (str): Path to the file that messages should be written to.
        \*\*kwargs: Additional keyword arguments are passed to parent class's
            __init__ method.

    Attributes (in addition to parent class's):
        -

    """
    
    def file_recv(self):
        r"""Receive a long message.

        Returns:
            str: Received message.

        """
        with self.lock:
            return self.ipc_recv_nolimit()

    def file_write(self, data):
        r"""Write received data to file. The data is first unpickled and then
        written in .mat format.

        Args:
            data (str): Pickled dictionary of objects to write to the .mat
                file.

        Raises:
            TypeError: If the unpickled object is not a dictionary.

        """
        with self.lock:
            self.debug(':put: unpickling %s bytes', len(data))
            data_dict = pickle.loads(data)
            if not isinstance(data_dict, dict):  # pragma: debug
                raise TypeError('Unpickled object (type %s) is not a dictionary' %
                                type(data_dict))
            self.debug(':put: saving %s', str(data_dict.keys()))
            savemat(self.fd, data_dict)
            self.debug(':put: %s complete', str(data_dict.keys()))
