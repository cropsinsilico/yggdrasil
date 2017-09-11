import sys
import signal
from cis_interface.interface.PsiInterface import (
    PsiAsciiFileInput, PsiAsciiFileOutput,
    PsiAsciiTableInput, PsiAsciiTableOutput)


def signal_handler(signal, frame):
    print('You pressed Ctrl+C!')
    sys.exit(0)

    
if __name__ == '__main__':
    signal.signal(signal.SIGINT, signal_handler)
    
    in_file = PsiAsciiFileInput('inputPy_file')
    out_file = PsiAsciiFileOutput('outputPy_file')
    in_table = PsiAsciiTableInput('inputPy_table')
    out_table = PsiAsciiTableOutput('outputPy_table', "%5s\t%ld\t%3.1f\n")
    in_array = PsiAsciiTableInput('inputPy_array')
    out_array = PsiAsciiTableOutput('outputPy_array', "%5s\t%ld\t%3.1f\n")

    # Generic text file
    ret = True
    while ret:
        (ret, line) = in_file.recv_line()
        if ret:
            print("File:", ret, line)
            out_file.send_line(line)
        else:
            print("End of file input (Python)")
            out_file.send_eof()

    # Table
    ret = True
    while ret:
        (ret, line) = in_table.recv_row()
        if ret:
            print("Table:", ret, line)
            out_table.send_row(*line)
        else:
            print("End of table input (Python)")
            out_table.send_eof()

    # Array
    ret, arr = in_array.recv_array()
    print("Array:", ret, arr)
    out_array.send_array(arr)
