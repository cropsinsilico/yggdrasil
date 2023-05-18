import os
import copy
import warnings
import pandas as pd
from yggdrasil.serialize.PandasSerialize import PandasSerialize
from yggdrasil.components import import_component
from yggdrasil.communication.DedicatedFileBase import DedicatedFileBase
try:
    import openpyxl
except ImportError:
    openpyxl = None
    warnings.warn("openpyxl not installed so reading of excel files will"
                  " be disabled.")


class ExcelFileComm(DedicatedFileBase):
    r"""Class for handling I/O from/to an Excel file."""

    _filetype = 'excel'
    _schema_subtype_description = ('The file is read/written as Excel')
    _schema_properties = {
        'sheets': {
            'type': 'array',
            'items': {'type': 'string'},
            'allowSingular': True,
            'description': (
                'Name(s) of one more more sheets that should be read/'
                'written. If not provided during read, all sheets will '
                'be read.')},
        'sheet_template': {
            'type': 'string',
            'description': (
                'Format string that can be completed with % operator to '
                'generate names for each subsequent sheet when writing.'
            )},
        'columns': {
            'type': 'array',
            'items': {'type': ['string', 'integer']},
            'description': 'Names of columns to read/write.'},
        'startrow': {
            'type': 'integer', 'default': 0,
            'description': 'Row to start read/write at.'},
        'startcol': {
            'type': 'integer', 'default': 0,
            'description': 'Column to start read/write at.'},
        'endrow': {
            'type': 'integer',
            'description': 'Row to stop read at (non-inclusive).'},
        'endcol': {
            'type': 'integer',
            'description': 'Column to stop read at (non-inclusive).'},
        'str_as_bytes': {
            'type': 'boolean', 'default': False,
            'description': ('If true, strings in columns are read as '
                            'bytes')},
    }
    _extensions = ['.xlsx', '.xls', '.xlsm', '.xlsb', '.odf', '.ods',
                   '.odt']
    no_serialization = True
    _synchronous_read = True
    concats_as_str = True

    def __init__(self, *args, **kwargs):
        if kwargs.get('direction', 'send') == 'send':
            transform = 'pandas'
            kwargs['serializer'] = {'seritype': 'pandas'}
        else:
            transform = 'array'
            kwargs['serializer'] = {
                'seritype': 'table', 'as_array': True}
        super(ExcelFileComm, self).__init__(*args, **kwargs)
        if self.direction == 'send' and not (self.sheets
                                             or self.sheet_template):
            self.sheet_template = 'Sheet%d'
        self.transform.append(import_component('transform', transform)())
        self._remaining_sheets = copy.deepcopy(self.sheets)
        if self._remaining_sheets is None:
            self._remaining_sheets = []
        if self.sheet_template and self.direction == 'send':
            self._remaining_sheets.append(self.sheet_template)
        self._processed_sheets = []
        self._cached_sheets = {}
        # self.read_meth = 'readline'

    @classmethod
    def is_installed(cls, language=None):
        r"""Determine if the necessary libraries are installed for this
        communication class.

        Args:
            language (str, optional): Specific language that should be checked
                for compatibility. Defaults to None and all languages supported
                on the current platform will be checked. If set to 'any', the
                result will be True if this comm is installed for any of the
                supported languages.

        Returns:
            bool: Is the comm installed.

        """
        return (language == 'python') and (openpyxl is not None)

    @property
    def current_sheet(self):
        r"""str: Current sheet name."""
        if ((self.sheets or self._cached_sheets
             and self.sheet_template != self._remaining_sheets[0])):
            return self._remaining_sheets[0]
        if self.sheet_template:
            return self.sheet_template % (
                len(self._processed_sheets) + 1)
        return None

    def pop_current_sheet(self):
        r"""Remove the current sheet from the list of remaining
        sheets."""
        curr = self.current_sheet
        if curr is not None:
            if curr in self._remaining_sheets:
                self._remaining_sheets.remove(curr)
            self._processed_sheets.append(curr)

    def read_header(self):
        r"""Read header lines from the file and update serializer info."""
        self.header_was_read = True
        
    def write_header(self):
        r"""Write header lines to the file based on the serializer
        info."""
        self.header_was_written = True

    # def record_position(self):
    #     r"""Record the current position in the file/series."""
    #     out = list(super(ExcelFileComm, self).record_position())
    #     out.append(len(self._processed_sheets))
    #     return tuple(out)

    # def change_position(self, file_pos, series_index=None,
    #                     header_was_read=None, header_was_written=None,
    #                     processed_sheets=0):
    #     r"""Change the position in the file/series."""
    #     super(ExcelFileComm, self).change_position(
    #         file_pos, series_index=series_index,
    #         header_was_read=header_was_read,
    #         header_was_written=header_was_written)
    #     allsheets = self._processed_sheets + self._remaining_sheets
    #     if processed_sheets is not None:
    #         idx = min(len(allsheets), processed_sheets)
    #         self._processed_sheets = allsheets[:idx]
    #         self._remaining_sheets = allsheets[idx:]
        
    @property
    def file_size(self):
        r"""int: Current size of file."""
        out = super(ExcelFileComm, self).file_size
        if self.direction == 'recv':
            if self.sheets or self._cached_sheets:
                out = len(self._processed_sheets + self._remaining_sheets)
            else:
                out = int(out > 0)
                if out:
                    out += 1
        return out

    @property
    def _file_size_recv(self):
        r"""int: Current size of file."""
        out = super(ExcelFileComm, self).file_size
        if self.direction == 'recv':
            return len(self._processed_sheets)
        return out

    def file_seek(self, *args, **kwargs):
        r"""Move in the file to the specified position."""
        super(ExcelFileComm, self).file_seek(*args, **kwargs)
        if self.direction == 'recv':
            allsheets = self._processed_sheets + self._remaining_sheets
            allsheets[:self._last_size]
            allsheets[self._last_size:]
            # self._processed_sheets[:self._last_size]
            # self._remaining_sheets[self._last_size:]
        
    def _dedicated_open(self, address, mode):
        self._external_fd = address
        if self.sheets:
            self._remaining_sheets = [
                k for k in self.sheets if k not in self._processed_sheets]
        return self._external_fd

    def _dedicated_close(self):
        self._external_fd = None
        self._cached_sheets = {}

    def _dedicated_send(self, msg):
        if not self._external_fd:  # pragma: debug
            raise IOError("File address not set")
        if self.columns:
            msg = msg[self.columns]
        msg = PandasSerialize.normalize_bytes2unicode(msg)
        kws = {}
        mode = self.open_mode
        if mode == 'a' and not os.path.isfile(self._external_fd):
            mode = 'w'
        if mode == 'a':
            kws['if_sheet_exists'] = 'new'
        writer = pd.ExcelWriter(self._external_fd, mode=mode, **kws)
        msg.to_excel(
            writer, index=False,
            startrow=self.startrow, startcol=self.startcol,
            sheet_name=self.current_sheet)
        writer.close()
        self.pop_current_sheet()

    def _dedicated_recv(self):
        if not self._external_fd:  # pragma: debug
            raise IOError("File address not set")
        if self._cached_sheets:
            out = self._cached_sheets[self.current_sheet]
        else:
            out = pd.read_excel(
                self._external_fd, sheet_name=self.current_sheet,
                usecols=self.columns)
            if isinstance(out, dict):
                self._cached_sheets = out
                if not self.sheets:
                    # self._processed_sheets = []
                    # self._remaining_sheets = list(out.keys())
                    # Do this instead if recv in append mode should only
                    # read new sheets
                    self._remaining_sheets = [
                        k for k in out.keys() if k not in
                        self._processed_sheets]
                return self._dedicated_recv()
        out = out.iloc[slice(self.startrow, self.endrow),
                       slice(self.startcol, self.endcol)]
        if self.str_as_bytes:
            out = PandasSerialize.normalize_unicode2bytes(out)
        self.pop_current_sheet()
        self.transform[-1].set_original_datatype_from_data(out)
        return out

    @classmethod
    def get_testing_options(cls):
        r"""Method to return a dictionary of testing options for this
        class.

        Returns:
            dict: Dictionary of variables to use for testing. Items:
                kwargs (dict): Keyword arguments for comms tested with
                    the provided content.
                send (list): List of objects to send to test file.
                recv (list): List of objects that will be received from a
                    test file that was sent the messages in 'send'.
                contents (bytes): Bytes contents of test file created by
                    sending the messages in 'send'.

        """
        out = super(DedicatedFileBase, cls).get_testing_options(
            serializer='table', array_columns=True, no_units=True,
            table_string_type='bytes', read_meth='readline')
        out.update(contents=None,
                   exact_contents=False)
        out.setdefault('kwargs', {})
        out['kwargs']['str_as_bytes'] = True
        return out
            
