from cis_interface.drivers.FileOutputDriver import FileOutputDriver
from cis_interface.serialize import MatSerialize, PickleSerialize


class MatOutputDriver(FileOutputDriver):
    r"""Class to handle output to .mat Matlab files.

    Args:
        name (str): Name of the output queue to receive messages from.
        args (str): Path to the file that messages should be written to.
        **kwargs: Additional keyword arguments are passed to parent class.

    """
    def __init__(self, name, args, **kwargs):
        icomm_kws = kwargs.get('icomm_kws', {})
        ocomm_kws = kwargs.get('ocomm_kws', {})
        icomm_kws.setdefault('serializer', PickleSerialize.PickleSerialize())
        ocomm_kws.setdefault('serializer', MatSerialize.MatSerialize())
        kwargs['icomm_kws'] = icomm_kws
        kwargs['ocomm_kws'] = ocomm_kws
        super(MatOutputDriver, self).__init__(name, args, **kwargs)
