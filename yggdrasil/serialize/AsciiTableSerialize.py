from yggdrasil import units, serialize, tools
from yggdrasil.serialize import _default_delimiter_str
from yggdrasil.serialize.DefaultSerialize import DefaultSerialize
from yggdrasil.metaschema import get_metaschema
from yggdrasil.metaschema.properties.ScalarMetaschemaProperties import (
    definition2dtype, data2dtype)


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

    _seritype = 'table'
    _schema_subtype_description = ('ASCII tab (or otherwise) delimited table.')
    _schema_properties = {
        'format_str': {'type': 'string'},
        'field_names': {'type': 'array', 'items': {'type': 'string'}},
        'field_units': {'type': 'array', 'items': {'type': 'string'}},
        'as_array': {'type': 'boolean', 'default': False},
        'delimiter': {'type': 'string',
                      'default': _default_delimiter_str},
        'use_astropy': {'type': 'boolean', 'default': False}}
    _attr_conv = DefaultSerialize._attr_conv + ['format_str', 'delimiter']
    has_header = True
    default_read_meth = 'readline'  # because default for as_array is False
    default_datatype = {'type': 'array'}

    def update_serializer(self, *args, **kwargs):
        # Transform scalar into array for table
        if kwargs.get('type', 'array') != 'array':
            old_typedef = {}
            _metaschema = get_metaschema()
            for k in _metaschema['properties'].keys():
                if k in kwargs:
                    old_typedef[k] = kwargs.pop(k)
            if old_typedef['type'] == 'object':
                names = self.get_field_names()
                if not names:
                    names = list(old_typedef['properties'].keys())
                assert(len(old_typedef['properties']) == len(names))
                new_typedef = {'type': 'array', 'items': []}
                for n in names:
                    new_typedef['items'].append(dict(
                        old_typedef['properties'][n], title=n))
            else:
                new_typedef = {'type': 'array', 'items': [old_typedef]}
            kwargs.update(new_typedef)
        out = super(AsciiTableSerialize, self).update_serializer(*args, **kwargs)
        self.initialized = (self.typedef != self.default_datatype)
        self.update_format_str()
        self.update_field_names()
        self.update_field_units()
        return out

    def update_format_str(self):
        r"""Update the format string based on the type definition."""
        # Get format information from precision etc.
        if (self.format_str is None) and self.initialized:
            assert(self.typedef['type'] == 'array')
            fmts = []
            if isinstance(self.typedef['items'], dict):  # pragma: debug
                idtype = definition2dtype(self.typedef['items'])
                ifmt = serialize.nptype2cformat(idtype, asbytes=True)
                # fmts = [ifmt for x in msg]
                raise Exception("Variable number of items not yet supported.")
            elif isinstance(self.typedef['items'], list):
                for x in self.typedef['items']:
                    idtype = definition2dtype(x)
                    ifmt = serialize.nptype2cformat(idtype, asbytes=True)
                    fmts.append(ifmt)
            if fmts:
                self.format_str = serialize.table2format(
                    fmts=fmts, delimiter=self.delimiter, newline=self.newline,
                    comment=b'')

    def update_field_names(self):
        r"""list: Names for each field in the data type."""
        if (self.field_names is None) and self.initialized:
            assert(self.typedef['type'] == 'array')
            self.field_names = self.get_field_names()

    def update_field_units(self):
        r"""list: Units for each field in the data type."""
        if (self.field_units is None) and self.initialized:
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
            out = serialize.array_to_table(args, self.format_str,
                                           use_astropy=self.use_astropy)
        else:
            out = serialize.format_message(args, self.format_str)
        return tools.str2bytes(out)

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
            out = serialize.table_to_array(msg, self.format_str,
                                           use_astropy=self.use_astropy,
                                           names=self.get_field_names(as_bytes=True))
            out = self.datatype.coerce_type(out)
        else:
            out = list(serialize.process_message(msg, self.format_str))
        field_units = self.get_field_units()
        if field_units is not None:
            out = [units.add_units(x, u, dtype=data2dtype(x))
                   for x, u in zip(out, field_units)]
        return out

    @classmethod
    def get_testing_options(cls, **kwargs):
        r"""Method to return a dictionary of testing options for this class.

        Args:
            **kwargs: Keyword arguments are passed to the parent class's method.

        Returns:
            dict: Dictionary of variables to use for testing.

        """
        out = super(AsciiTableSerialize, cls).get_testing_options(
            table_example=True, include_oldkws=True, **kwargs)
        out['extra_kwargs'] = {}
        out['concatenate'] = []
        return out

    @property
    def read_meth(self):
        r"""str: Method that should be used to read data for deserialization."""
        if self.as_array:
            return 'read'
        else:
            return 'readline'

    def serialize_file_header(self):
        r"""Return the serialized header information that should be prepended
        to files serialized using this class.

        Returns:
            bytes: Header string that should be written to the file.

        """
        out = serialize.format_header(
            format_str=self.format_str,
            field_names=self.get_field_names(as_bytes=True),
            field_units=self.get_field_units(as_bytes=True),
            comment=self.comment, newline=self.newline, delimiter=self.delimiter)
        return out

    def deserialize_file_header(self, fd):
        r"""Deserialize the header information from the file and update the
        serializer.

        Args:
            fd (file): File containing header.

        """
        fd.seek(0)
        serialize.discover_header(fd, self, newline=self.newline,
                                  comment=self.comment, delimiter=self.delimiter)
