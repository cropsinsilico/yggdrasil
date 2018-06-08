from cis_interface.communication.PlyFileComm import PlyFileComm
from cis_interface.schema import register_component


@register_component
class ObjFileComm(PlyFileComm):
    r"""Class for handling I/O from/to a .obj file on disk.

    Args:
        name (str): The environment variable where communication address is
            stored.
        **kwargs: Additional keywords arguments are passed to parent class.

    """

    _filetype = 'obj'

    def _init_before_open(self, serializer_kwargs=None, **kwargs):
        if serializer_kwargs is None:
            serializer_kwargs = {}
        serializer_kwargs.setdefault('stype', 9)
        kwargs['serializer_kwargs'] = serializer_kwargs
        super(ObjFileComm, self)._init_before_open(**kwargs)
