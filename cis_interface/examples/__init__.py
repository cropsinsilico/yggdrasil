"""Tools for accessing examples from python."""
import os


yaml_list = [
    ('ascii_io_python', 'ascii_io', 'ascii_io_Python'),
    ('ascii_io_matlab', 'ascii_io', 'ascii_io_Matlab'),
    ('ascii_io_gcc', 'ascii_io', 'ascii_io_GCC'),
    ('ascii_io_all', 'ascii_io', 'ascii_io_all')]
yamls = {}
for k, d, f in yaml_list:
    yamls[k] = os.path.join(os.path.dirname(__file__), d, f + '.yml')


__all__ = ['yamls']
