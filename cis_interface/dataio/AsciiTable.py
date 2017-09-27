import numpy as np
import copy
from cis_interface.interface.scanf import scanf
from cis_interface.dataio.AsciiFile import AsciiFile
from cis_interface import backwards
from numpy.compat import asbytes
try:
    from astropy.io import ascii as apy_ascii
    from astropy.table import Table as apy_Table
    _use_astropy = True
    from astropy.io.ascii import TableOutputter, convert_numpy
    apy_tableout = TableOutputter()
    apy_tableout.default_converters = [convert_numpy(np.int),
                                       convert_numpy(np.float),
                                       convert_numpy(np.str),
                                       convert_numpy(np.complex)]
    if not backwards.PY2:  # pragma: Python 3
        _use_astropy = False
except:  # pragma: no cover
    apy_ascii, apy_Table = None, None
    print("astropy is not installed, reading/writing as an array will be " +
          "disabled. astropy can be installed using 'pip install astropy'.")
    _use_astropy = False


_default_args = {'column': '\t'}
_fmt_char = backwards.unicode2bytes('%')


def nptype2cformat(nptype):
    r"""Convert a numpy data type to a c format string.

    Args:
        nptype (str or numpy.dtype): Numpy data type that should be converted.

    Returns:
        str: Corresponding c format specification string.

    Raises:
        TypeError: If nptype is not a string or numpy.dtype.
        ValueError: If a matching format string cannot be determined.

    """
    if isinstance(nptype, np.dtype):
        t = nptype
    elif isinstance(nptype, str):
        t = np.dtype(nptype)
    else:
        raise TypeError("Input must be a string or a numpy.dtype")
    if t in [np.dtype(x) for x in ["float_", "float16", "float32", "float64"]]:
        cfmt = "%g"  # Ensures readability
    elif t in [np.dtype(x) for x in ["complex_", "complex64", "complex128"]]:
        cfmt = "%g%+gj"
    elif t == np.dtype("int8"):
        cfmt = "%hhd"
    elif t == np.dtype("short"):
        cfmt = "%hd"
    elif t == np.dtype("intc"):
        cfmt = "%d"
    elif t == np.dtype("int_"):
        cfmt = "%ld"
    elif t == np.dtype("longlong"):  # pragma: no cover
        # If it is different than C long
        cfmt = "%lld"
    elif t == np.dtype("uint8"):
        cfmt = "%hhu"
    elif t == np.dtype("ushort"):
        cfmt = "%hu"
    elif t == np.dtype("uintc"):
        cfmt = "%u"
    elif t == np.dtype("uint64"):  # Platform dependent
        cfmt = "%lu"
    elif t == np.dtype("ulonglong"):  # pragma: no cover
        cfmt = "%llu"
    elif np.issubdtype(t, np.dtype("S")):
        if t.itemsize is 0:
            cfmt = '%s'
        else:
            cfmt = "%" + str(t.itemsize) + "s"
    elif np.issubdtype(t, np.dtype("U")):
        if t.itemsize is 0:
            cfmt = '%s'
        else:
            cfmt = "%" + str(t.itemsize) + "s"
    else:
        raise ValueError("No format specification string for dtype %s" % t)
    # Short and long specifiers not supported by python scanf
    # cfmt = cfmt.replace("h", "")
    # cfmt = cfmt.replace("l", "")
    return cfmt


def cformat2nptype(cfmt):
    r"""Convert a c format string to a numpy data type.

    Args:
        cfmt (str): c format that should be translated.

    Returns:
        str: Corresponding numpy data type.

    Raises:
        TypeError: if cfmt is not a string.
        ValueError: If the c format does not begin with '%'.
        ValueError: If the c format does not contain type info.
        ValueError: If the c format cannot be translated to a numpy datatype.

    """
    # TODO: this may fail on 32bit systems where C long types are 32 bit
    if not isinstance(cfmt, backwards.bytes_type):
        raise TypeError("Input must be of type %s, not %s" %
                        (backwards.bytes_type, type(cfmt)))
    elif not cfmt.startswith(_fmt_char):
        raise ValueError("Provided C format string (%s) " % cfmt +
                         "does not start with '%%'")
    elif len(cfmt) == 1:
        raise ValueError("Provided C format string (%s) " % cfmt +
                         "does not contain type info")
    out = None
    cfmt_str = backwards.bytes2unicode(cfmt)
    if cfmt_str[-1] in ['j']:
        out = 'complex128'
    elif cfmt_str[-1] in ['f', 'F', 'e', 'E', 'g', 'G']:
        # if 'hh' in cfmt_str:
        #     out = 'float8'
        # elif cfmt_str[-2] == 'h':
        #     out = 'float16'
        # elif 'll' in cfmt_str:
        #     out = 'longfloat'
        # elif cfmt_str[-2] == 'l':
        #     out = 'double'
        # else:
        #     out = 'single'
        out = 'float64'
    elif cfmt_str[-1] in ['d', 'i']:
        if 'hh' in cfmt_str:  # short short, single char
            out = 'int8'
        elif cfmt_str[-2] == 'h':  # short
            out = 'short'
        elif 'll' in cfmt_str:
            out = 'longlong'  # long long
        elif cfmt_str[-2] == 'l':
            out = 'int_'  # long (broken in python)
        else:
            out = 'intc'  # int, platform dependent
    elif cfmt_str[-1] in ['u', 'o', 'x', 'X']:
        if 'hh' in cfmt_str:  # short short, single char
            out = 'uint8'
        elif cfmt_str[-2] == 'h':  # short
            out = 'ushort'
        elif 'll' in cfmt_str:
            out = 'ulonglong'  # long long
        elif cfmt_str[-2] == 'l':
            out = 'uint64'  # long (broken in python)
        else:
            out = 'uintc'  # int, platform dependent
    elif cfmt_str[-1] in ['c', 's']:
        lstr = cfmt_str[1:-1]
        if lstr:
            lint = int(lstr)
        else:
            lint = 0
        lsiz = lint * np.dtype(backwards.np_dtype_str + '1').itemsize
        out = '%s%d' % (backwards.np_dtype_str, lsiz)
    else:
        raise ValueError("Could not find match for format str %s" % cfmt)
    return np.dtype(out).str


def cformat2pyscanf(cfmt):
    r"""Convert a c format specification string to a version that the
    python scanf module can use.

    Args:
        cfmt (str): C format specification string.

    Returns:
        str: Version of cfmt that can be parsed by scanf.

    Raises:
        TypeError: if cfmt is not a bytes/str.
        ValueError: If the c format does not begin with '%'.
        ValueError: If the c format does not contain type info.

    """
    if not isinstance(cfmt, backwards.bytes_type):
        raise TypeError("Input must be of type %s." % backwards.bytes_type)
    elif not cfmt.startswith(_fmt_char):
        raise ValueError("Provided C format string (%s) " % cfmt +
                         "does not start with '%%'")
    elif len(cfmt) == 1:
        raise ValueError("Provided C format string (%s) " % cfmt +
                         "does not contain type info")
    # Hacky, but necessary to handle concatenation of a single byte
    cfmt_str = backwards.bytes2unicode(cfmt)
    if cfmt_str[-1] == 'j':
        # Handle complex format specifier
        out = '%g%+gj'
    else:
        out = backwards.bytes2unicode(_fmt_char)
        out += cfmt_str[-1]
        out = out.replace('h', '')
        out = out.replace('l', '')
    return backwards.unicode2bytes(out)


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
        if self.use_astropy:
            kwargs['open_as_binary'] = False
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
        if isinstance(column_names, list) and (len(column_names) == self.ncols):
            self.column_names = column_names

    @property
    def format_str(self):
        if not hasattr(self, '_format_str'):
            if hasattr(self, '_dtype'):
                fmts = [backwards.unicode2bytes(nptype2cformat(self.dtype[i]))
                        for i in range(len(self.dtype))]
                self._format_str = backwards.unicode2bytes(
                    self.column.join(fmts) + self.newline)
            else:  # pragma: debug
                raise RuntimeError("Format string not set " +
                                   "and cannot be determined.")
        return self._format_str

    @property
    def dtype(self):
        if not hasattr(self, '_dtype'):
            # typs = [(f[-1] + str(i), np.dtype(cformat2nptype(f)))
            #         for i, f in enumerate(self.fmts)]
            typs = [('f' + str(i), np.dtype(cformat2nptype(f)))
                    for i, f in enumerate(self.fmts)]
            self._dtype = np.dtype(typs)
        return self._dtype

    @property
    def fmts(self):
        r"""List of formats in format string."""
        return self.format_str.split(self.newline)[0].split(self.column)

    @property
    def ncols(self):
        return len(self.fmts)
        # return self.format_str.count(_fmt_char)

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
        line = (self.comment + backwards.unicode2bytes(' ') +
                self.column.join(names) + self.newline)
        self.writeline_full(line)
            
    def writeformat(self):
        r"""Write the format string to the file."""
        line = self.comment + backwards.unicode2bytes(' ') + self.format_str
        self.writeline_full(line)

    def readline(self, dont_parse=False):
        r"""Continue reading lines until a valid line (uncommented) is
        encountered and return the arguments found there.

        Args:
            dont_parse (bool, optional): If True, the raw line is returned.
                Defaults to False.

        Returns:
            tuple (bool, tuple): End of file flag and the arguments that
                were read from the line. If the end of file is reached,
                None is returned.

        """
        
        eof, line = False, None
        while (not eof) and (line is None):
            eof, line = self.readline_full(validate=True)
        if dont_parse:
            return eof, line
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

        Raises:
            RuntimeError: If the incorrect number of arguments are passed.

        """
        if len(args) < self.ncols:
            raise RuntimeError("Incorrect number of arguments.")
        # Handle complex
        args_ = []
        for a in args:
            if np.iscomplexobj(a):
                args_ += [a.real, a.imag]
            else:
                args_.append(a)
        out = backwards.bytes2unicode(self.format_str) % tuple(args_)
        return backwards.unicode2bytes(out)

    def process_line(self, line):
        r"""Extract values from the columns in the line using the table format.

        Args:
            line (str): String to extract arguments from.

        Returns:
            tuple: The arguments extracted from line.

        """
        new_fmt = (self.column.join(
            [backwards.unicode2bytes(cformat2pyscanf(f)) for f in self.fmts]) +
            self.newline)
        out = scanf(backwards.bytes2unicode(new_fmt),
                    backwards.bytes2unicode(line))
        return out
        
    def validate_line(self, line):
        r"""Assert that the line matches the format string and produces the
        expected number of values.

        Raises:
            TypeError: If the line is not a bytes/str.
            AssertionError: If the line does not match the format string.

        """
        if not isinstance(line, backwards.bytes_type):
            raise TypeError("Line must be of type %s, not %s."
                            % (backwards.bytes_type, type(line)))
        args = self.process_line(line)
        if args is None or (len(args) != self.ncols):
            raise AssertionError("The line does not match the format string.")

    def discover_format_str(self):
        r"""Determine the format string by reading it from the file. The format
        string is assumed to start with a comment and contain C-style format
        codes (e.g. '%f').

        Raises:
            RuntimeError: If a format string cannot be located within the file.

        """
        if self.use_astropy:
            arr = self.read_array()
            self._arr = arr
            self._dtype = self._arr.dtype
            if getattr(self, 'column_names', None) is None:
                self.column_names = [c for c in arr.dtype.names]
        else:
            comment_list = []
            out = None
            with open(self.filepath, self.open_mode) as fd:
                for line in fd:
                    line = backwards.unicode2bytes(line)
                    if line.startswith(self.comment):
                        sline = line.lstrip(self.comment)
                        sline = sline.lstrip(backwards.unicode2bytes(' '))
                        fmts = sline.split(self.column)
                        is_fmt = [f.startswith(_fmt_char) for f in fmts]
                        if sum(is_fmt) == len(fmts):
                            out = sline
                            break
                        comment_list.append(sline)
            if out is None:  # pragma: debug
                raise Exception("Could not locate a line containing format descriptors.")
            self._format_str = backwards.unicode2bytes(out)
            # Do column names
            if getattr(self, 'column_names', None) is None:
                self.column_names = None
                for sline in comment_list:
                    names = sline.split(self.newline)[0].split(self.column)
                    if len(names) == self.ncols:
                        self.column_names = [
                            backwards.bytes2unicode(n) for n in names]
                        break
            # Do string lengths
            str_fmt = backwards.unicode2bytes('%s')
            if str_fmt in self._format_str:
                fmts = self.fmts
                idx_str = []
                for i, ifmt in enumerate(fmts):
                    if ifmt == str_fmt:
                        idx_str.append(i)
                max_len = {i: 0 for i in idx_str}
                with open(self.filepath, self.open_mode) as fd:
                    for line in fd:
                        line = backwards.unicode2bytes(line)
                        if line.startswith(self.comment):
                            continue
                        cols = line.split(self.newline)[0].split(self.column)
                        for i in idx_str:
                            max_len[i] = max(max_len[i], len(cols[i]))
                for i in idx_str:
                    fmts[i] = backwards.unicode2bytes('%' + str(max_len[i]) + 's')
                new_format_str = self.column.join(fmts) + self.newline
                self.update_format_str(new_format_str)

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
        if self.use_astropy:
            tab = apy_ascii.read(self.fd, names=names,
                                 **getattr(self, 'astropy_kwargs', {}))
            arr = tab.as_array()
            typs = [arr.dtype[i].str for i in range(len(arr.dtype))]
            cols = tab.columns
            for i in range(len(arr.dtype)):
                if np.issubdtype(arr.dtype[i], np.dtype('S')):
                    new_typs = copy.copy(typs)
                    new_typs[i] = 'complex'
                    new_dtyp = np.dtype([(c, t) for c, t in zip(cols, new_typs)])
                    try:
                        arr = arr.astype(new_dtyp)
                    except ValueError:
                        pass
        else:
            arr = np.genfromtxt(self.fd,
                                comments=backwards.bytes2unicode(self.comment),
                                delimiter=backwards.bytes2unicode(self.column),
                                dtype=self.dtype,
                                autostrip=True, names=names)
        if openned:
            self.close()
        return arr

    def write_array(self, array, names=None, skip_header=False, append=False):
        r"""Write a numpy array to the table.

        Args:
            array (np.ndarray): Array to be written.
            names (list, optional): List of column names to write out. If
                not provided, existing names are used if they exist. Defaults
                to None.
            skip_header (bool, optional): If True, no header information is
                written (it is assumed it was already written. Defaults to
                False.
            append (bool, optional): If True, array is appended to existing
                table. This sets skip_header to True. Defaults to False.

        Raises:
            ValueError: If names are provided, but not the same number as
                there are columns.

        """
        fmt = backwards.bytes2unicode(self.format_str.split(self.newline)[0])
        column = backwards.bytes2unicode(self.column)
        comment = backwards.bytes2unicode(self.comment) + ' '
        newline = backwards.bytes2unicode(self.newline)
        open_mode = self.open_mode
        openned = False
        fd = self.fd
        if append:
            skip_header = True
            open_mode = 'a'
            if self.open_as_binary:
                open_mode += 'b'
        if not self.is_open:
            fd = open(self.filepath, open_mode)
            openned = True
        if skip_header:
            names = None
        else:
            if names is None:
                names = self.column_names
            if (names is not None) and (len(names) != self.ncols):
                raise ValueError("The number of names does not match " +
                                 "the number of columns")
        if self.use_astropy:
            table = apy_Table(array)
            if skip_header:
                table_format = 'no_header'
            else:
                table_format = 'commented_header'
                table.meta["comments"] = [fmt]
            apy_ascii.write(table, fd,
                            delimiter=column, comment=comment,
                            format=table_format, names=names)
        else:
            if skip_header:
                head = ''
            else:
                head = fmt
                if names is not None:
                    head = column.join(names) + newline + " " + head
            # Write directly to file, savetxt writes bytes as "b'body'"
            if len(head) > 0:
                head = head.replace(newline, newline + comment)
                fd.write(asbytes(comment + head + newline))
            for row in array:
                row2 = []
                for x in row:
                    if np.iscomplexobj(x):
                        row2.append(x.real)
                        row2.append(x.imag)
                    else:
                        row2.append(x)
                fd.write(asbytes(fmt) % tuple(row2) + asbytes(newline))
            # np.savetxt(fd, array,
            #            fmt=fmt, delimiter=column, comments=comment,
            #            newline=newline, header=head)
        if openned:
            fd.close()
            fd = None

    def array_to_bytes(self, arr=None, order='C'):
        r"""Convert arr to bytestring.

        Args:
            arr (np.ndarray, optional): Array to write to bytestring. If None
                the array of table data is used.
            order (str, optional): Order that array should be written to the
                bytestring. Defaults to 'C'.

        Returns:
            str: Bytestring.

        Raises:
            TypeError: If the provided array is not a numpy array.
            ValueError: If the array is not the correct type.

        """
        if arr is None:
            arr = self.arr
        if not isinstance(arr, np.ndarray):
            raise TypeError("Provided array must be an array.")
        if (arr.dtype != self.dtype):
            if (arr.ndim != 2) or (arr.shape[1] != len(self.dtype)):
                raise ValueError("Data types do not match.")
            arr1 = np.empty(arr.shape[0], dtype=self.dtype)
            for i, n in enumerate(self.dtype.names):
                arr1[n] = arr[:, i]
        else:
            arr1 = arr
        if order == 'F':
            out = backwards.unicode2bytes('')
            for i in range(len(arr1.dtype)):
                n = arr1.dtype.names[i]
                if np.issubdtype(arr1.dtype[i], np.dtype('complex')):
                    out = out + arr1[n].real.tobytes()
                    out = out + arr1[n].imag.tobytes()
                else:
                    out = out + arr1[n].tobytes()
        else:
            out = arr1.tobytes(order='C')
        return out

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
        if (len(data) % self.dtype.itemsize) != 0:
            raise RuntimeError("Data length (%d) must a multiple of the itemsize (%d)."
                               % (len(data), self.dtype.itemsize))
        nrows = len(data) // self.dtype.itemsize
        if order == 'F':
            arr = np.empty((nrows,), dtype=self.dtype)
            prev = 0
            j = 0
            for i in range(len(self.dtype)):
                idata = data[prev:(prev + (nrows * self.dtype[i].itemsize))]
                if np.issubdtype(self.dtype[i], np.dtype('complex')):
                    idata_real = idata[:(nrows * self.dtype[i].itemsize // 2)]
                    idata_imag = idata[(nrows * self.dtype[i].itemsize // 2):]
                    arr_real = np.fromstring(idata_real, dtype='float64')
                    arr_imag = np.fromstring(idata_imag, dtype='float64')
                    arr[self.dtype.names[i]] = np.zeros(nrows, dtype=self.dtype[i])
                    arr[self.dtype.names[i]] += arr_real
                    arr[self.dtype.names[i]] += arr_imag * 1j
                else:
                    arr[self.dtype.names[i]] = np.fromstring(idata, dtype=self.dtype[i])
                prev += len(idata)
                j += 1
        else:
            arr = np.fromstring(data, dtype=self.dtype)
            if (len(arr) % self.ncols) != 0:
                raise ValueError("Returned data does not match")
            nrows = len(arr) // self.ncols
            arr.reshape((nrows, self.ncols), order=order)
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
