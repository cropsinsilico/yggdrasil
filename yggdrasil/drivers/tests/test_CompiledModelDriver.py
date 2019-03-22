import yggdrasil.drivers.tests.test_ModelDriver as parent


class TestCompiledModelParam(parent.TestModelParam):
    r"""Test parameters for basic CompiledModelDriver class."""

    driver = 'CompiledModelDriver'
    
    def __init__(self, *args, **kwargs):
        super(TestCompiledModelParam, self).__init__(*args, **kwargs)
        self.attr_list += ['source_files']
        for k in ['compiler', 'linker', 'archiver']:
            self.attr_list += [k, '%s_flags' % k, '%s_tool' % k]
        if self.src is not None:
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
