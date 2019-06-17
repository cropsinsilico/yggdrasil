import os
import gc
import sys
import glob
import logging
import warnings
lang_dir = os.path.join(os.path.abspath(os.path.dirname(__file__)),
                        'yggdrasil', 'languages')


def call_install_language(language, results):
    r"""Call install for a specific language.

    Args:
        language (str): Name of language that should be checked.
        results (dict): Dictionary where result (whether or not the language is
            installed) should be logged.

    """
    if not os.path.isfile(os.path.join(lang_dir, language, 'install.py')):
        return True
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


def install_all_languages():
    r"""Call install.py for all languages that have one and return a dictionary
    mapping from language name to the installation state (True if install was
    successful, False otherwise).

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
        call_install_language(ilang, installed_languages)
    return installed_languages


if __name__ == "__main__":
    install_all_languages()
