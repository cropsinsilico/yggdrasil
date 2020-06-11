from yggdrasil.examples.tests import ExampleTstBase


class TestExampleTimesync2(ExampleTstBase):
    r"""Test the timesync2 example."""

    example_name = 'timesync2'
    env = {'TIMESYNC_TSTEP_A': '20', 'TIMESYNC_TSTEP_B': '3'}
