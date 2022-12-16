import os
import argparse
import setup_test_env
from install_from_requirements import prune


def create_recipe():
    fname = os.path.join(os.path.dirname(os.path.dirname(__file__)),
                         'recipe', 'meta.yaml')
    install_opts = setup_test_env.get_install_opts()
    env = {}
    env['platform_system'] = 'Darwin'
    install_opts['os'] = 'osx'
    odeps_osx = prune(['requirements.txt', 'requirements_condaonly.txt'],
                      install_opts=install_opts, excl_method='pip',
                      return_list=True, environment=env)
    env['platform_system'] = 'Windows'
    install_opts['os'] = 'win'
    odeps_win = prune(['requirements.txt', 'requirements_condaonly.txt'],
                      install_opts=install_opts, excl_method='pip',
                      return_list=True, environment=env)
    env['platform_system'] = 'Ubuntu'
    install_opts['os'] = 'linux'
    odeps_lin = prune(['requirements.txt', 'requirements_condaonly.txt'],
                      install_opts=install_opts, excl_method='pip',
                      return_list=True, environment=env)
    deps_all = sorted(list(set(odeps_osx) | set(odeps_win) | set(odeps_lin)))
    deps_uni = sorted(list((set(odeps_osx) & set(odeps_lin)) - set(odeps_win)))
    deps_osx = sorted(list(set(odeps_osx) - (set(odeps_win) | set(odeps_lin))))
    deps_win = sorted(list(set(odeps_win) - (set(odeps_osx) | set(odeps_lin))))
    deps_lin = sorted(list(set(odeps_lin) - (set(odeps_win) | set(odeps_osx))))
    lines = open(fname, 'r').read()
    idx_ver_beg = lines.find('{% set version = "') + len('{% set version = "')
    idx_ver_end = lines.find('"', idx_ver_beg)
    idx_req_beg = lines.find('\n  run:') + len('\n  run:')
    idx_req_end = lines.find('\ntest:')
    if any(x == -1 for x in [idx_ver_beg, idx_ver_end, idx_req_beg, idx_req_end]):
        raise ValueError(f"Could not find indices to replace: "
                         f"[{idx_ver_beg}, {idx_ver_end}, {idx_ver_end},"
                         f" {idx_req_end}]")
    skip = ['matplotlib']  # do matplotlib-base on conda
    deps_tot = ['python']
    for x in deps_all:
        if x in skip:
            continue
        if x in deps_osx:
            x += '  # [osx]'
        elif x in deps_win:
            x += '  # [win]'
        elif x in deps_lin:
            x += '  # [linux]'
        elif x in deps_uni:
            x += '  # [not win]'
        deps_tot.append(x)
    deps_tot = sorted(deps_tot)
    deps_tot += ["{{ compiler('c') }}  # [win]",
                 "{{ compiler('cxx') }}  # [win]",
                 "{{ compiler('fortran') }}  # [not win]"]
    new_lines = lines[:idx_req_beg]
    new_lines += '\n    - ' + '\n    - '.join(deps_tot)
    new_lines += '\n' + lines[idx_req_end:]
    with open(fname, 'w') as fd:
        fd.write(new_lines)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        "Generate a conda recipe from the various requirements files.")
    create_recipe()
