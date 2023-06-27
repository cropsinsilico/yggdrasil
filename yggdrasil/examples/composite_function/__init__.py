import os


def get_testing_options():
    r"""Get testing parameters for this example."""
    return dict(
        expected_output_files=[
            os.path.join('Output', 'expected.txt')],
        output_dir=None,
        output_files=['output.txt'])
