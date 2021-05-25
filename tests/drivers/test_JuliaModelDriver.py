import yggdrasil.drivers.tests.test_InterpretedModelDriver as parent


class TestJuliaModelParam(parent.TestInterpretedModelParam):
    r"""Test parameters for JuliaModelDriver."""

    driver = "JuliaModelDriver"


class TestJuliaModelDriverNoInit(TestJuliaModelParam,
                                 parent.TestInterpretedModelDriverNoInit):
    r"""Test runner for JuliaModelDriver without init."""

    def test_is_library_installed(self):
        r"""Test is_library_installed for invalid library."""
        self.assert_equal(
            self.import_cls.is_library_installed('invalid_unicorn'),
            False)


class TestJuliaModelDriverNoStart(TestJuliaModelParam,
                                  parent.TestInterpretedModelDriverNoStart):
    r"""Test runner for JuliaModelDriver without start."""
    pass


class TestJuliaModelDriver(TestJuliaModelParam,
                           parent.TestInterpretedModelDriver):
    r"""Test runner for JuliaModelDriver."""
    pass
