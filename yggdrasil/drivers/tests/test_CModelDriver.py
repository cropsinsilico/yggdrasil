import os
import yggdrasil.drivers.tests.test_CompiledModelDriver as parent


class TestCModelParam(parent.TestCompiledModelParam):
    r"""Test parameters for CModelDriver."""

    driver = 'CModelDriver'
    
    def __init__(self, *args, **kwargs):
        super(TestCModelParam, self).__init__(*args, **kwargs)
        script_dir = os.path.dirname(self.src[0])
        self.args = [self.args[0], '1']
        self._inst_kwargs.update(compiler_flags=['-I' + script_dir],
                                 linker_flags=['-L' + script_dir])


class TestCModelDriverNoStart(TestCModelParam,
                              parent.TestCompiledModelDriverNoStart):
    r"""Test runner for CModelDriver without start."""
    pass


class TestCModelDriver(TestCModelParam, parent.TestCompiledModelDriver):
    r"""Test runner for CModelDriver."""
    pass
