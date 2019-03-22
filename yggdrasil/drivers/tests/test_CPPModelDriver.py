import yggdrasil.drivers.tests.test_CModelDriver as parent


class TestCPPModelParam(parent.TestCModelParam):
    r"""Test parameters for CPPModelDriver."""

    driver = 'CPPModelDriver'

    
class TestCPPModelDriverNoStart(TestCPPModelParam,
                                parent.TestCModelDriverNoStart):
    r"""Test runner for CPPModelDriver without start."""
    pass

        
class TestCPPModelDriver(TestCPPModelParam, parent.TestCModelDriver):
    r"""Test runner for CPPModelDriver."""
    pass
