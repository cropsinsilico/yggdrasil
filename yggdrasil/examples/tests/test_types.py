import os
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
    def setup_model(cls, language, typename, language_ext=None):
        r"""Write the model file for the specified combination of
        language and type.

        Args:
            language (str): Language that model should be written in.
            typename (str): Type that should be expected by the model.
            language_ext (str, optional): Extension that should be used
                for the model file. If not provided, the extension is
                determined from the specified language.

        Returns:
            str: Full path to the file that was written.

        """
        if language_ext is None:
            language_ext = get_language_ext(language)
        modelfile = os.path.join(_example_dir, cls.example_name,
                                 'src', 'model' + language_ext)
        drv = import_component('model', language)
        testdata = cls.get_test_data(typename)
        testtype = encode_type(testdata)
        inputs = [{'name': 'x', 'datatype': testtype}]
        outputs = [{'name': 'y', 'datatype': testtype}]
        # Write the model
        function_contents = drv.write_assign_to_output(
            outputs[0], inputs[0],
            outputs_in_inputs=drv.outputs_in_inputs)
        function_contents.append(
            drv.format_function_param('print', message='IN MODEL'))
        print_key = None
        if ('print_%s' % testtype['type']) in drv.function_param:
            print_key = ('print_%s' % testtype['type'])
        elif 'print_any' in drv.function_param:
            print_key = 'print_any'
        if print_key is not None:
            for x in inputs:
                function_contents += [
                    drv.format_function_param('print', message=(
                        'INPUT[%s]:' % x['name'])),
                    drv.format_function_param(print_key,
                                              object=x['name'])]
            for x in outputs:
                function_contents += [
                    drv.format_function_param('print', message=(
                        'OUTPUT[%s]:' % x['name'])),
                    drv.format_function_param(print_key,
                                              object=x['name'])]
        lines = drv.write_function_def(
            'model', function_contents=function_contents,
            inputs=inputs, outputs=outputs, outputs_in_inputs=drv.outputs_in_inputs)
        with open(modelfile, 'w') as fd:
            fd.write('\n'.join(lines))
        os.environ['TEST_LANGUAGE'] = language
        os.environ['TEST_LANGUAGE_EXT'] = language_ext
        os.environ['TEST_TYPENAME'] = typename
        if language == 'c':
            in_vars = 'x'
            out_vars = 'y'
            if typename in ['string', 'bytes', 'unicode', '1darray']:
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
