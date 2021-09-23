import os


def get_testing_options():
    r"""Get testing parameters for this example."""
    return dict(
        expected_output_files=[
            os.path.join('Output', 'outputB.txt'),
            os.path.join('Output', 'outputC.txt')],
        output_dir=None,
        output_files=['outputB.txt', 'outputC.txt'])
