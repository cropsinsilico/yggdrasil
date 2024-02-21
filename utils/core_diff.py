import os
import glob
import argparse
from yggdrasil import tools


def default_converter(fbase):
    return fbase


def converter_upper_ext(fbase):
    parts = os.path.splitext(fbase)
    return ''.join(parts[:-1]) + parts[-1].upper()


def file_diff(root1, root2, fbase, outdir=None, converter=None):
    if outdir is None:
        outdir = os.getcwd()
    if converter is None:
        converter = default_converter
    fdiff = os.path.join(outdir, f"diff_{fbase}")
    fname1 = os.path.join(root1, fbase)
    if not os.path.isfile(fname1):
        # print(f"< {fname1} does not exist")
        return
    fname2 = os.path.join(root2, converter(fbase))
    if not os.path.isfile(fname2):
        # print(f"> {fname2} does not exist")
        return
    cmd = ['diff', fname1, fname2]
    proc = tools.popen_nobuffer(cmd)
    out, err = proc.communicate()
    out = out.decode("utf-8")
    err = err.decode("utf-8") if err else ''
    assert not err
    if out:
        with open(fdiff, 'w') as fd:
            fd.write(out)


def dir_diff(root1, root2, outdir=None, converter=None):
    if outdir is None:
        outdir = os.path.join(os.getcwd(), os.path.basename(root1))
        assert os.path.isdir(outdir)
    if converter is None:
        converter = default_converter
    files = glob.glob(os.path.join(root1, '*'))
    for x in files:
        file_diff(root1, root2, os.path.basename(x), outdir=outdir,
                  converter=converter)
    

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        "Get a diff between two directories")
    parser.add_argument('root1', help='First directory for diff')
    parser.add_argument('root2', help='Second directory for diff')
    parser.add_argument('--converter',
                        help='Converter used for file names in root2',
                        choices=['upper_ext'])
    parser.add_argument('--outdir', help='Output directory')
    args = parser.parse_args()
    if args.converter == 'upper_ext':
        args.converter = converter_upper_ext
    dir_diff(args.root1, args.root2, outdir=args.outdir,
             converter=args.converter)
