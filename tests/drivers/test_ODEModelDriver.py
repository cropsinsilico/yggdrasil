from yggdrasil.drivers.ODEModelDriver import ODEModel


def test_derivative_regexs():
    r"""Test that regexes identify derivatives."""
    pairs = [
        ('dx/dt = x**2',
         [{'name': 'dx/dt', 't': 't', 'f': 'x', 'n': 1, 'tval': None}]),
        ('d^2x/dt^2 = 1 + t',
         [{'name': 'd^2x/dt^2', 't': 't', 'f': 'x', 'n': 2, 'tval': None}]),
        ('y\'\'(x) = x + 5',
         [{'name': 'y\'\'(x)', 't': 'x', 'f': 'y', 'n': 2, 'tval': 'x'}])]
    for x, y in pairs:
        assert(ODEModel.extract_derivatives(x) == y)
