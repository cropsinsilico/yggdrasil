from __future__ import print_function
import sys
# Import necessary connection interfaces
from cis_interface import backwards
from cis_interface.interface.PsiInterface import (
    PsiAsciiFileInput, PsiAsciiFileOutput,
    PsiAsciiTableInput, PsiAsciiTableOutput)

    
if __name__ == '__main__':

    # Input & output to an ASCII file line by line
    in_file = PsiAsciiFileInput('inputPy_file')
    out_file = PsiAsciiFileOutput('outputPy_file')
    # Input & output from a table row by row
    in_table = PsiAsciiTableInput('inputPy_table')
    out_table = PsiAsciiTableOutput('outputPy_table',
                                    '%5s\t%ld\t%3.1f\t%3.1lf%+3.1lfj\n')
    # Input & output from a table as an array
    in_array = PsiAsciiTableInput('inputPy_array')
    out_array = PsiAsciiTableOutput('outputPy_array',
                                    '%5s\t%ld\t%3.1f\t%3.1lf%+3.1lfj\n')

    # Read lines from ASCII text file until end of file is reached.
    # As each line is received, it is then sent to the output ASCII file.
    print('ascii_io(P): Receiving/sending ASCII file.')
    ret = True
    while ret:
        # Receive a single line
        (ret, line) = in_file.recv_line()
        if ret:
            # If the receive was succesful, send the line to output
            print("File: %s" % backwards.bytes2unicode(line), end='')
            ret = out_file.send_line(line)
            if not ret:
                print("ascii_io(P): ERROR SENDING LINE")
                break
        else:
            # If the receive was not succesful, send the end-of-file message to
            # close the output file.
            print("End of file input (Python)")
            out_file.send_eof()

    # Read rows from ASCII table until end of file is reached.
    # As each row is received, it is then sent to the output ASCII table
    print('ascii_io(P): Receiving/sending ASCII table.')
    ret = True
    while ret:
        # Receive a single row
        (ret, line) = in_table.recv_row()
        if ret:
            # If the receive was succesful, send the values to output.
            # Formatting is taken care of on the output driver side.
            print("Table: %s, %d, %3.1f, %s" % line)
            ret = out_table.send_row(*line)
            if not ret:
                print("ascii_io(P): ERROR SENDING ROW")
                break
        else:
            # If the receive was not succesful, send the end-of-file message to
            # close the output file.
            print("End of table input (Python)")
            out_table.send_eof()

    # Read entire array from ASCII table into numpy array
    ret, arr = in_array.recv_array()
    if not ret:
        print("ascii_io(P): ERROR RECVING ARRAY")
        sys.exit(-1)
    print("Array: (%d rows)" % len(arr))
    # Print each line in the array
    for i in range(len(arr)):
        print("%5s, %d, %3.1f, %s" % tuple(arr[i]))
    # Send the array to output. Formatting is handled on the output driver side.
    ret = out_array.send_array(arr)
    if not ret:
        print("ascii_io(P): ERROR SENDING ARRAY")
