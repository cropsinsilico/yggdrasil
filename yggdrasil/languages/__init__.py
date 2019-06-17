import os
from yggdrasil.components import import_component


_lang_dir = os.path.dirname(__file__)
_top_dir = os.path.normpath(os.path.join(_lang_dir, '../'))


def get_language_dir(lang):
    r"""Return the directory containing the interface for the requested language.

    Args:
        lang (str): The name of the language to return a directory for.

    Returns:
        str: The full path to the interface directory for the language.

    """
    mod_list = [lang, lang.lower(), lang.upper(), lang.title()]
    if lang.lower() in ['cmake', 'lpy']:
        mod_list.insert(0, lang[:2].upper() + lang[2:].lower())
    elif lang.lower() == 'cpp':
        mod_list = ['c++', 'C++'] + mod_list
    elif lang.lower() == 'c++':
        mod_list += ['cpp', 'CPP']
    for ilang in mod_list:
        idir = os.path.join(_lang_dir, ilang)
        if os.path.isdir(idir):
            return idir
    raise ValueError("Could not determine directory for the language: '%s'" % lang)


def get_language_ext(lang, default=None):
    r"""Return the file extension associated with the requirested language.

    Args:
        lang (str): Programming language that extension should be returned for.
        default (str, optional): Extension that should be returned if no
            extensions are registered for the language. Defaults to None and
            an error will be raised if there are not any extensions associated
            with the language.

    Returns:
        str: The most common extension associated with the specified language.

    Raises:
        ValueError: If there are not any executables associated with a language.

    """
    driver = import_component('model', lang)
    all_ext = driver.get_language_ext()
    if not all_ext:
        if default is not None:
            return default
        raise ValueError("No extension associated with language: %s" % lang)
    return all_ext[0]
