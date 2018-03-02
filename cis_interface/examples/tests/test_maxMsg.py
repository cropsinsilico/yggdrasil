from cis_interface.examples.tests import TestExample


class TestExampleMaxMsg(TestExample):
    r"""Test the MaxMsg example."""

    def __init__(self, *args, **kwargs):
        super(TestExampleMaxMsg, self).__init__(*args, **kwargs)
        self._name = 'maxMsg'
