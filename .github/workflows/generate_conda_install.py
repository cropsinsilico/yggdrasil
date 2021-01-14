import os
import yaml
import pprint
import argparse


class NoAliasDumper(yaml.SafeDumper):
    def ignore_aliases(self, data):
        return True


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        "Generate a Github Actions (GHA) workflow yaml file from "
        "a version of the file that uses anchors (not supported by "
        "GHA as of 2021-01-14).")
    parser.add_argument(
        '--base', '--base-file', default='conda-install-base.yml',
        help="Version of GHA workflow yaml that contains anchors.")
    parser.add_argument(
        '--dest', default='conda-install.yml',
        help="Name of target GHA workflow yaml file.")
    parser.add_argument(
        '--verbose', action='store_true',
        help="Print yaml contents.")
    args = parser.parse_args()
    base = os.path.join(os.path.dirname(__file__), args.base)
    dest = os.path.join(os.path.dirname(__file__), args.dest)
    with open(base, 'r') as fd:
        contents = yaml.load(fd, Loader=yaml.SafeLoader)
    if args.verbose:
        pprint.pprint(contents)
    with open(dest, 'w') as fd:
        fd.write(('# DO NOT MODIFY THIS FILE, IT IS GENERATED.\n'
                  '# To make changes, modify \'%s\'\n'
                  '# and run \'python generate_conda_install.py\'\n')
                 % args.base)
        yaml.dump(contents, fd, Dumper=NoAliasDumper)
