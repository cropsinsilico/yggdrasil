import numpy as np
# from cis_interface.interface.scanf import scanf
from cis_interface.dataio.AsciiFile import AsciiFile
from cis_interface import backwards, serialize
from cis_interface.serialize import AsciiTableSerialize
try:
    if not backwards.PY2:  # pragma: Python 3
        from astropy.io import ascii as apy_ascii
        from astropy.table import Table as apy_Table
        _use_astropy = True
    else:  # pragma: Python 2
        apy_ascii, apy_Table = None, None
        _use_astropy = False
except ImportError:
    apy_ascii, apy_Table = None, None
    # print("astropy is not installed, reading/writing as an array will be " +
    #       "disabled. astropy can be installed using 'pip install astropy'.")
    _use_astropy = False


_default_args = {'column': serialize._default_delimiter}


class AsciiTable(AsciiFile):
    def __init__(self, filepath, io_mode, format_str=None, dtype=None,
                 column_names=None, use_astropy=False,
                 column=_default_args['column'], **kwargs):
        r"""Class for reading/writing an ASCII table.

        Args:
            filepath (str): Full path to the file that should be read from
                or written to.
            io_mode (str): Mode that should be used to open the file. Valid
                values include 'r', 'w', and None. None can be used to
                indicate an in memory table that will not be read from or
                written to a file.
            format_str (str): Format string that should be used to format
                output in the case that the io_mode is 'w' (write). It is not
                required if the io_mode is any other value.
            dtype (str): Numpy structured data type for each row. If not
                provided it is set using format_str. Defaults to None.
            column_names (list, optional): List of column names. Defaults to
                None.
            use_astropy (bool, optional): If True, astropy is used to determine
                a table's format if it is installed. If False, a format string
                must be contained in the table. Defaults to False.
            column (str, optional): String that should be used to separate
                columns. Defaults to "\t" (tab-delimited).
            **kwargs: Additonal keyword arguments are passed to AsciiFile.

        Raises:
            RuntimeError: If format_str is not provided and the io_mode is 'w'
                (write).

        """
        if use_astropy:
            self.use_astropy = _use_astropy
        else:
            self.use_astropy = False
        # if self.use_astropy:
        #     kwargs['open_as_binary'] = False
        super(AsciiTable, self).__init__(filepath, io_mode, **kwargs)
        self.column_names = None
        # Add default args specific to ascii table
        self.column = backwards.unicode2bytes(column)
        try:
            self._format_str = backwards.unicode2bytes(format_str)
        except TypeError:
            if isinstance(dtype, (str, np.dtype)):
                self._dtype = np.dtype(dtype)
            else:
                if (io_mode == 'r'):
                    self.discover_format_str()
                else:
                    raise RuntimeError("'format_str' must be provided for output")
        if ((isinstance(column_names, (list, tuple)) and
             (len(column_names) == self.ncols))):
            self.column_names = tuple([c for c in column_names])

    @property
    def format_str(self):
        r"""str: Format string describing the table column types."""
        if not hasattr(self, '_format_str'):
            if hasattr(self, '_dtype'):
                fmts = serialize.nptype2cformat(self.dtype, asbytes=True)
                self._format_str = self.column.join(fmts) + self.newline
            else:  # pragma: debug
                raise RuntimeError("Format string not set " +
                                   "and cannot be determined.")
        return self._format_str

    @property
    def dtype(self):
        r"""np.dtype: Data type of the table."""
        if not hasattr(self, '_dtype'):
            self._dtype = serialize.cformat2nptype(
                self.format_str, names=self.column_names)
        return self._dtype

    @property
    def fmts(self):
        r"""list: Formats in format string."""
        return serialize.extract_formats(self.format_str)

    @property
    def ncols(self):
        r"""int: The number of columns in the table."""
        return len(self.fmts)

    def update_format_str(self, new_format_str):
        r"""Change the format string and update the data type.

        Args:
            new_format_str (str): New format string.

        """
        self._format_str = backwards.unicode2bytes(new_format_str)
        if hasattr(self, '_dtype'):
            delattr(self, '_dtype')

    def update_dtype(self, new_dtype):
        r"""Change the data type and update the format string.

        Args:
            new_dtype (str or np.dtype): New numpy data type.

        """
        if isinstance(new_dtype, np.dtype):
            pass
        elif isinstance(new_dtype, str):
            new_dtype = np.dtype(new_dtype)
        self._dtype = new_dtype
        if hasattr(self, '_format_str'):
            delattr(self, '_format_str')

    def writeheader(self, names=None):
        r"""Write header including column names and format.

        Args:
            names (list, optional): List of names of columns. Defaults to
                None and the ones provided at construction are used if they
                exist. Otherwise, no names are written.

        """
        self.writenames(names=names)
        self.writeformat()

    def writenames(self, names=None):
        r"""Write column names to file.

        Args:
            names (list, optional): List of names of columns. Defaults to
                None and the ones provided at construction are used if they
                exist. Otherwise, no names are written.

        Raises:
            IndexError: If there are not enough names for all of the columns.

        """
        if names is None:
            names = self.column_names
        if names is None:
            return
        if len(names) != self.ncols:
            raise IndexError("The number of names must match the number of columns.")
        names = [backwards.unicode2bytes(n) for n in names]
        line = (self.comment + self.column.join(names) + self.newline)
        self.writeline_full(line)
            
    def writeformat(self):
        r"""Write the format string to the file."""
        line = self.comment + self.format_str
        self.writeline_full(line)

    def readline(self):
        r"""Continue reading lines until a valid line (uncommented) is
        encountered and return the arguments found there.

        Returns:
            tuple (bool, tuple): End of file flag and the arguments that
                were read from the line. If the end of file is reached,
                None is returned.

        """
        
        eof, line = False, None
        while (not eof) and (line is None):
            eof, line = self.readline_full(validate=True)
        if (not line) or eof:
            args = None
        else:
            args = self.process_line(line)
        return eof, args

    def writeline(self, *args):
        r"""Write arguments to a file in the table format.

        Args:
            \*args: Any number of arguments that should be written to the file.

        """
        if self.is_open:
            line = self.format_line(*args)
        else:
            line = backwards.unicode2bytes('')
        self.writeline_full(line, validate=True)

    def readline_full(self, validate=False):
        r"""Read a line and return it if it is not a comment.

        Args:
            validate (bool, optional): If True, the line is checked to see if
                it matches the expected table format. Defaults to False.

        Returns:
            tuple (bool, str): End of file flag and the line that was read (an
                empty string if the end of file was encountered). If the line is
                a comment, None is returned.

        """
        eof, line = super(AsciiTable, self).readline_full()
        if self.is_open and (not eof) and (line is not None) and validate:
            self.validate_line(line)
        return eof, line

    def writeline_full(self, line, validate=False):
        r"""Write a line to the file in its present state.

        Args:
            line (str): Line to be written.
            validate (bool, optional): If True, the line is checked to see if
                it matches the expected table format. Defaults to False.

        """
        if self.is_open and isinstance(line, str) and validate:
            self.validate_line(line)
        super(AsciiTable, self).writeline_full(line)
        
    def format_line(self, *args):
        r"""Create a line from the provided arguments using the table format.

        Args:
            \*args: Arguments to create line from.

        Returns:
            str: The line created from the arguments.

        """
        return serialize.format_message(args, self.format_str)

    def process_line(self, line):
        r"""Extract values from the columns in the line using the table format.

        Args:
            line (str): String to extract arguments from.

        Returns:
            tuple: The arguments extracted from line.

        """
        return serialize.process_message(line, self.format_str)
        
    def validate_line(self, line):
        r"""Assert that the line matches the format string and produces the
        expected number of values."""
        self.process_line(line)

    def discover_format_str(self):
        r"""Determine the format string by reading it from the file. The format
        string is assumed to start with a comment and contain C-style format
        codes (e.g. '%f').

        Raises:
            RuntimeError: If a format string cannot be located within the file.

        """
        serializer = AsciiTableSerialize.AsciiTableSerialize()
        serializer.field_names = getattr(self, 'column_names', None)
        with open(self.filepath, self.open_mode) as fd:
            serialize.discover_header(fd, serializer, newline=self.newline,
                                      comment=self.comment, delimiter=self.column,
                                      use_astropy=self.use_astropy)
        self.column_names = serializer.field_names
        self._format_str = serializer.format_str
        self.column = serializer.table_info['delimiter']

    @property
    def arr(self):
        r"""Numpy array of table contents if opened in read mode."""
        if self.io_mode == 'w':
            return None
        if not hasattr(self, '_arr'):
            self._arr = self.read_array()
        return self._arr

    def read_array(self, names=None):
        r"""Read the table in as an array.

        Args:
            names (list, optional): List of column names to label columns. If
                not provided, existing names are used if they exist. Defaults
                to None.

        Returns:
            np.ndarray: Array of table contents.

        Raises:
            ValueError: If names are provided, but not the same number as
                there are columns.

        """
        if names is None:
            names = self.column_names
        if (names is not None) and (len(names) != self.ncols):
            raise ValueError("The number of names does not match the number of columns")
        if hasattr(self, '_arr'):
            return self._arr
        openned = False
        if not self.is_open:
            self.open()
            openned = True
        msg = self.fd.read()
        arr = serialize.table_to_array(msg, fmt_str=self.format_str,
                                       use_astropy=self.use_astropy,
                                       delimiter=self.column, comment=self.comment,
                                       names=names)
        if openned:
            self.close()
        return arr

    def write_array(self, array, names=None, skip_header=False):
        r"""Write a numpy array to the table.

        Args:
            array (np.ndarray): Array to be written.
            names (list, optional): List of column names to write out. If
                not provided, existing names are used if they exist. Defaults
                to None.
            skip_header (bool, optional): If True, no header information is
                written (it is assumed it was already written. Defaults to
                False.

        Raises:
            ValueError: If names are provided, but not the same number as
                there are columns.

        """
        openned = False
        fd = self.fd
        if not self.is_open:
            fd = open(self.filepath, self.open_mode)
            openned = True
        # Write header
        if not skip_header:
            if names is None:
                names = self.column_names
            header = serialize.format_header(format_str=self.format_str,
                                             comment=self.comment,
                                             delimiter=self.column,
                                             newline=self.newline,
                                             field_names=names)
            fd.write(header)
        # Write array
        fd.write(serialize.array_to_table(array, self.format_str,
                                          use_astropy=self.use_astropy))
        if openned:
            fd.close()
            fd = None

    def array_to_bytes(self, arr=None, order='C'):
        r"""Convert arr to bytestring.

        Args:
            arr (np.ndarray, optional): Array to write to bytestring. If None
                the array of table data is used. This can also be a list of
                arrays, one for each field in the table, or a list of lists,
                one for each element containing the fields for that element.
            order (str, optional): Order that array should be written to the
                bytestring. Defaults to 'C'.

        Returns:
            str: Bytestring.

        Raises:
            TypeError: If the provided array is not a numpy array, list, or tuple.
            ValueError: If the array is not the correct type.
            ValueError: If there are not enough arrays in the input list.
            ValueError: If any of the listed arrays doesn't have enough fields.
            ValueError: If any of the listed arrays doesn't have enough elements.

        """
        if arr is None:
            arr = self.arr
        return serialize.array_to_bytes(arr, dtype=self.dtype, order=order)

    def bytes_to_array(self, data, order='C'):
        r"""Process bytes according to the table format and return it as an
        array.

        Args:
            data (bytes): Byte string of table data.
            order (str, optional): Order of data for reshaping. Defaults to
                'C'.

        Returns:
            np.ndarray: Numpy array containing data from bytes.

        """
        arr = serialize.bytes_to_array(data, self.dtype, order=order)
        return arr

    def read_bytes(self, order='C', **kwargs):
        r"""Read the table in as array and encode as bytes.

        Args:
            order (str, optional): Order that array should be written to the
                bytestring. Defaults to 'C'.
            **kwargs: Additional keyword arguments are passed to read_array.

        Returns:
            bytes: Array as bytes.

        """
        arr = self.read_array(**kwargs)
        out = self.array_to_bytes(arr, order=order)
        return out

    def write_bytes(self, data, order='C', **kwargs):
        r"""Write a numpy array to the table.

        Args:
            data (bytes): Bytes string to be interpreted as array and
                written to file.
            order (str, optional): Order of data for reshaping. Defaults to
                'C'.
            **kwargs: Additional keyword arguments are passed to write_array.

        """
        arr = self.bytes_to_array(data, order=order)
        self.write_array(arr, **kwargs)
