from cis_interface import backwards
import cis_interface.drivers.tests.test_AsciiFileOutputDriver as parent


class TestAsciiTableOutputParam(parent.TestAsciiFileOutputParam):
    r"""Test parameters for AsciiTableOutputDriver."""

    def __init__(self, *args, **kwargs):
        super(TestAsciiTableOutputParam, self).__init__(*args, **kwargs)
        self.driver = 'AsciiTableOutputDriver'
        self.inst_kwargs['column'] = '\t'
        self.inst_kwargs['format_str'] = self.fmt_str
        self.ocomm_name = 'AsciiTableComm'

    @property
    def send_comm_kwargs(self):
        r"""dict: Keyword arguments for send comm."""
        out = super(TestAsciiTableOutputParam, self).send_comm_kwargs
        out['serializer'] = None
        out['serializer_kwargs'] = {'format_str': self.fmt_str,
                                    'field_names': self.field_names,
                                    'field_units': self.field_units}
        return out
        

class TestAsciiTableOutputDriverNoStart(TestAsciiTableOutputParam,
                                        parent.TestAsciiFileOutputDriverNoStart):
    r"""Test runner for AsciiTableOutputDriver without start."""
    pass
    

class TestAsciiTableOutputDriver(TestAsciiTableOutputParam,
                                 parent.TestAsciiFileOutputDriver):
    r"""Test runner for AsciiTableOutputDriver."""

    def send_file_contents(self):
        r"""Send file contents to driver."""
        for line in self.file_rows:
            self.send_comm.send_nolimit(line)
        self.send_comm.send_nolimit_eof()


class TestAsciiTableOutputDriver_Array(TestAsciiTableOutputParam,
                                       parent.TestAsciiFileOutputDriver):
    r"""Test runner for AsciiTableOutputDriver with array input."""

    def __init__(self, *args, **kwargs):
        super(TestAsciiTableOutputDriver_Array, self).__init__(*args, **kwargs)
        self.inst_kwargs['as_array'] = True
        names = [backwards.bytes2unicode(n) for n in self.field_names]
        units = [backwards.bytes2unicode(n) for n in self.field_units]
        self.inst_kwargs['column_names'] = names
        self.inst_kwargs['column_units'] = units
        self.inst_kwargs['use_astropy'] = False

    @property
    def send_comm_kwargs(self):
        r"""dict: Keyword arguments for send comm."""
        out = super(TestAsciiTableOutputDriver_Array, self).send_comm_kwargs
        out['serializer_kwargs']['as_array'] = True
        return out

    def send_file_contents(self):
        r"""Send file contents to driver."""
        self.send_comm.send_nolimit(self.file_array)
        self.send_comm.send_nolimit_eof()
