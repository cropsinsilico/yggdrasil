import os
from yggdrasil.tests import (
    scripts, assert_raises, assert_equal, requires_language)
import yggdrasil.drivers.tests.test_CompiledModelDriver as parent
from yggdrasil.drivers.MakeModelDriver import MakeModelDriver, MakeCompiler


@requires_language('make', installed='any')
def test_MakeCompiler():
    r"""Test MakeCompiler class."""
    assert_equal(MakeCompiler.get_output_file(None, target='clean'), 'clean')


@requires_language('make', installed=False)
def test_MakeModelDriver_no_C_library():  # pragma: windows
    r"""Test MakeModelDriver error when C library not installed."""
    assert_raises(RuntimeError, MakeModelDriver, 'test', scripts['make'])


@requires_language('make')
def test_MakeModelDriver_error_notarget():
    r"""Test MakeModelDriver error for invalid target."""
    makedir, target = os.path.split(scripts['make'])
    assert_raises(RuntimeError, MakeModelDriver, 'test', 'invalid',
                  makedir=makedir)


@requires_language('make')
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

    def __init__(self, *args, **kwargs):
        super(TestMakeModelDriver, self).__init__(*args, **kwargs)
        # Version specifying makedir in parts
        makedir_parts = os.path.split(self.makedir)
        self._inst_kwargs['working_dir'] = makedir_parts[0]
        self._inst_kwargs['makedir'] = makedir_parts[1]
