from yggdrasil.drivers.ODEModelDriver import ODEModelDriver


def test_derivative_regexs():
    r"""Test that regexes identify derivatives."""
    pairs = [('dx/dt = x**2',
              [{'name': 'dx/dt', 't': 't', 'f': 'x', 'n': 1}]),
             ('d^2x/dt^2 = 1 + t',
              [{'name': 'd^2x/dt^2', 't': 't', 'f': 'x', 'n': 2}]),
             ('y\'\'(x) = x + 5',
              [{'name': 'y\'\'(x)', 't': 'x', 'f': 'y', 'n': 2}])]
    for x, y in pairs:
        assert(ODEModelDriver.extract_derivatives(x) == y)
