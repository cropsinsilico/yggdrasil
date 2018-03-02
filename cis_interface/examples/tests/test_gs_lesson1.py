from cis_interface.examples.tests import TestExample


class TestExampleGS1(TestExample):
    r"""Test the Getting Started Lesson 1 example."""

    def __init__(self, *args, **kwargs):
        super(TestExampleGS1, self).__init__(*args, **kwargs)
        self._name = 'gs_lesson1'
