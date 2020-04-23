import unittest
import yggdrasil.drivers.tests.test_InterpretedModelDriver as parent


class TestSBMLModelParam(parent.TestInterpretedModelParam):
    r"""Test parameters for SBMLModelDriver class."""

    driver = 'SBMLModelDriver'
    
    def tests_on_not_installed(self):
        r"""Tests for when the driver is not installed."""
        super(TestSBMLModelParam, self).tests_on_not_installed()
        self.assert_raises(RuntimeError, self.import_cls.language_version)

        
class TestSBMLModelDriverNoInit(TestSBMLModelParam,
                                parent.TestInterpretedModelDriverNoInit):
    r"""Test runner for SBMLModelDriver class without initing the driver."""
    
    def run_model_instance(self, **kwargs):  # pragma: sbml
        r"""Create a driver for a model and run it."""
        # This method of running dosn't work with SBML which requires io
        raise unittest.SkipTest("SBML requires I/O channels to run.")


class TestSBMLModelDriverNoStart(TestSBMLModelParam,
                                 parent.TestInterpretedModelDriverNoStart):
    r"""Test runner for SBMLModelDriver class without starting the driver."""
    pass


class TestSBMLModelDriver(TestSBMLModelParam,
                          parent.TestInterpretedModelDriver):
    r"""Test runner for SBMLModelDriver class."""
    pass
