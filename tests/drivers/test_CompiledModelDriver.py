import pytest
from tests import TestClassBase as base_class
from tests.drivers.test_ModelDriver import TestModelDriver as model_base_class
import os
import copy
import shutil
from yggdrasil import platform, constants
from yggdrasil.config import ygg_cfg
from yggdrasil.drivers import CompiledModelDriver
from yggdrasil.components import import_component


def test_get_compatible_tool():
    r"""Test get_compatible_tool when default provided."""
    with pytest.raises(ValueError):
        CompiledModelDriver.get_compatible_tool('invalid', 'compiler', 'c')
    assert(CompiledModelDriver.get_compatible_tool(
        'invalid', 'compiler', 'c', default=None) is None)


def test_get_compilation_tool_registry():
    r"""Test errors raised by get_compilation_tool_registry."""
    with pytest.raises(ValueError):
        CompiledModelDriver.get_compilation_tool_registry('invalid')

    
def test_find_compilation_tool():
    r"""Test errors raised by find_compilation_tool."""
    with pytest.raises(RuntimeError):
        CompiledModelDriver.find_compilation_tool('archiver', 'cmake')


def test_get_alternate_class():
    r"""Test get_alternate_class."""
    import_component('model', subtype='c')
    gcc = CompiledModelDriver.get_compilation_tool('compiler', 'gcc')
    gcc.get_alternate_class(toolname='clang')
    

def test_get_compilation_tool():
    r"""Test get_compilation_tool for different name variations."""
    from yggdrasil.drivers.CModelDriver import CModelDriver
    if CModelDriver.is_language_installed():
        tooltype = 'compiler'
        out = CModelDriver.get_tool('compiler').__class__
        toolname = out.toolname.lower()
        toolpath = os.path.join('somedir', toolname)
        toolfile = toolpath + '.exe'
        vals = [toolpath, toolfile]
        if platform._is_win:
            vals += [toolname.upper(), toolfile.upper()]
        for v in vals:
            assert(CompiledModelDriver.get_compilation_tool(tooltype, v) == out)
        with pytest.raises(ValueError):
            CompiledModelDriver.get_compilation_tool('compiler', 'invalid')
    else:
        with pytest.raises(NotImplementedError):
            CModelDriver.get_tool('compiler')
        assert(CModelDriver.get_tool(
            'compiler', default='invalid') == 'invalid')
    assert(CompiledModelDriver.get_compilation_tool('compiler', 'invalid',
                                                    default='invalid')
           == 'invalid')


def test_CompilationToolBase():
    r"""Test error in CompilationToolBase."""
    with pytest.raises(RuntimeError):
        CompiledModelDriver.CompilationToolBase(invalid='invalid')


class DummyCompiler(CompiledModelDriver.CompilerBase):
    r"""Dummy test class."""
    _dont_register = True
    toolname = 'dummy12345'
    languages = ['dummy']
    search_path_envvar = ['PATH']
    _language_ext = ['.c']
    default_linker = False
    default_archiver = None
    combine_with_linker = True
    compile_only_flag = None
    linker_attributes = {'_dont_register': True}


class TestCompilationTool(base_class):
    r"""Test class for compilation tools."""

    _mod = 'yggdrasil.drivers.CompiledModelDriver'
    _cls = 'CompilationToolBase'

    def test_append_flags(self, python_class):
        r"""Test append_flags."""
        with pytest.raises(ValueError):
            python_class.append_flags([], '-T', 'bye', invalid='invalid')
        with pytest.raises(ValueError):
            python_class.append_flags(['-Thello'], '-T%s', 'bye',
                                      no_duplicates=True)
        kws_list = [((['a', 'b', 'c'], '0', '1'), {'prepend': True},
                     ['0', '1', 'a', 'b', 'c']),
                    ((['a', 'b', 'c'], '0', '1'), {'position': -1},
                     ['a', 'b', 'c', '0', '1']),
                    ((['a', 'b', 'c'], '0', '1'), {'position': -2},
                     ['a', 'b', '0', '1', 'c'])]
        for (out, key, val), kws, res in kws_list:
            python_class.append_flags(out, key, val, **kws)
            assert(out == res)

    def test_create_flag(self, python_class):
        r"""Test create_flag."""
        test_args = [({'key': '-T%s'}, ['a', 'b', 'c'], ['-Ta', '-Tb', '-Tc']),
                     ('-set-this', True, ['-set-this']),
                     ('-set-this', False, []),
                     ('-set-this', None, [])]
        for (key, val, out) in test_args:
            assert(python_class.create_flag(key, val) == out)

    def test_not_implemented(self):
        r"""Test raising of NotImplementedErrors for incomplete classes."""
        pass

    def test_get_flags(self, python_class):
        r"""Test get_flags."""
        assert(python_class.get_flags(flags='hello') == ['hello'])

    def test_get_search_path(self, class_name, python_class):
        r"""Test get_search_path."""
        if class_name == 'CompilationToolBase':
            with pytest.raises(NotImplementedError):
                python_class.get_search_path()
        else:
            python_class.get_search_path(libtype='include')
            python_class.get_search_path(libtype='shared')
            python_class.get_search_path(libtype='static')
            
    def test_get_executable_command(self, python_class):
        r"""Test get_executable_command."""
        if python_class.toolname is None:
            with pytest.raises(NotImplementedError):
                python_class.get_executable_command([])
            

class TestDummyCompiler(TestCompilationTool):
    r"""Test class for DummyCompiler."""

    _mod = 'tests.drivers.test_CompiledModelDriver'
    _cls = 'DummyCompiler'

    @pytest.fixture
    def instance_kwargs(self):
        r"""Keyword arguments for a new instance of the tested class."""
        return dict(linker=False)

    def test_call(self, python_class):
        r"""Test call."""
        out = 'test123'
        assert(not shutil.which(python_class.toolname))
        assert(not (os.path.isfile(out) or os.path.isdir(out)))
        with pytest.raises(RuntimeError):
            python_class.call('args', out=out, dont_link=True)

    def test_linker(self, python_class):
        r"""Test linker."""
        assert(python_class.linker() is False)

    def test_archiver(self, python_class):
        r"""Test archiver."""
        with pytest.raises(RuntimeError):
            python_class.archiver()
        
    def test_get_flags(self, python_class):
        r"""Test get_flags."""
        assert(python_class.get_flags(flags='hello', libtype='object')
               == ['hello', '-DWITH_YGGDRASIL'])
        
    def test_get_executable_command(self, python_class):
        r"""Test get_executable_command."""
        python_class.get_executable_command([], dont_link=True)


class TestCompiledModelDriver(model_base_class):
    r"""Test runner for CompiledModelDriver."""

    parametrize_language = constants.LANGUAGES['compiled']

    @pytest.fixture(scope="class")
    def compiler(self, python_class):
        r"""Compiler for the class."""
        return python_class.get_tool('compiler')
        
    @pytest.fixture
    def instance_args(self, name, source, testing_options, compiler,
                      is_installed):
        r"""Arguments for a new instance of the tested class."""
        return tuple(
            [name, ([compiler.get_output_file(source[0])]
                    + copy.deepcopy(
                        testing_options.get('args', [])))])

    @pytest.fixture
    def instance_kwargs(self, testing_options, timeout, working_dir,
                        polling_interval, namespace, source):
        r"""Keyword arguments for a new instance of the tested class."""
        return dict(
            copy.deepcopy(
                testing_options.get('kwargs', {})),
            yml={'working_dir': working_dir},
            timeout=timeout, sleeptime=polling_interval,
            namespace=namespace, source_files=source)
    
    @pytest.fixture
    def run_model_instance_kwargs(self):
        r"""dict: Additional keyword arguments that should be used in calls
        to run_model_instance"""
        return {'skip_compile': False}
        
    def test_build(self, python_class):
        r"""Test building libraries as a shared/static library or object files."""
        # Finish on the default libtype
        order = ['shared', 'object', 'static']
        order.remove(CompiledModelDriver._default_libtype)
        order.append(CompiledModelDriver._default_libtype)
        for libtype in ['shared', 'object', 'static']:
            python_class.compile_dependencies(
                libtype=libtype, overwrite=True)
            if libtype == 'shared':
                python_class.compile_dependencies(
                    libtype=libtype, overwrite=False)
            python_class.cleanup_dependencies(libtype=libtype)

    def test_get_tool(self, python_class):
        r"""Test other methods of calling get_tool."""
        python_class.get_tool('compiler', return_prop='name')
        python_class.get_tool('compiler', return_prop='flags')
        with pytest.raises(ValueError):
            python_class.get_tool('compiler', return_prop='invalid')

    def test_get_dependency_info(self, python_class):
        r"""Test get_dependency_info."""
        dep_list = (
            python_class.get_dependency_order(
                python_class.interface_library)
            + list(python_class.external_libraries.keys()))
        for dep in dep_list:
            python_class.get_dependency_info(dep, default='default')
        with pytest.raises(KeyError):
            python_class.get_dependency_info('invalid')
        assert(python_class.get_dependency_info('invalid', default='default')
               == 'default')

    def test_get_dependency_source(self, python_class):
        r"""Test get_dependency_source."""
        dep_list = (
            python_class.get_dependency_order(
                python_class.interface_library)
            + list(python_class.external_libraries.keys()))
        for dep in dep_list:
            python_class.get_dependency_source(dep, default='default')
        with pytest.raises(ValueError):
            python_class.get_dependency_source('invalid')
        assert(python_class.get_dependency_source(__file__) == __file__)
        assert(python_class.get_dependency_source(
            'invalid', default='default') == 'default')

    def test_get_dependency_object(self, python_class):
        r"""Test get_dependency_object."""
        dep_list = (
            python_class.get_dependency_order(
                python_class.interface_library)
            + list(python_class.external_libraries.keys()))
        for dep in dep_list:
            python_class.get_dependency_object(dep, default='default')
        with pytest.raises(ValueError):
            python_class.get_dependency_object('invalid')
        assert(python_class.get_dependency_object(__file__) == __file__)
        assert(python_class.get_dependency_object(
            'invalid', default='default') == 'default')

    def test_get_dependency_library(self, python_class):
        r"""Test get_dependency_library."""
        with pytest.raises(ValueError):
            python_class.get_dependency_library('invalid', libtype='invalid')
        for dep, info in python_class.external_libraries.items():
            libtype_orig = info.get('libtype', None)
            if libtype_orig not in ['static', 'shared']:
                continue
            if libtype_orig == 'static':  # pragma: no cover
                libtype = 'shared'
            else:
                libtype = 'static'
            with pytest.raises(ValueError):
                python_class.get_dependency_library(dep, libtype=libtype)
        with pytest.raises(ValueError):
            python_class.get_dependency_library('invalid')
        assert(python_class.get_dependency_library(__file__) == __file__)
        assert(python_class.get_dependency_library(
            'invalid', default='default') == 'default')

    def test_get_dependency_include_dirs(self, python_class):
        r"""Test get_dependency_include_dirs."""
        with pytest.raises(ValueError):
            python_class.get_dependency_include_dirs('invalid')
        assert(python_class.get_dependency_include_dirs(__file__)
               == [os.path.dirname(__file__)])
        assert(python_class.get_dependency_include_dirs(
            'invalid', default='default') == ['default'])

    def test_get_dependency_order(self, python_class):
        r"""Test get_dependency_order."""
        deps = list(python_class.internal_libraries.keys())
        python_class.get_dependency_order(deps)

    def test_get_flags(self, python_class):
        r"""Test get_flags."""
        compiler = python_class.get_tool('compiler')
        if compiler:
            if ((compiler.combine_with_linker
                 or compiler.no_separate_linking)):
                print(compiler, compiler.get_flags(invalid_kw=True,
                                                   unused_kwargs={},
                                                   libraries=[]))
            else:
                with pytest.raises(ValueError):
                    compiler.get_flags()

    def test_get_linker_flags(self, python_class):
        r"""Test get_linker_flags."""
        if python_class.get_tool('archiver') is False:
            with pytest.raises(RuntimeError):
                python_class.get_linker_flags(libtype='static')
        else:
            python_class.get_linker_flags(libtype='static', for_model=True,
                                          use_library_path_internal=True)
        if getattr(python_class.get_tool('linker'), 'is_dummy', False):
            with pytest.raises(RuntimeError):
                python_class.get_linker_flags(libtype='shared')
        else:
            python_class.get_linker_flags(libtype='shared', for_model=True,
                                          use_library_path=True)
            python_class.get_linker_flags(libtype='shared', for_model=True,
                                          skip_library_libs=True,
                                          use_library_path=True)
            python_class.get_linker_flags(libtype='shared', for_model=True,
                                          skip_library_libs=True,
                                          use_library_path_internal=True)

    def test_executable_command(self, python_class):
        r"""Test executable_command."""
        with pytest.raises(ValueError):
            python_class.executable_command(['test'], exec_type='invalid')
        if python_class.get_tool('compiler').no_separate_linking:
            with pytest.raises(RuntimeError):
                python_class.executable_command(['test'], exec_type='linker')
        else:
            python_class.executable_command(['test'], exec_type='linker')

    def test_compiler_call(self, python_class):
        r"""Test compiler call."""
        tool = python_class.get_tool('compiler')
        assert(tool.call('args', out='test',
                         dry_run=True, skip_flags=True) == '')
        src = [x + tool.get_language_ext()[0] for x in ['args1', 'args2']]
        with pytest.raises(ValueError):
            tool.call(src, out='out1', dont_link=True)
        kwargs = dict(dry_run=True, working_dir=os.getcwd())
        if python_class.language in ['cmake']:
            src = src[:1]
            kwargs['target'] = tool.file2base(src[0])
        tool.call(src, dont_link=True, **kwargs)
        tool.call(src, **kwargs)

    def test_configure(self, python_class):
        r"""Test configuration (presumably after it has already been done)."""
        python_class.configure(ygg_cfg)
        
    def test_get_output_file(self, python_class, source):
        r"""Test get_output_file."""
        tool = python_class.get_tool('compiler')
        fname = source[0]
        tool.get_output_file([fname])

    def test_invalid_function_param2(self, python_class, instance_kwargs):
        r"""Test errors raise during class creation when parameters are invalid."""
        kwargs = copy.deepcopy(instance_kwargs)
        kwargs['name'] = 'test'
        kwargs['args'] = ['test']
        kwargs['function'] = 'invalid'
        kwargs['source_files'] = []
        # With source_files
        if python_class.language_ext:
            kwargs['source_files'] = ['invalid' + python_class.language_ext[0]]
        with pytest.raises(ValueError):
            python_class(**kwargs)
        
    def test_compilers(self, python_class, instance):
        r"""Test available compilers."""
        # Record old tools
        old_tools = {}
        for k in ['compiler', 'linker', 'achiver']:
            old_tools['%s_tool' % k] = getattr(instance,
                                               '%s_tool' % k, None)
        for k in ['compiler_flags', 'linker_flags']:
            old_tools[k] = getattr(instance, k, None)
            setattr(instance, k, [])
        # Compile with each compiler
        for k, v in python_class.get_available_tools('compiler').items():
            if not v.is_installed():
                continue  # pragma: debug
            setattr(instance, 'compiler_tool', v)
            setattr(instance, 'linker_tool', v.linker())
            setattr(instance, 'archiver_tool', v.archiver())
            instance.compile_model(use_ccache=True)
        # Restore the old tools
        for k, v in old_tools.items():
            setattr(instance, k, v)

    def test_compile_model(self, instance, source):
        r"""Test compile model with alternate set of input arguments."""
        fname = source[0]
        with pytest.raises(RuntimeError):
            instance.compile_model(out=os.path.basename(fname),
                                   working_dir=os.path.dirname(fname),
                                   overwrite=True)
        if not instance.is_build_tool:
            instance.compile_model(out=instance.model_file,
                                   overwrite=False)
            assert(os.path.isfile(instance.model_file))
            instance.compile_model(out=instance.model_file,
                                   overwrite=False)
            assert(os.path.isfile(instance.model_file))
            os.remove(instance.model_file)

    def test_call_linker(self, instance):
        r"""Test call_linker with static."""
        out = instance.compile_model(dont_link=True, out=None)
        instance.call_linker(out, for_model=True,
                             working_dir=instance.working_dir,
                             libtype='static')

    def test_parse_arguments(self, python_class, instance):
        r"""Run test to initialize driver using the executable."""
        x = os.path.splitext(instance.source_files[0])[0] + '.out'
        new_inst = python_class('test_name', [x], skip_compile=True)
        assert(new_inst.model_file == x)
        assert(new_inst.source_files == instance.source_files[:1])
