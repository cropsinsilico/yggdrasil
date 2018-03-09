from cis_interface.examples.tests import TestExample


class TestExampleGS2(TestExample):
    r"""Test the Getting Started Lesson 2 example."""

    def __init__(self, *args, **kwargs):
        super(TestExampleGS2, self).__init__(*args, **kwargs)
        self._name = 'gs_lesson2'
