from cis_interface.serialize import DefaultSerialize
from cis_interface.serialize import AsciiTableSerialize
from cis_interface.serialize import PickleSerialize
from cis_interface.serialize import MatSerialize


def get_serializer(stype=0, **kwargs):
    r"""Create a serializer from the provided information.

    Args:
        stype (int, optional): Integer code specifying which serializer to
            use. Defaults to 0.
        **kwargs: Additional keyword arguments are passed to the serializer
            class.

    Returns:
        DefaultSerializer: Serializer based on provided information.

    """
    if stype in [0, 1]:
        cls = DefaultSerialize.DefaultSerialize
    elif stype in [2, 3]:
        cls = AsciiTableSerialize.AsciiTableSerialize
    elif stype == 4:
        cls = PickleSerialize.PickleSerialize
    elif stype == 5:
        cls = MatSerialize.MatSerialize
    else:
        raise RuntimeError("Unknown serializer type code: %d" % stype)
    return cls(**kwargs)
    

__all__ = ['DefaultSerialize', 'AsciiTableSerialize',
           'MatSerialize', 'PickleSerialize']
