from yggdrasil.examples.tests import ExampleTstBase


class TestExampleTimesync1(ExampleTstBase):
    r"""Test the timesync1 example."""

    example_name = 'timesync1'
    env = {'TIMESYNC_TSTEP_A': '20', 'TIMESYNC_TSTEP_B': '3'}
