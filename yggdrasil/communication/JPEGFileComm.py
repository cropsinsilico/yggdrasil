import cv2
import numpy as np
from yggdrasil.communication.DedicatedFileBase import DedicatedFileBase


class JPEGFileComm(DedicatedFileBase):
    r"""Class for handling I/O from/to a JPEG file."""

    _filetype = 'jpeg'
    _schema_subtype_description = ('The file is read/written as JPEG.')
    _extensions = ['.jpg', '.jpeg']

    def _dedicated_open(self, address, mode):
        self._external_fd = address
        return self._external_fd

    def _dedicated_close(self):
        self._external_fd = None

    def _dedicated_send(self, msg):
        # TODO: pass params?
        if not self._external_fd:  # pragma: debug
            raise IOError("File address not set")
        assert cv2.imwrite(self._external_fd, msg,
                           [cv2.IMWRITE_JPEG_QUALITY, 100])

    def _dedicated_recv(self):
        # TODO: pass flags?
        if not self._external_fd:  # pragma: debug
            raise IOError("File address not set")
        out = cv2.imread(self._external_fd)
        assert out is not None
        return out

    @classmethod
    def get_testing_options(cls):
        r"""Method to return a dictionary of testing options for this
        class.

        Returns:
            dict: Dictionary of variables to use for testing. Items:
                kwargs (dict): Keyword arguments for comms tested with
                    the provided content.
                send (list): List of objects to send to test file.
                recv (list): List of objects that will be received from a
                    test file that was sent the messages in 'send'.
                contents (bytes): Bytes contents of test file created by
                    sending the messages in 'send'.

        """
        layer = np.arange(100).astype('uint8').reshape((10, 10))
        data = np.stack([layer, layer, layer], axis=2)
        out = {'kwargs': {},
               'exact_contents': False,
               'msg': data,
               'dict': False,
               'objects': [data],
               'send': [data],
               'recv': [data],
               'recv_partial': [[data]],
               'contents': (
                   b'\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x00\x00'
                   b'\x01\x00\x01\x00\x00\xff\xdb\x00C\x00\x01\x01\x01'
                   b'\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01'
                   b'\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01'
                   b'\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01'
                   b'\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01'
                   b'\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01'
                   b'\x01\xff\xdb\x00C\x01\x01\x01\x01\x01\x01\x01\x01'
                   b'\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01'
                   b'\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01'
                   b'\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01'
                   b'\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01'
                   b'\x01\x01\x01\x01\x01\x01\x01\x01\x01\xff\xc0\x00'
                   b'\x11\x08\x00\n\x00\n\x03\x01"\x00\x02\x11\x01\x03'
                   b'\x11\x01\xff\xc4\x00\x1f\x00\x00\x01\x05\x01\x01'
                   b'\x01\x01\x01\x01\x00\x00\x00\x00\x00\x00\x00\x00'
                   b'\x01\x02\x03\x04\x05\x06\x07\x08\t\n\x0b\xff\xc4'
                   b'\x00\xb5\x10\x00\x02\x01\x03\x03\x02\x04\x03\x05'
                   b'\x05\x04\x04\x00\x00\x01}\x01\x02\x03\x00\x04\x11'
                   b'\x05\x12!1A\x06\x13Qa\x07"q\x142\x81\x91\xa1\x08#B'
                   b'\xb1\xc1\x15R\xd1\xf0$3br\x82\t\n\x16\x17\x18\x19'
                   b'\x1a%&\'()*456789:CDEFGHIJSTUVWXYZcdefghijstuvwxyz'
                   b'\x83\x84\x85\x86\x87\x88\x89\x8a\x92\x93\x94\x95'
                   b'\x96\x97\x98\x99\x9a\xa2\xa3\xa4\xa5\xa6\xa7\xa8'
                   b'\xa9\xaa\xb2\xb3\xb4\xb5\xb6\xb7\xb8\xb9\xba\xc2'
                   b'\xc3\xc4\xc5\xc6\xc7\xc8\xc9\xca\xd2\xd3\xd4\xd5'
                   b'\xd6\xd7\xd8\xd9\xda\xe1\xe2\xe3\xe4\xe5\xe6\xe7'
                   b'\xe8\xe9\xea\xf1\xf2\xf3\xf4\xf5\xf6\xf7\xf8\xf9'
                   b'\xfa\xff\xc4\x00\x1f\x01\x00\x03\x01\x01\x01\x01'
                   b'\x01\x01\x01\x01\x01\x00\x00\x00\x00\x00\x00\x01'
                   b'\x02\x03\x04\x05\x06\x07\x08\t\n\x0b\xff\xc4\x00'
                   b'\xb5\x11\x00\x02\x01\x02\x04\x04\x03\x04\x07\x05'
                   b'\x04\x04\x00\x01\x02w\x00\x01\x02\x03\x11\x04\x05'
                   b'!1\x06\x12AQ\x07aq\x13"2\x81\x08\x14B\x91\xa1\xb1'
                   b'\xc1\t#3R\xf0\x15br\xd1\n\x16$4\xe1%\xf1\x17\x18'
                   b'\x19\x1a&\'()*56789:CDEFGHIJSTUVWXYZcdefghijstuvw'
                   b'xyz\x82\x83\x84\x85\x86\x87\x88\x89\x8a\x92\x93'
                   b'\x94\x95\x96\x97\x98\x99\x9a\xa2\xa3\xa4\xa5\xa6'
                   b'\xa7\xa8\xa9\xaa\xb2\xb3\xb4\xb5\xb6\xb7\xb8\xb9'
                   b'\xba\xc2\xc3\xc4\xc5\xc6\xc7\xc8\xc9\xca\xd2\xd3'
                   b'\xd4\xd5\xd6\xd7\xd8\xd9\xda\xe2\xe3\xe4\xe5\xe6'
                   b'\xe7\xe8\xe9\xea\xf2\xf3\xf4\xf5\xf6\xf7\xf8\xf9'
                   b'\xfa\xff\xda\x00\x0c\x03\x01\x00\x02\x11\x03\x11'
                   b'\x00?\x00\xfeL\xf4\xdf\xd9\'\xee\xff\x00\xc4\xb3'
                   b'\xd3\xfeX\xff\x00\xf5\xab\xab_\xd9\'\x81\xff\x00'
                   b'\x12\xce\xc3\xfeX\xfb}+\xf6\x0fM\xb1\xb2\xf9\x7f'
                   b'\xd0\xed{\x7f\xcb\xbc_\xfcEukce\x81\xfe\x87k\xd0'
                   b'\x7f\xcb\xbc^\x9f\xeeP\x07\xff\xd9')
               }
        return out
