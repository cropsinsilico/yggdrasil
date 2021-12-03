import os
import numpy as np
from yggdrasil import serialize, platform


def get_testing_options():
    r"""Get testing parameters for this example."""
    def read_file(fname):
        with open(fname, 'rb') as fd:
            return serialize.table_to_array(fd.read(), comment='#')
        
    def compare_results(a, b):
        np.testing.assert_allclose(a, b, rtol=1e-5, atol=1e-8)
    out = dict(
        input_files='input.txt',
        read_file=read_file,
        compare_results=compare_results,
        expected_output_files=os.path.join('Output', 'expected.txt'),
        output_dir=None,
        output_files=['output.txt'])
    if platform._is_win:  # pragma: windows
        # Default on windows is often 'cp1252', which will be incorrect for
        # the symbols in ode6 (which are 'utf-8')
        out['runner_kwargs'] = {'yaml_encoding': 'utf-8'}
    return out
