import os


def get_testing_options():
    r"""Get testing parameters for this example."""
    return dict(
        expected_output_files=[
            os.path.join('Output', 'outputD.txt')],
        output_dir=None,
        output_files=['outputD.txt'])
