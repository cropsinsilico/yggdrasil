# python generate_conda_install.py conda-install-base.yml conda-install.yml
import sys
import yaml
import pprint


class NoAliasDumper(yaml.SafeDumper):
    def ignore_aliases(self, data):
        return True


if __name__ == "__main__":
    fileA = sys.argv[1]
    fileB = sys.argv[2]
    with open(sys.argv[1], 'r') as fd:
        contents = yaml.load(fd, Loader=yaml.SafeLoader)
    if '--verbose' in sys.argv:
        pprint.pprint(contents)
    with open(sys.argv[2], 'w') as fd:
        yaml.dump(contents, fd, Dumper=NoAliasDumper)
