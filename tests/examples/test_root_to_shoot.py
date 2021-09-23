import os
from yggdrasil.examples.tests import ExampleTstBase


class TestExampleRootToShoot(ExampleTstBase):
    r"""Test the Root to Shoot example."""

    example_name = 'root_to_shoot'

    @property
    def output_dir(self):
        r"""str: Output directory."""
        if self.yamldir is None:  # pragma: debug
            return None
        return os.path.join(self.yamldir, 'Output')

    @property
    def output_files(self):
        r"""list: Output files for the run."""
        outdir = self.output_dir
        filelist = ['root_output.txt',
                    'shoot_output.txt']
        out = [os.path.join(outdir, f) for f in filelist]
        return out

    def check_results(self):
        r"""This should be overridden with checks for the result."""
        pass

    def run_example(self):
        r"""This runs an example in the correct language."""
        if self.output_dir is not None:
            if not os.path.isdir(self.output_dir):
                os.mkdir(self.output_dir)
        super(TestExampleRootToShoot, self).run_example()
