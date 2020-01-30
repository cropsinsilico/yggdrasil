import os
import copy
import pprint
import yaml
from yggdrasil import tools
from yggdrasil.components import import_component
from yggdrasil.languages import get_language_ext
from yggdrasil.metaschema.datatypes import get_type_class
from yggdrasil.tests import long_running
from yggdrasil.examples import _example_dir
from yggdrasil.examples.tests import ExampleTstBase
from yggdrasil.metaschema.datatypes import encode_type


_all_lang = tools.get_supported_lang()
_typed_lang = tuple([x for x in _all_lang if
                     import_component('model', x).is_typed])


@long_running
class TestExampleTypes(ExampleTstBase):
    r"""Test the Types example."""

    example_name = 'types'
    iter_over = ['language', 'type', 'method']
    iter_skip = [(set(_typed_lang), '*', 'run_example_generic'),
                 (set(_typed_lang), '*', 'run_example_pointers'),
                 (set(['c']), '*', 'run_example_c_nolengths'),
                 (set(['c']), '*', 'run_example_c_prefixes'),
                 ('c', set(['string', 'bytes', 'unicode']), 'run_example_c_nolengths'),
                 ('c', set(['1darray', 'ndarray']), 'run_example_c_prefixes'),
                 ('*', set(['array']), 'run_example_split_array')]
    iter_flaky = [('c', 'instance', '*'), ('cpp', 'instance', '*')]
    iter_list_language = _all_lang
    iter_list_method = ['run_example', 'run_example_generic',
                        'run_example_pointers', 'run_example_c_nolengths',
                        'run_example_c_prefixes', 'run_example_split_array']

    def __init__(self, *args, **kwargs):
        self._output_files = None
        super(TestExampleTypes, self).__init__(*args, **kwargs)

    @property
    def datatype(self):
        r"""str: Name of datatype being used by the current iteration."""
        return self.iter_param.get('datatype', None)

    @property
    def output_files(self):
        r"""list: Output files for the run."""
        return self._output_files

    @classmethod
    def get_test_data(cls, typename):
        r"""Determine a test data set for the specified type.

        Args:
            typename (str): Name of datatype.

        Returns:
            object: Example of specified datatype.

        """
        typeclass = get_type_class(typename)
        testclass = typeclass.import_test_class()
        out = testclass._valid_decoded[0]
        return out

    @classmethod
    def check_received_data(cls, typename, x_recv):
        r"""Check that the received message is equivalent to the
        test data for the specified type.

        Args:
            typename (str): Name of datatype.
            x_recv (object): Received object.

        Raises:
            AssertionError: If the received message is not equivalent
                to the received message.

        """
        typeclass = get_type_class(typename)
        testclass = typeclass.import_test_class()
        x_sent = cls.get_test_data(typename)
        print('RECEIVED:')
        pprint.pprint(x_recv)
        print('EXPECTED:')
        pprint.pprint(x_sent)
        testclass.assert_result_equal(x_recv, x_sent)

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
        
    @classmethod
    def setup_model(cls, language, typename, language_ext=None,
                    using_pointers=False, using_generics=False,
                    split_array=False, dont_add_lengths=False,
                    length_prefix=False, assign_kws=None, **kwargs):
        r"""Write the model file for the specified combination of
        language and type.

        Args:
            language (str): Language that model should be written in.
            typename (str): Type that should be expected by the model.
            language_ext (str, optional): Extension that should be used
                for the model file. If not provided, the extension is
                determined from the specified language.
            using_pointers (bool, optional): If True and the tested
                language supports pointers, pointers will be used rather
                than explicit arrays. Defaults to False.
            using_generics (bool, optional): If True and the tested
                language has a dedicated generic class, the generic
                type will be used rather than explict types. Defaults
                to False.
            split_array (bool, optional): If True and the tested datatype
                is an array, the variables will be split and specified
                explicitly in the yaml. Defaults to False.
            dont_add_lengths (bool, optional): If True, lengths will not
                be added to the definition or assignments. Defaults to
                False.
            length_prefix (bool, optional): If True, the length variables
                will be given prefixes instead of suffixes. Defaults to
                False.
            assign_kws (dict, optional): Keyword arguments for the calls
                to write_assign_to_output. Defaults to {}.
            **kwargs: Additional keyword arguments are passed to
                the write_function_def class method of the language
                driver.

        Returns:
            str: Full path to the file that was written.

        """
        if assign_kws is None:
            assign_kws = {}
        if language in ['c', 'c++', 'cpp']:
            # dont_add_lengths is only valid for C/C++
            kwargs['dont_add_lengths'] = dont_add_lengths
            kwargs['use_length_prefix'] = length_prefix
            assign_kws.setdefault('dont_add_lengths', dont_add_lengths)
            assign_kws.setdefault('use_length_prefix', length_prefix)
        yaml_fields = {'vars': False, 'dtype': False}
        if language_ext is None:
            language_ext = get_language_ext(language)
        modelfile = os.path.join(_example_dir, cls.example_name,
                                 'src', 'model' + language_ext)
        drv = import_component('model', language)
        if using_generics and drv.is_typed:
            testtype = {'type': 'any'}
        else:
            testdata = cls.get_test_data(typename)
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
        os.environ['TEST_LANGUAGE'] = language
        os.environ['TEST_LANGUAGE_EXT'] = language_ext
        os.environ['TEST_TYPENAME'] = typename
        if language == 'c' and (not using_generics):
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
                        '  vars: %s' % cls.get_varstr(
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
            os.environ['TEST_MODEL_IO'] = '\n    '.join(lines) + '\n'
        else:
            os.environ['TEST_MODEL_IO'] = ''
        return modelfile

    def check_results(self):
        r"""This should be overridden with checks for the result."""
        pass

    def run_example(self, **kwargs):
        r"""This runs an example in the correct language."""
        if self.yaml is not None:
            self._output_files = [self.setup_model(self.language,
                                                   self.datatype,
                                                   **kwargs)]
        super(TestExampleTypes, self).run_example()
        
    def run_example_generic(self):
        r"""Version of the example using generic type."""
        drv = import_component('model', self.language)
        if drv.is_typed:
            self.run_example(using_generics=True)

    def run_example_pointers(self):
        r"""Version of the example using pointers."""
        drv = import_component('model', self.language)
        if drv.is_typed:
            self.run_example(using_pointers=True)
    
    def run_example_c_nolengths(self):
        r"""Version of the example in C using pointers & no lengths."""
        drv = import_component('model', self.language)
        if ((drv.is_typed and (self.language == 'c')
             and (self.datatype in ['string', 'bytes', 'unicode']))):
            self.run_example(using_pointers=True,
                             dont_add_lengths=True)
    
    def run_example_c_prefixes(self):
        r"""Version of the example in C using pointers & prefixes."""
        drv = import_component('model', self.language)
        if ((drv.is_typed and (self.language == 'c')
             and (self.datatype in ['1darray', 'ndarray']))):
            self.run_example(using_pointers=True,
                             length_prefix=True)

    def run_example_split_array(self):
        r"""Version of the example where array is split."""
        if self.datatype == 'array':
            self.run_example(split_array=True)
