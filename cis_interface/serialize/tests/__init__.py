import numpy as np
import nose.tools as nt
from cis_interface import serialize, backwards, platform


unsupported_nptype = ['bool_']
map_nptype2cformat = [
    (['float_', 'float16', 'float32', 'float64'], '%g'),
    (['complex_', 'complex64', 'complex128'], '%g%+gj'),
    # (['int8', 'short', 'intc', 'int_', 'longlong'], '%d'),
    # (['uint8', 'ushort', 'uintc', 'uint64', 'ulonglong'], '%u'),
    ('int8', '%hhd'), ('short', '%hd'), ('intc', '%d'),
    ('uint8', '%hhu'), ('ushort', '%hu'), ('uintc', '%u'),
    ('S', '%s'), ('S5', '%5s'), ('U', '%s'), ('U5', '%20s')]
if platform._is_win:  # pragma: windows
    map_nptype2cformat.append(('int64', '%l64d'))
    map_nptype2cformat.append(('uint64', '%l64u'))
else:
    map_nptype2cformat.append(('int64', '%ld'))
    map_nptype2cformat.append(('uint64', '%lu'))
# Conditional on if default int 32bit or 64bit
# This is for when default int is 32bit
if np.dtype('int_') != np.dtype('intc'):
    map_nptype2cformat.append(('int_', '%ld'))
else:
    map_nptype2cformat.append(('int_', '%d'))  # pragma: windows
if np.dtype('int_') != np.dtype('longlong'):
    if platform._is_win:  # pragma: windows
        map_nptype2cformat.append(('longlong', '%l64d'))
        map_nptype2cformat.append(('ulonglong', '%l64u'))
    else:  # pragma: debug
        map_nptype2cformat.append(('longlong', '%lld'))
        map_nptype2cformat.append(('ulonglong', '%llu'))
map_cformat2pyscanf = [(['%5s', '%s'], '%s'),
                       ('%s', '%s'),
                       # (['%hhd', '%hd', '%d', '%ld', '%lld', '%l64d'], '%d'),
                       # (['%hhu', '%hu', '%u', '%lu', '%llu', '%l64u'], '%u'),
                       ('%g%+gj', '%g%+gj')]

unsupported_cfmt = ['a', 'A', 'p', 'n', '']
map_cformat2nptype = [(['f', 'F', 'e', 'E', 'g', 'G'], 'float64'),
                      # (['f', 'F', 'e', 'E', 'g', 'G'], 'float32'),
                      # (['lf', 'lF', 'le', 'lE', 'lg', 'lG'], 'float64'),
                      (['hhd', 'hhi'], 'int8'),
                      (['hd', 'hi'], 'short'),
                      (['d', 'i'], 'intc'),
                      (['ld', 'li'], 'int_'),
                      (['lld', 'lli', 'l64d'], 'longlong'),
                      (['hhu', 'hho', 'hhx', 'hhX'], 'uint8'),
                      (['hu', 'ho', 'hx', 'hX'], 'ushort'),
                      (['u', 'o', 'x', 'X'], 'uintc'),
                      (['lu', 'lo', 'lx', 'lX'], 'uint64'),
                      (['llu', 'llo', 'llx', 'llX', 'l64u'], 'ulonglong'),
                      (['c', 's'], backwards.np_dtype_str),
                      ('s', backwards.np_dtype_str)]
# if np.dtype('int_') != np.dtype('intc'):
#     map_cformat2nptype.append((['ld', 'li'], 'int_'))
map_cformat2nptype.append(
    (['%{}%+{}j'.format(_, _) for _ in ['f', 'F', 'e', 'E', 'g', 'G']],
     'complex128'))


def test_guess_serializer():
    r"""Test guess_serializer."""
    nele = 5
    names = ["name", "number", "value", "complex"]
    field_names = [backwards.unicode2bytes(n) for n in names]
    dtypes = ['S5', 'i8', 'f8', 'c16']
    dtype = np.dtype([(n, f) for n, f in zip(names, dtypes)])
    arr_mix = np.zeros(nele, dtype)
    arr_mix['name'][0] = 'hello'
    fmt_arr = serialize._default_delimiter.join(
        serialize.nptype2cformat(arr_mix.dtype, asbytes=True))
    fmt_arr += serialize._default_newline
    if platform._is_win:  # pragma: windows
        x = arr_mix[0].tolist()
        for i in x:
            print(type(i))
        if backwards.PY2:  # pragma: Python 2
            # tolist maps to long on python 2, but int on python 3?!
            fmt = backwards.unicode2bytes('%s\t%l64d\t%g\t%g%+gj\n')
        else:  # pragma: Python 3
            fmt = backwards.unicode2bytes('%s\t%d\t%g\t%g%+gj\n')
    else:
        fmt = backwards.unicode2bytes('%s\t%ld\t%g\t%g%+gj\n')
    test_list = [(arr_mix, dict(field_names=field_names, format_str=fmt_arr,
                                stype=2, as_array=1)),
                 (arr_mix[0].tolist(), dict(format_str=fmt, stype=1)),
                 ('hello', dict(stype=0))]
    for obj, sinfo_ans in test_list:
        sinfo_res = serialize.guess_serializer(obj)
        s = serialize.get_serializer(**sinfo_res)
        nt.assert_equal(s.serializer_info, sinfo_ans)


def test_get_serializer():
    r"""Test get_serializer."""
    max_code = 9
    for x in range(max_code + 1):
        serialize.get_serializer(stype=x, format_str='%s\n')
    nt.assert_raises(RuntimeError, serialize.get_serializer, stype=max_code + 1)


def test_extract_formats():
    r"""Test extract_formats."""
    test_str = ['%10s\t%5.2f\t%4d\t%g%+gj']
    test_fmt = [['%10s', '%5.2f', '%4d', '%g%+gj']]
    for s, f in zip(test_str, test_fmt):
        nt.assert_equal(serialize.extract_formats(s), f)
        nt.assert_equal(serialize.extract_formats(backwards.unicode2bytes(s)),
                        [backwards.unicode2bytes(i) for i in f])


def test_nptype2cformat():
    r"""Test conversion from numpy dtype to C format string."""
    for a, b in map_nptype2cformat:
        if isinstance(a, str):
            a = [a]
        for ia in a:
            nt.assert_equal(serialize.nptype2cformat(ia), b)
    nt.assert_raises(TypeError, serialize.nptype2cformat, 0)
    for a in unsupported_nptype:
        nt.assert_raises(ValueError, serialize.nptype2cformat, a)


def test_nptype2cformat_structured():
    r"""Test conversion from structured numpy dtype to C format string."""
    if platform._is_win:  # pragma: windows
        fmts = ["%5s", "%l64d", "%g", "%g%+gj"]
    else:
        fmts = ["%5s", "%ld", "%g", "%g%+gj"]
    names0 = ['f0', 'f1', 'f2', 'f3']
    names1 = ["name", "number", "value", "complex"]
    dtypes = ['S5', 'i8', 'f8', 'c16']
    dtype0 = np.dtype([(n, f) for n, f in zip(names0, dtypes)])
    dtype1 = np.dtype([(n, f) for n, f in zip(names1, dtypes)])
    alist = [dtype0, dtype1]
    blist = [fmts, fmts]
    for a, b in zip(alist, blist):
        nt.assert_equal(serialize.nptype2cformat(a), b)
        nt.assert_equal(serialize.nptype2cformat(a, asbytes=True),
                        [backwards.unicode2bytes(ib) for ib in b])


def test_cformat2nptype():
    r"""Test conversion from C format string to numpy dtype."""
    for a, b in map_cformat2nptype:
        if isinstance(a, str):
            a = [a]
        for _ia in a:
            if _ia.startswith(backwards.bytes2unicode(serialize._fmt_char)):
                ia = backwards.unicode2bytes(_ia)
            else:
                ia = serialize._fmt_char + backwards.unicode2bytes(_ia)
            nt.assert_equal(serialize.cformat2nptype(ia), np.dtype(b))  # .str)
            # nt.assert_equal(serialize.cformat2nptype(ia), np.dtype(b).str)
    nt.assert_raises(TypeError, serialize.cformat2nptype, 0)
    nt.assert_raises(ValueError, serialize.cformat2nptype,
                     backwards.unicode2bytes('s'))
    nt.assert_raises(ValueError, serialize.cformat2nptype,
                     backwards.unicode2bytes('%'))
    nt.assert_raises(ValueError, serialize.cformat2nptype,
                     '%d\t%f', names=['one'])
    for a in unsupported_nptype:
        nt.assert_raises(ValueError, serialize.cformat2nptype,
                         backwards.unicode2bytes('%' + a))


def test_cformat2nptype_structured():
    r"""Test conversion from C format string to numpy dtype for structured
    data types."""
    if platform._is_win:  # pragma: debug
        fmts = ["%5s", "%l64d", "%lf", "%g%+gj"]
    else:
        fmts = ["%5s", "%ld", "%lf", "%g%+gj"]
    names0 = ['f0', 'f1', 'f2', 'f3']
    names1 = ["name", "number", "value", "complex"]
    dtypes = ['S5', 'i8', 'f8', 'c16']
    dtype0 = np.dtype([(n, f) for n, f in zip(names0, dtypes)])
    dtype1 = np.dtype([(n, f) for n, f in zip(names1, dtypes)])
    alist = ["\t".join(fmts) + "\n", ''.join(fmts), fmts]
    for a in alist:
        b0 = serialize.cformat2nptype(a)
        nt.assert_equal(b0, dtype0)
        b1 = serialize.cformat2nptype(a, names=names1)
        nt.assert_equal(b1, dtype1)


def test_cformat2pyscanf():
    r"""Test conversion of C format string to version for python scanf."""
    all_a = []
    all_b = []
    for a, b in map_cformat2pyscanf:
        if isinstance(a, str):
            a = [a]
        for _ia in a:
            ia = backwards.unicode2bytes(_ia)
            ib = backwards.unicode2bytes(b)
            all_a.append(ia)
            all_b.append(ib)
            nt.assert_equal(serialize.cformat2pyscanf(ia), ib)
    nt.assert_raises(TypeError, serialize.cformat2pyscanf, 0)
    nt.assert_raises(ValueError, serialize.cformat2pyscanf,
                     backwards.unicode2bytes('s'))
    nt.assert_raises(ValueError, serialize.cformat2pyscanf,
                     backwards.unicode2bytes('%'))
    fmt_a = backwards.unicode2bytes('\t').join(all_a)
    fmt_b = backwards.unicode2bytes('\t').join(all_b)
    nt.assert_equal(serialize.cformat2pyscanf(all_a), all_b)
    nt.assert_equal(serialize.cformat2pyscanf(fmt_a), fmt_b)


def test_format_message():
    r"""Test formatting message from a list or arguments and back."""
    fmt = backwards.unicode2bytes("%5s\t%ld\t%lf\t%g%+gj\n")
    dtype = serialize.cformat2nptype(fmt)
    x_arr = np.ones(1, dtype)
    x_tup = [x_arr[n][0] for n in x_arr.dtype.names]
    # x_tup[0] = backwards.bytes2unicode(x_tup[0])
    flist = [fmt, "%ld"]
    alist = [tuple(x_tup), 0]
    for a, f in zip(alist, flist):
        msg = serialize.format_message(a, f)
        b = serialize.process_message(msg, f)
        if not isinstance(a, tuple):
            nt.assert_equal(b, (a, ))
        else:
            nt.assert_equal(b, a)
    # Errors
    nt.assert_raises(RuntimeError, serialize.format_message, (0, ), "%d %d")
    nt.assert_raises(TypeError, serialize.process_message, 0, "%d")
    nt.assert_raises(ValueError, serialize.process_message,
                     backwards.unicode2bytes("hello"), "%d")


def test_combine_flds():
    r"""Test combine_flds."""
    names0 = ['f0', 'f1', 'f2', 'f3']
    names1 = ["name", "number", "value", "complex"]
    dtypes = ['S5', 'i8', 'f8', 'c16']
    dtype0 = np.dtype([(n, f) for n, f in zip(names0, dtypes)])
    dtype1 = np.dtype([(n, f) for n, f in zip(names1, dtypes)])
    nfld = len(names0)
    nele = 5
    arrs = [np.zeros(nele, dtype=dtype0[i]) for i in range(nfld)]
    np.testing.assert_array_equal(serialize.combine_flds(arrs),
                                  np.zeros(nele, dtype0))
    np.testing.assert_array_equal(serialize.combine_flds(arrs, dtype=dtype1),
                                  np.zeros(nele, dtype1))
    nt.assert_raises(ValueError, serialize.combine_flds, arrs[:-1], dtype=dtype0)
    arrs[0] = np.zeros(nele - 1, dtype=dtype0[0])
    nt.assert_raises(ValueError, serialize.combine_flds, arrs)


def test_combine_eles():
    r"""Test combine_eles."""
    names0 = ['f0', 'f1', 'f2', 'f3']
    names1 = ["name", "number", "value", "complex"]
    dtypes = ['S5', 'i8', 'f8', 'c16']
    dtype0 = np.dtype([(n, f) for n, f in zip(names0, dtypes)])
    dtype1 = np.dtype([(n, f) for n, f in zip(names1, dtypes)])
    dtype_short = np.dtype([(n, f) for n, f in zip(names1[:-1], dtypes[:-1])])
    # nfld = len(names0)
    nele = 5
    res0 = np.zeros(nele, dtype0)
    res1 = np.zeros(nele, dtype1)
    res0['f0'][0] = 'hello'
    res1['name'][0] = 'hello'
    arrs = [np.zeros(1, dtype=dtype0) for i in range(nele)]
    arrs[0]['f0'] = backwards.unicode2bytes('hello')
    arrs_list = [a.tolist()[0] for a in arrs]
    arrs_void = [res1[i] for i in range(nele)]
    arrs_mixd = [a.tolist() for a in res1]
    arrs_mixd[-1] = arrs_void[-1]
    if platform._is_win:  # pragma: windows
        if backwards.PY2:  # pragma: Python 2
            res0_list = res0
            res1_list = res1
        else:  # pragma: Python 3
            dtype0_w = np.dtype({'names': names0, 'formats': ['S5', 'i4', 'f8', 'c16']})
            dtype1_w = np.dtype({'names': names1, 'formats': ['S5', 'i4', 'f8', 'c16']})
            res0_list = res0.astype(dtype0_w)
            res1_list = res1.astype(dtype1_w)
    else:
        res0_list = res0
        res1_list = res1
    np.testing.assert_array_equal(serialize.combine_eles(arrs), res0)
    np.testing.assert_array_equal(serialize.combine_eles(arrs_list), res0_list)
    np.testing.assert_array_equal(serialize.combine_eles(arrs_void), res1)
    np.testing.assert_array_equal(serialize.combine_eles(arrs_mixd), res1_list)
    np.testing.assert_array_equal(serialize.combine_eles(arrs, dtype=dtype1),
                                  res1)
    np.testing.assert_array_equal(serialize.combine_eles(arrs_list, dtype=dtype1),
                                  res1)
    arrs_list[0] = arrs_list[0][:-1]
    nt.assert_raises(ValueError, serialize.combine_eles, arrs_list, dtype=dtype1)
    nt.assert_raises(ValueError, serialize.combine_eles, arrs_list)
    arrs_list[0] = None
    nt.assert_raises(TypeError, serialize.combine_eles, arrs_list)
    nt.assert_raises(ValueError, serialize.combine_eles, arrs_void,
                     dtype=dtype_short)


def test_consolidate_array():
    r"""Test consolidation of array information in different forms."""
    names0 = ['f0', 'f1', 'f2', 'f3']
    # names1 = ["name", "number", "value", "complex"]
    dtypes = ['S5', 'i8', 'f8', 'c16']
    dtype0 = np.dtype([(n, f) for n, f in zip(names0, dtypes)])
    if platform._is_win:  # pragma: windows
        if backwards.PY2:  # pragma: Python 2
            dtype0_list = dtype0
        else:  # pragma: Python 3
            dtype0_list = np.dtype({'names': names0,
                                    'formats': ['S5', 'i4', 'f8', 'c16']})
    else:
        dtype0_list = dtype0
    # dtype1 = np.dtype([(n, f) for n, f in zip(names1, dtypes)])
    dtype2 = np.dtype([('f0', 'i8'), ('f1', 'f8')])
    dtype3 = np.dtype([('f0', 'i4'), ('f1', 'f4')])
    shape = (5, 5)
    # Create list of input variables
    dlist = []
    x0list = []
    x1list = []
    for dtype in [np.dtype('float'), dtype0]:
        x = np.zeros(shape, dtype=dtype)
        if dtype == dtype0:
            x['f0'][:] = 'hello'
        x_flat = x.flatten()
        dlist.append(dtype)
        x0list.append(x)
        x1list.append(x)
        if len(dtype) > 0:
            dlist += [dtype, dtype]
            if dtype == dtype0:
                dtype_list = dtype0_list
            else:  # pragma: debug
                dtype_list = dtype
            dlist.append(dtype_list)
            x0list += [x, x_flat, x_flat.astype(dtype_list)]
            # Tests with lists of arrays rows or columns
            x1list.append([x[n] for n in dtype.names])
            x1list.append([x_flat[i] for i in range(len(x_flat))])
            x1list.append([x_flat[i].tolist() for i in range(len(x_flat))])
    # Tests with single array mapped onto structured array
    nrow = 4
    x0 = np.zeros(nrow, dtype2)
    x1 = np.zeros((nrow, len(dtype2)))
    dlist += [None]
    x0list += [x0]
    x1list.append(x0)
    x2 = serialize.consolidate_array(x1, dtype=dtype2)
    np.testing.assert_array_equal(x0, x2)
    np.testing.assert_array_equal(x0, serialize.consolidate_array(
        np.zeros(nrow, dtype3), dtype=dtype2))
    # Test with list of arrays
    arr_void = np.ones(5, dtype0)
    x0list.append(arr_void)
    x1list.append([a for a in arr_void])
    dlist.append(dtype0)
    # Loop over different test inputs
    i = 0
    for x0, x1, dtype in zip(x0list, x1list, dlist):
        i += 1
        # Dtype provided
        x2 = serialize.consolidate_array(x1, dtype=dtype)
        np.testing.assert_array_equal(x0, x2)
        # Dtype not provided
        x2 = serialize.consolidate_array(x1)
        np.testing.assert_array_equal(x0, x2)
    # Error on incorrect data format
    nt.assert_raises(ValueError, serialize.consolidate_array,
                     np.zeros((4, 1)), dtype=dtype2)
    # Error on incorrect type
    nt.assert_raises(TypeError, serialize.consolidate_array, None)
    # Error on dtypes with differing numbers of fields
    nt.assert_raises(ValueError, serialize.consolidate_array,
                     np.zeros(3, dtype0), dtype=dtype3)
                     

def test_format2table():
    r"""Test getting table information from a format string."""
    out = {'delimiter': backwards.unicode2bytes('\t'),
           'newline': backwards.unicode2bytes('\n'),
           'comment': backwards.unicode2bytes('# '),
           'fmts': ["%5s", "%ld", "%lf", "%g%+gj"]}
    out['fmts'] = [backwards.unicode2bytes(f) for f in out['fmts']]
    sfmt = out['fmts'][0]
    sout = dict(**out)
    sout['fmts'] = [sfmt]
    del sout['newline'], sout['comment']
    fmt = backwards.unicode2bytes("# %5s\t%ld\t%lf\t%g%+gj\n")
    nt.assert_equal(dict(fmts=[]), serialize.format2table('hello'))
    nt.assert_equal(sout, serialize.format2table(sfmt))
    nt.assert_equal(fmt, serialize.table2format(**out))
    nt.assert_equal(out, serialize.format2table(fmt))
    nt.assert_equal(fmt, serialize.table2format(fmts=out['fmts']))
    nt.assert_raises(RuntimeError, serialize.format2table, "%5s,%ld\t%g\n")


def test_array_to_table():
    r"""Test conversion of arrays to ASCII table and back."""
    flist = [backwards.unicode2bytes("%5s\t%ld\t%lf\t%g%+gj\n")]
    for use_astropy in [False, True]:
        for f in flist:
            dtype = serialize.cformat2nptype(f)
            arr0 = np.ones(5, dtype)
            arr0['f0'][0] = backwards.unicode2bytes('hello')
            tab = serialize.array_to_table(arr0, f, use_astropy=use_astropy)
            arr1 = serialize.table_to_array(tab, f, use_astropy=use_astropy)
            np.testing.assert_array_equal(arr1, arr0)


def test_array_to_bytes():
    r"""Test conversion of arrays to bytes and back."""
    names0 = ['f0', 'f1', 'f2', 'f3']
    # names1 = ["name", "number", "value", "complex"]
    dtypes = ['S5', 'i8', 'f8', 'c16']
    dtype0 = np.dtype([(n, f) for n, f in zip(names0, dtypes)])
    # dtype1 = np.dtype([(n, f) for n, f in zip(names1, dtypes)])
    shape = (5, 5)
    for order in ['C', 'F']:
        for dtype in [np.dtype('float'), dtype0]:
            x0 = np.zeros(shape, dtype=dtype)
            if dtype == dtype0:
                x0['f0'][:] = 'hello'
            # An array of the same type, dtype provided
            b = serialize.array_to_bytes(x0, dtype=dtype, order=order)
            x1 = serialize.bytes_to_array(b, dtype, order=order, shape=shape)
            np.testing.assert_array_equal(x1, x0)
            # An array of the same type, dtype not provided
            b = serialize.array_to_bytes(x0, order=order)
            x1 = serialize.bytes_to_array(b, dtype, order=order, shape=shape)
            np.testing.assert_array_equal(x1, x0)
        # Tests with single array mapped onto structured array
        dtype2 = np.dtype([('f0', 'i8'), ('f1', 'f8')])
        nrow = 4
        ncol = len(dtype2)
        b0 = serialize.array_to_bytes(np.zeros(nrow, dtype2), order=order)
        b1 = serialize.array_to_bytes(np.zeros((nrow, ncol)), dtype=dtype2,
                                      order=order)
        nt.assert_equal(b1, b0)
        # Error on incomplete serial array
        nt.assert_raises(RuntimeError, serialize.bytes_to_array,
                         b0[:-1], dtype2, order=order)


def test_format_header():
    r"""Test formatting header."""
    kws_all = dict(
        field_names=['name', 'number', 'value', 'complex'],
        field_units=['n/a', 'g', 'cm', 'n/a'])
    res_all = dict(
        names="# name\tnumber\tvalue\tcomplex\n",
        units="# n/a\tg\tcm\tn/a\n")
    if platform._is_win:  # pragma: windows
        kws_all['format_str'] = "%5s\t%l64d\t%g\t%g%+gj\n"
        res_all['format'] = "# " + kws_all['format_str']
    else:
        kws_all['format_str'] = "%5s\t%ld\t%g\t%g%+gj\n"
        res_all['format'] = "# " + kws_all['format_str']
    kws_all['dtype'] = serialize.cformat2nptype(kws_all['format_str'],
                                                names=kws_all['field_names'])
    for x in [kws_all, res_all]:
        for k, v in x.items():
            if isinstance(v, str):
                x[k] = backwards.unicode2bytes(v)
            elif isinstance(v, list):
                x[k] = [backwards.unicode2bytes(iv) for iv in v]
    test_list = [(['format_str', 'field_names', 'field_units'],
                  ['names', 'units', 'format']),
                 (['field_names', 'field_units', 'dtype'],
                  ['names', 'units', 'format']),
                 (['field_units', 'dtype'],
                  ['names', 'units', 'format']),
                 (['field_names'], ['names']),
                 (['field_units'], ['units'])]
    for kws_keys, res_keys in test_list:
        kws = {k: kws_all[k] for k in kws_keys}
        res = backwards.unicode2bytes('').join([res_all[k] for k in res_keys])
        nt.assert_equal(serialize.format_header(**kws), res)
    nt.assert_raises(ValueError, serialize.format_header)


def test_parse_header():
    r"""Test parsing header."""
    header = ["# name\tnumber\tvalue\tcomplex\n",
              "# n/a\tg\tcm\tn/a\n",
              "# %5s\t%ld\t%lf\t%g%+gj\n"]
    res = dict(delimiter='\t', comment='# ', newline='\n',
               format_str="%5s\t%ld\t%lf\t%g%+gj\n",
               fmts=['%5s', '%ld', '%lf', '%g%+gj'],
               field_names=['name', 'number', 'value', 'complex'],
               field_units=['n/a', 'g', 'cm', 'n/a'])
    for i in range(len(header)):
        header[i] = backwards.unicode2bytes(header[i])
    for k, v in res.items():
        if isinstance(v, str):
            res[k] = backwards.unicode2bytes(v)
        elif isinstance(v, list):
            res[k] = [backwards.unicode2bytes(s) for s in v]
    nt.assert_equal(serialize.parse_header(header), res)
    nt.assert_equal(serialize.parse_header(header[::-1]), res)
    _empty = backwards.unicode2bytes('')
    nt.assert_equal(serialize.parse_header(_empty.join(header)), res)
    # Test without formats
    header2 = header[:2]
    res2 = dict(**res)
    del res2['format_str']
    res2['fmts'] = []
    nt.assert_equal(serialize.parse_header(header2), res2)
    # Test with explicit line numbers
    nt.assert_equal(serialize.parse_header(header, lineno_names=0, lineno_units=1),
                    res)
    # Test errors
    header3 = [header[0], header[0]]
    nt.assert_raises(RuntimeError, serialize.parse_header, header3)
    header4 = [header[1], header[1]]
    nt.assert_raises(RuntimeError, serialize.parse_header, header4)


def test_numpy2pandas():
    r"""Test conversion of a numpy array to a pandas data frame and back."""
    nele = 5
    names = ["name", "number", "value", "complex"]
    dtypes = ['S5', 'i8', 'f8', 'c16']
    dtype = np.dtype([(n, f) for n, f in zip(names, dtypes)])
    arr_mix = np.zeros(nele, dtype)
    arr_mix['name'][0] = 'hello'
    arr_obj = np.array([list(), 'hello', 5], dtype='O')
    test_arrs = [arr_mix,
                 np.zeros(nele, 'float'),
                 arr_mix['name'],
                 arr_obj]
    for ans in test_arrs:
        frame = serialize.numpy2pandas(ans)
        res = serialize.pandas2numpy(frame)
        np.testing.assert_array_equal(ans, res)


def test_numpy2dict():
    r"""Test conversion of a numpy array to a dictionary and back."""
    nele = 5
    names = ["complex", "name", "number", "value"]
    dtypes = ['c16', 'S5', 'i8', 'f8']
    dtype = np.dtype([(n, f) for n, f in zip(names, dtypes)])
    arr_mix = np.zeros(nele, dtype)
    arr_mix['name'][0] = 'hello'
    test_arrs = [arr_mix]
    for ans in test_arrs:
        d = serialize.numpy2dict(ans)
        # Sorted
        res = serialize.dict2numpy(d)
        np.testing.assert_array_equal(ans, res)
        # Provided
        res = serialize.dict2numpy(d, order=names)
        np.testing.assert_array_equal(ans, res)


def test_pandas2dict():
    r"""Test conversion of a Pandas data frame to a dictionary and back."""
    nele = 5
    names = ["complex", "name", "number", "value"]
    dtypes = ['c16', 'S5', 'i8', 'f8']
    dtype = np.dtype([(n, f) for n, f in zip(names, dtypes)])
    arr_mix = np.zeros(nele, dtype)
    arr_mix['name'][0] = 'hello'
    arr_obj = np.array([list(), 'hello', 5], dtype='O')
    test_arrs = [arr_mix,
                 np.zeros(nele, 'float'),
                 arr_mix['name'],
                 arr_obj]
    for ans in test_arrs:
        frame = serialize.numpy2pandas(ans)
        # Sorted
        d = serialize.pandas2dict(frame)
        res = serialize.dict2pandas(d)
        np.testing.assert_array_equal(res, frame)
        # Provided
        d = serialize.pandas2dict(frame)
        res = serialize.dict2pandas(d, order=ans.dtype.names)
        np.testing.assert_array_equal(res, frame)


__all__ = []
