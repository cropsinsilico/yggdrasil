import os


def get_testing_options():
    r"""Get testing parameters for this example."""
    return dict(
        expected_output_files=[
            os.path.join('Output', 'expected.json')],
        output_dir=None,
        output_files=['output.json'])
