import os
import numpy as np
import tempfile
from nose.tools import assert_raises, assert_equal
from cis_interface.dataio import AsciiTable
from cis_interface.tests import data
from cis_interface import backwards


input_file = data['table']
output_dir = tempfile.gettempdir()
output_file = os.path.join(output_dir, os.path.basename(input_file))

ncols = 4
nrows = 4
input_ncomments = 2  # Names & formats
input_nlines = nrows
output_ncomments = 2  # Just formats
output_nlines = nrows
format_str = "%5s\t%ld\t%lf\t%g%+gj\n"
column_names = ("name", "number", "value", "complex")


mode_list = ['r', 'w', None]
mode2file = {'r': input_file,
             'w': output_file,
             None: 'null'}
mode2kws = {'r': {},
            'w': {'format_str': format_str, 'column_names': column_names},
            None: {'format_str': format_str, 'column_names': column_names}}


def test_AsciiTable():
    r"""Test creation of an AsciiTable."""
    for mode in mode_list:
        for use_astropy in [False, True]:
            AF = AsciiTable.AsciiTable(mode2file[mode], mode,
                                       use_astropy=use_astropy, **mode2kws[mode])
            assert_equal(AF.column_names, column_names)
        assert_raises(TypeError, AsciiTable.AsciiTable, 0, 'r')
        assert_raises(ValueError, AsciiTable.AsciiTable, input_file, 0)
        assert_raises(ValueError, AsciiTable.AsciiTable, 'null', 'r')
        assert_raises(RuntimeError, AsciiTable.AsciiTable, output_file, 'w')
        assert_raises(RuntimeError, AsciiTable.AsciiTable, output_file, None)

        
def test_AsciiTable_open_close():
    r"""Test opening/closing and AsciiTable file."""
    for use_astropy in [False, True]:
        for mode in mode_list:
            AF = AsciiTable.AsciiTable(mode2file[mode], mode,
                                       use_astropy=use_astropy, **mode2kws[mode])
            assert(not AF.is_open)
            if mode is None:
                assert_raises(Exception, AF.open)
            else:
                AF.open()
                assert(AF.is_open)
                AF.close()
            assert(not AF.is_open)


def test_AsciiTable_line_full():
    r"""Test writing/reading a full line to/from an AsciiTable file."""
    for use_astropy in [False, True]:
        AF_in = AsciiTable.AsciiTable(input_file, 'r',
                                      use_astropy=use_astropy, **mode2kws['r'])
        AF_out = AsciiTable.AsciiTable(output_file, 'w',
                                       use_astropy=use_astropy, **mode2kws['w'])
        # Read/write before open returns None
        eof, line = AF_in.readline_full()
        AF_in.writeline_full(line)
        assert(eof)
        assert_equal(line, None)
        # Read/write all lines
        AF_in.open()
        AF_out.open()
        AF_out.writeheader()
        count_lines = 0
        count_comments = 0
        assert_raises(TypeError, AF_in.writeline_full, 0)
        eof, line = False, None
        while not eof:
            eof, line = AF_in.readline_full(validate=True)
            if not eof:
                if line is None:
                    count_comments += 1
                else:
                    AF_out.writeline_full(line, validate=True)
                    count_lines += 1
        AF_in.close()
        AF_out.close()
        assert_equal(count_lines, input_nlines)
        assert_equal(count_comments, input_ncomments)
        # Read output file to make sure it has lines
        AF_out = AsciiTable.AsciiTable(output_file, 'r',
                                       use_astropy=use_astropy)
        count_lines = 0
        count_comments = 0
        AF_out.open()
        eof, line = False, None
        while not eof:
            eof, line = AF_out.readline_full(validate=True)
            if not eof:
                if line is None:
                    count_comments += 1
                else:
                    count_lines += 1
        AF_out.close()
        assert_equal(count_lines, output_nlines)
        assert_equal(count_comments, output_ncomments)
        os.remove(output_file)


def test_AsciiTable_line():
    r"""Test reading/writing a row from/to an AsciiTable file."""
    for use_astropy in [False, True]:
        AF_in = AsciiTable.AsciiTable(input_file, 'r',
                                      use_astropy=use_astropy, **mode2kws['r'])
        AF_out = AsciiTable.AsciiTable(output_file, 'w',
                                       use_astropy=use_astropy, **mode2kws['w'])
        # Read/write before open returns None
        eof, line = AF_in.readline()
        AF_in.writeline(line)
        assert(eof)
        assert_equal(line, None)
        # Read/write all lines
        AF_in.open()
        AF_out.open()
        AF_out.writeheader()
        count_lines = 0
        count_comments = 0
        assert_raises(RuntimeError, AF_in.writeline, 0)
        eof, line = False, None
        while not eof:
            eof, line = AF_in.readline()
            if not eof:
                if line is None:
                    count_comments += 1  # pragma: debug
                else:
                    AF_out.writeline(*line)
                    count_lines += 1
        AF_in.close()
        AF_out.close()
        assert_equal(count_lines, input_nlines)
        assert_equal(count_comments, 0)
        # Read output file to make sure it has lines
        AF_out = AsciiTable.AsciiTable(output_file, 'r',
                                       use_astropy=use_astropy)
        count_lines = 0
        count_comments = 0
        AF_out.open()
        eof, line = False, None
        while not eof:
            eof, line = AF_out.readline()
            if not eof:
                if line is None:
                    count_comments += 1  # pragma: debug
                else:
                    count_lines += 1
        AF_out.close()
        assert_equal(count_lines, output_nlines)
        assert_equal(count_comments, 0)
        os.remove(output_file)


def test_AsciiTable_io_array():
    r"""Test writing/reading an array to/from an AsciiTable file."""
    for use_astropy in [False, True]:
        AF_in = AsciiTable.AsciiTable(input_file, 'r',
                                      use_astropy=use_astropy, **mode2kws['r'])
        AF_out = AsciiTable.AsciiTable(output_file, 'w',
                                       use_astropy=use_astropy, **mode2kws['w'])
        # Read matrix
        in_arr = AF_in.read_array()
        assert_equal(in_arr.shape, (nrows,))
        # Write matrix
        AF_out.write_array(in_arr)
        # Read output matrix
        AF_out = AsciiTable.AsciiTable(output_file, 'r',
                                       use_astropy=use_astropy)
        out_arr = AF_out.read_array()
        np.testing.assert_equal(out_arr, in_arr)
        # Read output file normally to make sure it has correct lines
        count_lines = 0
        count_comments = 0
        AF_out.open()
        eof, line = False, None
        while not eof:
            eof, line = AF_out.readline_full()
            if not eof:
                if line is None:
                    count_comments += 1  # pragma: debug
                else:
                    count_lines += 1
        AF_out.close()
        assert_equal(count_lines, output_nlines)
        assert_equal(count_comments, output_ncomments)  # names
        os.remove(output_file)

        
def test_AsciiTable_io_array_skip_header():
    r"""Test writing/reading an array to/from an AsciiTable file w/o a header."""
    for use_astropy in [False, True]:
        AF_in = AsciiTable.AsciiTable(input_file, 'r',
                                      use_astropy=use_astropy, **mode2kws['r'])
        AF_out = AsciiTable.AsciiTable(output_file, 'w',
                                       use_astropy=use_astropy, **mode2kws['w'])
        # Read matrix
        in_arr = AF_in.read_array()
        assert_equal(in_arr.shape, (nrows,))
        # Write matrix
        AF_out.write_array(in_arr, skip_header=True)
        # Read output matrix
        AF_out = AsciiTable.AsciiTable(output_file, 'r',
                                       format_str=format_str,
                                       column_names=column_names,
                                       use_astropy=use_astropy)
        out_arr = AF_out.read_array()
        np.testing.assert_equal(out_arr, in_arr)
        # Read output file normally to make sure it has correct lines
        count_lines = 0
        count_comments = 0
        AF_out.open()
        eof, line = False, None
        while not eof:
            eof, line = AF_out.readline_full()
            if not eof:
                if line is None:
                    count_comments += 1  # pragma: debug
                else:
                    count_lines += 1
        AF_out.close()
        assert_equal(count_lines, output_nlines)
        assert_equal(count_comments, 0)
        os.remove(output_file)

        
def test_AsciiTable_array_bytes():
    r"""Test converting an array from/to bytes using AsciiTable."""
    for use_astropy in [False, True]:
        for order in ['C', 'F']:
            AF_in = AsciiTable.AsciiTable(input_file, 'r',
                                          use_astropy=use_astropy,
                                          **mode2kws['r'])
            AF_out = AsciiTable.AsciiTable(output_file, 'w',
                                           use_astropy=use_astropy,
                                           format_str=AF_in.format_str,
                                           column_names=AF_in.column_names)
            # Read matrix
            assert_equal(AF_out.arr, None)
            assert_raises(ValueError, AF_in.read_array, names=['wrong'])
            in_arr = AF_in.arr
            in_arr = AF_in.read_array()
            # Errors
            assert_raises(TypeError, AF_in.array_to_bytes, 0)
            # assert_raises(ValueError, AF_in.array_to_bytes, np.zeros(nrows))
            assert_raises(ValueError, AF_in.array_to_bytes,
                          np.zeros((nrows, ncols - 1)))
            list_of_arr = [in_arr[n] for n in in_arr.dtype.names]
            list_of_arr[1] = list_of_arr[1][1:]
            assert_raises(ValueError, AF_in.array_to_bytes, list_of_arr)
            list_of_ele = [in_arr[i].tolist() for i in range(len(in_arr))]
            list_of_ele[1] = list_of_ele[1][1:]
            assert_raises(ValueError, AF_in.array_to_bytes, list_of_ele)
            assert_raises(ValueError, AF_in.array_to_bytes, [np.zeros(0)])
            # Check direct conversion of bytes
            in_bts = AF_in.array_to_bytes(order=order)
            out_arr = AF_in.bytes_to_array(in_bts, order=order)
            np.testing.assert_equal(out_arr, in_arr)
            # Lists of arrays for each field
            list_of_arr = [in_arr[n] for n in in_arr.dtype.names]
            in_bts = AF_in.array_to_bytes(list_of_arr, order=order)
            out_arr = AF_in.bytes_to_array(in_bts, order=order)
            np.testing.assert_equal(out_arr, in_arr)
            # Lists of element lists
            list_of_ele = [in_arr[i].tolist() for i in range(len(in_arr))]
            in_bts = AF_in.array_to_bytes(list_of_ele, order=order)
            out_arr = AF_in.bytes_to_array(in_bts, order=order)
            np.testing.assert_equal(out_arr, in_arr)
            # Write matrix
            assert_raises(RuntimeError, AF_out.bytes_to_array, in_bts[:-1],
                          order=order)
            out_arr = AF_out.bytes_to_array(in_bts, order=order)
            # assert_raises(ValueError, AF_out.write_array, out_arr,
            #               names=['wrong'])
            AF_out.write_array(out_arr)
            # Read output matrix
            AF_out = AsciiTable.AsciiTable(output_file, 'r',
                                           use_astropy=use_astropy)
            out_arr = AF_out.read_array()
            np.testing.assert_equal(out_arr, in_arr)
            os.remove(output_file)
    mat = np.zeros((4, 3), dtype='float')
    AF0 = AsciiTable.AsciiTable(output_file, 'w', format_str='%f\t%f\t%f')
    AF0.array_to_bytes(mat)


def test_AsciiTable_io_bytes():
    r"""Test writing/reading an array to/from an AsciiTable file as bytes."""
    for use_astropy in [False, True]:
        AF_in = AsciiTable.AsciiTable(input_file, 'r',
                                      use_astropy=use_astropy, **mode2kws['r'])
        AF_out = AsciiTable.AsciiTable(output_file, 'w',
                                       use_astropy=use_astropy,
                                       format_str=AF_in.format_str,
                                       column_names=AF_in.column_names)
        # Read matrix
        in_arr = AF_in.read_bytes()
        # Write matrix
        AF_out.write_bytes(in_arr)
        # Read output matrix
        AF_out = AsciiTable.AsciiTable(output_file, 'r',
                                       use_astropy=use_astropy)
        out_arr = AF_out.read_bytes()
        np.testing.assert_equal(out_arr, in_arr)
        # Read output file normally to make sure it has correct lines
        count_lines = 0
        count_comments = 0
        AF_out.open()
        eof, line = False, None
        while not eof:
            eof, line = AF_out.readline_full()
            if not eof:
                if line is None:
                    count_comments += 1
                else:
                    count_lines += 1
        AF_out.close()
        assert_equal(count_lines, output_nlines)
        assert_equal(count_comments, output_ncomments)  # names
        os.remove(output_file)

        
def test_AsciiTable_complex():
    r"""Test write/read of a table with a complex entry."""
    dtype = np.dtype([('f0', 'float'), ('f1', 'complex')])
    fmt = '%f\t%f%+fj\n'
    out_arr = np.ones(3, dtype)
    AF_out = AsciiTable.AsciiTable(output_file, 'w', dtype=dtype)
    AF_out.write_array(out_arr)
    AF_out.close()
    AF_in = AsciiTable.AsciiTable(output_file, 'r', format_str=fmt)
    in_arr = AF_in.read_array()
    AF_in.close()
    np.testing.assert_equal(in_arr, out_arr)

    
def test_AsciiTable_dtype_vs_format():
    r"""Test updating the format string/numpy dtype for an AsciiTable."""
    AF0 = AsciiTable.AsciiTable(mode2file['r'], 'r', **mode2kws['r'])
    AF1 = AsciiTable.AsciiTable(mode2file['r'], 'r', dtype=AF0.dtype)
    AF1.update_format_str(AF0.format_str)
    AF1.update_dtype(AF0.dtype)
    AF1.update_dtype(AF0.dtype.str)

    
def test_AsciiTable_writenames():
    r"""Test writing column names to an AsciiTable file."""
    AF0 = AsciiTable.AsciiTable(mode2file['w'], 'w', **mode2kws['w'])
    AF0.column_names = None
    AF0.writenames()
    assert_raises(IndexError, AF0.writenames, names=column_names[1:])

    
def test_AsciiTable_validate_line():
    r"""Test errors raised in line validation."""
    AF0 = AsciiTable.AsciiTable(mode2file['w'], 'w', **mode2kws['w'])
    assert_raises(ValueError, AF0.validate_line,
                  backwards.unicode2bytes('wrong format'))
    assert_raises(TypeError, AF0.validate_line, 5)
