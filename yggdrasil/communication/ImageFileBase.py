import numpy as np
import warnings
from yggdrasil.components import create_component_class
from yggdrasil.communication.DedicatedFileBase import DedicatedFileBase
try:
    from PIL import Image
except ImportError:  # pragma: debug
    Image = None
    warnings.warn("Pillow not installed. I/O of image files will be "
                  "disabled.")


class PILFileBase(DedicatedFileBase):
    r"""Class for handling I/O from/to a JPEG file."""

    _schema_subtype_description = ('The file is read/written as JPEG.')
    _schema_properties = {
        'params': {
            'type': 'object', 'default': {},
            'description': ('Parameters that should be based to the '
                            'PIL.Image save/open command')
        }
    }
    _image_types = {
        'jpeg': ['.jpg', '.jfif', '.jpe', '.jpeg'],
        'bmp': ['.bmp'],
        'eps': ['.eps', '.ps'],
        'gif': ['.gif'],
        'png': ['.png', '.apng'],
        'tiff': ['.tiff', '.tif'],
    }
    _test_parameters = None
    _greyscale = False

    @staticmethod
    def before_registration(cls):
        r"""Operations that should be performed to modify class attributes prior
        to registration."""
        DedicatedFileBase.before_registration(cls)
        cls._extensions = cls._image_types[cls._filetype]
        cls._schema_subtype_description = f'{cls._filetype} image I/O'
        
    @classmethod
    def is_installed(cls, language=None):
        r"""Determine if the necessary libraries are installed for this
        communication class.

        Args:
            language (str, optional): Specific language that should be checked
                for compatibility. Defaults to None and all languages supported
                on the current platform will be checked. If set to 'any', the
                result will be True if this comm is installed for any of the
                supported languages.

        Returns:
            bool: Is the comm installed.

        """
        import shutil
        if cls._filetype == 'eps' and not shutil.which('gs'):
            return False
        return (language == 'python') and (Image is not None)

    def _dedicated_open(self, address, mode):
        self._external_fd = address
        return self._external_fd

    def _dedicated_close(self):
        self._external_fd = None

    def _dedicated_send(self, msg):
        if not self._external_fd:  # pragma: debug
            raise IOError("File address not set")
        im = Image.fromarray(msg)
        im.save(self._external_fd, self._filetype, **self.params)

    def _dedicated_recv(self):
        if not self._external_fd:  # pragma: debug
            raise IOError("File address not set")
        with Image.open(self._external_fd, formats=[self._filetype],
                        **self.params) as im:
            self.info(f"_dedicated_recv: Before asarray {im.getdata()}")
            try:
                out = np.asarray(im)
            except SystemError:  # pragma: debug
                out = np.array(im.getdata()).reshape(
                    im.size[0], im.size[1], 3)
            self.info(f"_dedicated_recv: After asarray {out}")
        return out

    @classmethod
    def get_testing_options(cls, **kwargs):
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
        if cls._greyscale:
            data = layer
        else:
            data = np.stack([layer, layer, layer], axis=2)
        out = {
            'kwargs': {},
            'exact_contents': False,
            'msg': data,
            'dict': False,
            'objects': [data],
            'send': [data],
            'recv': [data],
            'recv_partial': [[data]],
        }
        if cls._test_parameters:
            out.update(cls._test_parameters)
        return out


_pil_class_attr = {
    'bmp': {
        '_test_parameters': {
            'contents': (
                b'BMv\x01\x00\x00\x00\x00\x00\x006\x00\x00\x00(\x00\x00'
                b'\x00\n\x00\x00\x00\n\x00\x00\x00\x01\x00\x18\x00\x00'
                b'\x00\x00\x00@\x01\x00\x00\xc4\x0e\x00\x00\xc4\x0e\x00'
                b'\x00\x00\x00\x00\x00\x00\x00\x00\x00ZZZ[[[\\\\\\]]]'
                b'^^^___```aaabbbccc\x00\x00PPPQQQRRRSSSTTTUUUVVVWWWXXX'
                b'YYY\x00\x00FFFGGGHHHIIIJJJKKKLLLMMMNNNOOO\x00\x00<<<==='
                b'>>>???@@@AAABBBCCCDDDEEE\x00\x0022233344455566677788899'
                b'9:::;;;\x00\x00((()))***+++,,,---...///000111\x00\x00'
                b'\x1e\x1e\x1e\x1f\x1f\x1f   !!!"""###$$$%%%&&&\'\'\''
                b'\x00\x00\x14\x14\x14\x15\x15\x15\x16\x16\x16\x17\x17'
                b'\x17\x18\x18\x18\x19\x19\x19\x1a\x1a\x1a\x1b\x1b\x1b'
                b'\x1c\x1c\x1c\x1d\x1d\x1d\x00\x00\n\n\n\x0b\x0b\x0b\x0c'
                b'\x0c\x0c\r\r\r\x0e\x0e\x0e\x0f\x0f\x0f\x10\x10\x10\x11'
                b'\x11\x11\x12\x12\x12\x13\x13\x13\x00\x00\x00\x00\x00'
                b'\x01\x01\x01\x02\x02\x02\x03\x03\x03\x04\x04\x04\x05'
                b'\x05\x05\x06\x06\x06\x07\x07\x07\x08\x08\x08\t\t\t\x00'
                b'\x00')
        }
    },
    'eps': {
        '_test_parameters': {
            'contents': (
                b'%!PS-Adobe-3.0 EPSF-3.0\n%%Creator: PIL 0.1 EpsEncode\n'
                b'%%BoundingBox: 0 0 10 10\n%%Pages: 1\n%%EndComments\n'
                b'%%Page: 1 1\n%ImageData: 10 10 8 3 0 1 1 "false 3 '
                b'colorimage"\ngsave\n10 dict begin\n/buf 30 string '
                b'def\n10 10 scale\n10 10 8\n[10 0 0 -10 0 10]\n{ '
                b'currentfile buf readhexstring pop } bind\nfalse 3 '
                b'colorimage\n000000010101020202030303040404050505060'
                b'6060707070808080909090a0a0a0b0b0b0c0c0c\n0d0d0d0e0e0'
                b'e0f0f0f101010111111121212131313141414151515161616171'
                b'717181818191919\n1a1a1a1b1b1b1c1c1c1d1d1d1e1e1e1f1f1'
                b'f202020212121222222232323242424252525262626\n2727272'
                b'828282929292a2a2a2b2b2b2c2c2c2d2d2d2e2e2e2f2f2f30303'
                b'0313131323232333333\n3434343535353636363737373838383'
                b'939393a3a3a3b3b3b3c3c3c3d3d3d3e3e3e3f3f3f404040\n414'
                b'1414242424343434444444545454646464747474848484949494'
                b'a4a4a4b4b4b4c4c4c4d4d4d\n4e4e4e4f4f4f505050515151525'
                b'2525353535454545555555656565757575858585959595a5a5a\n'
                b'5b5b5b5c5c5c5d5d5d5e5e5e5f5f5f6060606161616262626363'
                b'63\n%%%%EndBinary\ngrestore end\n')
        }
    },
    'gif': {
        '_greyscale': True,
        '_test_parameters': {
            'contents': (
                b'GIF87a\n\x00\n\x00\x86\x00\x00\x00\x00\x00\x01\x01\x01'
                b'\x02\x02\x02\x03\x03\x03\x04\x04\x04\x05\x05\x05\x06'
                b'\x06\x06\x07\x07\x07\x08\x08\x08\t\t\t\n\n\n\x0b\x0b'
                b'\x0b\x0c\x0c\x0c\r\r\r\x0e\x0e\x0e\x0f\x0f\x0f\x10'
                b'\x10\x10\x11\x11\x11\x12\x12\x12\x13\x13\x13\x14\x14'
                b'\x14\x15\x15\x15\x16\x16\x16\x17\x17\x17\x18\x18\x18'
                b'\x19\x19\x19\x1a\x1a\x1a\x1b\x1b\x1b\x1c\x1c\x1c\x1d'
                b'\x1d\x1d\x1e\x1e\x1e\x1f\x1f\x1f   !!!"""###$$$%%%&&&'
                b'\'\'\'((()))***+++,,,---...///000111222333444555666777'
                b'888999:::;;;<<<===>>>???@@@AAABBBCCCDDDEEEFFFGGGHHHIII'
                b'JJJKKKLLLMMMNNNOOOPPPQQQRRRSSSTTTUUUVVVWWWXXXYYYZZZ[[['
                b'\\\\\\]]]^^^___```aaabbbccc\x00\x00\x00\x00\x00\x00'
                b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
                b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
                b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
                b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
                b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
                b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
                b',\x00\x00\x00\x00\n\x00\n\x00\x00\x08s\x00\x01\x04'
                b'\x100\x80@\x01\x03\x07\x10$P\xb0\x80A\x03\x07\x0f '
                b'D\x900\x81B\x05\x0b\x170d\xd0\xb0\x81C\x07\x0f\x1f@'
                b'\x84\x101\x82D\t\x13\'P\xa4P\xb1\x82E\x0b\x17/`\xc4'
                b'\x901\x83F\r\x1b7p\xe4\xd0\xb1\x83G\x0f\x1f?\x80\x04'
                b'\x112\x84H\x11#G\x90$Q\xb2\x84I\x13\'O\xa0D\x912\x85J'
                b'\x15+W\xb0d\xd1\xb2\x85K\x17/_\xc0\x84\x113& \x00;'
            )
        }
    },
    'png': {
        '_test_parameters': {
            'contents': (
                b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\n\x00'
                b'\x00\x00\n\x08\x02\x00\x00\x00\x02PX\xea\x00\x00\x00'
                b'\x17IDATx\x9ccd```\xc4\x03\xb8\xb8\xb8\xf0\xc8\xb2'
                b'\x8cPi\x00XE\x02?\x04\x142\x84\x00\x00\x00\x00IEND'
                b'\xaeB`\x82'
            )
        }
    },
    'tiff': {
        '_test_parameters': {
            'contents': (
                b'II*\x00\x08\x00\x00\x00\n\x00\x00\x01\x04\x00\x01\x00'
                b'\x00\x00\n\x00\x00\x00\x01\x01\x04\x00\x01\x00\x00\x00'
                b'\n\x00\x00\x00\x02\x01\x03\x00\x03\x00\x00\x00\x86\x00'
                b'\x00\x00\x03\x01\x03\x00\x01\x00\x00\x00\x01\x00\x00'
                b'\x00\x06\x01\x03\x00\x01\x00\x00\x00\x02\x00\x00\x00'
                b'\x11\x01\x04\x00\x01\x00\x00\x00\x8c\x00\x00\x00\x15'
                b'\x01\x03\x00\x01\x00\x00\x00\x03\x00\x00\x00\x16\x01'
                b'\x04\x00\x01\x00\x00\x00\n\x00\x00\x00\x17\x01\x04\x00'
                b'\x01\x00\x00\x00,\x01\x00\x00\x1c\x01\x03\x00\x01\x00'
                b'\x00\x00\x01\x00\x00\x00\x00\x00\x00\x00\x08\x00\x08'
                b'\x00\x08\x00\x00\x00\x00\x01\x01\x01\x02\x02\x02\x03'
                b'\x03\x03\x04\x04\x04\x05\x05\x05\x06\x06\x06\x07\x07'
                b'\x07\x08\x08\x08\t\t\t\n\n\n\x0b\x0b\x0b\x0c\x0c\x0c'
                b'\r\r\r\x0e\x0e\x0e\x0f\x0f\x0f\x10\x10\x10\x11\x11\x11'
                b'\x12\x12\x12\x13\x13\x13\x14\x14\x14\x15\x15\x15\x16'
                b'\x16\x16\x17\x17\x17\x18\x18\x18\x19\x19\x19\x1a\x1a'
                b'\x1a\x1b\x1b\x1b\x1c\x1c\x1c\x1d\x1d\x1d\x1e\x1e\x1e'
                b'\x1f\x1f\x1f   !!!"""###$$$%%%&&&\'\'\'((()))***+++,,,'
                b'---...///000111222333444555666777888999:::;;;<<<===>>>'
                b'???@@@AAABBBCCCDDDEEEFFFGGGHHHIIIJJJKKKLLLMMMNNNOOOPPP'
                b'QQQRRRSSSTTTUUUVVVWWWXXXYYYZZZ[[[\\\\\\]]]^^^___```aaa'
                b'bbbccc'
            )
        }
    },
    'jpeg': {
        '_test_parameters': {
            'send_kwargs': {'params': {'quality': 100}},
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
        }}
}
_pil_classes = [(x.upper(), dict(_pil_class_attr.get(x, {}), _filetype=x))
                for x in PILFileBase._image_types.keys()]
for name, attr in _pil_classes:
    create_component_class(globals(), PILFileBase,
                           f'{name}FileComm', attr)
