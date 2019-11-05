import os
import copy
import pprint
from yggdrasil.components import import_component
from yggdrasil.languages import get_language_ext
from yggdrasil.metaschema.datatypes import get_type_class
from yggdrasil.examples import _example_dir
from yggdrasil.examples.tests import ExampleTstBase
from yggdrasil.metaschema.datatypes import encode_type


class TestExampleTypes(ExampleTstBase):
    r"""Test the Types example."""

    example_name = 'types'
    iter_over = ['language', 'type']

    def __init__(self, *args, **kwargs):
        self.datatype = None
        self._output_files = None
        super(TestExampleTypes, self).__init__(*args, **kwargs)

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
    def setup_model(cls, language, typename, language_ext=None,
                    using_pointers=False, using_generics=False):
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

        Returns:
            str: Full path to the file that was written.

        """
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
        inputs = [{'name': 'x', 'datatype': copy.deepcopy(testtype)}]
        outputs = [{'name': 'y', 'datatype': copy.deepcopy(testtype)}]
        # Write the model
        function_contents = []
        for i, o in zip(inputs, outputs):
            if using_pointers and drv.is_typed:
                for k in ['shape', 'length']:
                    i['datatype'].pop(k, None)
                    o['datatype'].pop(k, None)
            function_contents += drv.write_assign_to_output(
                o, i, outputs_in_inputs=drv.outputs_in_inputs)
        lines = drv.write_function_def(
            'model', function_contents=function_contents,
            inputs=inputs, outputs=outputs,
            outputs_in_inputs=drv.outputs_in_inputs,
            opening_msg='IN MODEL',
            print_inputs=True, print_outputs=True)
        with open(modelfile, 'w') as fd:
            print(modelfile)
            print('\n'.join(lines))
            fd.write('\n'.join(lines))
        os.environ['TEST_LANGUAGE'] = language
        os.environ['TEST_LANGUAGE_EXT'] = language_ext
        os.environ['TEST_TYPENAME'] = typename
        if language == 'c' and (not using_generics):
            in_vars = 'x'
            out_vars = 'y'
            if using_pointers:
                if typename in ['string', 'bytes', 'unicode', '1darray']:
                    in_vars += ', x_length'
                    out_vars += ', y_length'
                elif typename in ['ndarray']:
                    in_vars += ', x_ndim, x_shape'
                    out_vars += ', y_ndim, y_shape'
            elif typename in ['string', 'bytes', 'unicode']:
                in_vars += ', x_length'
                out_vars += ', y_length'
            os.environ['TEST_MODEL_IO'] = (
                'inputs:\n'
                '      name: input\n'
                '      vars: ' + in_vars + '\n'
                '    outputs:\n'
                '      name: output\n'
                '      vars: ' + out_vars + '\n')
        else:
            os.environ['TEST_MODEL_IO'] = ''
        return modelfile

    def check_results(self):
        r"""This should be overridden with checks for the result."""
        pass
    
    def run_example(self):
        r"""This runs an example in the correct language."""
        self._output_files = [self.setup_model(self.language,
                                               self.datatype)]
        super(TestExampleTypes, self).run_example()
        drv = import_component('model', self.language)
        if drv.is_typed:
            # Version using generic type
            self._output_files = [self.setup_model(self.language,
                                                   self.datatype,
                                                   using_generics=True)]
            super(TestExampleTypes, self).run_example()
            # Version using pointers
            self._output_files = [self.setup_model(self.language,
                                                   self.datatype,
                                                   using_pointers=True)]
            super(TestExampleTypes, self).run_example()
