import os
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
    
    def put(self, data):
        r"""Write received data to file. The data is first unpickled and then
        written in .mat format.

        Args:
            data (str): Pickled dictionary of objects to write to the .mat
                file.

        """
        self.debug(':put: unpickling %s bytes', len(data))
        data_dict = pickle.loads(data)
        if not isinstance(data_dict, dict):  # pragma: debug
            self.error(':put unpickled object (type %s) is not a dictionary',
                       type(data_dict))
            return
        self.debug(':put: saving %s', str(data_dict.keys()))
        savemat(self.fd, data_dict)
        self.debug(':put: %s complete', str(data_dict.keys()))

    def run(self):
        r"""Run the driver. The driver will open the file and write receieved
        messages to the file as they are received until the file is closed.
        """
        self.debug(':run in %s', os.getcwd())
        try:
            with self.lock:
                self.fd = open(self.args, 'wb')
        except:  # pragma: debug
            self.exception('Could not open file.')
            return
        while self.fd is not None:
            data = self.ipc_recv_nolimit()
            if data is None:  # pragma: debug
                self.debug(':recv: closed')
                break
            self.debug(':recvd %s bytes', len(data))
            if len(data) > 0:
                with self.lock:
                    if self.fd is None:  # pragma: debug
                        self.debug(':recv: file closed')
                        break
                    else:
                        self.put(data)
            else:
                self.debug(':recv: no data')
                self.sleep()
        self.debug(':run returns')
