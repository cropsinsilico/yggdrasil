import os
import gc
import sys
import glob
import logging
import warnings
lang_dir = os.path.dirname(__file__)


def install_language(language, results=None, no_import=False):
    r"""Call install for a specific language.

    Args:
        language (str): Name of language that should be checked.
        results (dict, optional): Dictionary where result (whether or not the
            language is installed) should be logged. Defaults to None and is
            initialized to an empty dict.
        no_import (bool, optional): If True, yggdrasil will not be imported.
            Defaults to False.

    """
    if no_import is None:
        no_import = ('--no-import' in sys.argv)
    if results is None:
        results = {}
    if not os.path.isfile(os.path.join(lang_dir, language, 'install.py')):
        if not (no_import or os.path.isdir(os.path.join(lang_dir, language))):
            from yggdrasil.languages import get_language_dir
            return install_language(os.path.basename(get_language_dir(language)),
                                    results=results, no_import=True)
        logging.info("Nothing to be done for %s" % language)
        name_in_pragmas = language.lower()
        results[name_in_pragmas] = True
        return
    try:
        sys.path.insert(0, os.path.join(lang_dir, language))
        import install
        name_in_pragmas = getattr(install, 'name_in_pragmas', language.lower())
        out = install.install()
        results[name_in_pragmas] = out
    finally:
        sys.path.pop(0)
        del install
        del name_in_pragmas
        if 'install' in globals():
            del globals()['install']
        if 'install' in sys.modules:
            del sys.modules['install']
        gc.collect()
    if not out:
        warnings.warn(("Could not complete installation for {lang}. "
                       "{lang} support will be disabled.").format(lang=language))
    else:
        logging.info("Language %s installed." % language)


def install_all_languages(**kwargs):
    r"""Call install.py for all languages that have one and return a dictionary
    mapping from language name to the installation state (True if install was
    successful, False otherwise).

    Args:
        **kwargs: Additional keyword arguments are passed to each call to
            install_language.

    Returns:
        dict: Mapping from language name to boolean describing installation
            success.

    """
    installed_languages = {}
    lang_dirs = sorted(glob.glob(os.path.join(lang_dir, '*')))
    for x in lang_dirs:
        if not os.path.isdir(x):
            continue
        ilang = os.path.basename(x)
        install_language(ilang, installed_languages, **kwargs)
    return installed_languages


if __name__ == "__main__":
    install_all_languages()
