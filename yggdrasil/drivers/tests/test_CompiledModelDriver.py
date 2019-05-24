import os
from yggdrasil.tests import assert_equal, assert_raises
from yggdrasil.drivers import CompiledModelDriver
import yggdrasil.drivers.tests.test_ModelDriver as parent


def test_get_compilation_tool_registry():
    r"""Test errors raised by get_compilation_tool_registry."""
    assert_raises(ValueError, CompiledModelDriver.get_compilation_tool_registry,
                  'invalid')

    
def test_find_compilation_tool():
    r"""Test errors raised by find_compilation_tool."""
    assert_raises(RuntimeError, CompiledModelDriver.find_compilation_tool,
                  'archiver', 'cmake')
    

def test_get_compilation_tool():
    r"""Test get_compilation_tool for different name variations."""
    from yggdrasil.drivers.CModelDriver import CModelDriver
    tooltype = 'compiler'
    out = CModelDriver.get_tool('compiler').__class__
    toolname = out.name.lower()
    toolpath = os.path.join('somedir', toolname)
    toolfile = toolpath + '.exe'
    vals = [toolname.upper(), toolpath, toolfile, toolfile.upper()]
    for v in vals:
        assert_equal(CompiledModelDriver.get_compilation_tool(tooltype, v), out)
    assert_raises(ValueError, CompiledModelDriver.get_compilation_tool,
                  'compiler', 'invalid')


class TestCompiledModelParam(parent.TestModelParam):
    r"""Test parameters for basic CompiledModelDriver class."""

    driver = 'CompiledModelDriver'
    
    def __init__(self, *args, **kwargs):
        super(TestCompiledModelParam, self).__init__(*args, **kwargs)
        self.attr_list += ['source_files']
        for k in ['compiler', 'linker', 'archiver']:
            self.attr_list += [k, '%s_flags' % k, '%s_tool' % k]
        if (self.src is not None) and self.import_cls.is_installed():
            self.args = [self.import_cls.get_tool('compiler').get_output_file(
                self.src[0])]
            self._inst_kwargs['source_files'] = self.src


class TestCompiledModelDriverNoStart(TestCompiledModelParam,
                                     parent.TestModelDriverNoStart):
    r"""Test runner for CompiledModelDriver without start."""

    def test_compilers(self):
        r"""Test available compilers."""
        # Record old tools
        old_tools = {}
        for k in ['compiler', 'linker', 'achiver']:
            old_tools[k] = getattr(self.instance, '%s_tool' % k, None)
        # Compile with each compiler
        for k, v in self.import_cls.get_available_tools('compiler').items():
            if not v.is_installed():
                continue
            setattr(self.instance, 'compiler_tool', v)
            setattr(self.instance, 'linker_tool', v.linker())
            setattr(self.instance, 'archiver_tool', v.archiver())
            self.instance.compile_model()
        # Restore the old tools
        for k, v in old_tools.items():
            setattr(self.instance, '%s_tool' % k, v)

    def test_build_shared(self):
        r"""Test building libraries as shared."""
        self.import_cls.compile_dependencies(libtype='shared', overwrite=True)
        self.import_cls.compile_dependencies(libtype='static', overwrite=True)
        self.import_cls.compile_dependencies(libtype='shared', overwrite=False)

    # Done in driver, but driver not started
    def teardown(self):
        r"""Remove the instance, stoppping it."""
        self.instance.cleanup()
        super(TestCompiledModelDriverNoStart, self).teardown()


class TestCompiledModelDriver(TestCompiledModelParam,
                              parent.TestModelDriver):
    r"""Test runner for CompiledModelDriver."""
    pass
