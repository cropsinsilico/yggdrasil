import os
import sys
import numpy as np
import shutil

src_file = 'Input/input1_file.txt'
src_table = 'Input/input1_table.txt'
src_array = 'Input/input1_array.txt'

if __name__ == '__main__':

    src_list = [src_file, src_table, src_array]
    tag_list = ['Py', 'C', 'M']

    for src in src_list:
        for tag in tag_list:
            dst = src.replace('1', tag)
            if not os.path.isfile(dst):
                shutil.copy(src, dst)
