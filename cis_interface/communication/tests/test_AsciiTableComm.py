from cis_interface.communication.tests import test_AsciiFileComm as parent


class TestAsciiTableComm(parent.TestAsciiFileComm):
    r"""Test for AsciiTableComm communication class."""
    def __init__(self, *args, **kwargs):
        super(TestAsciiTableComm, self).__init__(*args, **kwargs)
        self.comm = 'AsciiTableComm'
        self.attr_list += ['as_array']

    @property
    def send_inst_kwargs(self):
        r"""dict: Keyword arguments for send instance."""
        out = super(TestAsciiTableComm, self).send_inst_kwargs
        out['format_str'] = self.fmt_str
        return out

    @property
    def msg_short(self):
        r"""str: Always use file lines as message."""
        return self.file_lines[0]
    
    @property
    def msg_long(self):
        r"""str: Always use file lines as message."""
        return self.file_lines[0]
        

class TestAsciiTableComm_AsArray(TestAsciiTableComm):
    r"""Test for AsciiTableComm communication class."""

    @property
    def send_inst_kwargs(self):
        r"""dict: Keyword arguments for send instance."""
        out = super(TestAsciiTableComm_AsArray, self).send_inst_kwargs
        out['as_array'] = True
        return out

    @property
    def msg_short(self):
        r"""str: Always use file bytes as message."""
        return self.file_bytes
    
    @property
    def msg_long(self):
        r"""str: Always use file bytes as message."""
        return self.file_bytes
