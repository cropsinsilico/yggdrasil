import re
import copy
import numpy as np
import pandas
from cis_interface import backwards, platform, units
try:
    if not backwards.PY2:  # pragma: Python 3
        from astropy.io import ascii as apy_ascii
        from astropy.table import Table as apy_Table
        _use_astropy = True
    else:  # pragma: Python 2
        apy_ascii, apy_Table = None, None
        _use_astropy = False
except ImportError:  # pragma: no cover
    apy_ascii, apy_Table = None, None
    # print("astropy is not installed, reading/writing as an array will be " +
    #       "disabled. astropy can be installed using 'pip install astropy'.")
    _use_astropy = False


_fmt_char = backwards.unicode2bytes('%')
_default_comment = backwards.unicode2bytes('# ')
_default_delimiter = backwards.unicode2bytes('\t')
_default_newline = backwards.unicode2bytes('\n')


def guess_serializer(msg, **kwargs):
    r"""Guess the type of serializer required based on the message object.

    Args:
        msg (obj): Python object that needs to be serialized.
        **kwargs: Additional keyword arguments are passed to the serializer.

    Returns:
        dict: Extracted keyword arguments for creating a serializer.

    """
    sinfo = dict(**kwargs)
    kws_fmt = {k: kwargs.get(k, None) for k in ['delimiter', 'newline']}
    kws_fmt['comment'] = backwards.unicode2bytes('')
    if sinfo.get('stype', 0) > 3:
        # Don't guess for Pandas, Pickle, Map
        pass
    elif isinstance(msg, np.ndarray):
        names = [backwards.unicode2bytes(n) for n in msg.dtype.names]
        sinfo.setdefault('field_names', names)
        sinfo.setdefault('format_str', table2format(msg.dtype, **kws_fmt))
        sinfo.setdefault('as_array', True)
    elif isinstance(msg, (list, tuple)):
        if 'format_str' not in sinfo:
            typ_list = []
            for x in msg:
                if isinstance(x, backwards.string_types):
                    typ_list.append(np.dtype('S1'))
                else:
                    typ_list.append(np.dtype(type(x)))
            new_type = dict(formats=typ_list,
                            names=['f%d' % i for i in range(len(typ_list))])
            row_dtype = np.dtype(new_type)
            format_str = table2format(row_dtype, **kws_fmt)
            format_str = format_str.replace(backwards.unicode2bytes('%1s'),
                                            backwards.unicode2bytes('%s'))
            sinfo.setdefault('format_str', format_str)
    return sinfo


def get_serializer(stype=None, **kwargs):
    r"""Create a serializer from the provided information.

    Args:
        stype (int, optional): Integer code specifying which serializer to
            use. Defaults to 0.
        **kwargs: Additional keyword arguments are passed to the serializer
            class.

    Returns:
        DefaultSerializer: Serializer based on provided information.

    """
    if stype is None:
        stype = 0
    if stype in [0, 1, 2]:
        from cis_interface.serialize import DefaultSerialize
        cls = DefaultSerialize.DefaultSerialize
    elif stype in [3]:
        from cis_interface.serialize import AsciiTableSerialize
        cls = AsciiTableSerialize.AsciiTableSerialize
    elif stype == 4:
        from cis_interface.serialize import PickleSerialize
        cls = PickleSerialize.PickleSerialize
    elif stype == 5:
        from cis_interface.serialize import MatSerialize
        cls = MatSerialize.MatSerialize
    elif stype == 6:
        from cis_interface.serialize import PandasSerialize
        cls = PandasSerialize.PandasSerialize
    elif stype == 7:
        from cis_interface.serialize import AsciiMapSerialize
        cls = AsciiMapSerialize.AsciiMapSerialize
    elif stype == 8:
        from cis_interface.serialize import PlySerialize
        cls = PlySerialize.PlySerialize
    elif stype == 9:
        from cis_interface.serialize import ObjSerialize
        cls = ObjSerialize.ObjSerialize
    else:
        raise RuntimeError("Unknown serializer type code: %d" % stype)
    return cls(**kwargs)


def extract_formats(fmt_str):
    r"""Locate format codes within a format string.

    Args:
        fmt_str (str, bytes): Format string.

    Returns:
        list: List of identified format codes.

    """
    fmt_regex = (
        "%(?:\d+\\$)?[+-]?(?:[ 0]|\'.{1})?-?\d*(?:\\.\d+)?" +
        "[lhjztL]*(?:64)?[bcdeEufFgGosxXi]" +
        "(?:%(?:\d+\\$)?[+-](?:[ 0]|\'.{1})?-?\d*(?:\\.\d+)?" +
        "[lhjztL]*[eEfFgG]j)?")
    out = re.findall(fmt_regex, backwards.bytes2unicode(fmt_str))
    if isinstance(fmt_str, backwards.bytes_type):
        out = [backwards.unicode2bytes(f) for f in out]
    return out
    

def nptype2cformat(nptype, asbytes=False):
    r"""Convert a numpy data type to a c format string.

    Args:
        nptype (str or numpy.dtype): Numpy data type that should be converted.
        asbytes (bool, optional): If True, the returned format codes will be
            in bytes format (str for Python 2, bytes for Python 3). Defaults to
            False.

    Returns:
        str, list: Corresponding c format specification string or list of
            format strings for complex types..

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
    if len(t) > 0:
        out = [nptype2cformat(t[n], asbytes=asbytes) for n in t.names]
        return out
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
    # elif t == np.dtype("int64"):
    #     if platform._is_win:
    #         cfmt = "%l64d"
    #     else:  # pragma: no cover
    #         cfmt = "%ld"
    elif t == np.dtype("longlong"):
        # On windows C long is 32bit and long long is 64bit
        if platform._is_win:  # pragma: windows
            cfmt = "%l64d"
        else:  # pragma: no cover
            cfmt = "%lld"
    elif t == np.dtype("uint8"):
        cfmt = "%hhu"
    elif t == np.dtype("ushort"):
        cfmt = "%hu"
    elif t == np.dtype("uintc"):
        cfmt = "%u"
    elif t == np.dtype("uint64"):  # Platform dependent
        if platform._is_win:  # pragma: windows
            cfmt = "%l64u"
        else:
            cfmt = "%lu"
    elif t == np.dtype("ulonglong"):  # pragma: no cover
        # On windows C unsigned long is 32bit and unsigned long long is 64bit
        if platform._is_win:  # pragma: windows
            cfmt = "%l64u"
        else:
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
    if asbytes:
        cfmt = backwards.unicode2bytes(cfmt)
    return cfmt


def cformat2nptype(cfmt, names=None):
    r"""Convert a c format string to a numpy data type.

    Args:
        cfmt (str, bytes): c format that should be translated.
        names (list, optional): Names that should be assigned to fields in the
            format string if there is more than one. If not provided, names
            are generated based on the order of the format codes.

    Returns:
        np.dtype: Corresponding numpy data type.

    Raises:
        TypeError: if cfmt is not a string.
        ValueError: If the c format does not begin with '%'.
        ValueError: If the c format does not contain type info.
        ValueError: If the c format cannot be translated to a numpy datatype.

    """
    # TODO: this may fail on 32bit systems where C long types are 32 bit
    if not (isinstance(cfmt, list) or isinstance(cfmt, backwards.string_types)):
        raise TypeError("Input must be a string, bytes string, or list, not %s" %
                        type(cfmt))
    if isinstance(cfmt, backwards.string_types):
        fmt_list = extract_formats(backwards.bytes2unicode(cfmt))
        if len(fmt_list) == 0:
            raise ValueError("Could not locate any format codes in the " +
                             "provided format string (%s)." % cfmt)
    else:
        fmt_list = cfmt
    nfmt = len(fmt_list)
    if nfmt == 1:
        cfmt_str = fmt_list[0]
    else:
        dtype_list = [cformat2nptype(f) for f in fmt_list]
        if names is None:
            names = ['f%d' % i for i in range(nfmt)]
        elif len(names) != nfmt:
            raise ValueError("Number of names does not match the number of fields.")
        else:
            names = [backwards.bytes2unicode(n) for n in names]
        out = np.dtype(dict(names=names, formats=dtype_list))
        # out = np.dtype([(n, d) for n, d in zip(names, dtype_list)])
        return out
    out = None
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
        elif ('ll' in cfmt_str) or ('l64' in cfmt_str):
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
        elif ('ll' in cfmt_str) or ('l64' in cfmt_str):
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
    return np.dtype(out)


def cformat2pyscanf(cfmt):
    r"""Convert a c format specification string to a version that the
    python scanf module can use.

    Args:
        cfmt (str, bytes, list): C format specification string or list of format
            strings.

    Returns:
        str, bytes, list: Version of cfmt or list of cfmts that can be parsed by
            scanf.

    Raises:
        TypeError: If cfmt is not a bytes/str/list.
        ValueError: If there are not an format codes in the format string.

    """
    if not (isinstance(cfmt, list) or isinstance(cfmt, backwards.string_types)):
        raise TypeError("Input must be a string, bytes string, or list, not %s" %
                        type(cfmt))
    if isinstance(cfmt, list):
        return [cformat2pyscanf(f) for f in cfmt]
    cfmt_out = backwards.bytes2unicode(cfmt)
    fmt_list = extract_formats(cfmt_out)
    if len(fmt_list) == 0:
        raise ValueError("Could not locate any format codes in the " +
                         "provided format string (%s)." % cfmt)
    for cfmt_str in fmt_list:
        # Hacky, but necessary to handle concatenation of a single byte
        if cfmt_str[-1] == 's':
            out = '%s'
        else:
            out = cfmt_str
        # if cfmt_str[-1] == 'j':
        #     # Handle complex format specifier
        #     out = '%g%+gj'
        # else:
        #     out = backwards.bytes2unicode(_fmt_char)
        #     out += cfmt_str[-1]
        #     out = out.replace('h', '')
        #     out = out.replace('l', '')
        #     out = out.replace('64', '')
        cfmt_out = cfmt_out.replace(cfmt_str, out, 1)
    if isinstance(cfmt, backwards.bytes_type):
        cfmt_out = backwards.unicode2bytes(cfmt_out)
    return cfmt_out


def format_message(args, fmt_str):
    r"""Format a message from a list of arguments and a format string.

    Args:
        args (list, obj): List of arguments or single argument that should be
            formatted using the format string.
        fmt_str (str, bytes): Format string that should be used to format the
            arguments.

    Returns:
        str, bytes: Formatted message. The type will match the type of the
            fmt_str.

    Raises:
        RuntimeError: If the number of arguments does not match the number of
            format fields.

    """
    if not isinstance(args, (tuple, list)):
        args = (args, )
    nfmt = len(extract_formats(fmt_str))
    args_ = []
    if len(args) < nfmt:
        raise RuntimeError("Number of arguments (%d) does not match " % len(args) +
                           "number of format fields (%d)." % nfmt)
    for a in args:
        if np.iscomplexobj(a):
            args_ += [a.real, a.imag]
        else:
            args_.append(a)
    out = backwards.format_bytes(fmt_str, tuple(args_))
    return out


def process_message(msg, fmt_str):
    r"""Extract python objects from a message using a format string.

    Args:
        msg (str, bytes): Message that should be parsed.
        fmt_str (str, bytes): Format string that should be used to parse the
            message using scanf.

    Returns:
        tuple: Variables extracted from the message.

    Raises:
        TypeError: If the message is not a string or bytes string type.
        ValueError: If the expected number of variables cannot be extracted
            from the message.

    """
    if not isinstance(msg, backwards.string_types):
        raise TypeError("Message must be a string or bytes string type.")
    nfmt = len(extract_formats(fmt_str))
    py_fmt_str = cformat2pyscanf(fmt_str)
    args = backwards.scanf_bytes(py_fmt_str, msg)
    if args is None:
        nargs = 0
    else:
        nargs = len(args)
    if nargs != nfmt:
        raise ValueError("%d arguments were extracted, " % nargs +
                         "but format string expected %d." % nfmt)
    return args


def combine_flds(arrs, dtype=None):
    r"""Combine a list of arrays as fields in a structured array.

    Args:
        arrs (list): List of arrays, one for each field in a structured array.
        dtype (np.dtype, optional): Data type that resulting array should have.
            If not provided, it is determined from the types of the input arrays.

    Returns:
        np.ndarray: Structured numpy array with fields assigned from the
            provided arrays.

    Raises:
        ValueError: If the number of arrays does not match the number of fields
            in the provided data type.
        ValueError: If any of the provided arrays does not have the same number
            of elements as the first array.

    """
    # Get dtype
    nflds = len(arrs)
    shape = arrs[0].shape
    if dtype is None:
        names = ['f%d' % i for i in range(nflds)]
        dtype = np.dtype([(n, a.dtype) for n, a in zip(names, arrs)])
    # Check number of fields and array shapes
    if len(dtype) != nflds:
        raise ValueError("dtype has %d fields, but %d arrays were provided." %
                         (len(dtype), nflds))
    for i, a in enumerate(arrs):
        if a.shape != shape:
            raise ValueError("Shape of array %d (%s) does " % (i, a.shape) +
                             "match shape of 1st array (%s)." % shape)
    # Combine arrays
    out = np.empty(shape, dtype=dtype)
    for i, a in enumerate(arrs):
        out[dtype.names[i]] = a
    return out


def combine_eles(arrs, dtype=None):
    r"""Combine arrays as elements in a structure numpy array.

    Args:
        arrs (list): List of numpy arrays or lists specifying the values of
            fields in elements of a structured numpy array.
        dtype (np.dtype, optional): Data type that the resulting array should
            have. If not provided, it is determined from the provided arrays.

    Returns:
        np.ndarray: Structured numpy array with information from the provided
            arrays/lists as elements.

    Raises:
        ValueError: If the number of fields in any of the provided arrays/lists
            does not match the number of fields in the provided/created dtype.

    """
    neles = len(arrs)
    # Check types of arrays
    for i, a in enumerate(arrs):
        if not isinstance(a, (np.ndarray, np.void, list, tuple)):
            raise TypeError("Elements must be arrays, lists or tuples. " +
                            "Element %d has type %s." % (i, type(a)))
    # Check that there are enough elements for each data type
    if dtype is None:
        if isinstance(arrs[0], (np.ndarray, np.void)):
            nflds = len(arrs[0].dtype)
        else:
            nflds = len(arrs[0])
    else:
        nflds = len(dtype)
    for i, a in enumerate(arrs):
        if isinstance(a, (np.ndarray, np.void)):
            if len(a.dtype) != nflds:
                raise ValueError("Element %d has dtype %s, but " % (i, a.dtype) +
                                 "%d fields are expected." % nflds)
        else:
            if len(a) != nflds:
                raise ValueError("Element %d has %d values, but " % (i, len(a)) +
                                 "%d fields are expected." % nflds)
    # Get data type
    if dtype is None:
        if isinstance(arrs[0], (np.ndarray, np.void)):
            dtype = arrs[0].dtype
        elif isinstance(arrs[0], (list, tuple)):
            names = None
            for iele in arrs:
                if isinstance(iele, (np.ndarray, np.void)):
                    names = iele.dtype.names
                    break
            nflds = len(arrs[0])
            dtype_list = []
            for i, a in enumerate(arrs[0]):
                dtype_str = np.dtype(type(a)).str
                if 'S' in dtype_str:
                    max_len = 0
                    for iele in arrs:
                        if isinstance(iele, (np.ndarray, np.void)):
                            n = iele.dtype.names[i]
                            max_len = max(max_len, len(iele[n]))
                        else:
                            max_len = max(max_len, len(iele[i]))
                    dtype_str = 'S%d' % max_len
                dtype_list.append(np.dtype(dtype_str))
            if names is None:
                names = ['f%d' % i for i in range(nflds)]
            dtype = np.dtype({'names': names, 'formats': dtype_list})
    # Combine rows
    out = np.empty(neles, dtype=dtype)
    for i, a in enumerate(arrs):
        if isinstance(a, (np.ndarray, np.void)):
            out[i] = a
        else:
            for j, n in enumerate(dtype.names):
                out[n][i] = a[j]
    return out


def consolidate_array(arrs, dtype=None):
    r"""Consolidate arrays either as fields or elements in a structured array.

    Args:
        arrs (np.ndarray, list, tuple): Array or list of arrays that should be
            reformatted/consolidated as a structured array.
        dtype (np.dtype, optional): Data type that the resulting array should
            have. If not provided, it is determined from the input.

    Returns:
        np.ndarray: Structured array of the specified type with values taken
            from the provided array(s).

    Raises:
        ValueError: If an unstructured array is provided, but the last dimension
            of the array does not have the proper size to fill the fields in
            the specified data type.
        ValueError: If a structured array is provided, but it does not have a
            data type compatible with the specified data type.
        TypeError: If 'arrs' is not a numpy array, list, or tuple.

    """
    if isinstance(arrs, np.ndarray):
        if (dtype is None) or (dtype == arrs.dtype):
            out = arrs
        else:
            if len(arrs.dtype) == 0:
                if arrs.shape[-1] != len(dtype):
                    raise ValueError("The last dimension of the input array " +
                                     "(%d) " % arrs.shape[-1] +
                                     "dosn't match the number of fields in " +
                                     "the dtype (%d)." % len(dtype))
                out = np.empty(arrs.shape[:-1], dtype=dtype)
                for i in range(arrs.shape[-1]):
                    out[dtype.names[i]] = arrs[..., i]
            elif len(arrs.dtype) == len(dtype):
                out = np.empty(arrs.shape, dtype=dtype)
                for n1, n2 in zip(arrs.dtype.names, dtype.names):
                    out[n2] = arrs[n1]
            else:
                raise ValueError("The input array data type (%s) " % arrs.dtype +
                                 "is not compatible with the specified " +
                                 "data type (%s)." % dtype)
    elif isinstance(arrs, (list, tuple)):
        if isinstance(arrs[0], (np.ndarray, np.void)):
            if len(arrs[0].dtype) > 1:
                out = combine_eles(arrs, dtype=dtype)
            else:
                out = combine_flds(arrs, dtype=dtype)
        else:
            out = combine_eles(arrs, dtype=dtype)
    else:
        raise TypeError("Input 'arrs' must be a numpy array, list, or tuple.")
    return out


def format2table(fmt_str):
    r"""Get table information from the table format string.

    Args:
        fmt_str (str, bytes): Format string that describes how the table
            columns are formatted.

    Returns:
        dict: Table information parameters.

    Raises:
        RuntimeError: If the column separator is not the same between all
            of the format codes.

    """
    out = {}
    out['fmts'] = extract_formats(fmt_str)
    if len(out['fmts']) == 0:
        return out
    seps = []
    comment, fmt_rem = fmt_str.split(out['fmts'][0], 1)
    if comment:
        out['comment'] = comment
    for f in out['fmts'][1:]:
        isep, fmt_rem = fmt_rem.split(f, 1)
        seps.append(isep)
    if fmt_rem:
        out['newline'] = fmt_rem
    seps = set(seps)
    if len(seps) == 0:
        out['delimiter'] = _default_delimiter
    elif len(seps) == 1:
        out['delimiter'] = list(seps)[0]
    elif len(seps) > 1:
        raise RuntimeError("There is more than one column separator (%s)." % seps)
    return out


def table2format(fmts=[], delimiter=None, newline=None, comment=None):
    r"""Create a format string from table information.

    Args:
        fmts (list, optional): List of format codes for each column. Defaults to
            [].
        delimiter (bytes, optional): String used to separate columns. Defaults
            to _default_delimiter.
        newline (bytes, optional): String used to indicate the end of a table
            line. Defaults to _default_newline.
        comment (bytes, optional): String that should be prepended to the format
            string to indicate a comment. Defaults to _default_comment.

    Returns:
        str, bytes: Table format string.

    """
    if delimiter is None:
        delimiter = _default_delimiter
    if newline is None:
        newline = _default_newline
    if comment is None:
        comment = _default_comment
    if isinstance(fmts, np.dtype):
        fmts = nptype2cformat(fmts)
    bytes_fmts = [backwards.unicode2bytes(f) for f in fmts]
    fmt_str = comment + delimiter.join(bytes_fmts) + newline
    return fmt_str


# def unicode_dtype(old_dtype):
#     r"""Convert a dtype to use unicode.

#     Args:
#         old_dtype (np.dtype): Numpy data type.

#     Returns:
#         np.dtype: Numpy dtype with bytes replaced with unicode.

#     """
#     if backwards.PY2:  # pragma: Python 2
#         new_dtype = old_dtype
#     else:  # pragma: Python 3
#         ntype = len(old_dtype)
#         if ntype > 0:
#             names = old_dtype.names
#             types = [unicode_dtype(old_dtype[i]) for i in range(ntype)]
#             new_type = dict(formats=types, names=names)
#             new_dtype = np.dtype(new_type)
#         else:
#             if np.issubdtype(old_dtype, np.dtype('S')):
#                 front, width = old_dtype.str.split('S')
#                 new_dtype = np.dtype(front + 'U' + width)
#             else:
#                 new_dtype = old_dtype
#     return new_dtype


def array_to_table(arrs, fmt_str, use_astropy=False):
    r"""Serialize an array as an ASCII table.

    Args:
        arrs (np.ndarray, list, tuple): Structured array or list/tuple of
            arrays that contain table information.
        fmt_str (str, bytes): Format string that should be used to structure
            the ASCII array.
        use_astropy (bool, optional): If True, astropy will be used to format
            the table if it is installed. Defaults to False.

    Returns:
        bytes: ASCII table.

    """
    if not _use_astropy:
        use_astropy = False
    dtype = cformat2nptype(fmt_str)
    info = format2table(fmt_str)
    arr1 = consolidate_array(arrs, dtype=dtype)
    if use_astropy:
        fd = backwards.StringIO()
        table = apy_Table(arr1)
        delimiter = info['delimiter']
        delimiter = backwards.bytes2unicode(delimiter)
        apy_ascii.write(table, fd, delimiter=delimiter,
                        format='no_header')
        out = backwards.unicode2bytes(fd.getvalue())
    else:
        fd = backwards.BytesIO()
        for ele in arr1:
            line = format_message(ele.tolist(), fmt_str)
            fd.write(line)
        # fmt = fmt_str.split(info['newline'])[0]
        # np.savetxt(fd, arr1,
        #            fmt=fmt, delimiter=info['delimiter'],
        #            newline=info['newline'], header='')
        out = fd.getvalue()
    fd.close()
    return out


def table_to_array(msg, fmt_str=None, use_astropy=False, names=None,
                   delimiter=None, comment=None, encoding='utf-8'):
    r"""Extract information from an ASCII table as an array.

    Args:
        msg (bytes): ASCII table as bytes string.
        fmt_str (bytes): Format string that should be used to parse the table.
            If not provided, this will attempt to determine the types of columns
            based on their contents.
        use_astropy (bool, optional): If True, astropy will be used to parse
            the table if it is installed. Defaults to False.
        names (list, optional): Field names that should be used for the
            structured data type of the output array. If not provided, names
            are generated based on the order of the fields in the table.
        delimiter (str, optional): String used to separate columns. Defaults to
            None and is not used. This is only used if fmt_str is not provided.
        comment (str, optional): String used to denote comments. Defaults to
            None and is not used. This is only used if fmt_str is not provided.
        encoding (str, optional): Encoding that should be used in Python 3 or
            higher to extract information from the message. Defaults to 'utf-8'.

    Returns:
        np.ndarray: Table contents as an array.
    
    """
    if not _use_astropy:
        use_astropy = False
    if fmt_str is None:
        dtype = None
        info = dict(delimiter=delimiter, comment=comment)
    else:
        dtype = cformat2nptype(fmt_str, names=names)
        info = format2table(fmt_str)
        names = dtype.names
    fd = backwards.BytesIO(msg)
    if names is not None:
        names = [backwards.bytes2unicode(n) for n in names]
    np_kws = dict()
    if info.get('delimiter', None) is not None:
        np_kws['delimiter'] = info['delimiter']
    if info.get('comment', None) is not None:
        np_kws['comments'] = info['comment']
    for k, v in np_kws.items():
        np_kws[k] = backwards.bytes2unicode(v)
    if use_astropy:
        # fd = backwards.StringIO(backwards.bytes2unicode(msg))
        if 'comments' in np_kws:
            np_kws['comment'] = np_kws.pop('comments')
        tab = apy_ascii.read(fd, names=names, guess=True,
                             encoding=encoding,
                             format='no_header', **np_kws)
        arr = tab.as_array()
        typs = [arr.dtype[i].str for i in range(len(arr.dtype))]
        cols = [c for c in tab.columns]
        # Convert type bytes if python 3
        if not backwards.PY2:  # pragma: Python 3
            new_typs = copy.copy(typs)
            convert = []
            for i in range(len(arr.dtype)):
                if np.issubdtype(arr.dtype[i], np.dtype('U')):
                    new_typs[i] = 'S' + typs[i].split('U')[-1]
                    convert.append(i)
            if convert:
                old_arr = arr
                new_dtyp = np.dtype([(c, t) for c, t in zip(cols, new_typs)])
                new_arr = np.zeros(arr.shape, new_dtyp)
                for i in range(len(arr.dtype)):
                    if i in convert:
                        x = np.char.encode(old_arr[cols[i]], encoding='utf-8')
                        new_arr[cols[i]] = x
                    else:
                        new_arr[cols[i]] = old_arr[cols[i]]
                arr = new_arr
                typs = new_typs
        # Convert complex type
        for i in range(len(arr.dtype)):
            if np.issubdtype(arr.dtype[i], np.dtype('S')):
                new_typs = copy.copy(typs)
                new_typs[i] = 'complex'
                new_dtyp = np.dtype([(c, t) for c, t in zip(cols, new_typs)])
                try:
                    arr = arr.astype(new_dtyp)
                except ValueError:
                    pass
        if dtype is not None:
            arr = arr.astype(dtype)
    else:
        arr = np.genfromtxt(fd, autostrip=True, dtype=None,
                            names=names, **np_kws)
        if dtype is not None:
            arr = arr.astype(dtype)
    fd.close()
    return arr


def array_to_bytes(arrs, dtype=None, order='C'):
    r"""Serialize an array to bytes.

    Args:
        arrs (np.ndarray, list, tuple): Structured array or list/tuple of
            arrays that should be serialized. If 'arrs' is not a numpy
            structured array, a structured array will first be constructed
            from the provided data.
        dtype (np.dtype, optional): Structured data type that array should
            be converted to prior to serialization. If not provided, it
            will be determined from the array data.
        order (str, optional): Order that array should be serialized in.
            'C' for row first, 'F' for column/field first. Defaults to 'C'.

    Returns:
        bytes, str: Serialized array.

    Raises:

    """
    arr1 = consolidate_array(arrs, dtype=dtype)
    if order == 'F':
        ntyp = len(arr1.dtype)
        if ntyp == 0:
            out = arr1.tobytes(order='F')
        else:
            out = backwards.unicode2bytes('')
            for i in range(ntyp):
                n = arr1.dtype.names[i]
                if np.issubdtype(arr1.dtype[i], np.dtype('complex')):
                    out = out + arr1[n].real.tobytes(order='F')
                    out = out + arr1[n].imag.tobytes(order='F')
                else:
                    out = out + arr1[n].tobytes(order='F')
    else:
        out = arr1.tobytes(order='C')
    return out


def bytes_to_array(data, dtype, order='C', shape=None):
    r"""Deserialize an array from bytes data.

    Args:
        data (bytes): Serialized array data.
        dtype (np.dtype, optional): Structured data type of the serialized array.
        order (str, optional): Order that array was serialized in.
            'C' for row first, 'F' for column/field first. Defaults to 'C'.
        shape (tuple, optional): Shape that array should be reshaped to
            after being deserialized. Defaults to a flat array if not provided.

    Returns:
        np.ndarray: Deserialized array.

    Raises:

    """
    if (len(data) % dtype.itemsize) != 0:
        raise RuntimeError("Data length (%d) is not a multiple " % len(data) +
                           "of the itemsize (%d)." % dtype.itemsize)
    nele = len(data) // dtype.itemsize
    ntyp = len(dtype)
    if (order == 'F') and (ntyp > 0):
        arr = np.empty((nele,), dtype=dtype)
        prev = 0
        j = 0
        for i in range(ntyp):
            idata = data[prev:(prev + (nele * dtype[i].itemsize))]
            if np.issubdtype(dtype[i], np.dtype('complex')):
                idata_real = idata[:(nele * dtype[i].itemsize // 2)]
                idata_imag = idata[(nele * dtype[i].itemsize // 2):]
                arr_real = np.fromstring(idata_real, dtype='float64')
                arr_imag = np.fromstring(idata_imag, dtype='float64')
                arr[dtype.names[i]] = np.zeros(nele, dtype=dtype[i])
                arr[dtype.names[i]] += arr_real
                arr[dtype.names[i]] += arr_imag * 1j
            else:
                arr[dtype.names[i]] = np.fromstring(idata, dtype=dtype[i])
            prev += len(idata)
            j += 1
    else:
        arr = np.fromstring(data, dtype=dtype)
    # Reshape array
    if shape is not None:
        arr = arr.reshape(shape, order=order)
    return arr


def format_header(format_str=None, dtype=None,
                  comment=None, delimiter=None, newline=None,
                  field_names=None, field_units=None):
    r"""Get header lines for a table based on table information.

    Args:
        format_str (bytes, str, optional): Format string describing how the
            table should be formatted. If not provided, information on the
            formats is extracted from dtype.
        dtype (np.dtype, optional): Structured data type specifying the types
            of fields in the table. If not provided and format_str not
            specified, the formats will not be part of the header.
        comment (bytes, optional): String that should be used to comment the
            header lines. If not provided and not in format_str, defaults to
            _default_comment.
        delimiter (bytes, optional): String that should be used to separate
            columns. If not provided and not in format_str, defaults to
            _default_delimiter.
        newline (bytes, optional): String that should be used to end lines in
            the table. If not provided and not in format_str, defaults to
            _default_newline.
        field_names (list, optional): List of field names that should be
            included in the header. If not provided and dtype is None, names
            will not be included in the header.
        field_units (list, optional): List of field units that should be
            included in the header. If not provided, units will not be
            included.

    Returns:
        bytes: Bytes lines comprising a table header.

    Raises:
        ValueError: If there are not any format, names or units specified.

    """
    # Set defaults
    fmts = None
    if format_str is not None:
        info = format2table(format_str)
        if len(info['fmts']) > 0:
            fmts = info['fmts']
            if delimiter is None:
                delimiter = info['delimiter']
            if newline is None:
                newline = info.get('newline', None)
            if comment is None:
                comment = info.get('comment', None)
    if dtype is not None:
        if fmts is None:
            fmts = nptype2cformat(dtype, asbytes=True)
        if field_names is None:
            field_names = [backwards.unicode2bytes(n) for n in dtype.names]
    if delimiter is None:
        delimiter = _default_delimiter
    if comment is None:
        comment = _default_comment
    if newline is None:
        newline = _default_newline
    # Get count of fields
    if fmts is not None:
        nfld = len(fmts)
    elif field_names is not None:
        nfld = len(field_names)
    elif field_units is not None:
        nfld = len(field_units)
    else:
        raise ValueError("No formats, names, or units provided.")
    # Create lines
    out = []
    for x in [field_names, field_units, fmts]:
        if (x is None):
            continue
        # if (len(x) == 0) or (x[0] == 'None'):
        #     continue
        assert(len(x) == nfld)
        out.append(comment +
                   delimiter.join([backwards.unicode2bytes(ix) for ix in x]))
    out = newline.join(out) + newline
    return out


def discover_header(fd, serializer, newline=_default_newline,
                    comment=_default_comment, delimiter=None,
                    lineno_format=None, lineno_names=None, lineno_units=None,
                    use_astropy=False):
    r"""Discover ASCII table header info from a file.

    Args:
        fd (file): File object containing the table.
        serializer (DefaultSerialize): Serializer that should be updated with
            header information.
        newline (str, optional): Newline character that should be used to split
            header if it is not already a list. Defaults to _default_newline.
        comment (bytes, optional): String that should be used to mark the
            header lines. If not provided and not in format_str, defaults to
            _default_comment.
        delimiter (bytes, optional): String that should be used to separate
            columns. If not provided and not in format_str, defaults to
            _default_delimiter.
        lineno_format (int, optional): Line number where formats are located.
            If not provided, an attempt will be made to locate one.
        lineno_names (int, optional): Line number where field names are located.
            If not provided, an attempt will be made to locate one.
        lineno_units (int, optional): Line number where field units are located.
            If not provided, an attempt will be made to locate one.
        use_astropy (bool, optional): If True, astropy will be used to parse
            the table if it is installed. Defaults to False.

    """
    header_lines = []
    header_size = 0
    prev_pos = fd.tell()
    for line in fd:
        sline = backwards.unicode2bytes(line.replace(
            backwards.unicode2bytes(platform._newline), newline))
        if not sline.startswith(comment):
            break
        header_size += len(line)
        header_lines.append(sline)
    # Parse header & set serializer attributes
    header = parse_header(header_lines, newline=newline,
                          lineno_format=lineno_format,
                          lineno_names=lineno_names,
                          lineno_units=lineno_units)
    for k in ['format_str', 'field_names', 'field_units']:
        if header.get(k, False):
            setattr(serializer, k, header[k])
    if (delimiter is None) or ('format_str' in header):
        delimiter = header['delimiter']
    # Try to determine format from array without header
    str_fmt = backwards.unicode2bytes('%s')
    if (((serializer.format_str is None) or
         (str_fmt in serializer.format_str))):
        fd.seek(prev_pos + header_size)
        all_contents = fd.read()
        if len(all_contents) == 0:  # pragma: debug
            return  # In case the file has not been written
        arr = table_to_array(all_contents,
                             names=serializer.field_names,
                             comment=comment,
                             delimiter=delimiter,
                             use_astropy=use_astropy)
        serializer.field_names = arr.dtype.names
        if serializer.format_str is None:
            serializer.format_str = table2format(
                arr.dtype, delimiter=delimiter,
                comment=backwards.unicode2bytes(''),
                newline=header['newline'])
        while str_fmt in serializer.format_str:
            ifld = serializer.field_formats.index(str_fmt)
            max_len = len(max(arr[serializer.field_names[ifld]], key=len))
            new_str_fmt = backwards.unicode2bytes('%' + str(max_len) + 's')
            serializer.format_str = serializer.format_str.replace(
                str_fmt, new_str_fmt, 1)
    # Seek to just after the header
    fd.seek(prev_pos + header_size)


def parse_header(header, newline=_default_newline, lineno_format=None,
                 lineno_names=None, lineno_units=None):
    r"""Parse an ASCII table header to get information about the table.

    Args:
        header (list, str): Header lines that should be parsed.
        newline (str, optional): Newline character that should be used to split
            header if it is not already a list. Defaults to _default_newline.
        lineno_format (int, optional): Line number where formats are located.
            If not provided, an attempt will be made to locate one.
        lineno_names (int, optional): Line number where field names are located.
            If not provided, an attempt will be made to locate one.
        lineno_units (int, optional): Line number where field units are located.
            If not provided, an attempt will be made to locate one.

    Returns:
        dict: Parameters describing the information determined from the header.

    """
    out = dict()
    excl_lines = []
    if isinstance(header, backwards.bytes_type):
        header = [h + newline for h in header.split(newline)]
    # Locate format line
    if lineno_format is None:
        for i in range(len(header)):
            if len(extract_formats(header[i])) > 0:
                lineno_format = i
                break
    # Get format information from format line
    if lineno_format is not None:
        excl_lines.append(lineno_format)
        info = format2table(header[lineno_format])
        ncol = len(info['fmts'])
        out.update(**info)
        out['format_str'] = header[lineno_format].split(info['comment'])[-1]
    else:
        ncol = 0
        out.update(delimiter=_default_delimiter, comment=_default_comment,
                   fmts=[])
    out.setdefault('newline', newline)
    # Use explicit lines for names & units
    if lineno_names is not None:
        excl_lines.append(lineno_names)
        out['field_names'] = header[lineno_names].split(out['comment'])[-1].split(
            out['newline'])[0].split(out['delimiter'])
    if lineno_units is not None:
        excl_lines.append(lineno_units)
        out['field_units'] = header[lineno_units].split(out['comment'])[-1].split(
            out['newline'])[0].split(out['delimiter'])
    # Locate units & names
    for i in range(len(header)):
        if ('field_units' in out) and ('field_names' in out):
            break
        if i in excl_lines:
            continue
        cols = header[i].split(out['comment'])[-1].split(
            out['newline'])[0].split(out['delimiter'])
        if (len(cols) == ncol) or (ncol == 0):
            ncol = len(cols)
            is_unit = True
            for u in cols:
                if not units.is_unit(u):
                    is_unit = False
                    break
            if is_unit:
                if 'field_units' in out:
                    raise RuntimeError("Two lines could contain the field units.")
                out['field_units'] = cols
            else:
                if 'field_names' in out:
                    raise RuntimeError("Two lines could contain the field names.")
                out['field_names'] = cols
    return out


def numpy2dict(arr):
    r"""Covert a numpy structured array to a dictionary of arrays.

    Args:
        arr (np.ndarray): Array to convert.

    Returns:
        dict: Dictionary with contents from the input array.

    """
    out = dict()
    if arr.dtype.names is None:
        out['0'] = arr
    else:
        for n in arr.dtype.names:
            out[n] = arr[n]
    return out


def dict2numpy(d, order=None):
    r"""Convert a dictionary of arrays to a numpy structured array.

    Args:
        d (dict): Dictionary of arrays.
        order (list, optional): Order that keys should be in array.
            Defaults to None and will be sorted keys.

    Returns:
        np.ndarray: Structured numpy array.

    """
    if order is None:
        order = sorted([k for k in d.keys()])
    dtypes = [d[k].dtype for k in order]
    dtype = np.dtype(dict(names=order, formats=dtypes))
    shape = d[order[0]].shape
    out = np.empty(shape, dtype)
    for n in order:
        out[n] = d[n]
    return out


def numpy2pandas(arr):
    r"""Covert a numpy structured array to a Pandas DataFrame.

    Args:
        arr (np.ndarray): Array to convert.

    Returns:
        pandas.DataFrame: Pandas data frame with contents from the input array.

    """
    return pandas.DataFrame(arr)


def pandas2numpy(frame, index=False):
    r"""Convert a Pandas DataFrame to a numpy structured array.

    Args:
        frame (pandas.DataFrame): Frame to convert.
        index (bool, optional): If True, the index will be included as a field
            in the array. Defaults to False.

    Returns:
        np.ndarray: Structured numpy array.

    """
    arr = frame.to_records(index=index)
    # Covert object type to string
    old_dtype = arr.dtype
    new_dtype = dict(names=old_dtype.names, formats=[])
    for i in range(len(old_dtype)):
        if old_dtype[i] == object:
            try:
                max_len = len(max(arr[old_dtype.names[i]], key=len))
                new_dtype['formats'].append(np.dtype("S%s" % max_len))
            except TypeError:
                new_dtype['formats'].append(old_dtype[i])
        else:
            new_dtype['formats'].append(old_dtype[i])
    # Convert to unstructured array if name is default and only one column
    if (len(new_dtype['names']) == 1) and (new_dtype['names'][0] == '0'):
        out = np.zeros(arr.shape, dtype=new_dtype['formats'][0])
        out[:] = arr[new_dtype['names'][0]]
    else:
        new_dtype = np.dtype(new_dtype)
        out = np.zeros(arr.shape, dtype=new_dtype)
        out[:] = arr[:]
    return out


def dict2pandas(d, order=None):
    r"""Convert a dictionary of arrays to a numpy structured array.

    Args:
        d (dict): Dictionary of arrays.
        order (list, optional): Order that keys should be in array.
            Defaults to None and will be sorted keys.

    Returns:
        pandas.DataFrame: Pandas data frame with contents from the input dict.

    """
    return numpy2pandas(dict2numpy(d, order=order))


def pandas2dict(frame):
    r"""Convert a Pandas DataFrame to a numpy structured array.

    Args:
        frame (pandas.DataFrame): Frame to convert.

    Returns:
        dict: Dictionary with contents from the input frame.

    """
    return numpy2dict(pandas2numpy(frame))


__all__ = []
