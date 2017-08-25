import os
import numpy as np
from nose.tools import istest, nottest, assert_raises, assert_equal
import AsciiTable

input_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), "Input")
output_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), "Output")

input_file = os.path.join(input_dir, "ascii_table.txt")
output_file = os.path.join(output_dir, "ascii_table.txt")
ncols = 3
nrows = 3
input_ncomments = 2 # Names & formats
input_nlines = nrows
output_ncomments = 2  # Just formats
output_nlines = nrows
format_str = "%5s\t%d\t%f\n"
column_names = ["name", "number", "value"]


mode_list = ['r', 'w', None]
mode2file = {'r': input_file,
             'w': output_file,
             None: 'null'}
mode2kws = {'r': {},
            'w': {'format_str': format_str, 'column_names': column_names},
            None: {'format_str': format_str, 'column_names': column_names}}

unsupported_nptype = ['complex_', 'complex64', 'complex128', 'bool_']
map_nptype2cformat = [(['float_', 'float16', 'float32', 'float64'], '%g'),
                      # (['int8', 'short', 'intc', 'int_', 'longlong'], '%d'),
                      # (['uint8', 'ushort', 'uintc', 'uint64', 'ulonglong'], '%u'),
                      ('int8', '%hhd'), ('short', '%hd'), ('intc', '%d'), ('int_', '%ld'),
                      ('uint8', '%hhu'), ('ushort', '%hu'), ('uintc', '%u'), ('uint64', '%lu'), 
                      ('S', '%s')]
if np.dtype('int_') != np.dtype('longlong'):
    map_nptype2cformat.append(('longlong', '%lld'))
    map_nptype2cformat.append(('ulonglong', '%llu'))
map_cformat2pyscanf = [(['%hhd', '%hd', '%d', '%ld', '%lld'], '%d'),
                       (['%hhu', '%hu', '%u', '%lu', '%llu'], '%u'),
                       (['%5s', '%s'], '%s')]

unsupported_cfmt = ['a', 'A', 'p', 'n', '']
map_cformat2nptype = [(['f', 'F', 'e', 'E', 'g', 'G'], 'float64'),
                      (['hhd', 'hhi'], 'int8'),
                      (['hd', 'hi'], 'short'),
                      (['d', 'i'], 'intc'),
                      (['ld', 'li'], 'int_'),
                      (['lld', 'lli'], 'longlong'),
                      (['hhu', 'hho', 'hhx', 'hhX'], 'uint8'),
                      (['hu', 'ho', 'hx', 'hX'], 'ushort'),
                      (['u', 'o', 'x', 'X'], 'uintc'),
                      (['lu', 'lo', 'lx', 'lX'], 'uint64'),
                      (['llu', 'llo', 'llx', 'llX'], 'ulonglong'),
                      (['c', 's'], 'str')]


def test_nptype2cformat():
    for a, b in map_nptype2cformat:
        if isinstance(a, str):
            a = [a]
        for ia in a:
            assert_equal(AsciiTable.nptype2cformat(ia), b)
    assert_raises(TypeError, AsciiTable.nptype2cformat, 0)
    for a in unsupported_nptype:
        assert_raises(ValueError, AsciiTable.nptype2cformat, a)


def test_cformat2nptype():
    for a, b in map_cformat2nptype:
        if isinstance(a, str):
            a = [a]
        for ia in a:
            assert_equal(AsciiTable.cformat2nptype('%'+ia), np.dtype(b).str)
    assert_raises(TypeError, AsciiTable.cformat2nptype, 0)
    assert_raises(ValueError, AsciiTable.cformat2nptype, 's')
    assert_raises(ValueError, AsciiTable.cformat2nptype, '%')
    for a in unsupported_nptype:
        assert_raises(ValueError, AsciiTable.cformat2nptype, a)


def test_cformat2pyscanf():
    for a, b in map_cformat2pyscanf:
        if isinstance(a, str):
            a = [a]
        for ia in a:
            assert_equal(AsciiTable.cformat2pyscanf(ia), b)
    assert_raises(TypeError, AsciiTable.cformat2pyscanf, 0)
    assert_raises(ValueError, AsciiTable.cformat2pyscanf, 's')
    assert_raises(ValueError, AsciiTable.cformat2pyscanf, '%')


def test_AsciiTable():
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
                    count_comments+=1
                else:
                    AF_out.writeline_full(line, validate=True)
                    count_lines+=1
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
                    count_comments+=1
                else:
                    count_lines+=1
        AF_out.close()
        assert_equal(count_lines, output_nlines)
        assert_equal(count_comments, output_ncomments)
        os.remove(output_file)


def test_AsciiTable_line():
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
                    count_comments+=1
                else:
                    AF_out.writeline(*line)
                    count_lines+=1
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
                    count_comments+=1
                else:
                    count_lines+=1
        AF_out.close()
        assert_equal(count_lines, output_nlines)
        assert_equal(count_comments, 0)
        os.remove(output_file)


def test_AsciiTable_io_array():
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
                    count_comments+=1
                else:
                    count_lines+=1
        AF_out.close()
        assert_equal(count_lines, output_nlines)
        assert_equal(count_comments, output_ncomments) # names
        os.remove(output_file)

        
def test_AsciiTable_io_array_skip_header():
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
                    count_comments+=1
                else:
                    count_lines+=1
        AF_out.close()
        assert_equal(count_lines, output_nlines)
        assert_equal(count_comments, 0)
        os.remove(output_file)

        
def test_AsciiTable_array_bytes():
    for use_astropy in [False, True]:
        for order in ['C', 'F']:
            AF_in = AsciiTable.AsciiTable(input_file, 'r',
                                          use_astropy=use_astropy, **mode2kws['r'])
            AF_out = AsciiTable.AsciiTable(output_file, 'w',
                                           use_astropy=use_astropy, #**mode2kws['w'])
                                           format_str=AF_in.format_str,
                                           column_names=AF_in.column_names)
            # Read matrix
            in_arr = AF_in.read_array()
            # Errors
            assert_raises(TypeError, AF_in.array_to_bytes, 0)
            assert_raises(ValueError, AF_in.array_to_bytes, np.zeros(nrows))
            assert_raises(ValueError, AF_in.array_to_bytes, np.zeros((nrows, ncols-1)))
            # Check direct conversion of bytes
            in_bts = AF_in.array_to_bytes(order=order)
            out_arr = AF_in.bytes_to_array(in_bts, order=order)
            np.testing.assert_equal(out_arr, in_arr)
            # Write matrix
            out_arr = AF_out.bytes_to_array(in_bts, order=order)
            AF_out.write_array(out_arr)
            # Read output matrix
            AF_out = AsciiTable.AsciiTable(output_file, 'r',
                                           use_astropy=use_astropy)
            out_arr = AF_out.read_array()
            np.testing.assert_equal(out_arr, in_arr)
            os.remove(output_file)


def test_AsciiTable_io_bytes():
    for use_astropy in [False, True]:
        AF_in = AsciiTable.AsciiTable(input_file, 'r',
                                      use_astropy=use_astropy, **mode2kws['r'])
        AF_out = AsciiTable.AsciiTable(output_file, 'w',
                                       use_astropy=use_astropy, #**mode2kws['w'])
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
                    count_comments+=1
                else:
                    count_lines+=1
        AF_out.close()
        assert_equal(count_lines, output_nlines)
        assert_equal(count_comments, output_ncomments) # names
        os.remove(output_file)

        
