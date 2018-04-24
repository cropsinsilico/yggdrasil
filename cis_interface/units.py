import pint
from cis_interface import backwards
_ureg = pint.UnitRegistry()
_ureg.define('micro_mole = 1e-6 * mole = uMol = umol')


def is_unit(ustr):
    r"""Determine if a string is a valid unit.

    Args:
        ustr: String representation to test.

    Returns:
        bool: True if the string is a valid unit. False otherwise.

    """
    ustr = backwards.bytes2unicode(ustr)
    if ustr == 'n/a':
        return True
    try:
        _ureg(ustr)
    except pint.errors.UndefinedUnitError:
        return False
    return True
