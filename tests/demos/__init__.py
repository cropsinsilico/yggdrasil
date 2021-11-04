import pytest
import os
import six
from yggdrasil import yamlfile, runner, demos
from yggdrasil.components import import_component
from tests import TestBase as base_class


_demo_dir = os.path.dirname(os.path.abspath(demos.__file__))


class DemoMeta(type):

    def __new__(meta, name, bases, class_dict):
        
        @pytest.fixture(scope="class",
                        params=list(class_dict['runs'].keys()))
        def run_name(self, request):
            r"""str: Name of the run."""
            return request.param

        class_dict['run_name'] = run_name
        return type.__new__(meta, name, bases, class_dict)


@pytest.mark.suite("demos", disabled=True)
@six.add_metaclass(DemoMeta)
class DemoTstBase(base_class):
    r"""Base class for running demos."""

    runs = {}

    @pytest.fixture(scope="class", params=[])
    def demo_name(self, request):
        r"""str: Name of demo being tested."""
        return request.param

    @pytest.fixture(scope="class")
    def demo_directory(self, demo_name):
        r"""str: Directory containing the demo."""
        return os.path.join(_demo_dir, demo_name)

    @pytest.fixture(scope="class", params=[])
    def run_name(self, request):
        r"""str: Name of the run."""
        return request.param

    @pytest.fixture(scope="class")
    def yamls(self, run_name, demo_directory):
        r"""tuple: YAMLs required for the run."""
        return [os.path.join(demo_directory, x) for x in self.runs[run_name]]

    def test_run(self, run_name, yamls, check_required_languages):
        r"""Run the integration."""
        languages = []
        for x in yamlfile.parse_yaml(list(yamls))['model'].values():
            drv = import_component('model', x['driver'],
                                   without_schema=True)
            if drv.language not in languages:
                languages.append(drv.language)
        check_required_languages(languages)
        # Run
        r = runner.get_runner(yamls, namespace=run_name,
                              production_run=True)
        r.run()
        assert(not r.error_flag)
        del r

    @pytest.fixture(scope="class", autouse=True)
    def create_output_directory(self, demo_directory):
        r"""Create the output directory if it dosn't exist."""
        out_dir = os.path.join(demo_directory, 'output')
        if not os.path.isdir(out_dir):
            os.mkdir(out_dir)
