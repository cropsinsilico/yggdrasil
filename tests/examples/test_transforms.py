import pytest
import os
import copy
from yggdrasil import constants
from yggdrasil.languages import get_language_ext
from yggdrasil.examples import _example_dir
from yggdrasil.metaschema.datatypes import encode_type
from yggdrasil.components import import_component
from tests.examples import TestExample as base_class


_untyped_lang = sorted([k for k, v in constants.LANGUAGE_PROPERTIES.items()
                        if (v['full_language'] and not v['is_typed'])])


class TestExampleTransforms(base_class):
    r"""Test the Transforms example."""

    parametrize_language = _untyped_lang
    parametrize_transform = ['table', 'array', 'pandas']

    @pytest.fixture(scope="class")
    def example_name(self):
        r"""str: Name of example being tested."""
        return "transforms"

    @pytest.fixture(scope="class", autouse=True)
    def transform(self, request):
        r"""str: Transform being tested."""
        return request.param

    @pytest.fixture(scope="class")
    def env(self, example_name, language, transform, example_module):
        r"""dict: Environment variables set for the test."""
        language_ext = get_language_ext(language)
        modelfile = os.path.join(_example_dir, example_name,
                                 'src', 'model' + language_ext)
        drv = import_component('model', language)
        testdata = example_module.get_test_data(transform)
        testtype = encode_type(testdata)
        inputs = [{'name': 'x',
                   'datatype': copy.deepcopy(testtype)}]
        outputs = [{'name': 'y',
                    'datatype': copy.deepcopy(testtype)}]
        # Write the model
        function_contents = []
        for i, o in zip(inputs, outputs):
            function_contents += drv.write_assign_to_output(
                o, i, outputs_in_inputs=drv.outputs_in_inputs)
        lines = drv.write_function_def(
            'model', function_contents=function_contents,
            inputs=copy.deepcopy(inputs),
            outputs=copy.deepcopy(outputs),
            outputs_in_inputs=drv.outputs_in_inputs,
            opening_msg='IN MODEL', closing_msg='MODEL EXIT',
            print_inputs=True, print_outputs=True)
        with open(modelfile, 'w') as fd:
            print(modelfile)
            print('\n'.join(lines))
            fd.write('\n'.join(lines))
        env = {}
        env['TEST_LANGUAGE'] = language
        env['TEST_LANGUAGE_EXT'] = language_ext
        env['TEST_TRANSFORM'] = transform
        if transform == 'table':
            env['TEST_MODEL_IO'] = (
                'outputs:\n'
                + '      - name: '
                + language + '_model:output\n'
                + '        format_str: "%s\\t%d\\t%f\\n"')
        try:
            yield env
        finally:
            if os.path.isfile(modelfile):
                os.remove(modelfile)

    @pytest.fixture
    def check_results(self):
        r"""This should be overridden with checks for the result."""
        def check_results_w():
            pass
        return check_results_w
