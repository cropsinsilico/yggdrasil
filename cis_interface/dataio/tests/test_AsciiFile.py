import os
import tempfile
from nose.tools import assert_raises, assert_equal
from cis_interface.dataio import AsciiFile
from cis_interface.tests import data


input_file = data['txt']
output_dir = tempfile.gettempdir()
output_file = os.path.join(output_dir, os.path.basename(input_file))

input_ncomments = 1
input_nlines = 3
output_ncomments = 0
output_nlines = input_nlines

mode_list = ['r', 'w', None]
mode2file = {'r': input_file,
             'w': output_file,
             None: 'null'}


def test_AsciiFile():
    r"""Test creation of AsciiFile."""
    for mode in mode_list:
        AsciiFile.AsciiFile(mode2file[mode], mode)
    assert_raises(TypeError, AsciiFile.AsciiFile, 0, 'r')
    assert_raises(ValueError, AsciiFile.AsciiFile, input_file, 0)
    assert_raises(ValueError, AsciiFile.AsciiFile, 'null', 'r')


def test_AsciiFile_open_close():
    r"""Test opening and closing AsciiFile."""
    for mode in mode_list:
        AF = AsciiFile.AsciiFile(mode2file[mode], mode)
        assert(not AF.is_open)
        if mode is None:
            assert_raises(Exception, AF.open)
        else:
            AF.open()
            assert(AF.is_open)
            AF.close()
        assert(not AF.is_open)

        
def test_AsciiFile_line_full_binary():
    r"""Test reading/writing a full line in binary mode."""
    AF_in = AsciiFile.AsciiFile(input_file, 'r')
    AF_out = AsciiFile.AsciiFile(output_file, 'w')
    # Read/write before open returns None
    eof, line = AF_in.readline_full()
    AF_in.writeline_full(line)
    assert(eof)
    assert_equal(line, None)
    # Read/write all lines
    AF_in.open()
    AF_out.open()
    count_lines = 0
    count_comments = 0
    assert_raises(TypeError, AF_in.writeline_full, 0)
    eof, line = False, None
    while not eof:
        eof, line = AF_in.readline_full()
        if not eof:
            if line is None:
                count_comments += 1
            else:
                AF_out.writeline_full(line)
                count_lines += 1
    AF_in.close()
    AF_out.close()
    assert_equal(count_lines, input_nlines)
    assert_equal(count_comments, input_ncomments)
    # Read output file to make sure it has lines
    AF_out = AsciiFile.AsciiFile(output_file, 'r')
    count_lines = 0
    count_comments = 0
    AF_out.open()
    eof, line = False, None
    while not eof:
        eof, line = AF_out.readline_full()
        if not eof:
            if line is None:
                count_comments += 1  # pragma: no cover
            else:
                count_lines += 1
    AF_out.close()
    assert_equal(count_lines, output_nlines)
    assert_equal(count_comments, output_ncomments)
    os.remove(output_file)

    
def test_AsciiFile_line_full_text():
    r"""Test reading/writing a full line in text mode."""
    AF_in = AsciiFile.AsciiFile(input_file, 'r', open_as_binary=False)
    AF_out = AsciiFile.AsciiFile(output_file, 'w', open_as_binary=False)
    # Read/write before open returns None
    eof, line = AF_in.readline_full()
    AF_in.writeline_full(line)
    assert(eof)
    assert_equal(line, None)
    # Read/write all lines
    AF_in.open()
    AF_out.open()
    count_lines = 0
    count_comments = 0
    assert_raises(TypeError, AF_in.writeline_full, 0)
    eof, line = False, None
    while not eof:
        eof, line = AF_in.readline_full()
        if not eof:
            if line is None:
                count_comments += 1
            else:
                AF_out.writeline_full(line)
                count_lines += 1
    AF_in.close()
    AF_out.close()
    assert_equal(count_lines, input_nlines)
    assert_equal(count_comments, input_ncomments)
    # Read output file to make sure it has lines
    AF_out = AsciiFile.AsciiFile(output_file, 'r')
    count_lines = 0
    count_comments = 0
    AF_out.open()
    eof, line = False, None
    while not eof:
        eof, line = AF_out.readline_full()
        if not eof:
            if line is None:
                count_comments += 1  # pragma: no cover
            else:
                count_lines += 1
    AF_out.close()
    assert_equal(count_lines, output_nlines)
    assert_equal(count_comments, output_ncomments)
    os.remove(output_file)

    
def test_AsciiFile_line():
    r"""Test reading/writing a line without a newline."""
    AF_in = AsciiFile.AsciiFile(input_file, 'r')
    AF_out = AsciiFile.AsciiFile(output_file, 'w')
    # Read/write before open returns None
    eof, line = AF_in.readline()
    AF_in.writeline(line)
    assert(eof)
    assert_equal(line, None)
    # Read/write all lines
    AF_in.open()
    AF_out.open()
    count_lines = 0
    count_comments = 0
    assert_raises(TypeError, AF_in.writeline, 0)
    eof, line = False, None
    while not eof:
        eof, line = AF_in.readline()
        if not eof:
            if line is None:
                count_comments += 1  # pragma: no cover
            else:
                AF_out.writeline(line.rstrip(AF_out.newline))
                count_lines += 1
    AF_in.close()
    AF_out.close()
    assert_equal(count_lines, input_nlines)
    assert_equal(count_comments, 0)
    # Read output file to make sure it has lines
    AF_out = AsciiFile.AsciiFile(output_file, 'r')
    count_lines = 0
    count_comments = 0
    AF_out.open()
    eof, line = False, None
    while not eof:
        eof, line = AF_out.readline()
        if not eof:
            if line is None:
                count_comments += 1  # pragma: no cover
            else:
                count_lines += 1
    AF_out.close()
    assert_equal(count_lines, output_nlines)
    assert_equal(count_comments, 0)
    os.remove(output_file)
