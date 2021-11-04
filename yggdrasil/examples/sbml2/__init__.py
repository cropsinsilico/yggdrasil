import os


def get_testing_options():
    r"""Get testing parameters for this example."""
    return dict(
        input_files='input.txt',
        expected_output_files=[
            os.path.join('Output', f'expected{i}.txt') for i in range(2)],
        output_dir=None,
        output_files=[f'output{i}.txt' for i in range(2)])
