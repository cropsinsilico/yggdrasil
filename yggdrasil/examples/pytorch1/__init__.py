import os


def get_testing_options():
    r"""Get testing parameters for this example."""
    file_exp = os.path.join('Output', 'expected.txt')
    file_act = 'output.txt'
    
    return dict(
        input_files='input.png',
        expected_output_files=file_exp,
        output_dir=None,
        output_files=[file_act])
