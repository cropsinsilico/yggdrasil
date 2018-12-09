from cis_interface import backwards, serialize
from cis_interface.communication.AsciiTableComm import AsciiTableComm
from cis_interface.schema import register_component, inherit_schema
from cis_interface.serialize.PandasSerialize import PandasSerialize


@register_component
class PandasFileComm(AsciiTableComm):
    r"""Class for handling I/O from/to a pandas csv file on disk.

    Args:
        name (str): The environment variable where communication address is
            stored.
        delimiter (str, optional): String that should be used to separate
            columns. Defaults to '\t'.
        **kwargs: Additional keywords arguments are passed to parent class.

    """

    _filetype = 'pandas'
    _schema_properties = inherit_schema(
        AsciiTableComm._schema_properties, 'filetype', _filetype)
    _default_serializer = PandasSerialize

    def _init_before_open(self, **kwargs):
        r"""Set up dataio and attributes."""
        super(PandasFileComm, self)._init_before_open(**kwargs)
        self.read_meth = 'read'
        if self.append:
            self.serializer.write_header = False

    def read_header(self):
        r"""Read header lines from the file and update serializer info."""
        return

    def write_header(self):
        r"""Write header lines to the file based on the serializer info."""
        return

    def send_dict(self, args_dict, field_order=None, **kwargs):
        r"""Send a message with fields specified in the input dictionary.

        Args:
            args_dict (dict): Dictionary with fields specifying output fields.
            field_order (list, optional): List of fields in the order they
                should be passed to send. If not provided, the fields from
                the serializer are used. If the serializer dosn't have
                field names an error will be raised.
            **kwargs: Additiona keyword arguments are passed to send.

        Returns:
            bool: Success/failure of send.

        Raises:
            RuntimeError: If the field order can not be determined.

        """
        if field_order is None:
            if self.serializer.field_names is not None:
                field_order = [
                    backwards.bytes2unicode(n) for n in self.serializer.field_names]
            elif len(args_dict) <= 1:
                field_order = [k for k in args_dict.keys()]
            else:  # pragma: debug
                raise RuntimeError("Could not determine the field order.")
        args = (serialize.dict2pandas(args_dict, order=field_order), )
        return self.send(*args, **kwargs)
