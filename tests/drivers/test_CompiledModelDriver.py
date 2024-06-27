import pytest
from tests import TestClassBase as base_class
from tests.drivers.test_ModelDriver import TestModelDriver as model_base_class
import os
import copy
import shutil
from yggdrasil import platform, constants, tools
from yggdrasil.config import ygg_cfg
from yggdrasil.drivers import CompiledModelDriver


def test_get_compatible_tool():
    r"""Test get_compatible_tool when default provided."""
    tool_registry = CompiledModelDriver.get_tool_registry()
    with pytest.raises(CompiledModelDriver.InvalidCompilationTool):
        tool_registry.tool('compiler', 'invalid', language='c')
    assert (tool_registry.tool(
        'compiler', 'invalid', language='c', default=None) is None)


def test_find_compilation_tool():
    r"""Test errors raised by find_compilation_tool."""
    with pytest.raises(CompiledModelDriver.InvalidCompilationTool):
        CompiledModelDriver.get_tool_registry().tool('archiver', 'cmake')


def test_get_alternate_class():
    r"""Test get_alternate_class."""
    gcc = CompiledModelDriver.get_tool_registry(
        'c').tool('compiler', 'gcc')
    gcc.get_alternate_class(toolname='clang')
    

def test_get_compilation_tool():
    r"""Test get_compilation_tool for different name variations."""
    from yggdrasil.drivers.CModelDriver import CModelDriver
    tool_registry = CompiledModelDriver.get_tool_registry()
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
            assert tool_registry.tool(tooltype, v) == out
        with pytest.raises(CompiledModelDriver.InvalidCompilationTool):
            tool_registry.tool('compiler', 'invalid')
    else:
        with pytest.raises(NotImplementedError):
            CModelDriver.get_tool('compiler')
        assert (CModelDriver.get_tool(
            'compiler', default='invalid') == 'invalid')
    assert (tool_registry.tool('compiler', 'invalid',
                               default='invalid')
            == 'invalid')


def test_create_windows_import_gcc():
    r"""Test create_windows_import for GNU"""
    from yggdrasil.drivers.CModelDriver import CModelDriver
    gcc = CModelDriver.get_tool('compiler', toolname='gcc',
                                default=None)
    if gcc:
        kws = {'toolname': 'gcc'}
        filetype = 'library'
        if platform._is_win:
            filetype = 'shared'
        dll = CModelDriver.libraries.getfile('python', filetype, **kws)
        if platform._is_win:
            assert dll.endswith('.dll')
        CompiledModelDriver.create_windows_import(dll, for_gnu=True,
                                                  overwrite=True)
    else:
        with pytest.raises(CompiledModelDriver.InvalidCompilationTool):
            CModelDriver.get_tool('compiler', toolname='gcc')


def test_CompilationToolBase():
    r"""Test error in CompilationToolBase."""
    with pytest.raises(RuntimeError):
        CompiledModelDriver.CompilationToolBase(invalid='invalid')


class DummyCompiler(CompiledModelDriver.CompilerBase):
    r"""Dummy test class."""
    # _dont_register = True
    toolname = 'dummy12345'
    languages = ['dummy']
    search_path_envvar = ['PATH']
    _language_ext = ['.c']
    default_linker = False
    default_archiver = None
    no_additional_stages_flag = None
    create_next_stage_tool = True
    # create_next_stage_tool = {
    #     'attributes': {'_dont_register': True},
    # }
    combine_with_next_stage = 'linker'


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
            assert out == res

    def test_create_flag(self, python_class):
        r"""Test create_flag."""
        test_args = [({'key': '-T%s'}, ['a', 'b', 'c'], ['-Ta', '-Tb', '-Tc']),
                     ('-set-this', True, ['-set-this']),
                     ('-set-this', False, []),
                     ('-set-this', None, [])]
        for (key, val, out) in test_args:
            assert python_class.create_flag(key, val) == out

    def test_not_implemented(self):
        r"""Test raising of NotImplementedErrors for incomplete classes."""
        pass

    def test_get_flags(self, python_class):
        r"""Test get_flags."""
        assert python_class.get_flags(flags='hello') == ['hello']

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
            with pytest.raises(CompiledModelDriver.InvalidCompilationTool):
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
        assert not shutil.which(python_class.toolname)
        assert not (os.path.isfile(out) or os.path.isdir(out))
        with pytest.raises(CompiledModelDriver.InvalidCompilationTool):
            python_class.call('args', out=out)

    def test_linker(self, python_class):
        r"""Test linker."""
        with pytest.raises(CompiledModelDriver.InvalidCompilationTool):
            python_class.linker()
        # assert python_class.linker() is False

    def test_archiver(self, python_class):
        r"""Test archiver."""
        with pytest.raises(CompiledModelDriver.InvalidCompilationTool):
            python_class.archiver()
        
    def test_get_flags(self, python_class):
        r"""Test get_flags."""
        from yggdrasil import __version__ as yggver
        yggver = yggver.split('+')[0].split('v')[-1].split('.')
        assert (python_class.get_flags(flags='hello', libtype='object')
                == ['hello'])
        
    def test_get_search_path(self, python_class):
        r"""Test get_search_path."""
        with pytest.raises(CompiledModelDriver.InvalidCompilationTool):
            python_class.get_search_path()

    def test_get_executable_command(self, python_class):
        r"""Test get_executable_command."""
        with pytest.raises(CompiledModelDriver.InvalidCompilationTool):
            python_class.get_executable_command([])


class TestCompiledModelDriver(model_base_class):
    r"""Test runner for CompiledModelDriver."""

    parametrize_language = constants.LANGUAGES['compiled']

    @pytest.fixture(scope="class")
    def basetool(self, python_class):
        r"""Compiler for the class."""
        return python_class.get_tool('basetool')
        
    @pytest.fixture
    def instance_args(self, name, source, testing_options, is_installed):
        r"""Arguments for a new instance of the tested class."""
        return tuple(
            [name, ([source[0]]
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
            namespace=namespace, source_files=source,
            remove_products=True)
    
    @pytest.fixture
    def run_model_instance_kwargs(self):
        r"""dict: Additional keyword arguments that should be used in calls
        to run_model_instance"""
        return {'skip_compile': False, 'overwrite': True}
        
    @pytest.mark.skipif(platform._is_win,
                        reason="No ASAN for Windows MSVC")
    def test_asan_debugger(self, run_model_instance, testing_options,
                           asan_installed):
        r"""Test running with ASAN."""
        if testing_options.get('requires_partner', False):
            pytest.skip("requires partner model to run")
        if not asan_installed:
            pytest.skip("ASAN not installed")
        run_model_instance(with_debugger='asan')
        
    def test_build(self, python_class):
        r"""Test building libraries as a shared/static library or object files."""
        # Finish on the default libtype
        order = ['shared', 'object', 'static']
        order.remove(CompiledModelDriver._default_libtype)
        order.append(CompiledModelDriver._default_libtype)
        for libtype in order:
            python_class.compile_dependencies(
                libtype=libtype, overwrite=True)
            if libtype == CompiledModelDriver._default_libtype:
                python_class.compile_dependencies(
                    libtype=libtype, overwrite=False)
                break
            python_class.cleanup_dependencies(libtype=libtype)

    def test_get_tool(self, python_class):
        r"""Test other methods of calling get_tool."""
        python_class.get_tool('basetool', return_prop='name')
        python_class.get_tool('basetool', return_prop='flags')
        with pytest.raises(ValueError):
            python_class.get_tool('basetool', return_prop='invalid')

    def test_libraries_get(self, python_class):
        r"""Test libraries.get."""
        dep_list = python_class.libraries.keys()
        for dep in dep_list:
            python_class.libraries.get(dep, default='default')
        with pytest.raises(KeyError):
            python_class.libraries.get('invalid')
        assert (python_class.libraries.get('invalid', default='default')
                == 'default')

    def test_libraries_getfile_source(self, python_class):
        r"""Test libraries.getfile for source."""
        dep_list = python_class.libraries.keys()
        for dep in dep_list:
            python_class.libraries.getfile(dep, 'source',
                                           default='default')
        with pytest.raises(KeyError):
            python_class.libraries.getfile('invalid', 'source')
        assert (python_class.libraries.getfile(
            'invalid', 'source', default='default') == 'default')

    def test_libraries_getfile_object(self, python_class):
        r"""Test libraries.getfile for object.."""
        dep_list = python_class.libraries.keys()
        for dep in dep_list:
            python_class.libraries.getfile(dep, 'object',
                                           default='default')
        with pytest.raises(KeyError):
            python_class.libraries.getfile('invalid', 'object')
        assert (python_class.libraries.getfile(
            'invalid', 'object', default='default') == 'default')

    def test_libraries_getfile_library(self, python_class):
        r"""Test libraries.getfile for library."""
        with pytest.raises(KeyError):
            python_class.libraries.getfile(
                'invalid', 'library', libtype='invalid')
        for dep, info in python_class.libraries.external.items():
            libtype_orig = info.get('libtype', None)
            if libtype_orig not in ['static', 'shared']:
                continue
            if libtype_orig == 'static':  # pragma: no cover
                libtype = 'shared'
            else:
                libtype = 'static'
            try:
                python_class.libraries.getfile(dep, libtype)
            except KeyError:
                pass
        with pytest.raises(KeyError):
            python_class.libraries.getfile('invalid', 'library')
        assert (python_class.libraries.getfile(
            'invalid', 'library', default='default') == 'default')

    def test_libraries_getfile_include_dirs(self, python_class):
        r"""Test libraries.getfile for include_dirs."""
        with pytest.raises(KeyError):
            python_class.libraries.getfile('invalid', 'include_dirs')
        assert (python_class.libraries.getfile(
            'invalid', 'include_dirs', default=['default']) == ['default'])

    def test_dependency_order(self, python_class):
        r"""Test dependency_order."""
        if python_class.interface_library:
            dep = python_class.libraries.get(python_class.interface_library)
            dep.dependency_order()

    def test_get_flags(self, python_class):
        r"""Test get_flags."""
        basetool = python_class.get_tool('basetool')
        if basetool:
            print(basetool, basetool.get_flags(invalid_kw=True,
                                               unused_kwargs={},
                                               libraries=[]))

    # def test_get_linker_flags(self, python_class):
    #     r"""Test get_linker_flags."""
    #     if python_class.get_tool('archiver') is False:
    #         with pytest.raises(RuntimeError):
    #             python_class.get_linker_flags(libtype='static')
    #     else:
    #         python_class.get_linker_flags(libtype='static', for_model=True,
    #                                       use_library_path_internal=True)
    #     if getattr(python_class.get_tool('linker'), 'is_dummy', False):
    #         with pytest.raises(RuntimeError):
    #             python_class.get_linker_flags(libtype='shared')
    #     else:
    #         python_class.get_linker_flags(libtype='shared', for_model=True,
    #                                       use_library_path=True)
    #         python_class.get_linker_flags(libtype='shared', for_model=True,
    #                                       skip_library_libs=True,
    #                                       use_library_path=True)
    #         python_class.get_linker_flags(libtype='shared', for_model=True,
    #                                       skip_library_libs=True,
    #                                       use_library_path_internal=True)

    def test_executable_command(self, python_class):
        r"""Test executable_command."""
        with pytest.raises(ValueError):
            python_class.executable_command(['test'], exec_type='invalid')
        basetool = python_class.get_tool('basetool')
        next_tool = basetool.libtype_next_stage.get(
            basetool.get_default_libtype(), None)
        if not next_tool:
            return
        python_class.executable_command(['test'],
                                        no_additional_stages=True)
        python_class.executable_command(['test'],
                                        exec_type=next_tool)

    def test_basetool_call(self, python_class):
        r"""Test basetool call."""
        tool = python_class.get_tool('basetool')
        assert (tool.call('args', out='test',
                          dry_run=True, skip_flags=True) == [''])
        src = [x + tool.get_language_ext()[0] for x in ['args1', 'args2']]
        with pytest.raises(RuntimeError):
            tool.call(src, out='out1')
        kwargs = dict(dry_run=True, working_dir=os.getcwd())
        if python_class.language in ['make']:
            src = src[:1]
            kwargs['target'] = tool.file2base(src[0])
        tool.call(src, **kwargs)

    def test_configure(self, python_class):
        r"""Test configuration (presumably after it has already been done)."""
        python_class.configure(ygg_cfg)
        
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
        
    def test_basetools(self, python_class, instance):
        r"""Test available basetools."""
        # Record old tools
        old_tools = {}
        for k in CompiledModelDriver._tool_types:
            for kk in [f'{k}_tool', f'{k}_flags']:
                old_tools[kk] = getattr(instance, kk, None)
        # Build with each base tool
        for k, v in python_class.get_available_tools('basetool').items():
            if not v.is_installed():
                continue  # pragma: debug
            setattr(instance, f'{python_class.basetool}_tool', v)
            # setattr(instance, 'linker_tool', v.linker())
            # setattr(instance, 'archiver_tool', v.archiver())
            products = tools.IntegrationPathSet()
            instance.build_model(use_ccache=True, products=products)
            products.teardown()
        # Restore the old tools
        for k, v in old_tools.items():
            setattr(instance, k, v)

    def test_build_model(self, instance, source, temporary_products):
        r"""Test build model with alternate set of input arguments."""
        fname = source[0]
        with pytest.raises(RuntimeError):
            # Error raised when output is a source file
            instance.build_model(out=os.path.basename(fname),
                                 working_dir=os.path.dirname(fname),
                                 overwrite=True)
        # if not instance.is_build_tool:
        instance.build_model(out=instance.model_file,
                             overwrite=True,
                             products=temporary_products)
        assert os.path.isfile(instance.model_file)
        instance.build_model(out=instance.model_file,
                             overwrite=False,
                             products=temporary_products)
        assert os.path.isfile(instance.model_file)

    def test_parse_arguments(self, python_class, instance):
        r"""Run test to initialize driver using the executable."""
        x = os.path.splitext(instance.source_files[0])[0] + '.out'
        new_inst = python_class('test_name', [x], skip_compile=True)
        assert new_inst.model_file == x
        assert new_inst.source_files == instance.source_files[:1]
