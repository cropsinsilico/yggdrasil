import yggdrasil.drivers.tests.test_CModelDriver as parent


class TestCPPModelParam(parent.TestCModelParam):
    r"""Test parameters for CPPModelDriver."""

    driver = 'CPPModelDriver'

    def __init__(self, *args, **kwargs):
        super(TestCPPModelParam, self).__init__(*args, **kwargs)
        self._inst_kwargs['compiler_flags'].append('-std=c++11')
    
    
class TestCPPModelDriverNoStart(TestCPPModelParam,
                                parent.TestCModelDriverNoStart):
    r"""Test runner for CPPModelDriver without start."""
    pass

        
class TestCPPModelDriver(TestCPPModelParam, parent.TestCModelDriver):
    r"""Test runner for CPPModelDriver."""
    pass
