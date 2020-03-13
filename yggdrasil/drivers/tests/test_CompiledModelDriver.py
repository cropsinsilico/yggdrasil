import os
from yggdrasil.config import ygg_cfg
from yggdrasil.tests import assert_equal, assert_raises, YggTestClass
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
    if CModelDriver.is_language_installed():
        tooltype = 'compiler'
        out = CModelDriver.get_tool('compiler').__class__
        toolname = out.toolname.lower()
        toolpath = os.path.join('somedir', toolname)
        toolfile = toolpath + '.exe'
        vals = [toolname.upper(), toolpath, toolfile, toolfile.upper()]
        for v in vals:
            assert_equal(CompiledModelDriver.get_compilation_tool(tooltype, v), out)
        assert_raises(ValueError, CompiledModelDriver.get_compilation_tool,
                      'compiler', 'invalid')
    # else:
    #     assert_raises(NotImplementedError, CModelDriver.get_tool, 'compiler')
    #     assert_equal(CModelDriver.get_tool(
    #         'compiler', default='invalid'), 'invalid')
    assert_equal(CompiledModelDriver.get_compilation_tool('compiler', 'invalid',
                                                          default='invalid'), 'invalid')


def test_CompilationToolBase():
    r"""Test error in CompilationToolBase."""
    assert_raises(RuntimeError, CompiledModelDriver.CompilationToolBase,
                  invalid='invalid')


class DummyCompiler(CompiledModelDriver.CompilerBase):
    r"""Dummy test class."""
    _dont_register = True
    toolname = 'dummy'
    languages = ['dummy']
    search_path_env = 'PATH'
    _language_ext = ['.c']
    default_linker = False
    default_archiver = None
    combine_with_linker = True
    compile_only_flag = None


class TestCompilationTool(YggTestClass):
    r"""Test class for compilation tools."""

    _mod = 'yggdrasil.drivers.CompiledModelDriver'
    _cls = 'CompilationToolBase'

    def test_append_flags(self):
        r"""Test append_flags."""
        self.assert_raises(ValueError, self.import_cls.append_flags,
                           [], '-T', 'bye', invalid='invalid')
        self.assert_raises(ValueError, self.import_cls.append_flags,
                           ['-Thello'], '-T%s', 'bye', no_duplicates=True)
        kws_list = [((['a', 'b', 'c'], '0', '1'), {'prepend': True},
                     ['0', '1', 'a', 'b', 'c']),
                    ((['a', 'b', 'c'], '0', '1'), {'position': -1},
                     ['a', 'b', 'c', '0', '1']),
                    ((['a', 'b', 'c'], '0', '1'), {'position': -2},
                     ['a', 'b', '0', '1', 'c'])]
        for (out, key, val), kws, res in kws_list:
            self.import_cls.append_flags(out, key, val, **kws)
            self.assert_equal(out, res)

    def test_create_flag(self):
        r"""Test create_flag."""
        test_args = [({'key': '-T%s'}, ['a', 'b', 'c'], ['-Ta', '-Tb', '-Tc']),
                     ('-set-this', True, ['-set-this']),
                     ('-set-this', False, []),
                     ('-set-this', None, [])]
        for (key, val, out) in test_args:
            self.assert_equal(self.import_cls.create_flag(key, val), out)

    def test_not_implemented(self):
        r"""Test raising of NotImplementedErrors for incomplete classes."""
        pass

    def test_get_flags(self):
        r"""Test get_flags."""
        self.assert_equal(self.import_cls.get_flags(flags='hello'), ['hello'])

    def test_get_search_path(self):
        r"""Test get_search_path."""
        if self._cls == 'CompilationToolBase':
            self.assert_raises(NotImplementedError, self.import_cls.get_search_path)
        else:
            self.import_cls.get_search_path()
            
    def test_get_executable_command(self):
        r"""Test get_executable_command."""
        if self.import_cls.toolname is None:
            self.assert_raises(NotImplementedError,
                               self.import_cls.get_executable_command, [])
            

class TestDummyCompiler(TestCompilationTool):
    r"""Test class for DummyCompiler."""

    _mod = 'yggdrasil.drivers.tests.test_CompiledModelDriver'
    _cls = 'DummyCompiler'

    def __init__(self, *args, **kwargs):
        super(TestDummyCompiler, self).__init__(*args, **kwargs)
        self._inst_kwargs['linker'] = False

    def test_call(self):
        r"""Test call."""
        self.assert_raises(RuntimeError, self.import_cls.call, 'args',
                           out='test', dont_link=True)

    def test_linker(self):
        r"""Test linker."""
        self.assert_equal(self.import_cls.linker(), False)

    def test_archiver(self):
        r"""Test archiver."""
        self.assert_raises(RuntimeError, self.import_cls.archiver)
        
    def test_get_flags(self):
        r"""Test get_flags."""
        self.assert_equal(self.import_cls.get_flags(flags='hello',
                                                    libtype='object'), ['hello'])
        
    def test_get_executable_command(self):
        r"""Test get_executable_command."""
        self.import_cls.get_executable_command([], dont_link=True)
        

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


class TestCompiledModelDriverNoInit(TestCompiledModelParam,
                                    parent.TestModelDriverNoInit):
    r"""Test runner for CompiledModelDriver without creating an instance."""
    
    def test_build(self):
        r"""Test building libraries as a shared/static library or object files."""
        for libtype in ['shared', 'object', 'static']:
            self.import_cls.compile_dependencies(
                libtype=libtype, overwrite=True)
            if libtype == 'shared':
                self.import_cls.compile_dependencies(
                    libtype=libtype, overwrite=False)
            self.import_cls.cleanup_dependencies(libtype=libtype)

    def test_get_tool(self):
        r"""Test other methods of calling get_tool."""
        self.import_cls.get_tool('compiler', return_prop='name')
        self.import_cls.get_tool('compiler', return_prop='flags')
        self.assert_raises(ValueError, self.import_cls.get_tool, 'compiler',
                           return_prop='invalid')

    def test_get_dependency_source(self):
        r"""Test get_dependency_source."""
        dep_list = (list(self.import_cls.external_libraries.keys())
                    + list(self.import_cls.internal_libraries.keys()))
        for dep in dep_list:
            self.import_cls.get_dependency_source(dep, default='default')
        self.assert_raises(ValueError, self.import_cls.get_dependency_source,
                           'invalid')
        self.assert_equal(self.import_cls.get_dependency_source(__file__),
                          __file__)
        self.assert_equal(self.import_cls.get_dependency_source(
            'invalid', default='default'), 'default')

    def test_get_dependency_library(self):
        r"""Test get_dependency_library."""
        self.assert_raises(ValueError, self.import_cls.get_dependency_library,
                           'invalid', libtype='invalid')
        for dep, info in self.import_cls.external_libraries.items():
            libtype_orig = info.get('libtype', None)
            if libtype_orig not in ['static', 'shared']:
                continue
            if libtype_orig == 'static':  # pragma: no cover
                libtype = 'shared'
            else:
                libtype = 'static'
            self.assert_raises(ValueError, self.import_cls.get_dependency_library,
                               dep, libtype=libtype)
        self.assert_raises(ValueError, self.import_cls.get_dependency_library,
                           'invalid')
        self.assert_equal(self.import_cls.get_dependency_library(__file__),
                          __file__)
        self.assert_equal(self.import_cls.get_dependency_library(
            'invalid', default='default'), 'default')

    def test_get_dependency_include_dirs(self):
        r"""Test get_dependency_include_dirs."""
        self.assert_raises(ValueError, self.import_cls.get_dependency_include_dirs,
                           'invalid')
        self.assert_equal(self.import_cls.get_dependency_include_dirs(__file__),
                          [os.path.dirname(__file__)])
        self.assert_equal(self.import_cls.get_dependency_include_dirs(
            'invalid', default='default'), ['default'])

    def test_get_dependency_order(self):
        r"""Test get_dependency_order."""
        deps = list(self.import_cls.internal_libraries.keys())
        self.import_cls.get_dependency_order(deps)

    def test_get_flags(self):
        r"""Test get_flags."""
        compiler = self.import_cls.get_tool('compiler')
        if compiler:
            if ((compiler.combine_with_linker
                 or compiler.no_separate_linking)):
                print(compiler, compiler.get_flags(invalid_kw=True,
                                                   unused_kwargs={},
                                                   libraries=[]))
            else:
                self.assert_raises(ValueError, compiler.get_flags)

    def test_get_linker_flags(self):
        r"""Test get_linker_flags."""
        if self.import_cls.get_tool('archiver') is False:
            self.assert_raises(RuntimeError, self.import_cls.get_linker_flags,
                               libtype='static')
        else:
            self.import_cls.get_linker_flags(libtype='static', for_model=True,
                                             use_library_path_internal=True)
        if getattr(self.import_cls.get_tool('linker'), 'is_dummy', False):
            self.assert_raises(RuntimeError, self.import_cls.get_linker_flags,
                               libtype='shared')
        else:
            self.import_cls.get_linker_flags(libtype='shared', for_model=True,
                                             use_library_path=True)
            self.import_cls.get_linker_flags(libtype='shared', for_model=True,
                                             skip_library_libs=True,
                                             use_library_path=True)
            self.import_cls.get_linker_flags(libtype='shared', for_model=True,
                                             skip_library_libs=True,
                                             use_library_path_internal=True)

    def test_executable_command(self):
        r"""Test executable_command."""
        self.assert_raises(ValueError, self.import_cls.executable_command, ['test'],
                           exec_type='invalid')
        if self.import_cls.get_tool('compiler').no_separate_linking:
            self.assert_raises(RuntimeError, self.import_cls.executable_command,
                               ['test'], exec_type='linker')
        else:
            self.import_cls.executable_command(['test'], exec_type='linker')

    def test_compiler_call(self):
        r"""Test compiler call."""
        tool = self.import_cls.get_tool('compiler')
        self.assert_equal(tool.call('args', out='test',
                                    dry_run=True, skip_flags=True), '')
        src = [x + tool.get_language_ext()[0] for x in ['args1', 'args2']]
        self.assert_raises(ValueError, tool.call, src,
                           out='out1', dont_link=True)
        kwargs = dict(dry_run=True, working_dir=os.getcwd())
        if self.import_cls.language in ['cmake']:
            src = src[:1]
            kwargs['target'] = tool.file2base(src[0])
        tool.call(src, dont_link=True, **kwargs)
        tool.call(src, **kwargs)

    def test_configure(self):
        r"""Test configuration (presumably after it has already been done)."""
        self.import_cls.configure(ygg_cfg)
        
    def test_get_output_file(self):
        r"""Test get_output_file."""
        tool = self.import_cls.get_tool('compiler')
        fname = self.src[0]
        tool.get_output_file([fname])

    def test_invalid_function_param(self):
        r"""Test errors raise during class creation when parameters are invalid."""
        super(TestCompiledModelDriverNoInit, self).test_invalid_function_param()
        kwargs = dict(self.inst_kwargs)
        kwargs['name'] = 'test'
        kwargs['args'] = ['test']
        kwargs['function'] = 'invalid'
        kwargs['source_files'] = []
        # With source_files
        if self.import_cls.language_ext:
            kwargs['source_files'] = ['invalid' + self.import_cls.language_ext[0]]
        self.assert_raises(ValueError, self.import_cls, **kwargs)
        

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
            if (not v.is_installed()) or getattr(v, 'is_build_tool', False):
                continue
            setattr(self.instance, 'compiler_tool', v)
            setattr(self.instance, 'linker_tool', v.linker())
            setattr(self.instance, 'archiver_tool', v.archiver())
            self.instance.compile_model()
        # Restore the old tools
        for k, v in old_tools.items():
            setattr(self.instance, '%s_tool' % k, v)

    def test_compile_model(self):
        r"""Test compile model with alternate set of input arguments."""
        fname = self.src[0]
        self.assert_raises(RuntimeError, self.instance.compile_model,
                           out=os.path.basename(fname),
                           working_dir=os.path.dirname(fname),
                           overwrite=True)
        
    # Done in driver, but driver not started
    def teardown(self):
        r"""Remove the instance, stoppping it."""
        self.instance.cleanup()
        super(TestCompiledModelDriverNoStart, self).teardown()


class TestCompiledModelDriver(TestCompiledModelParam,
                              parent.TestModelDriver):
    r"""Test runner for CompiledModelDriver."""
    pass
