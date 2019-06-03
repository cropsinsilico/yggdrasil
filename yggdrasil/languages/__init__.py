import os


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
