import yggdrasil.drivers.tests.test_InterpretedModelDriver as parent


class TestPythonModelParam(parent.TestInterpretedModelParam):
    r"""Test parameters for PythonModelDriver."""

    driver = "PythonModelDriver"


class TestPythonModelDriverNoInit(TestPythonModelParam,
                                  parent.TestInterpretedModelDriverNoInit):
    r"""Test runner for PythonModelDriver without init."""
    
    def test_write_model_wrapper(self):
        r"""Test writing a model based on yaml parameters."""
        inputs = [{'name': 'a', 'type': 'bytes', 'outside_loop': True},
                  {'name': 'b', 'type': {'type': 'int', 'precision': 64}}]
        outputs = [{'name': 'y', 'type': {'type': 'float', 'precision': 32}},
                   {'name': 'z', 'type': 'bytes', 'outside_loop': True}]
        self.import_cls.write_model_wrapper(None, 'test',
                                            inputs=inputs,
                                            outputs=outputs)
        super(TestPythonModelDriverNoInit, self).test_write_model_wrapper()
        

class TestPythonModelDriverNoStart(TestPythonModelParam,
                                   parent.TestInterpretedModelDriverNoStart):
    r"""Test runner for PythonModelDriver without start."""
    pass


class TestPythonModelDriver(TestPythonModelParam,
                            parent.TestInterpretedModelDriver):
    r"""Test runner for PythonModelDriver."""
    pass
