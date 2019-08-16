import yggdrasil.drivers.tests.test_InterpretedModelDriver as parent


class TestRModelParam(parent.TestInterpretedModelParam):
    r"""Test parameters for RModelDriver."""

    driver = "RModelDriver"


class TestRModelDriverNoInit(TestRModelParam,
                             parent.TestInterpretedModelDriverNoInit):
    r"""Test runner for RModelDriver without init."""

    def test_is_library_installed(self):
        r"""Test is_library_installed for invalid library."""
        self.assert_equal(
            self.import_cls.is_library_installed('invalid_unicorn'),
            False)


class TestRModelDriverNoStart(TestRModelParam,
                              parent.TestInterpretedModelDriverNoStart):
    r"""Test runner for RModelDriver without start."""
    pass


class TestRModelDriver(TestRModelParam,
                       parent.TestInterpretedModelDriver):
    r"""Test runner for RModelDriver."""
    pass
