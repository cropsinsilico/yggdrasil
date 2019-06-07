import os
import unittest
from yggdrasil.tests import scripts, assert_raises, assert_equal
import yggdrasil.drivers.tests.test_CompiledModelDriver as parent
from yggdrasil.drivers.MakeModelDriver import MakeModelDriver, MakeCompiler


_driver_installed = MakeModelDriver.is_installed()


def test_MakeCompiler():
    r"""Test MakeCompiler class."""
    assert_equal(MakeCompiler.get_output_file(None, target='clean'), 'clean')


@unittest.skipIf(_driver_installed, "C Library installed")
def test_MakeModelDriver_no_C_library():  # pragma: windows
    r"""Test MakeModelDriver error when C library not installed."""
    assert_raises(RuntimeError, MakeModelDriver, 'test', scripts['make'])


@unittest.skipIf(not _driver_installed, "C Library not installed")
def test_MakeModelDriver_error_notarget():
    r"""Test MakeModelDriver error for invalid target."""
    makedir, target = os.path.split(scripts['make'])
    assert_raises(RuntimeError, MakeModelDriver, 'test', 'invalid',
                  makedir=makedir)


@unittest.skipIf(not _driver_installed, "C Library not installed")
def test_MakeModelDriver_error_nofile():
    r"""Test MakeModelDriver error for missing Makefile."""
    makedir, target = os.path.split(scripts['make'])
    assert_raises(RuntimeError, MakeModelDriver, 'test', 'invalid')


class TestMakeModelParam(parent.TestCompiledModelParam):
    r"""Test parameters for MakeModelDriver."""

    driver = 'MakeModelDriver'
    
    def __init__(self, *args, **kwargs):
        super(TestMakeModelParam, self).__init__(*args, **kwargs)
        self.attr_list += ['target', 'makedir', 'makefile']
        self.makedir, self.target = os.path.split(self.src[0])
        self.makefile = os.path.join(self.makedir, 'Makefile')
        self.args = [self.target]
        self._inst_kwargs['makefile'] = self.makefile
        if 'source_files' in self._inst_kwargs:
            del self._inst_kwargs['source_files']
        

class TestMakeModelDriverNoInit(TestMakeModelParam,
                                parent.TestCompiledModelDriverNoInit):
    r"""Test runner for MakeModelDriver without init."""
    pass


class TestMakeModelDriverNoStart(TestMakeModelParam,
                                 parent.TestCompiledModelDriverNoStart):
    r"""Test runner for MakeModelDriver without start."""
    
    def __init__(self, *args, **kwargs):
        super(TestMakeModelDriverNoStart, self).__init__(*args, **kwargs)
        # Version specifying makedir via working_dir
        self._inst_kwargs['yml']['working_dir'] = self.makedir
        del self._inst_kwargs['makefile']

    def test_compile_model(self):
        r"""Test compile model with alternate set of input arguments."""
        src = [self.target + '.c']
        self.instance.compile_model(target=self.target)
        self.instance.compile_model(source_files=src)
        self.assert_raises(RuntimeError, self.instance.compile_model,
                           source_files=src, target=self.target + 'invalid')
        

class TestMakeModelDriver(TestMakeModelParam, parent.TestCompiledModelDriver):
    r"""Test runner for MakeModelDriver."""
    pass
