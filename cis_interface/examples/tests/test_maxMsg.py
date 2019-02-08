from cis_interface.tests import long_running
from cis_interface.examples.tests import TestExample


@long_running
class TestExampleMaxMsg(TestExample):
    r"""Test the MaxMsg example."""

    example_name = 'maxMsg'
