import sys
from logging import *
import os
import time
from scanf import scanf
from cis_interface.drivers.AsciiFileOutputDriver import AsciiFileOutputDriver
from cis_interface.drivers.FileOutputDriver import FileOutputDriver
from cis_interface.io.AsciiTable import AsciiTable


class AsciiTableOutputDriver(AsciiFileOutputDriver):
    r"""Class to handle output of received messages to an ASCII table. 

    Args:
        name (str): Name of the output queue to receive messages from.  
        args (str or dict): Path to the file that messages should be written to
            or dictionary containing the filepath and other keyword arguments
            to be passed to the created AsciiTable object.
        \*\*kwargs: Additional keyword arguments are passed to parent class's
            __init__ method.

    Attributes (in additon to parent class's):  
        file (:class:`AsciiTable.AsciiTable`): Associated special class for
            ASCII table.
        as_array (bool): If True, the table contents are received all at once 
            as an array. Defaults to False if not set in args dict.

    """
    def __init__(self, name, args, **kwargs):
        super(AsciiTableOutputDriver, self).__init__(
            name, args, skip_AsciiFile=True, **kwargs)
        self.debug('(%s)', args)
        self.as_array = self.file_kwargs.pop('as_array', False)
        self.file_kwargs['format_str'] = ''
        self.file = AsciiTable(self.args, 'w', **self.file_kwargs)
        self.debug('(%s): done with init', args)

    def run(self):
        r"""Run the driver. The format string is received then output is written
        to the file as it is received from the message queue until eof is 
        encountered or the file is closed.
        """
        self.debug(':run in %s', os.getcwd())
        fmt = self.recv_wait()
        if fmt is None:
            self.debug(':recv: did not receive format string')
            return
        fmt = fmt.decode('string_escape')
        self.file.update_format_str(fmt)
        if self.as_array:
            while True:
                data = self.ipc_recv_nolimit()
                if data is None:
                    self.debug(':recv: closed')
                    break
                self.debug(':recvd %s bytes', len(data))
                if len(data) > 0:
                    with self.lock:
                        self.file.write_bytes(data, order='F')
                    break
                else:
                    self.debug(':recv: no data')
                    self.sleep()
        else:
            with self.lock:
                self.file.open()
                self.file.writeformat()
            while self.file.is_open:
                data = self.ipc_recv_nolimit()
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
                            self.file.writeline_full(data, validate=True)
                        else:
                            break
                else:
                    self.debug(':recv: no data')
                    self.sleep()
        self.debug(':run returned')


