import unittest
import yggdrasil.drivers.tests.test_ExecutableModelDriver as parent


class TestOSRModelParam(parent.TestExecutableModelParam):
    r"""Test parameters for OSRModelDriver."""

    driver = "OSRModelDriver"

    @property
    def inst_kwargs(self):
        r"""dict: Keyword arguments for creating a class instance."""
        out = super(TestOSRModelParam, self).inst_kwargs
        out.update(timesync={'name': 'timesync',
                             'inputs': ['carbonAllocation2Roots'],
                             'outputs': ['carbonAllocation2Roots']},
                   copy_xml_to_osr=True)
        return out

    @unittest.skipIf(True, "Requires partner model.")
    def test_run_model(self, *args, **kwargs):  # pragma: no cover
        r"""Test running script used without debug."""
        pass

    @unittest.skipIf(True, "Requires partner model.")
    def test_valgrind(self, *args, **kwargs):  # pragma: no cover
        pass

    @unittest.skipIf(True, "Requires partner model.")
    def test_strace(self, *args, **kwargs):  # pragma: no cover
        pass


class TestOSRModelDriverNoInit(TestOSRModelParam,
                               parent.TestExecutableModelDriverNoInit):
    r"""Test runner for OSRModelDriver without init."""

    def test_cleanup_dependencies(self):
        r"""Test cleanup_dependencies method."""
        super(TestOSRModelDriverNoInit, self).test_cleanup_dependencies()
        self.import_cls.cleanup_dependencies()
        

class TestOSRModelDriverNoStart(TestOSRModelParam,
                                parent.TestExecutableModelDriverNoStart):
    r"""Test runner for OSRModelDriver without start."""
    pass


class TestOSRModelDriver(TestOSRModelParam,
                         parent.TestExecutableModelDriver):
    r"""Test runner for OSRModelDriver."""
    pass
