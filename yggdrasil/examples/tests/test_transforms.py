import os
import copy
import pprint
import numpy as np
from yggdrasil import tools, units
from yggdrasil.tests import assert_equal
from yggdrasil.components import import_component, create_component
from yggdrasil.languages import get_language_ext
from yggdrasil.examples import _example_dir
from yggdrasil.examples.tests import ExampleTstBase
from yggdrasil.metaschema.datatypes import encode_type


_all_lang = tools.get_supported_lang()
_untyped_lang = tuple([x for x in _all_lang if
                       (not import_component('model', x).is_typed)])


class TestExampleTransforms(ExampleTstBase):
    r"""Test the Transforms example."""

    example_name = 'transforms'
    iter_over = ['language', 'transform']
    iter_list_language = _untyped_lang
    iter_list_transform = ['table', 'array', 'pandas']

    def __init__(self, *args, **kwargs):
        self._output_files = None
        super(TestExampleTransforms, self).__init__(*args, **kwargs)

    @property
    def output_files(self):
        r"""list: Output files for the run."""
        return self._output_files

    @classmethod
    def get_test_data(cls):
        r"""Determine a test data set for the specified type.

        Returns:
            object: Example of specified datatype.

        """
        field_names = ['name', 'count', 'size']
        field_units = ['n/a', 'umol', 'cm']
        dtype = np.dtype(
            {'names': field_names,
             'formats': ['S5', 'i4', 'f8']})
        rows = [(b'one', np.int32(1), 1.0),
                (b'two', np.int32(2), 2.0),
                (b'three', np.int32(3), 3.0)]
        arr = np.array(rows, dtype=dtype)
        lst = [units.add_units(arr[n], u) for n, u
               in zip(field_names, field_units)]
        return lst

    @classmethod
    def check_received_data(cls, transform, x_recv):
        r"""Check that the received message is equivalent to the
        test data for the specified type.

        Args:
            transform (str): Name of transform being tested.
            x_recv (object): Received object.

        Raises:
            AssertionError: If the received message is not equivalent
                to the received message.

        """
        try:
            t = create_component('transform', subtype=transform)
        except ValueError:
            def t(x):
                return x
        x_sent = t(cls.get_test_data())
        print('RECEIVED:')
        pprint.pprint(x_recv)
        print('EXPECTED:')
        pprint.pprint(x_sent)
        assert_equal(x_recv, x_sent)

    @classmethod
    def setup_model(cls, language, transform, language_ext=None, **kwargs):
        r"""Write the model file for the specified combination of
        language and type.

        Args:
            language (str): Language that model should be written in.
            transform (str): Transformation that should be performed.
            language_ext (str, optional): Extension that should be used
                for the model file. If not provided, the extension is
                determined from the specified language.
            **kwargs: Additional keyword arguments are passed to
                the write_function_def class method of the language
                driver.

        Returns:
            tuple(str, dict): Full path to the file that was written
                and the environment variables that should be set before
                running the integration.

        """
        if language_ext is None:
            language_ext = get_language_ext(language)
        modelfile = os.path.join(_example_dir, cls.example_name,
                                 'src', 'model' + language_ext)
        drv = import_component('model', language)
        testdata = cls.get_test_data()
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
            print_inputs=True, print_outputs=True, **kwargs)
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
        return modelfile, env

    def check_results(self):
        r"""This should be overridden with checks for the result."""
        pass

    def run_example(self, **kwargs):
        r"""This runs an example in the correct language."""
        self.oldenv_yaml = {}
        if self.yaml is not None:
            modelfile, env = self.setup_model(self.language,
                                              self.iter_param['transform'],
                                              **kwargs)
            self._output_files = [modelfile]
            for k, v in env.items():
                self.oldenv_yaml[k] = os.environ.get(k, None)
                os.environ[k] = v
        try:
            super(TestExampleTransforms, self).run_example()
        finally:
            for k, v in self.oldenv_yaml.items():
                if v is None:
                    del os.environ[k]
                else:
                    os.environ[k] = v  # pragma: no cover
