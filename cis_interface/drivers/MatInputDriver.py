from cis_interface.drivers.FileInputDriver import FileInputDriver
from cis_interface.serialize import MatSerialize, PickleSerialize


class MatInputDriver(FileInputDriver):
    r"""Class that sends pickled dictionaries of matricies read from a .mat
    file.

    Args:
        name (str): Name of the queue that messages should be sent to.
        args (str): Path to the .mat file that messages should be read from.
        **kwargs: Additional keyword arguments are passed to parent class.

    """
    def __init__(self, name, args, **kwargs):
        icomm_kws = kwargs.get('icomm_kws', {})
        ocomm_kws = kwargs.get('ocomm_kws', {})
        icomm_kws.setdefault('serializer', MatSerialize.MatSerialize())
        ocomm_kws.setdefault('serializer', PickleSerialize.PickleSerialize())
        kwargs['icomm_kws'] = icomm_kws
        kwargs['ocomm_kws'] = ocomm_kws
        super(MatInputDriver, self).__init__(name, args, **kwargs)
        # if self.fd.tell() == (os.fstat(self.fd.fileno()).st_size - 1):
        # self.debug(':file_read: eof')
        # return self.eof_msg
