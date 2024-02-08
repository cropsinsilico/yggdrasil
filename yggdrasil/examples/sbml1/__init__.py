import os


def get_testing_options():
    r"""Get testing parameters for this example."""
    file_exp = os.path.join('Output', 'expected.txt')
    file_act = 'output.txt'
    
    # def validation_function(rootdir=None):
    #     from yggdrasil import serialize
    #     import numpy as np
    #     if rootdir is None:
    #         rootdir = os.path.dirname(__file__)
    #     fname_exp = os.path.join(rootdir, file_exp)
    #     fname_act = os.path.join(rootdir, file_act)
    #     with open(fname_exp, 'rb') as fd:
    #         exp = serialize.table_to_array(fd.read(), comment='#')
    #     with open(fname_act, 'rb') as fd:
    #         act = serialize.table_to_array(fd.read(), comment='#')
    #     assert act.dtype == exp.dtype
    #     np.testing.assert_array_equal(act, exp)
        
    return dict(
        input_files='input.txt',
        expected_output_files=file_exp,
        # skip_check_results=True,
        # validation_function=validation_function,
        output_dir=None,
        output_files=[file_act])
