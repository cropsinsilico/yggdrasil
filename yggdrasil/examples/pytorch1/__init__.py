import os


def get_testing_options():
    r"""Get testing parameters for this example."""
    file_exp = os.path.join('Output', 'expected.txt')
    file_act = 'output.txt'

    def validation_function():
        from yggdrasil import serialize
        import numpy as np
        fname_exp = os.path.join(os.path.dirname(__file__), file_exp)
        fname_act = os.path.join(os.path.dirname(__file__), file_act)
        with open(fname_exp, 'rb') as fd:
            exp = serialize.table_to_array(fd.read(), comment='#')
        with open(fname_act, 'rb') as fd:
            act = serialize.table_to_array(fd.read(), comment='#')
        assert act.dtype == exp.dtype
        np.testing.assert_allclose(act, exp, rtol=1.e-05)
    
    return dict(
        skip_check_results=True,
        validation_function=validation_function,
        input_files='input.png',
        expected_output_files=file_exp,
        output_dir=None,
        output_files=[file_act])
