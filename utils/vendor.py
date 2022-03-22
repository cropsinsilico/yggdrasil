import os
import shutil
import argparse


VENDOR_DIR = os.path.join(
    os.path.dirname(os.path.abspath(os.path.dirname(__file__))), '_vendor')
PYRJ_DIR = os.path.join(VENDOR_DIR, 'python_rapidjson')


def vendor(srcdir):
    if not os.path.isdir(VENDOR_DIR):
        os.mkdir(VENDOR_DIR)
    if not os.path.isdir(PYRJ_DIR):
        os.mkdir(PYRJ_DIR)
    
    files_to_copy = [
        'version.txt',
        'README.rst',
        'CHANGES.rst',
        'rapidjson.cpp',
    ]
    for x in files_to_copy:
        shutil.copy2(os.path.join(srcdir, x), os.path.join(PYRJ_DIR, x))

    setup_lines = open(os.path.join(srcdir, 'setup.py'), 'r').read().split(
        '\nsetup(')[0]
    open(os.path.join(PYRJ_DIR, 'pyrj_setup.py'), 'w').write(
        '# flake8: noqa\n' + setup_lines)
    

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        "Update the vendored python-rapidjson.")
    parser.add_argument('source',
                        help="Root directory for the python-rapidjson package.")
    args = parser.parse_args()
    vendor(args.source)
