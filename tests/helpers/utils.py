import logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class MagicTestError(Exception):
    r"""Special exception for testing."""
    pass


def magic_error_replacement(*args, **kwargs):
    r"""Replacement for monkeypatching to raise an error."""
    raise MagicTestError()


def functions_equal(a, b):
    a_str = f"{a.__module__}.{a.__name__}"
    b_str = f"{b.__module__}.{b.__name__}"
    if not (a_str.endswith(b_str) or b_str.endswith(a_str)):
        return False
    return a.__dict__ == b.__dict__


def pprint_diff(x, y):  # pragma: no cover
    r"""Get the diff between the pprint.pformat string for two objects."""
    import difflib
    import pprint
    from yggdrasil import tools
    tools.print_encoded('\n'.join(difflib.ndiff(
        pprint.pformat(x).splitlines(),
        pprint.pformat(y).splitlines())))
