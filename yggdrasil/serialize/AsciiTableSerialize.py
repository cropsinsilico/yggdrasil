from yggdrasil import backwards, units
from yggdrasil.serialize import (
    register_serializer, _default_delimiter, _default_newline, _default_comment,
    nptype2cformat, table2format, array_to_table, table_to_array,
    format_message, process_message)
from yggdrasil.serialize.DefaultSerialize import DefaultSerialize
from yggdrasil.metaschema import get_metaschema
from yggdrasil.metaschema.properties.ScalarMetaschemaProperties import (
    definition2dtype)


@register_serializer
class AsciiTableSerialize(DefaultSerialize):
    r"""Class for serialize table output into bytes messages comprising a
    formatted ASCII table.

    Args:
        format_str (str, optional): If provided, this string will be used to
            format messages from a list of arguments and parse messages to
            get a list of arguments in C printf/scanf style. Defaults to
            None and messages are assumed to already be bytes.
        field_names (list, optional): The names of fields in the format string.
            If not provided, names are set based on the order of the fields in
            the format string.
        field_units (list, optional): The units of fields in the format string.
            If not provided, all fields are assumed to be dimensionless.
        as_array (bool, optional): If True, each of the arguments being
            serialized/deserialized will be arrays that are converted to/from
            bytes in column major ('F') order. Otherwise, each argument should
            be a scalar. Defaults to False.
        delimiter (str, optional): Character(s) that should be used to separate
            columns. Defaults to '\t'.
        use_astropy (bool, optional): If True, the astropy package will be used
            to serialize/deserialize table. Defaults to False.
        **kwargs: Additional keyword args are processed as part of the type
            definition.

    Attributes:
        format_str (str): Format string used to format/parse bytes messages
            from/to a list of arguments in C printf/scanf style.
        field_names (list): The names of fields in the format string.
        field_units (list): The units of fields in the format string.
        as_array (bool): True or False depending if serialized/deserialized
            python objects will be arrays or scalars.
        delimiter (str): Character(s) that should be used to separate columns.
        use_astropy (bool): If True, the astropy package will be used to
            serialize/deserialize table.

    """

    _seritype = 'ascii_table'
    _schema_properties = dict(
        DefaultSerialize._schema_properties,
        format_str={'type': 'string'},
        field_names={'type': 'array', 'items': {'type': 'string'}},
        field_units={'type': 'array', 'items': {'type': 'string'}},
        as_array={'type': 'boolean', 'default': False},
        delimiter={'type': 'string',
                   'default': backwards.as_str(_default_delimiter)},
        newline={'type': 'string',
                 'default': backwards.as_str(_default_newline)},
        comment={'type': 'string',
                 'default': backwards.as_str(_default_comment)},
        use_astropy={'type': 'boolean', 'default': False})

    def update_serializer(self, *args, **kwargs):
        # Transform scalar into array for table
        if kwargs.get('type', 'array') != 'array':
            old_typedef = {}
            _metaschema = get_metaschema()
            for k in _metaschema['properties'].keys():
                if k in kwargs:
                    old_typedef[k] = kwargs.pop(k)
            new_typedef = {'type': 'array', 'items': [old_typedef]}
            kwargs.update(new_typedef)
        out = super(AsciiTableSerialize, self).update_serializer(*args, **kwargs)
        for k in ['format_str', 'delimiter', 'newline', 'comment']:
            v = getattr(self, k, None)
            if isinstance(v, backwards.string_types):
                setattr(self, k, backwards.as_bytes(v))
        self.update_format_str()
        self.update_field_names()
        self.update_field_units()
        return out

    def update_format_str(self):
        r"""Update the format string based on the type definition."""
        # Get format information from precision etc.
        if (self.format_str is None) and self._initialized:
            assert(self.typedef['type'] == 'array')
            fmts = []
            if isinstance(self.typedef['items'], dict):  # pragma: debug
                idtype = definition2dtype(self.typedef['items'])
                ifmt = nptype2cformat(idtype, asbytes=True)
                # fmts = [ifmt for x in msg]
                raise Exception("Variable number of items not yet supported.")
            elif isinstance(self.typedef['items'], list):
                for x in self.typedef['items']:
                    idtype = definition2dtype(x)
                    ifmt = nptype2cformat(idtype, asbytes=True)
                    fmts.append(ifmt)
            if fmts:
                self.format_str = table2format(
                    fmts=fmts, delimiter=self.delimiter, newline=self.newline,
                    comment=b'')

    def update_field_names(self):
        r"""list: Names for each field in the data type."""
        if (self.field_names is None) and self._initialized:
            assert(self.typedef['type'] == 'array')
            self.field_names = self.get_field_names()

    def update_field_units(self):
        r"""list: Units for each field in the data type."""
        if (self.field_units is None) and self._initialized:
            assert(self.typedef['type'] == 'array')
            self.field_units = self.get_field_units()

    def func_serialize(self, args):
        r"""Serialize a message.

        Args:
            args: List of arguments to be formatted or numpy array to be
                serialized.

        Returns:
            bytes, str: Serialized message.

        """
        if self.format_str is None:
            raise RuntimeError("Format string is not defined.")
        args = self.datatype.coerce_type(args,
                                         key_order=self.get_field_names())
        if self.as_array:
            out = array_to_table(args, self.format_str,
                                 use_astropy=self.use_astropy)
        else:
            out = format_message(args, self.format_str)
        return backwards.as_bytes(out)

    def func_deserialize(self, msg):
        r"""Deserialize a message.

        Args:
            msg: Message to be deserialized.

        Returns:
            obj: Deserialized message.

        """
        if self.format_str is None:
            raise RuntimeError("Format string is not defined.")
        if self.as_array:
            out = table_to_array(msg, self.format_str,
                                 use_astropy=self.use_astropy,
                                 names=self.get_field_names(as_bytes=True))
            out = self.datatype.coerce_type(out)
        else:
            out = list(process_message(msg, self.format_str))
        field_units = self.get_field_units()
        if field_units is not None:
            out = [units.add_units(x, u) for x, u in zip(out, field_units)]
        return out

    @classmethod
    def get_testing_options(cls, as_array=False):
        r"""Method to return a dictionary of testing options for this class.

        Returns:
            dict: Dictionary of variables to use for testing.

        """
        out = super(AsciiTableSerialize, cls).get_testing_options(
            as_format=True, as_array=as_array)
        out['extra_kwargs'] = {}
        return out
