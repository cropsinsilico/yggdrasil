import os
import argparse
from yggdrasil.examples.tests.test_transforms import TestExampleTransforms
from yggdrasil.languages import get_language_ext
from yggdrasil.runner import run
_this_dir = os.path.dirname(__file__)


def main(language, transform, language_ext=None):
    yamlfile = os.path.join(_this_dir, 'transforms.yml')
    modelfile, env = TestExampleTransforms.setup_model(
        language, transform, language_ext=language_ext)
    os.environ.update(env)
    try:
        run(yamlfile)
    finally:
        if os.path.isfile(modelfile):
            os.remove(modelfile)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        "Test application of a transform for the specified language.")
    # TODO: Set to list of installed languages/transforms?
    parser.add_argument('language',
                        help='Language that should be tested.')
    parser.add_argument('transform',
                        help='Name of data transform that should be tested.')
    args = parser.parse_args()
    args.language_ext = get_language_ext(args.language)
    main(args.language, args.transform, args.language_ext)
