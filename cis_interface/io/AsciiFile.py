from logging import *
import os


_default_args = {'comment': '#',
                 'newline': '\n'}


class AsciiFile(object):
    def __init__(self, filepath, io_mode, **kwargs):
        r"""Class for reading/writing an ASCII file.

        Args:
            filepath (str): Full path to the file that should be read from
                or written to.
            io_mode (str): Mode that should be used to open the file. Valid
                values include 'r', 'w', and None. None can be used to
                indicate an in memory table that will not be read from or 
                written to a file.
            comment (str, optional): String that should be used to identify
                comments. Defaults to '#'.
            newline (str, optional): String that should be used to identify
                the end of a line. Defaults to '\n'.

        Raises:
            TypeError: If filepath is not a string.
            ValueError: If io_mode is not one of the allowed values.
            ValueError: If filepath is not a valid path and io_mode is 'r'.

        """
        if not isinstance(filepath, str):
            raise TypeError('File path must be provided as a string.')
        self.filepath = os.path.abspath(filepath)
        if io_mode not in ['r', 'w', None]:
            raise ValueError("IO specifier must be 'r' or 'w'.")
        self.io_mode = io_mode
        if self.io_mode == 'r' and not os.path.isfile(filepath):
            raise ValueError("File does not exist.")
        for k, v in kwargs.items():
            setattr(self, k, v)
        for k, v in _default_args.items():
            if not hasattr(self, k):
                setattr(self, k, v)
        self.fd = None

    @property
    def is_open(self):
        r"""Returns True if the file descriptor is open."""
        return (self.fd is not None)

    def open(self):
        r"""Open the associated file descriptor if it is not already open."""
        if self.io_mode is None:
            raise Exception("Cannot open in memory table.")
        if not self.is_open:
            self.fd = open(self.filepath, self.io_mode)

    def close(self):
        r"""Close the associated file descriptor if it is open."""
        if self.is_open:
            self.fd.close()
            self.fd = None

    def readline(self):
        r"""Continue reading lines until a valid line (uncommented) is
        encountered
        
        Returns:
            tuple (bool, str): End of file flag and the line that was read
                (None if the end of file was encountered).

        """
        eof, line = False, None
        while (not eof) and (line is None):
            eof, line = self.readline_full()
        if eof:
            line = None
        return eof, line

    def writeline(self, line):
        r"""Write a line to the file, adding a newline character if it is not
        present.

        Args:
            line (str): Line to be written with/without the newline character.

        Raises:
            TypeError: If line is not a string.

        """
        if not self.is_open:
            print("The file is not open. Nothing written.")
            return
        if not isinstance(line, str):
            raise TypeError("Line must be a string.")
        if not line.endswith(self.newline):
            line += self.newline
        self.writeline_full(line)

    def readline_full(self):
        r"""Read a line and return it if it is not a comment.

        Returns:
            tuple (bool, str): End of file flag and the line that was read (an
                empty string if the end of file was encountered). If the line is
                a comment, None is returned.

        """
        line = None
        eof = False
        if not self.is_open:
            print("The file is not open. Nothing read.")
            return True, line
        line = self.fd.readline()
        if len(line) == 0:
            return True, line
        if line.startswith(self.comment):
            return False, None
        return False, line

    def writeline_full(self, line):
        r"""Write a line to the file in its present state. If it is not open,
        nothing happens.

        Args:
            line (str): Line to be written.

        Raises:
            TypeError: If line is not a string.

        """
        if not self.is_open:
            print("The file is not open. Nothing written.")
            return
        if not isinstance(line, str):
            raise TypeError("Line must be a string.")
        self.fd.write(line)
    
