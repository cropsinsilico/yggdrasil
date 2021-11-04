import os


def get_testing_options():
    r"""Get testing parameters for this example."""
    return dict(
        output_dir=None,
        input_files=['input.txt'],
        output_files=['output.txt'],
        expected_output_files=[os.path.join('Output', 'expected_output.txt')])
