import os
import shutil
import subprocess
from yggdrasil.config import create_coveragerc
from yggdrasil.constants import LANGUAGES


def test_update_config():
    r"""Test the yggconfig entry point."""
    subprocess.check_call(['yggconfig', '-h'])


def test_create_coveragerc():
    r"""Test the creation of coveragerc file."""
    covered_languages = {}
    for k in LANGUAGES['all']:
        v = os.environ.get(f"INSTALL{k.upper()}", None)
        if v is not None:
            covered_languages[k] = (v == '1')
    fname = os.path.join(os.getcwd(), '.coveragerc')
    fname_cpy = None
    if os.path.isfile(fname):
        fname_cpy = os.path.join(os.getcwd(), '.coveragerc_cpy')
        shutil.copy2(fname, fname_cpy)
        os.remove(fname)
    try:
        create_coveragerc(covered_languages)
        contents1 = open(fname, 'r').read()
        create_coveragerc(covered_languages, filename=fname)
        contents2 = open(fname, 'r').read()
        assert contents2 == contents1
    finally:
        if fname_cpy:
            shutil.copy2(fname_cpy, fname)
        elif os.path.isfile(fname):
            os.remove(fname)
