# TODO: Test conda_env
import pytest
import os
import copy
import site
from contextlib import nullcontext
from tests import TestComponentBase as base_class
from yggdrasil import dependencies, tools
from yggdrasil.components import create_component


@pytest.mark.parametrize("version,expected", [
    ('1.2', {
        'strict': '1.2', 'stricteq': False,
        'constraints': [{'ver': '1.2', 'op': '=='}]
    }),
    ('==1.2.5a', {
        'strict': '1.2.5a', 'stricteq': True,
        'constraints': [{'ver': '1.2.5a', 'op': '=='}]
    }),
    (' < 1.2 ', {
        'max': '1.2', 'maxeq': False,
        'constraints': [{'ver': '1.2', 'op': '<'}]
    }),
    ('<=1.2.5', {
        'max': '1.2.5', 'maxeq': True,
        'constraints': [{'ver': '1.2.5', 'op': '<='}]
    }),
    ('=<1.2.5', {
        'max': '1.2.5', 'maxeq': True,
        'constraints': [{'ver': '1.2.5', 'op': '=<'}]
    }),
    ('> 1.2', {
        'min': '1.2', 'mineq': False,
        'constraints': [{'ver': '1.2', 'op': '>'}]
    }),
    ('>=1.2.5', {
        'min': '1.2.5', 'mineq': True,
        'constraints': [{'ver': '1.2.5', 'op': '>='}]
    }),
    ('=> 1.2.5', {
        'min': '1.2.5', 'mineq': True,
        'constraints': [{'ver': '1.2.5', 'op': '=>'}]
    }),
    ('=> 1.2.5, < 2.0', {
        'min': '1.2.5', 'mineq': True,
        'max': '2.0', 'maxeq': False,
        'constraints': [
            {'ver': '1.2.5', 'op': '=>'},
            {'ver': '2.0', 'op': '<'},
        ]
    }),
    ('<=2.0,>1.0', {
        'max': '2.0', 'maxeq': True,
        'min': '1.0', 'mineq': False,
        'constraints': [
            {'ver': '2.0', 'op': '<='},
            {'ver': '1.0', 'op': '>'},
        ]
    }),
    ('==2.0,>1.0', {
        'strict': '2.0', 'stricteq': True,
        'constraints': [
            {'ver': '2.0', 'op': '=='},
        ]
    }),
])
def test_parse_version_string(version, expected):
    r"""Test parse_version_string."""
    actual = dependencies.parse_version_string(version)
    if actual != expected:
        import pprint
        print('EXPECTED')
        pprint.pprint(expected)
        print('ACTUAL')
        pprint.pprint(actual)
    assert actual == expected


@pytest.mark.parametrize("version", [
    '5%f2',
    '==2.0, ==1.0',
    '==2.0, >3.0',
])
def test_parse_version_string_errors(version):
    r"""Test parse_version_string errors for invalid version formats"""
    with pytest.raises(dependencies.VersionParsingError):
        dependencies.parse_version_string(version)


def test_conda_uninstall_pip(requires_conda):
    r"""Test that error is raised if conda attempts to uninstall a
    package installed via pip"""
    always_yes = True
    x_conda = create_component('dependency', 'conda', package='astropy')
    x_pip = create_component('dependency', 'pip', package='astropy')
    if x_conda.is_installed or x_pip.is_installed:
        pytest.skip("astropy already installed")
    if not (x_conda.manager_installed(always_yes=always_yes)
            and x_pip.manager_installed(always_yes=always_yes)):
        pytest.skip("conda & pip must be installed")
    x_pip.install(always_yes=always_yes)
    try:
        assert x_pip.is_installed
        conda_installed = x_conda.is_installed
        assert conda_installed and conda_installed['channel'] == 'pypi'
        x_conda.install(always_yes=always_yes)
        with pytest.raises(dependencies.DependencyError):
            x_conda.uninstall(always_yes=always_yes)
    finally:
        x_pip.uninstall(always_yes=always_yes)


def test_error_no_uninstall_command():
    r"""Test that error is raised if command_uninstall not provided."""
    always_yes = True
    kwargs = {'package': 'pip-install-test',
              'command': ['pip', 'install', 'pip-install-test'],
              'command_uninstall': [
                  'pip', 'uninstall', 'pip-install-test', '-y'],
              'products': [
                  os.path.join(site.getsitepackages()[0],
                               'pip_install_test')]}
    kwargs_no_uninstall = dict(kwargs)
    kwargs_no_uninstall.pop('command_uninstall')
    instance = dependencies.CommandDependency(**kwargs)
    instance.install(always_yes=always_yes)
    try:
        kwargs_no_uninstall = dependencies.CommandDependency(
            **kwargs_no_uninstall)
        assert kwargs_no_uninstall.is_installed
        with pytest.raises(dependencies.DependencyError):
            kwargs_no_uninstall.uninstall(always_yes=always_yes)
    finally:
        instance.uninstall(always_yes=always_yes)


class TestManagedDependencyBase(base_class):
    r"""Tests for dependency classes."""

    _component_type = 'dependency'
    _component_instance_param = {
        'set': [
            ({
                'members': [
                    {'package': 'python'},
                    {'package': 'invalid1939502'},
                ],
                'shared_properties': {
                    'package_manager': 'conda'
                }
            }, False, False, None),
            ({
                'members': [
                    {'package': 'pyyaml', 'package_manager': 'pip'},
                    {'package': 'pyyaml', 'package_manager': 'conda'},
                ],
            }, True, True, True),
            ({
                'members': [
                    {'package': 'pyyaml', 'package_manager': 'conda'},
                    {'package': 'pyyaml', 'package_manager': 'pip'},
                ],
            }, True, True, True),
        ],
        'options': [
            ({
                'package': 'pyyaml',
                'options': [
                    {'package': 'pyyaml', 'package_manager': 'pip',
                     'operating_systems': ['unix']},
                    {'package': 'pyyaml', 'package_manager': 'conda',
                     'operating_systems': ['windows']},
                ],
            }, True, True, True),
        ],
        'conda': [
            ({'package': 'python'}, True, True, None),
            ({'package': 'pyyaml'}, True, True, True),
            # ({'package': 'nbconvert'}, False, True, True),
        ],
        'pip': [
            ({'package': 'pyyaml'}, True, True, True),
            ({'package': 'pip-install-test', 'version': '0.5'},
             False, True, True),
        ],
        'cran': [
            # ({'package': 'BioCro'}, False, True, True),
            ({'package': 'tinytest'}, False, True, True),
        ],
        'apt': [
            ({'package': 'rolldice'}, False, True, True),
        ],
        'brew': [
            ({'package': 'dixa'}, False, True, True),
            ({'package': 'gcc', 'version': '13'}, True, True, True),
        ],
        'choco': [
            ({'package': '7zip'}, False, True, True),
        ],
        'vcpkg': [],
        'source': [],
        'git': [
            ({'package': 'sundials',
              'repository': 'https://github.com/LLNL/sundials.git',
              'buildfile': 'CMakeLists.txt',
              'args_config': [
                  # '-DCMAKE_VERBOSE_MAKEFILE:BOOL=ON',
                  '-DEXAMPLES_ENABLE_C:BOOL=OFF',
                  '-DEXAMPLES_ENABLE_CXX:BOOL=OFF',
              ],
              'args_build': [
                  '--config', 'RelWithDebInfo'
              ],
              'products': [
                  'include/sundials/sundials_base.hpp'
              ]},
             False, True, True),
            ({'package': 'invalid1939502',
              'repository': ('https://github.com/cropsinsilico/'
                             'invalid1939502.git')},
             False, False, False),
        ],
        ('conda', 'pip', 'cran', 'apt', 'brew', 'choco', 'vcpkg'): [
            ({'package': 'invalid1939502'}, False, False, None),
        ],
        'command': [
            ({'package': 'invalid1939502', 'command': ['invalid'],
              'command_uninstall': ['invalid']},
             False, False, None),
            ({'package': 'pip-install-test',
              'command': ['pip', 'install', 'pip-install-test'],
              'command_uninstall': [
                  'pip', 'uninstall', 'pip-install-test', '-y'],
              'products': [
                  os.path.join(site.getsitepackages()[0],
                               'pip_install_test')]},
             False, True, True),
        ],
    }

    @classmethod
    def wrap_expectation(cls, expectation):
        if isinstance(expectation, bool):
            if expectation:
                return nullcontext(True)
            else:
                return pytest.raises(dependencies.DependencyError)
        elif expectation is None:
            return None
        return pytest.raises(expectation)
    
    @pytest.fixture
    def always_yes(self, package_manager):
        return True

    @pytest.fixture
    def instance_kwargs(self, component_subtype_param):
        r"""Keyword arguments for a new instance of the tested class."""
        return copy.deepcopy(component_subtype_param[0])

    @pytest.fixture
    def preinstall_status(self, component_subtype_param):
        r"""bool: True if component is expected to be installed, False
        otherwise."""
        return component_subtype_param[1]
    
    @pytest.fixture
    def install_expectation(self, component_subtype_param):
        r"""Context with expectation for result of install"""
        return self.wrap_expectation(component_subtype_param[2])
    
    @pytest.fixture
    def uninstall_expectation(self, component_subtype_param):
        r"""Context with expectation for result of uninstall"""
        return self.wrap_expectation(component_subtype_param[3])

    def test_manager_not_installed(self, instance, always_yes):
        r"""Test results when manager not installed."""
        if instance.manager_installed():
            pytest.skip("Requires manager not be installed")
        assert not instance.is_installed
        with pytest.raises(dependencies.DependencyError):
            instance.install(always_yes=always_yes)
        with pytest.raises(dependencies.DependencyError):
            instance.uninstall(always_yes=always_yes)

    def test_invalid_conda_env(self, python_class, instance_kwargs):
        r"""Test that error is raised if conda_env is invalid."""
        if not python_class.affected_by_conda_env:
            pytest.skip("Manager not affected by conda_env")
        instance = python_class(conda_env='invalid1939502',
                                **instance_kwargs)
        assert not instance.is_valid
        with pytest.raises(dependencies.DependencyError):
            instance.install()
        with pytest.raises(dependencies.DependencyError):
            instance.uninstall()

    @pytest.mark.parametrize("conda_env", [None, 'valid1939502'])
    def test_install(self, python_class, instance_kwargs, always_yes,
                     preinstall_status, install_expectation,
                     uninstall_expectation, conda_env):
        r"""Test install/uninstall of dependency."""
        if conda_env and not python_class.affected_by_conda_env:
            pytest.skip("Manager not affected by conda_env")
        instance = python_class(conda_env=conda_env, **instance_kwargs)
        # Don't test install/uninstall if package manager not installed
        print("INSTANCE", instance, instance.is_installed)
        if not instance.manager_installed(conda_env=conda_env):
            pytest.skip("Requires manager be installed")
        try:
            instance.install_manager(always_yes=always_yes)
        except dependencies.DependencyError as e:
            pytest.skip(f"install_manager failed: {e}")
        # Create conda env
        if conda_env:
            conda_prefix = tools.get_conda_prefix(conda_env)
            if conda_prefix is None:
                pytest.skip("Requires conda be installed")
            if not os.path.isdir(conda_prefix):
                tools.call_conda_command('create', env=conda_env,
                                         default_to_mamba=True)
                assert os.path.isdir(conda_prefix)
        # Test install
        preinstall_status_act1 = instance.is_installed
        preuninstall_status_act1 = instance.is_uninstalled
        if install_expectation:
            with install_expectation as e:
                instance.install(always_yes=always_yes)
                if e is True:
                    assert instance.is_installed
                    assert not instance.is_uninstalled
                else:
                    # Check that nothing changed
                    assert instance.is_installed == preinstall_status_act1
                    assert instance.is_uninstalled == preuninstall_status_act1
        # Don't uninstall a package that was installed before tests
        if preinstall_status and (not conda_env):
            return
        debugging_tests = True  # TODO: Disable this
        if preinstall_status_act1:
            if ((os.environ.get('GITHUB_ACTIONS', False)
                 or not debugging_tests)):
                return
            always_yes = False
        # Test uninstall
        preinstall_status_act2 = instance.is_installed
        preuninstall_status_act2 = instance.is_uninstalled
        if uninstall_expectation:
            if ((instance._package_manager == 'conda'
                 and preinstall_status_act1
                 and preinstall_status_act1['channel'] == 'pypi')):
                uninstall_expectation = pytest.raises(
                    dependencies.DependencyError)
            with uninstall_expectation as e:
                instance.uninstall(always_yes=always_yes)
                if e is True:
                    assert not instance.is_installed
                    assert instance.is_uninstalled
                else:
                    # Check that nothing changed
                    assert instance.is_installed == preinstall_status_act2
                    assert instance.is_uninstalled == preuninstall_status_act2
