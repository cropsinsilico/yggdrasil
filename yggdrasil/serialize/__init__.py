import re
import copy
import numpy as np
import pandas
import io as sio
from yggdrasil import platform, units, scanf, tools
try:
    from astropy.io import ascii as apy_ascii
    from astropy.table import Table as apy_Table
    _use_astropy = True
except ImportError:  # pragma: no cover
    apy_ascii, apy_Table = None, None
    # print("astropy is not installed, reading/writing as an array will be "
    #       + "disabled. astropy can be installed using 'pip install astropy'.")
    _use_astropy = False


_fmt_char = b'%'
_default_comment = b'# '
_default_delimiter = b'\t'
_default_newline = b'\n'
_fmt_char_str = _fmt_char.decode("utf-8")
_default_comment_str = _default_comment.decode("utf-8")
_default_delimiter_str = _default_delimiter.decode("utf-8")
_default_newline_str = _default_newline.decode("utf-8")


def extract_formats(fmt_str):
    r"""Locate format codes within a format string.

    Args:
        fmt_str (str, bytes): Format string.

    Returns:
        list: List of identified format codes.

    """
    fmt_regex = (
        "%(?:\\d+\\$)?[+-]?(?:[ 0]|\'.{1})?-?\\d*(?:\\.\\d+)?"
        + "[lhjztL]*(?:64)?[bcdeEufFgGosxXi]"
        + "(?:%(?:\\d+\\$)?[+-](?:[ 0]|\'.{1})?-?\\d*(?:\\.\\d+)?"
        + "[lhjztL]*[eEfFgG]j)?")
    as_bytes = False
    if isinstance(fmt_str, bytes):
        as_bytes = True
        fmt_str = fmt_str.decode("utf-8")
    out = re.findall(fmt_regex, fmt_str)
    if as_bytes:
        out = [f.encode("utf-8") for f in out]
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
        if t.itemsize == 0:
            cfmt = '%s'
        else:
            cfmt = "%" + str(t.itemsize) + "s"
    elif np.issubdtype(t, np.dtype("U")):
        if t.itemsize == 0:
            cfmt = '%s'
        else:
            cfmt = "%" + str(t.itemsize) + "s"
    else:
        raise ValueError("No format specification string for dtype %s" % t)
    # Short and long specifiers not supported by python scanf
    # cfmt = cfmt.replace("h", "")
    # cfmt = cfmt.replace("l", "")
    if asbytes and (not isinstance(cfmt, bytes)):
        cfmt = cfmt.encode("utf-8")
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
    if not (isinstance(cfmt, list) or isinstance(cfmt, (str, bytes))):
        raise TypeError("Input must be a string, bytes string, or list, not %s" %
                        type(cfmt))
    if isinstance(cfmt, (str, bytes)):
        cfmt = tools.bytes2str(cfmt)
        fmt_list = extract_formats(cfmt)
        if len(fmt_list) == 0:
            raise ValueError("Could not locate any format codes in the "
                             + "provided format string (%s)." % cfmt)
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
            names = tools.bytes2str(names, recurse=True)
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
        lsiz = lint * np.dtype('S1').itemsize
        out = 'S%d' % lsiz
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
    if not (isinstance(cfmt, list) or isinstance(cfmt, (str, bytes))):
        raise TypeError("Input must be a string, bytes string, or list, not %s" %
                        type(cfmt))
    if isinstance(cfmt, list):
        return [cformat2pyscanf(f) for f in cfmt]
    if isinstance(cfmt, str):
        as_bytes = False
        cfmt_out = cfmt
    else:
        as_bytes = True
        cfmt_out = cfmt.decode("utf-8")
    fmt_list = extract_formats(cfmt_out)
    if len(fmt_list) == 0:
        raise ValueError("Could not locate any format codes in the "
                         + "provided format string (%s)." % cfmt)
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
        #     out += cfmt_str[-1]
        #     out = out.replace('h', '')
        #     out = out.replace('l', '')
        #     out = out.replace('64', '')
        cfmt_out = cfmt_out.replace(cfmt_str, out, 1)
    if as_bytes:
        cfmt_out = cfmt_out.encode("utf-8")
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
        raise RuntimeError("Number of arguments (%d) does not match " % len(args)
                           + "number of format fields (%d)." % nfmt)
    for a0 in args:
        a = units.get_data(a0)
        if np.iscomplexobj(a):
            args_ += [a.real, a.imag]
        elif isinstance(a, bytes) and isinstance(fmt_str, str):
            args_.append(a.decode("utf-8"))
        elif isinstance(a, str) and isinstance(fmt_str, bytes):
            args_.append(a.encode("utf-8"))
        else:
            args_.append(a)
    out = fmt_str % tuple(args_)
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
    if not isinstance(msg, (str, bytes)):
        raise TypeError("Message must be a string or bytes string type.")
    nfmt = len(extract_formats(fmt_str))
    py_fmt_str = cformat2pyscanf(fmt_str)
    args = scanf.scanf(py_fmt_str, msg)
    if args is None:
        nargs = 0
    else:
        nargs = len(args)
        if len(args) > 1:
            dtype = cformat2nptype(fmt_str)
            dtype_list = [dtype[i] for i in range(nargs)]
            args = tuple([np.array([a], idtype)[0] for
                          a, idtype in zip(args, dtype_list)])
    if nargs != nfmt:
        raise ValueError("%d arguments were extracted, " % nargs
                         + "but format string expected %d." % nfmt)
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
    else:
        formats = [dtype[i].str for i in range(len(dtype))]
        update_dtype = False
        for i in range(len(dtype)):
            if not dtype[i].str.endswith('S0'):
                continue
            formats[i] = 'S%d' % max([len(x) for x in arrs[i]])
            update_dtype = True
        if update_dtype:
            dtype = np.dtype({'names': dtype.names, 'formats': formats})
    # Check number of fields and array shapes
    if len(dtype) != nflds:
        raise ValueError("dtype has %d fields, but %d arrays were provided." %
                         (len(dtype), nflds))
    for i, a in enumerate(arrs):
        if a.shape != shape:
            raise ValueError("Shape of array %d (%s) does " % (i, a.shape)
                             + "match shape of 1st array (%s)." % shape)
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
    any_arrays = False
    all_arrays = True
    for i, a in enumerate(arrs):
        if isinstance(a, (np.ndarray, np.void, list, tuple)):
            any_arrays = True
        else:
            all_arrays = False
    if not all_arrays:
        if not any_arrays:
            arrs = [arrs]
            neles = 1
        else:
            raise TypeError("Elements must be arrays, lists or tuples. "
                            + "Element %d has type %s." % (i, type(a)))
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
                raise ValueError("Element %d has dtype %s, but " % (i, a.dtype)
                                 + "%d fields are expected." % nflds)
        else:
            if len(a) != nflds:
                raise ValueError("Element %d has %d values, but " % (i, len(a))
                                 + "%d fields are expected." % nflds)
    
    # Get data type
    def get_max_len(i):
        max_len = 0
        for iele in arrs:
            if isinstance(iele, (np.ndarray, np.void)):
                n = iele.dtype.names[i]
                max_len = max(max_len, len(iele[n]))
            else:
                max_len = max(max_len, len(iele[i]))
        return max_len
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
                    max_len = get_max_len(i)
                    dtype_str = 'S%d' % max_len
                dtype_list.append(np.dtype(dtype_str))
            if names is None:
                names = ['f%d' % i for i in range(nflds)]
            dtype = np.dtype({'names': names, 'formats': dtype_list})
    else:
        formats = [dtype[i].str for i in range(len(dtype))]
        update_dtype = False
        for i in range(len(dtype)):
            if not dtype[i].str.endswith('S0'):
                continue
            max_len = get_max_len(i)
            formats[i] = 'S%d' % max_len
            update_dtype = True
        if update_dtype:
            dtype = np.dtype({'names': dtype.names, 'formats': formats})
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
                    raise ValueError("The last dimension of the input array "
                                     + "(%d) " % arrs.shape[-1]
                                     + "dosn't match the number of fields in "
                                     + "the dtype (%d)." % len(dtype))
                out = np.empty(arrs.shape[:-1], dtype=dtype)
                for i in range(arrs.shape[-1]):
                    out[dtype.names[i]] = arrs[..., i]
            elif len(arrs.dtype) == len(dtype):
                out = np.empty(arrs.shape, dtype=dtype)
                for n1, n2 in zip(arrs.dtype.names, dtype.names):
                    out[n2] = arrs[n1]
            else:
                raise ValueError("The input array data type (%s) " % arrs.dtype
                                 + "is not compatible with the specified "
                                 + "data type (%s)." % dtype)
    elif isinstance(arrs, (list, tuple)):
        if isinstance(arrs[0], (np.ndarray, np.void,
                                units._unit_array)):
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
        for s in seps:
            if not s.isspace():
                raise RuntimeError("There is more than one column separator (%s)." % seps)
        out['delimiter'] = min(seps, key=len)
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
    bytes_fmts = tools.str2bytes(fmts, recurse=True)
    fmt_str = (tools.str2bytes(comment)
               + tools.str2bytes(delimiter).join(bytes_fmts)
               + tools.str2bytes(newline))
    return fmt_str


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
    if len(dtype) == 0:
        dtype = np.dtype([('f0', dtype)])
    info = format2table(fmt_str)
    comment = info.get('comment', None)
    if comment is not None:
        fmt_str = fmt_str.split(comment, 1)[-1]
    arr1 = consolidate_array(arrs, dtype=dtype)
    if use_astropy:
        fd = sio.StringIO()
        table = apy_Table(arr1)
        delimiter = tools.bytes2str(info['delimiter'])
        apy_ascii.write(table, fd, delimiter=delimiter,
                        format='no_header')
        out = tools.str2bytes(fd.getvalue())
    else:
        fd = sio.BytesIO()
        fmt_str = tools.str2bytes(fmt_str)
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
    fd = sio.BytesIO(msg)
    if names is not None:
        names = tools.bytes2str(names, recurse=True)
    np_kws = dict()
    if info.get('delimiter', None) is not None:
        np_kws['delimiter'] = info['delimiter']
    if info.get('comment', None) is not None:
        np_kws['comments'] = info['comment']
    np_kws = tools.bytes2str(np_kws, recurse=True)
    if use_astropy:
        if 'comments' in np_kws:
            np_kws['comment'] = np_kws.pop('comments')
        tab = apy_ascii.read(fd, names=names, guess=True,
                             encoding=encoding,
                             format='no_header', **np_kws)
        arr = tab.as_array()
        typs = [arr.dtype[i].str for i in range(len(arr.dtype))]
        cols = [c for c in tab.columns]
        # Convert type bytes if python 3
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
        np_ver = tuple([float(x) for x in (np.__version__).split('.')])
        np_kws.update(autostrip=True, dtype=None, names=names)
        if (np_ver >= (1.0, 14.0, 0.0)):
            np_kws['encoding'] = 'bytes'
        arr = np.genfromtxt(fd, **np_kws)
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
            out = b''
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
        raise RuntimeError("Data length (%d) is not a multiple " % len(data)
                           + "of the itemsize (%d)." % dtype.itemsize)
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
                arr_real = np.frombuffer(idata_real, dtype='float64')
                arr_imag = np.frombuffer(idata_imag, dtype='float64')
                # arr_real = np.fromstring(idata_real, dtype='float64')
                # arr_imag = np.fromstring(idata_imag, dtype='float64')
                arr[dtype.names[i]] = np.zeros(nele, dtype=dtype[i])
                arr[dtype.names[i]] += arr_real
                arr[dtype.names[i]] += arr_imag * 1j
            else:
                arr[dtype.names[i]] = np.frombuffer(idata, dtype=dtype[i])
                # arr[dtype.names[i]] = np.fromstring(idata, dtype=dtype[i])
            prev += len(idata)
            j += 1
    else:
        arr = np.frombuffer(data, dtype=dtype)
        # arr = np.fromstring(data, dtype=dtype)
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
            field_names = [n.encode("utf-8") for n in dtype.names]
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
        if (x is not None) and (len(max(x, key=len)) > 0):
            assert(len(x) == nfld)
            x_bytes = tools.str2bytes(x, recurse=True)
            out.append(comment + delimiter.join(x_bytes))
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
        sline = line.replace(platform._newline, newline)
        if not sline.startswith(comment):
            break
        header_size += len(line)
        header_lines.append(sline)
    # Parse header & set serializer attributes
    header = parse_header(header_lines, newline=newline,
                          lineno_format=lineno_format,
                          lineno_names=lineno_names,
                          lineno_units=lineno_units)
    # Override header with information set explicitly in serializer
    for k in serializer._oldstyle_kws:
        v = getattr(serializer, k, None)
        if v is not None:
            header[k] = v
    header.setdefault('format_str', None)
    if (delimiter is None) or ('format_str' in header):
        delimiter = header['delimiter']
    # Try to determine format from array without header
    str_fmt = b'%s'
    if ((header['format_str'] is None) or (str_fmt in header['format_str'])):
        fd.seek(prev_pos + header_size)
        all_contents = fd.read()
        if len(all_contents) == 0:  # pragma: debug
            return  # In case the file has not been written
        arr = table_to_array(all_contents,
                             names=header.get('field_names', None),
                             comment=comment,
                             delimiter=delimiter,
                             use_astropy=use_astropy)
        header['field_names'] = arr.dtype.names
        # Get format from array
        if header['format_str'] is None:
            header['format_str'] = table2format(
                arr.dtype, delimiter=delimiter,
                comment=b'',
                newline=header['newline'])
        # Determine maximum size of string field
        while str_fmt in header['format_str']:
            field_formats = extract_formats(header['format_str'])
            ifld = tools.bytes2str(
                header['field_names'][field_formats.index(str_fmt)])
            max_len = len(max(arr[ifld], key=len))
            new_str_fmt = b'%%%ds' % max_len
            header['format_str'] = header['format_str'].replace(
                str_fmt, new_str_fmt, 1)
    # Update serializer
    serializer.initialize_serializer(header)
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
    if isinstance(header, bytes):
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


def dict2list(d, order=None):
    r"""Covert a dictionary of arrays to a list of arrays.

    Args:
        d (dict): Dictionary of arrays.
        order (list, optional): Key order in which values from the dictionary
            should be add to the list.

    Returns:
        list: List with contents from the input array.

    """
    if not isinstance(d, dict):
        raise TypeError("d must be a dictionary, not %s." % type(d))
    if order is None:
        order = sorted(list(d.keys()))
    out = [d[k] for k in order]
    return out


def list2dict(l, names=None):
    r"""Convert a list of arrays to a dictionary of arrays.

    Args:
        l (list): List of arrays.
        names (list, optional): Names to give to the new fields. Defaults to
            names based on order (e.g. 'f0', 'f1').

    Returns:
        dict: Dictionary of arrays.

    """
    if not isinstance(l, (list, tuple)):
        raise TypeError("l must be a list or tuple, not %s." % type(l))
    if names is None:
        names = ['f%d' % i for i in range(len(l))]
    out = {k: x for k, x in zip(names, l)}
    return out


def numpy2list(arr):
    r"""Covert a numpy structured array to a list of arrays.

    Args:
        arr (np.ndarray): Array to convert.

    Returns:
        list: List with contents from the input array.

    """
    if not isinstance(arr, np.ndarray):
        raise TypeError("arr must be a numpy array, not %s." % type(arr))
    return dict2list(numpy2dict(arr), order=arr.dtype.names)


def list2numpy(l, names=None):
    r"""Convert a list of arrays to a numpy structured array.

    Args:
        l (list): List of arrays.
        names (list, optional): Names to give to the new fields. Defaults to
            names based on order.

    Returns:
        np.ndarray: Structured numpy array.

    """
    return dict2numpy(list2dict(l, names=names), order=names)


def numpy2dict(arr):
    r"""Covert a numpy structured array to a dictionary of arrays.

    Args:
        arr (np.ndarray): Array to convert.

    Returns:
        dict: Dictionary with contents from the input array.

    """
    if not isinstance(arr, np.ndarray):
        raise TypeError("arr must be a numpy array, not %s." % type(arr))
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
    if not isinstance(d, dict):
        raise TypeError("d must be a dictionary, not %s." % type(d))
    if len(d) == 0:
        return np.array([])
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
    if not isinstance(arr, np.ndarray):
        raise TypeError("arr must be a numpy array, not %s." % type(arr))
    out = pandas.DataFrame(arr)
    return out


def pandas2numpy(frame, index=False):
    r"""Convert a Pandas DataFrame to a numpy structured array.

    Args:
        frame (pandas.DataFrame): Frame to convert.
        index (bool, optional): If True, the index will be included as a field
            in the array. Defaults to False.

    Returns:
        np.ndarray: Structured numpy array.

    """
    if not isinstance(frame, pandas.DataFrame):
        raise TypeError("frame must be a pandas data frame, not %s." % type(frame))
    arr = frame.to_records(index=index)
    # Covert object type to string
    old_dtype = arr.dtype
    new_dtype = dict(names=old_dtype.names, formats=[])
    for i in range(len(old_dtype)):
        if (old_dtype[i] == object) and (len(arr[old_dtype.names[i]]) > 0):
            if isinstance(arr[old_dtype.names[i]][0], bytes):
                char_str = 'S'
            else:
                char_str = 'U'
            try:
                max_len = len(max(arr[old_dtype.names[i]], key=len))
                new_dtype['formats'].append(np.dtype("%s%s" % (char_str, max_len)))
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
    r"""Convert a dictionary of arrays to a Pandas DataFrame.

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
    if not isinstance(frame, pandas.DataFrame):
        raise TypeError("frame must be a pandas data frame, not %s." % type(frame))
    return numpy2dict(pandas2numpy(frame))


def list2pandas(l, names=None):
    r"""Convert a list of arrays to a Pandas DataFrame.

    Args:
        l (list): List of arrays.
        names (list, optional): Names to give to the new fields. Defaults to
            names based on order (e.g. 'f0', 'f1').

    Returns:
        pandas.DataFrame: Pandas data frame with contents from the input list.

    """
    out = numpy2pandas(list2numpy(l, names=names))
    if names is None:
        out.columns = pandas.RangeIndex(len(l))
    return out


def pandas2list(frame):
    r"""Convert a Pandas DataFrame to a list of arrays.

    Args:
        frame (pandas.DataFrame): Frame to convert.

    Returns:
        list: List with contents from the input frame.

    """
    return numpy2list(pandas2numpy(frame))


__all__ = []
