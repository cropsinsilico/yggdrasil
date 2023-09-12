import pytest
from yggdrasil.examples import (
    get_example_yaml, get_example_source, get_example_languages,
    display_example, find_missing)


@pytest.mark.suite("examples", disabled=True)
def test_get_example_yaml():
    r"""Test get_example_yaml."""
    with pytest.raises(KeyError):
        get_example_yaml('invalid', 'invalid')
    with pytest.raises(KeyError):
        get_example_yaml('hello', 'invalid')
    get_example_yaml('hello', 'r')
    get_example_yaml('hello', 'R')


@pytest.mark.suite("examples", disabled=True)
def test_get_example_source():
    r"""Test get_example_source."""
    with pytest.raises(KeyError):
        get_example_source('invalid', 'invalid')
    with pytest.raises(KeyError):
        get_example_source('hello', 'invalid')
    get_example_source('hello', 'r')
    get_example_source('hello', 'R')


@pytest.mark.suite("examples", disabled=True)
def test_get_example_languages():
    r"""Test get_example_languages."""
    with pytest.raises(KeyError):
        get_example_languages('invalid')
    get_example_languages('ascii_io')
    get_example_languages('ascii_io', language='python')
    get_example_languages('ascii_io', language='all')
    get_example_languages('ascii_io', language='all_nomatlab')


@pytest.mark.suite("examples", disabled=True)
def test_display_example():
    r"""Test display_example."""
    display_example('hello', 'r')


def test_examples_for_all_languages():
    r"""Test that there examples are replicated across languages."""
    assert find_missing(ignore_examples=[])
    assert not find_missing(languages='c')['c']
    assert not find_missing()
