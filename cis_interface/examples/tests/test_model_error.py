from cis_interface.examples.tests import TestExample


class TestExampleModelError(TestExample):
    r"""Test the model_error example."""

    def __init__(self, *args, **kwargs):
        super(TestExampleModelError, self).__init__(*args, **kwargs)
        self.name = 'model_error'
