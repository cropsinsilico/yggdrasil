from yggdrasil import languages
from yggdrasil.tests import assert_raises


def test_get_language_dir(lang):
    r"""Test the get_language_dir method."""
    assert_raises(ValueError, languages.get_language_dir, 'invalid')
    test_lang = ['matlab']
    for lang in test_lang:
        languages.get_language_dir(lang)
