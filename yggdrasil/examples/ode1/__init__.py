import os
import numpy as np
from yggdrasil.communication.AsciiTableComm import AsciiTableComm
from yggdrasil import platform


def get_testing_options():
    r"""Get testing parameters for this example."""
    def read_file(fname):
        x = AsciiTableComm(fname, address=fname,
                           direction='recv', as_array=True)
        return x.recv_array()[1]

    def compare_results(a, b, rtol=1e-5, atol=1e-8):
        try:
            np.testing.assert_allclose(a, b, rtol=rtol, atol=atol)
        except TypeError:
            a2 = a.view(np.float).reshape(a.shape + (-1,))
            b2 = b.view(np.float).reshape(b.shape + (-1,))
            np.testing.assert_allclose(a2, b2, rtol=rtol, atol=atol)

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
