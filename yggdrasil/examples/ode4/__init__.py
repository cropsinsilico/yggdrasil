from packaging import version
from yggdrasil.examples.ode1 import get_testing_options as base


def get_testing_options():
    r"""Get testing parameters for this example."""
    out = base()
    try:
        import sympy
        sympy_ver = version.parse(sympy.__version__)
        # This example hangs indefinitely for sympy 1.10 and 1.11
        if version.parse("1.10") <= sympy_ver < version.parse("1.12"):
            out['skip'] = "sympy >= 1.12 or < 1.10 is required for this example"
    except ImportError:  # pragma: debug
        pass
    return out
