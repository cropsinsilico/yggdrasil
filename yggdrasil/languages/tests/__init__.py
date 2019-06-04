from yggdrasil import languages, tools
from yggdrasil.tests import assert_raises


def test_get_language_dir():
    r"""Test the get_language_dir method."""
    assert_raises(ValueError, languages.get_language_dir, 'invalid')
    test_lang = tools.get_supported_lang()
    test_skip = ['make', 'cmake', 'executable']
    for lang in test_lang:
        if lang in test_skip:
            continue
        languages.get_language_dir(lang)
