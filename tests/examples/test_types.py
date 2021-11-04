import pytest
import os
import copy
import yaml
import importlib
from yggdrasil import constants
from yggdrasil.components import import_component
from yggdrasil.languages import get_language_ext
from yggdrasil.metaschema.datatypes import encode_type
from tests.examples import TestExample as base_class


_full_lang = sorted([k for k, v in constants.LANGUAGE_PROPERTIES.items()
                     if v['full_language']])
_typed_lang = sorted([k for k, v in constants.LANGUAGE_PROPERTIES.items()
                      if (v['full_language'] and v['is_typed'])])


@pytest.mark.suite("types", disabled=True, ignore="examples")
class TestExampleTypes(base_class):
    r"""Test the Types example."""

    parametrize_language = _full_lang
    # iter_flaky = [('c', 'instance', '*'), ('cpp', 'instance', '*')]

    @pytest.fixture(scope="class")
    def example_name(self):
        r"""str: Name of example being tested."""
        return "types"

    @pytest.fixture(scope="class")
    def example_module(self, example_name):
        r"""Python module associated with the test."""
        try:
            return importlib.import_module(f'tests.examples.{example_name}')
        except ImportError:
            return None

    @pytest.fixture(scope="class", autouse=True)
    def language(self, request, check_required_languages):
        r"""str: Language of the currect test."""
        check_required_languages([request.param])
        return request.param

    @pytest.fixture(scope="class")
    def yaml(self, example_name, language):
        r"""str: The full path to the yaml file for this example."""
        return os.path.join(os.path.dirname(__file__), 'types', 'types.yml')

    @pytest.fixture(scope="class", autouse=True)
    def typename(self, request):
        r"""str: Type being tested."""
        return request.param

    @pytest.fixture(scope="class")
    def is_typed(self, language):
        r"""bool: True if the tested is for a typed language."""
        return (language in _typed_lang)

    @pytest.fixture(scope="class",
                    params=[{},
                            {'using_pointers': True},
                            {'using_generics': True},
                            {'using_pointers': True,
                             'dont_add_lengths': True},
                            {'using_pointers': True,
                             'length_prefix': True},
                            {'split_array': True}])
    def options(self, request):
        r"""Options used to create the test."""
        return request.param

    @pytest.fixture(scope="class")
    def using_pointers(self, options, is_typed):
        r"""bool: True if the test should be for pointers rather than explicit
        types."""
        out = options.get('using_pointers', False)
        if out and (not is_typed):
            pytest.skip("pointers only tested for typed languages")
        return out

    @pytest.fixture(scope="class")
    def using_generics(self, options, is_typed):
        r"""bool: True if the test should use generic types."""
        out = options.get('using_generics', False)
        if out and (not is_typed):
            pytest.skip("generic only tested for typed languages")
        return out

    @pytest.fixture(scope="class")
    def dont_add_lengths(self, options, language, is_typed, typename):
        r"""bool: True if the test should not add length variables."""
        out = options.get('dont_add_lengths', False)
        if out and not (
                is_typed and (language == 'c')
                and (typename in ['string', 'bytes', 'unicode'])):
            pytest.skip("dont_add_lengths only enabled for c string types")
        return out

    @pytest.fixture(scope="class")
    def length_prefix(self, options, language, is_typed, typename):
        r"""bool: True if length prefixes should be used instead of suffixes."""
        out = options.get('length_prefix', False)
        if out and not (
                is_typed and (language == 'c')
                and (typename in ['1darray', 'ndarray'])):
            pytest.skip("length_prefix only enabled for c arrays")
        return out

    @pytest.fixture(scope="class")
    def split_array(self, options, using_pointers, using_generics,
                    typename):
        r"""bool: True if arrays should be split across multiple variables."""
        out = options.get('split_array', False)
        if out and not (typename == 'array'):
            pytest.skip("split_array only enabled for array types")
        return out

    @classmethod
    def get_varstr(cls, vars_list, language, using_pointers=False,
                   length_prefix=False, dont_add_lengths=False):
        r"""Determine the vars string that should be used in the yaml.

        Args:
            vars_list (list): List of variables.
            language (str): Language being tested.
            using_pointers (bool, optional): If True and the tested
                language supports pointers, pointers will be used rather
                than explicit arrays. Defaults to False.
            length_prefix (bool, optional): If True, the length variables
                will be given prefixes instead of suffixes. Defaults to
                False.
            dont_add_lengths (bool, optional): If True, lengths will not
                be added to the definition or assignments. Defaults to
                False.

        Returns:
            str: Variable string.

        """
        out = []
        if length_prefix:
            length_fmt = 'length_%s'
            ndim_fmt = 'ndim_%s'
            shape_fmt = 'shape_%s'
        else:
            length_fmt = '%s_length'
            ndim_fmt = '%s_ndim'
            shape_fmt = '%s_shape'
        for v in vars_list:
            out.append(v['name'])
            typename = v['datatype']['type']
            if (language == 'c') and (not dont_add_lengths):
                if using_pointers:
                    if typename in ['string', 'bytes',
                                    'unicode', '1darray']:
                        out.append(length_fmt % v['name'])
                    elif typename in ['ndarray']:
                        out += [ndim_fmt % v['name'],
                                shape_fmt % v['name']]
                elif typename in ['string', 'bytes', 'unicode']:
                    out.append(length_fmt % v['name'])
        return ', '.join(out)
        
    @pytest.fixture(scope="class")
    def env(self, example_name, language, typename, using_pointers,
            using_generics, split_array, dont_add_lengths,
            length_prefix, example_module):
        r"""dict: Environment variables set for the test."""
        kwargs = {}
        assign_kws = {}
        if language in ['c', 'c++', 'cpp']:
            # dont_add_lengths is only valid for C/C++
            kwargs['dont_add_lengths'] = dont_add_lengths
            kwargs['use_length_prefix'] = length_prefix
            assign_kws.setdefault('dont_add_lengths', dont_add_lengths)
            assign_kws.setdefault('use_length_prefix', length_prefix)
        yaml_fields = {'vars': False, 'dtype': False}
        language_ext = get_language_ext(language)
        modelfile = os.path.join(os.path.dirname(__file__), example_name,
                                 'src', 'model' + language_ext)
        drv = import_component('model', language)
        if using_generics and drv.is_typed:
            testtype = {'type': 'any'}
        else:
            testdata = example_module.get_test_data(typename)
            testtype = encode_type(testdata)
            using_generics = False
        if split_array and (typename == 'array'):
            inputs = [{'name': 'x%d' % i, 'datatype': x} for i, x in
                      enumerate(copy.deepcopy(testtype['items']))]
            outputs = [{'name': 'y%d' % i, 'datatype': x} for i, x in
                       enumerate(copy.deepcopy(testtype['items']))]
        else:
            inputs = [{'name': 'x',
                       'datatype': copy.deepcopy(testtype)}]
            outputs = [{'name': 'y',
                        'datatype': copy.deepcopy(testtype)}]
        # Write the model
        function_contents = []
        for i, o in zip(inputs, outputs):
            if using_pointers and drv.is_typed:
                for k in ['shape', 'length']:
                    i['datatype'].pop(k, None)
                    o['datatype'].pop(k, None)
            function_contents += drv.write_assign_to_output(
                o, i, outputs_in_inputs=drv.outputs_in_inputs,
                **assign_kws)
        lines = drv.write_function_def(
            'model', function_contents=function_contents,
            inputs=copy.deepcopy(inputs),
            outputs=copy.deepcopy(outputs),
            outputs_in_inputs=drv.outputs_in_inputs,
            opening_msg='IN MODEL', closing_msg='MODEL EXIT',
            print_inputs=True, print_outputs=True, **kwargs)
        with open(modelfile, 'w') as fd:
            print(modelfile)
            print('\n'.join(lines))
            fd.write('\n'.join(lines))
        env = {}
        env['TEST_LANGUAGE'] = language
        env['TEST_LANGUAGE_EXT'] = language_ext
        env['TEST_TYPENAME'] = typename
        if (language in ['c', 'fortran']) and (not using_generics):
            yaml_fields['vars'] = True
            if typename in ['array', 'object']:
                yaml_fields['dtype'] = True
        if any(list(yaml_fields.values())):
            lines = []
            for io, io_vars in zip(['input', 'output'],
                                   [inputs, outputs]):
                lines += [io + 's:',
                          '  name: %s' % io]
                if yaml_fields['vars']:
                    lines.append(
                        '  vars: %s' % self.get_varstr(
                            io_vars, language,
                            using_pointers=using_pointers,
                            length_prefix=length_prefix,
                            dont_add_lengths=dont_add_lengths))
                if yaml_fields['dtype']:
                    if len(io_vars) == 1:
                        dtype = io_vars[0]['datatype']
                    else:
                        dtype = {'type': 'array',
                                 'items': [x['datatype'] for
                                           x in io_vars]}
                    lines.append('  datatype:')
                    for x in yaml.dump(dtype).splitlines():
                        if "units: ''" in x:
                            continue
                        lines.append('    ' + x)
            env['TEST_MODEL_IO'] = '\n    '.join(lines) + '\n'
        else:
            env['TEST_MODEL_IO'] = ''
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
