import yggdrasil.drivers.tests.test_ExecutableModelDriver as parent


class TestOSRModelParam(parent.TestExecutableModelParam):
    r"""Test parameters for OSRModelDriver."""

    driver = "OSRModelDriver"

    @property
    def inst_kwargs(self):
        r"""dict: Keyword arguments for creating a class instance."""
        out = super(TestOSRModelParam, self).inst_kwargs
        out.update(timesync={'name': 'timesync',
                             'inputs': ['specificLeafArea'],
                             'outputs': ['ovar1', 'ovar2']},
                   copy_xml_to_osr=True)
        return out


class TestOSRModelDriverNoInit(TestOSRModelParam,
                               parent.TestExecutableModelDriverNoInit):
    r"""Test runner for OSRModelDriver without init."""
    pass
        

class TestOSRModelDriverNoStart(TestOSRModelParam,
                                parent.TestExecutableModelDriverNoStart):
    r"""Test runner for OSRModelDriver without start."""
    pass


class TestOSRModelDriver(TestOSRModelParam,
                         parent.TestExecutableModelDriver):
    r"""Test runner for OSRModelDriver."""
    pass
