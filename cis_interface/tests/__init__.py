"""Testing things."""
import os

# Test data
data_dir = os.path.join(os.path.dirname(__file__), 'data')
data_list = [
    ('txt', 'ascii_file.txt'),
    ('table', 'ascii_table.txt')]
data = {k: os.path.join(data_dir, v) for k, v in data_list}

# Test scripts
script_dir = os.path.join(os.path.dirname(__file__), 'scripts')
script_list = [
    ('c', 'gcc_model.c'),
    ('matlab', 'matlab_model.m'),
    ('python', 'python_model.py')]
scripts = {k: os.path.join(script_dir, v) for k, v in script_list}
    
__all__ = ['data', 'scripts']
