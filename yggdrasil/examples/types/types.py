import os
import argparse
from yggdrasil.examples.tests.test_types import TestExampleTypes
from yggdrasil.languages import get_language_ext
from yggdrasil.runner import run
_this_dir = os.path.dirname(__file__)


def main(language, typename, language_ext=None):
    yamlfile = os.path.join(_this_dir, 'types.yml')
    modelfile = TestExampleTypes.setup_model(
        language, typename, language_ext=language_ext)
    try:
        run(yamlfile)
    finally:
        if os.path.isfile(modelfile):
            os.remove(modelfile)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        "Test communication of a datatype for the specified language.")
    # TODO: Set to list of installed languages/types
    parser.add_argument('language',
                        help='Language that should be tested.')
    parser.add_argument('typename',
                        help='Name of data type that should be tested.')
    args = parser.parse_args()
    args.language_ext = get_language_ext(args.language)
    main(args.language, args.typename, args.language_ext)
