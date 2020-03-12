import numpy as np
from yggdrasil import serialize, platform
from yggdrasil.tests import assert_raises, assert_equal


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
                      (['c', 's'], 'S'),
                      ('s', 'S')]
# if np.dtype('int_') != np.dtype('intc'):
#     map_cformat2nptype.append((['ld', 'li'], 'int_'))
map_cformat2nptype.append(
    (['%{}%+{}j'.format(_, _) for _ in ['f', 'F', 'e', 'E', 'g', 'G']],
     'complex128'))


def test_extract_formats():
    r"""Test extract_formats."""
    test_str = ['%10s\t%5.2f\t%4d\t%g%+gj']
    test_fmt = [['%10s', '%5.2f', '%4d', '%g%+gj']]
    for s, f in zip(test_str, test_fmt):
        assert_equal(serialize.extract_formats(s), f)
        assert_equal(serialize.extract_formats(s.encode("utf-8")),
                     [i.encode("utf-8") for i in f])


def test_nptype2cformat():
    r"""Test conversion from numpy dtype to C format string."""
    for a, b in map_nptype2cformat:
        if isinstance(a, str):
            a = [a]
        for ia in a:
            assert_equal(serialize.nptype2cformat(ia), b)
    assert_raises(TypeError, serialize.nptype2cformat, 0)
    for a in unsupported_nptype:
        assert_raises(ValueError, serialize.nptype2cformat, a)


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
        assert_equal(serialize.nptype2cformat(a), b)
        assert_equal(serialize.nptype2cformat(a, asbytes=True),
                     [ib.encode("utf-8") for ib in b])


def test_cformat2nptype():
    r"""Test conversion from C format string to numpy dtype."""
    for a, b in map_cformat2nptype:
        if isinstance(a, str):
            a = [a]
        for _ia in a:
            if _ia.startswith(serialize._fmt_char_str):
                ia = _ia.encode("utf-8")
            else:
                ia = serialize._fmt_char + _ia.encode("utf-8")
            assert_equal(serialize.cformat2nptype(ia), np.dtype(b))  # .str)
            # assert_equal(serialize.cformat2nptype(ia), np.dtype(b).str)
    assert_raises(TypeError, serialize.cformat2nptype, 0)
    assert_raises(ValueError, serialize.cformat2nptype, b's')
    assert_raises(ValueError, serialize.cformat2nptype, b'%')
    assert_raises(ValueError, serialize.cformat2nptype,
                  '%d\t%f', names=['one'])
    for a in unsupported_nptype:
        assert_raises(ValueError, serialize.cformat2nptype,
                      ('%' + a).encode("utf-8"))


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
        assert_equal(b0, dtype0)
        b1 = serialize.cformat2nptype(a, names=names1)
        assert_equal(b1, dtype1)


def test_cformat2pyscanf():
    r"""Test conversion of C format string to version for python scanf."""
    all_a = []
    all_b = []
    for a, b in map_cformat2pyscanf:
        if isinstance(a, str):
            a = [a]
        for _ia in a:
            ia = _ia.encode("utf-8")
            ib = b.encode("utf-8")
            all_a.append(ia)
            all_b.append(ib)
            assert_equal(serialize.cformat2pyscanf(ia), ib)
    assert_raises(TypeError, serialize.cformat2pyscanf, 0)
    assert_raises(ValueError, serialize.cformat2pyscanf, b's')
    assert_raises(ValueError, serialize.cformat2pyscanf, b'%')
    fmt_a = b'\t'.join(all_a)
    fmt_b = b'\t'.join(all_b)
    assert_equal(serialize.cformat2pyscanf(all_a), all_b)
    assert_equal(serialize.cformat2pyscanf(fmt_a), fmt_b)


def test_format_message():
    r"""Test formatting message from a list or arguments and back."""
    fmt = b'%5s\t%ld\t%lf\t%g%+gj\n'
    dtype = serialize.cformat2nptype(fmt)
    x_arr = np.ones(1, dtype)
    x_tup = [x_arr[n][0] for n in x_arr.dtype.names]
    flist = [fmt, "%ld"]
    alist = [tuple(x_tup), 0]
    for a, f in zip(alist, flist):
        msg = serialize.format_message(a, f)
        b = serialize.process_message(msg, f)
        if not isinstance(a, tuple):
            assert_equal(b, (a, ))
        else:
            assert_equal(b, a)
    # Formats with mixed types
    assert_equal(serialize.format_message(b'hello', '%s'), 'hello')
    assert_equal(serialize.format_message('hello', b'%s'), b'hello')
    # Errors
    assert_raises(RuntimeError, serialize.format_message, (0, ), "%d %d")
    assert_raises(TypeError, serialize.process_message, 0, "%d")
    assert_raises(ValueError, serialize.process_message, b'hello', "%d")


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
    # Version of test where width of string field needs to be found
    dtype = np.dtype([("name", "S"), ("number", "i8"),
                      ("value", "f8"), ("complex", "c16")])
    arrs[0][0] = b"hello"
    result = np.zeros(nele, dtype1)
    result["name"][0] = b"hello"
    np.testing.assert_array_equal(serialize.combine_flds(arrs, dtype=dtype),
                                  result)
    # Errors
    assert_raises(ValueError, serialize.combine_flds, arrs[:-1], dtype=dtype0)
    arrs[0] = np.zeros(nele - 1, dtype=dtype0[0])
    assert_raises(ValueError, serialize.combine_flds, arrs)


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
    arrs[0]['f0'] = b'hello'
    arrs_list = [a.tolist()[0] for a in arrs]
    arrs_void = [res1[i] for i in range(nele)]
    arrs_mixd = [a.tolist() for a in res1]
    arrs_mixd[-1] = arrs_void[-1]
    if platform._is_win:  # pragma: windows
        dtype0_w = np.dtype({'names': names0, 'formats': ['S5', 'i4', 'f8', 'c16']})
        dtype1_w = np.dtype({'names': names1, 'formats': ['S5', 'i4', 'f8', 'c16']})
        res0_list = res0.astype(dtype0_w)
        res1_list = res1.astype(dtype1_w)
    else:
        res0_list = res0
        res1_list = res1
    np.testing.assert_array_equal(serialize.combine_eles([res1[n][0] for n in names1]),
                                  res0[0])
    np.testing.assert_array_equal(serialize.combine_eles(arrs), res0)
    np.testing.assert_array_equal(serialize.combine_eles(arrs_list), res0_list)
    np.testing.assert_array_equal(serialize.combine_eles(arrs_void), res1)
    np.testing.assert_array_equal(serialize.combine_eles(arrs_mixd), res1_list)
    np.testing.assert_array_equal(serialize.combine_eles(arrs, dtype=dtype1),
                                  res1)
    np.testing.assert_array_equal(serialize.combine_eles(arrs_list, dtype=dtype1),
                                  res1)
    # Version of test where width of string field needs to be found
    if platform._is_win:  # pragma: windows
        dtype = np.dtype([("f0", "S"), ("f1", "i4"),
                          ("f2", "f8"), ("f3", "c16")])
    else:
        dtype = np.dtype([("f0", "S"), ("f1", "i8"),
                          ("f2", "f8"), ("f3", "c16")])
    np.testing.assert_array_equal(serialize.combine_eles(arrs_list,
                                                         dtype=dtype),
                                  res0_list)
    # Errors
    arrs_list[0] = arrs_list[0][:-1]
    assert_raises(ValueError, serialize.combine_eles, arrs_list, dtype=dtype1)
    assert_raises(ValueError, serialize.combine_eles, arrs_list)
    arrs_list[0] = None
    assert_raises(TypeError, serialize.combine_eles, arrs_list)
    assert_raises(ValueError, serialize.combine_eles, arrs_void,
                  dtype=dtype_short)


def test_consolidate_array():
    r"""Test consolidation of array information in different forms."""
    names0 = ['f0', 'f1', 'f2', 'f3']
    # names1 = ["name", "number", "value", "complex"]
    dtypes = ['S5', 'i8', 'f8', 'c16']
    dtype0 = np.dtype([(n, f) for n, f in zip(names0, dtypes)])
    if platform._is_win:  # pragma: windows
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
    assert_raises(ValueError, serialize.consolidate_array,
                  np.zeros((4, 1)), dtype=dtype2)
    # Error on incorrect type
    assert_raises(TypeError, serialize.consolidate_array, None)
    # Error on dtypes with differing numbers of fields
    assert_raises(ValueError, serialize.consolidate_array,
                  np.zeros(3, dtype0), dtype=dtype3)
                     

def test_format2table():
    r"""Test getting table information from a format string."""
    out = {'delimiter': b'\t',
           'newline': b'\n',
           'comment': b'# ',
           'fmts': ["%5s", "%ld", "%lf", "%g%+gj"]}
    out['fmts'] = [f.encode("utf-8") for f in out['fmts']]
    sfmt = out['fmts'][0]
    sout = dict(**out)
    sout['fmts'] = [sfmt]
    del sout['newline'], sout['comment']
    fmt = b'# %5s\t%ld\t%lf\t%g%+gj\n'
    fmt2 = b'# %5s\t\t%ld\t%lf\t%g%+gj\n'
    assert_equal(dict(fmts=[]), serialize.format2table('hello'))
    assert_equal(sout, serialize.format2table(sfmt))
    assert_equal(fmt, serialize.table2format(**out))
    assert_equal(out, serialize.format2table(fmt))
    assert_equal(fmt, serialize.table2format(fmts=out['fmts']))
    assert_equal(out, serialize.format2table(fmt2))
    assert_raises(RuntimeError, serialize.format2table, "%5s,%ld\t%g\n")


def test_array_to_table():
    r"""Test conversion of arrays to ASCII table and back."""
    flist = ['# %5s\t%ld\t%lf\t%g%+gj\n']
    for use_astropy in [False, True]:
        for f in flist:
            dtype = serialize.cformat2nptype(f)
            arr0 = np.ones(5, dtype)
            arr0['f0'][0] = b'hello'
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
        assert_equal(b1, b0)
        # Error on incomplete serial array
        assert_raises(RuntimeError, serialize.bytes_to_array,
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
                x[k] = v.encode("utf-8")
            elif isinstance(v, list):
                x[k] = [iv.encode("utf-8") for iv in v]
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
        res = b''.join([res_all[k] for k in res_keys])
        assert_equal(serialize.format_header(**kws), res)
    assert_raises(ValueError, serialize.format_header)


def test_parse_header():
    r"""Test parsing header."""
    header = [b"# name\tnumber\tvalue\tcomplex\n",
              b"# n/a\tg\tcm\tn/a\n",
              b"# %5s\t%ld\t%lf\t%g%+gj\n"]
    res = dict(delimiter=b'\t', comment=b'# ', newline=b'\n',
               format_str=b"%5s\t%ld\t%lf\t%g%+gj\n",
               fmts=[b'%5s', b'%ld', b'%lf', b'%g%+gj'],
               field_names=[b'name', b'number', b'value', b'complex'],
               field_units=[b'n/a', b'g', b'cm', b'n/a'])
    assert_equal(serialize.parse_header(header), res)
    assert_equal(serialize.parse_header(header[::-1]), res)
    _empty = b''
    assert_equal(serialize.parse_header(_empty.join(header)), res)
    # Test without formats
    header2 = header[:2]
    res2 = dict(**res)
    del res2['format_str']
    res2['fmts'] = []
    assert_equal(serialize.parse_header(header2), res2)
    # Test with explicit line numbers
    assert_equal(serialize.parse_header(header, lineno_names=0, lineno_units=1),
                 res)
    # Test errors
    header3 = [header[0], header[0]]
    assert_raises(RuntimeError, serialize.parse_header, header3)
    header4 = [header[1], header[1]]
    assert_raises(RuntimeError, serialize.parse_header, header4)


def test_dict2list():
    r"""Test conversion of a dictionary to a list and back."""
    assert_raises(TypeError, serialize.dict2list, None)
    assert_raises(TypeError, serialize.list2dict, None)


def test_numpy2pandas():
    r"""Test conversion of a numpy array to a pandas data frame and back."""
    assert_raises(TypeError, serialize.numpy2pandas, None)
    assert_raises(TypeError, serialize.pandas2numpy, None)
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
                 arr_obj,
                 np.array([])]
    for ans in test_arrs:
        frame = serialize.numpy2pandas(ans)
        res = serialize.pandas2numpy(frame)
        np.testing.assert_array_equal(ans, res)


def test_numpy2list():
    r"""Test conversion of a numpy array to a list and back."""
    assert_raises(TypeError, serialize.numpy2list, None)
    assert_raises(TypeError, serialize.list2numpy, None)
    nele = 5
    names = ["complex", "name", "number", "value"]
    dtypes = ['c16', 'S5', 'i8', 'f8']
    dtype = np.dtype([(n, f) for n, f in zip(names, dtypes)])
    arr_mix = np.zeros(nele, dtype)
    arr_mix['name'][0] = 'hello'
    test_arrs = [arr_mix]
    for ans in test_arrs:
        d = serialize.numpy2list(ans)
        # Name provided
        res = serialize.list2numpy(d, names=names)
        np.testing.assert_array_equal(ans, res)


def test_numpy2dict():
    r"""Test conversion of a numpy array to a dictionary and back."""
    assert_raises(TypeError, serialize.numpy2dict, None)
    assert_raises(TypeError, serialize.dict2numpy, None)
    nele = 5
    names = ["complex", "name", "number", "value"]
    dtypes = ['c16', 'S5', 'i8', 'f8']
    dtype = np.dtype([(n, f) for n, f in zip(names, dtypes)])
    arr_mix = np.zeros(nele, dtype)
    arr_mix['name'][0] = 'hello'
    test_arrs = [arr_mix, np.zeros(0, dtype)]
    np.testing.assert_array_equal(serialize.dict2numpy({}),
                                  np.array([]))
    for ans in test_arrs:
        d = serialize.numpy2dict(ans)
        # Sorted
        res = serialize.dict2numpy(d)
        np.testing.assert_array_equal(ans, res)
        # Provided
        res = serialize.dict2numpy(d, order=ans.dtype.names)
        np.testing.assert_array_equal(ans, res)


def test_pandas2dict():
    r"""Test conversion of a Pandas data frame to a dictionary and back."""
    assert_raises(TypeError, serialize.dict2pandas, None)
    assert_raises(TypeError, serialize.pandas2dict, None)
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
                 arr_obj,
                 np.array([])]
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
