import os
from yggdrasil.examples.tests import ExampleTstBase


class TestExampleTransformedIO(ExampleTstBase):
    r"""Test the transformed_io example."""

    example_name = 'transformed_io'

    @property
    def expected_output_files(self):
        r"""list: Examples of expected output for the run."""
        return [os.path.join(self.yamldir, 'Output', 'outputB.txt'),
                os.path.join(self.yamldir, 'Output', 'outputC.txt')]
        
    @property
    def output_files(self):
        r"""list: Output files for the run."""
        return [os.path.join(self.yamldir, 'outputB.txt'),
                os.path.join(self.yamldir, 'outputC.txt')]
