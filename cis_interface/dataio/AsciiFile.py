import os
from cis_interface import backwards, platform, serialize


_default_args = {'comment': serialize._default_comment,
                 'newline': serialize._default_newline}


class AsciiFile(object):
    def __init__(self, filepath, io_mode, comment=_default_args['comment'],
                 newline=_default_args['newline'], open_as_binary=True):
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
            open_as_binary (bool, optional): If True, the file is opened in
                binary mode. Defaults to True.

        Attributes:
            filepath (str): Full path to the file that should be read from
                or written to.
            io_mode (str): Mode that should be used to open the file.
            comment (str): String that should be used to identify comments.
            newline (str): String that should be used to identify the end of a
                line.
            open_as_binary (bool): If True, the file is opened in binary mode.
            fd (file): File descriptor.

        Raises:
            TypeError: If filepath is not a string.
            ValueError: If io_mode is not one of the allowed values.
            ValueError: If filepath is not a valid path and io_mode is 'r'.

        """
        if not isinstance(filepath, str):
            raise TypeError('File path must be provided as a string.')
        self.filepath = os.path.abspath(filepath)
        if io_mode not in ['r', 'w', 'a', None]:
            raise ValueError("IO specifier must be 'r' or 'w'.")
        self.io_mode = io_mode
        if self.io_mode == 'r' and not os.path.isfile(filepath):
            raise ValueError("File does not exist.")
        self.comment = backwards.unicode2bytes(comment)
        self.newline = backwards.unicode2bytes(newline)
        self.open_as_binary = open_as_binary
        self.fd = None

    @property
    def is_open(self):
        r"""bool: Returns True if the file descriptor is open."""
        return (self.fd is not None)

    @property
    def open_mode(self):
        r"""str: Mode that should be used to open the file."""
        out = self.io_mode
        if self.open_as_binary:
            out += 'b'
        return out

    def open(self):
        r"""Open the associated file descriptor if it is not already open."""
        if self.io_mode is None:
            raise Exception("Cannot open in memory table.")
        if not self.is_open:
            self.fd = open(self.filepath, self.open_mode)

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
            line (str/bytes): Line to be written with/without the newline
                character.

        Raises:
            TypeError: If line is not the correct bytes type.

        """
        if not self.is_open:
            print("The file is not open. Nothing written.")
            return
        if not isinstance(line, backwards.bytes_type):
            raise TypeError("Line must be of type %s" % backwards.bytes_type)
        if not line.endswith(self.newline):
            line = line + self.newline
        self.writeline_full(line)

    def readline_full(self):
        r"""Read a line and return it if it is not a comment.

        Returns:
            tuple (bool, str): End of file flag and the line that was read (an
                empty string if the end of file was encountered). If the line is
                a comment, None is returned.

        """
        line = None
        if not self.is_open:
            print("The file is not open. Nothing read.")
            return True, line
        line = backwards.unicode2bytes(self.fd.readline())
        if len(line) == 0:
            return True, line
        line = line.replace(backwards.unicode2bytes(platform._newline),
                            backwards.unicode2bytes(self.newline))
        if line.startswith(self.comment):
            return False, None
        return False, line

    def writeline_full(self, line):
        r"""Write a line to the file in its present state. If it is not open,
        nothing happens.

        Args:
            line (str/bytes): Line to be written.

        Raises:
            TypeError: If line is not the correct bytes type.

        """
        if not self.is_open:
            print("The file is not open. Nothing written.")
            return
        if self.open_as_binary:
            line = backwards.unicode2bytes(line)
        else:
            line = backwards.bytes2unicode(line)
        # if not isinstance(line, backwards.bytes_type):
        #     raise TypeError("Line must be of type %s" % backwards.bytes_type)
        self.fd.write(line)
