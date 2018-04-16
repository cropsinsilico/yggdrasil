import tempfile
import os
import nose.tools as nt
from cis_interface import yamlfile
from cis_interface.tests import CisTestClass
_yaml_env = 'TEST_YAML_FILE'


def test_load_yaml_error():
    r"""Test error on loading invalid file."""
    nt.assert_raises(IOError, yamlfile.load_yaml, 'invalid')


def test_parse_component_error():
    r"""Test errors in parse_component."""
    nt.assert_raises(ValueError, yamlfile.parse_component,
                     {}, 'invalid', 'invalid')


class YamlTestBase(CisTestClass):
    r"""Test base for yamlfile."""
    _contents = tuple()

    def __init__(self, *args, **kwargs):
        super(YamlTestBase, self).__init__(*args, **kwargs)
        self.files = []
        for i in range(self.nfiles):
            self.files.append(self.get_fname(i))

    @property
    def nfiles(self):
        r"""int: Number of files."""
        return len(self.contents)

    @property
    def contents(self):
        r"""tuple: Contents of files."""
        return self._contents

    @property
    def yaml_env(self):
        r"""str: Environment variable where file path is stored."""
        return _yaml_env

    def setup(self):
        r"""Write contents to temp file."""
        super(YamlTestBase, self).setup()
        if self.nfiles > 0:
            os.environ[self.yaml_env] = self.files[0]
        for fname, content in zip(self.files, self.contents):
            with open(fname, 'w') as f:
                f.write('\n'.join(content))

    def teardown(self):
        r"""Remove the temporary file if it exists."""
        for fname in self.files:
            if os.path.isfile(fname):
                os.remove(fname)
        super(YamlTestBase, self).teardown()

    def get_fname(self, idx=0):
        r"""Path to temporary file."""
        return os.path.join(tempfile.gettempdir(),
                            '%s_%s_%d.yml' % (
                                tempfile.gettempprefix(), self.uuid, idx))

    def create_instance(self):
        r"""Disabled: Create a new instance of the class."""
        return None

    def test_parse_yaml(self):
        r"""Test successfully reading & parsing yaml."""
        if self.nfiles == 0:
            pass
        elif self.nfiles == 1:
            yamlfile.parse_yaml(self.files[0])
        else:
            yamlfile.parse_yaml(self.files)


class YamlTestBaseError(YamlTestBase):
    r"""Test error for yamlfile."""
    _error = None

    def test_parse_yaml(self):
        r"""Test error reading & parsing yaml."""
        if (self._error is None) or (self.nfiles == 0):
            return
        nt.assert_raises(self._error, yamlfile.parse_yaml, self.files)


class TestYamlModelOnly(YamlTestBase):
    r"""Test parsing of different numbers/styles of models."""
    _contents = (['models:',
                  '  - name: modelA',
                  '    driver: GCCModelDriver',
                  '    args: ./src/modelA.c'],
                 ['model:',
                  '  - name: modelB',
                  '    driver: GCCModelDriver',
                  '    args: ./src/modelB.c'],
                 ['model:',
                  '  name: modelC',
                  '  driver: GCCModelDriver',
                  '  args: ./src/modelC.c'],
                 ['models:',
                  '  name: modelD',
                  '  driver: GCCModelDriver',
                  '  args: ./src/modelD.c'], )


class TestYamlServerClient(YamlTestBase):
    r"""Test specification of server/client models."""
    _contents = (['models:',
                  '  - name: modelA',
                  '    driver: GCCModelDriver',
                  '    args: ./src/modelA.c',
                  '    is_server: True'],
                 ['model:',
                  '  - name: modelB',
                  '    driver: GCCModelDriver',
                  '    args: ./src/modelB.c',
                  '    client_of: modelA'],)


class TestYamlIODrivers(YamlTestBase):
    r"""Test full specification of IO drivers."""
    _contents = (['models:',
                  '  - name: modelA',
                  '    driver: GCCModelDriver',
                  '    args: ./src/modelA.c',
                  '    inputs:',
                  '      - name: inputA',
                  '        driver: FileInputDriver',
                  '        args: fileA.txt'],
                 ['model:',
                  '  - name: modelB',
                  '    driver: GCCModelDriver',
                  '    args: ./src/modelB.c',
                  '    input:',
                  '      - name: inputB',
                  '        driver: FileInputDriver',
                  '        args: fileB.txt'],
                 ['model:',
                  '  name: modelC',
                  '  driver: GCCModelDriver',
                  '  args: ./src/modelC.c',
                  '  input:',
                  '    name: inputC',
                  '    driver: FileInputDriver',
                  '    args: fileC.txt'],
                 ['models:',
                  '  name: modelD',
                  '  driver: GCCModelDriver',
                  '  args: ./src/modelD.c',
                  '  inputs:',
                  '    name: inputD',
                  '    driver: FileInputDriver',
                  '    args: fileD.txt'], )


class TestYamlConnection(YamlTestBase):
    r"""Test connection between I/O channels."""
    _contents = (['models:',
                  '  - name: modelA',
                  '    driver: GCCModelDriver',
                  '    args: ./src/modelA.c',
                  '    inputs:',
                  '      - inputA',
                  '',
                  'connections:',
                  '  - input: outputB',
                  '    output: inputA'],
                 ['models:',
                  '  - name: modelB',
                  '    driver: GCCModelDriver',
                  '    args: ./src/modelB.c',
                  '    outputs:',
                  '      - outputB'],)


class TestYamlConnectionInputFile(YamlTestBase):
    r"""Test connection with File."""
    _contents = (['models:',
                  '  - name: modelA',
                  '    driver: GCCModelDriver',
                  '    args: ./src/modelA.c',
                  '    inputs:',
                  '      - inputA',
                  '    outputs:',
                  '      - outputA',
                  '',
                  'connections:',
                  '  - input: {{ %s }}' % _yaml_env,
                  '    output: inputA',
                  '  - input: outputA',
                  '    output: output.txt'],)


class TestYamlConnectionInputAsciiFile(YamlTestBase):
    r"""Test connection with AsciiFile."""
    _contents = (['models:',
                  '  - name: modelA',
                  '    driver: GCCModelDriver',
                  '    args: ./src/modelA.c',
                  '    inputs:',
                  '      - inputA',
                  '    outputs:',
                  '      - outputA',
                  '',
                  'connections:',
                  '  - input: {{ %s }}' % _yaml_env,
                  '    output: inputA',
                  '    read_meth: line',
                  '  - input: outputA',
                  '    output: output.txt',
                  '    write_meth: line'],)


class TestYamlConnectionInputAsciiTable(YamlTestBase):
    r"""Test connection with AsciiTable."""
    _contents = (['models:',
                  '  - name: modelA',
                  '    driver: GCCModelDriver',
                  '    args: ./src/modelA.c',
                  '    inputs:',
                  '      - inputA',
                  '    outputs:',
                  '      - outputA',
                  '',
                  'connections:',
                  '  - input: {{ %s }}' % _yaml_env,
                  '    output: inputA',
                  '    read_meth: table',
                  '  - input: outputA',
                  '    output: output.txt',
                  '    write_meth: table'],)


class TestYamlConnectionInputAsciiTableArray(YamlTestBase):
    r"""Test connection with AsciiTable as array."""
    _contents = (['models:',
                  '  - name: modelA',
                  '    driver: GCCModelDriver',
                  '    args: ./src/modelA.c',
                  '    inputs:',
                  '      - inputA',
                  '    outputs:',
                  '      - outputA',
                  '',
                  'connections:',
                  '  - input: {{ %s }}' % _yaml_env,
                  '    output: inputA',
                  '    read_meth: table_array',
                  '    field_units: name,count,size',
                  '    format_str: "%5s\t%d\t%f\n"',
                  '  - input: outputA',
                  '    output: output.txt',
                  '    write_meth: table_array',
                  '    field_units: name,count,size',
                  '    format_str: "%5s\t%d\t%f\n"'], )


class TestYamlComponentError(YamlTestBaseError):
    r"""Test error for non-dictionary component."""
    _error = TypeError
    _contents = (['models: error'],)


class TestYamlDuplicateError(YamlTestBaseError):
    r"""Test error when there are two components with the same name."""
    _error = ValueError
    _contents = (['models:',
                  '  - name: modelA',
                  '    driver: GCCModelDriver',
                  '    args: ./src/modelA.c',
                  '  - name: modelA',
                  '    driver: GCCModelDriver',
                  '    args: ./src/modelA.c'],)


class TestYamlConnectionError(YamlTestBaseError):
    r"""Test error when there is not connection for a model I/O channel."""
    _error = RuntimeError
    _contents = (['models:',
                  '  - name: modelA',
                  '    driver: GCCModelDriver',
                  '    args: ./src/modelA.c',
                  '    inputs:',
                  '      - inputA'],)


class TestYamlMissingModelArgsError(YamlTestBaseError):
    r"""Test error when there is a missing arguments to a model."""
    _error = RuntimeError
    _contents = (['models:',
                  '  - name: modelA',
                  '    args: ./src/modelA.c',
                  '    inputs:',
                  '      name: inputA',
                  '      driver: FileInputDriver',
                  '      args: fileA.txt'],)


class TestYamlMissingIOArgsError(YamlTestBaseError):
    r"""Test error when there is a missing arguments to an I/O driver."""
    _error = RuntimeError
    _contents = (['models:',
                  '  - name: modelA',
                  '    driver: GCCModelDriver',
                  '    args: ./src/modelA.c',
                  '    inputs:',
                  '      name: inputA',
                  '      driver: FileInputDriver'],)


class TestYamlMissingConnArgsError(YamlTestBaseError):
    r"""Test error when there is a missing arguments to a connection."""
    _error = RuntimeError
    _contents = (['models:',
                  '  - name: modelA',
                  '    driver: GCCModelDriver',
                  '    args: ./src/modelA.c',
                  '    inputs:',
                  '      - inputA',
                  '',
                  'connections:',
                  '  - input: outputB'],
                 ['models:',
                  '  - name: modelB',
                  '    driver: GCCModelDriver',
                  '    args: ./src/modelB.c',
                  '    outputs:',
                  '      - outputB'],)


class TestYamlMissingConnInputError(YamlTestBaseError):
    r"""Test error when there is no model output matching connection input."""
    _error = RuntimeError
    _contents = (['models:',
                  '  - name: modelA',
                  '    driver: GCCModelDriver',
                  '    args: ./src/modelA.c',
                  '    inputs:',
                  '      - inputA',
                  '',
                  'connections:',
                  '  - input: outputB',
                  '    output: inputA'],
                 ['models:',
                  '  - name: modelB',
                  '    driver: GCCModelDriver',
                  '    args: ./src/modelB.c'],)


class TestYamlMissingConnInputFileError(YamlTestBaseError):
    r"""Test error when there is no file for missing connection input."""
    _error = RuntimeError
    _contents = (['models:',
                  '  - name: modelA',
                  '    driver: GCCModelDriver',
                  '    args: ./src/modelA.c',
                  '',
                  'connections:',
                  '  - input: outputB',
                  '    output: inputA'],
                 ['models:',
                  '  - name: modelB',
                  '    driver: GCCModelDriver',
                  '    args: ./src/modelB.c'],)


class TestYamlMissingConnIOError(YamlTestBaseError):
    r"""Test error when there is no model input/output matching connection."""
    _error = RuntimeError
    _contents = (['models:',
                  '  - name: modelA',
                  '    driver: GCCModelDriver',
                  '    args: ./src/modelA.c',
                  '',
                  'connections:',
                  '  - input: {{ %s }}' % _yaml_env,
                  '    output: inputA'],)


class TestYamlConnectionInputFileReadMethError(YamlTestBaseError):
    r"""Test error for invalid read_meth."""
    _error = ValueError
    _contents = (['models:',
                  '  - name: modelA',
                  '    driver: GCCModelDriver',
                  '    args: ./src/modelA.c',
                  '    inputs:',
                  '      - inputA',
                  '    outputs:',
                  '      - outputA',
                  '',
                  'connections:',
                  '  - input: {{ %s }}' % _yaml_env,
                  '    output: inputA',
                  '    read_meth: invalid',
                  '  - input: outputA',
                  '    output: output.txt'],)


class TestYamlConnectionInputFileWriteMethError(YamlTestBaseError):
    r"""Test error for invalid write_meth."""
    _error = ValueError
    _contents = (['models:',
                  '  - name: modelA',
                  '    driver: GCCModelDriver',
                  '    args: ./src/modelA.c',
                  '    inputs:',
                  '      - inputA',
                  '    outputs:',
                  '      - outputA',
                  '',
                  'connections:',
                  '  - input: {{ %s }}' % _yaml_env,
                  '    output: inputA',
                  '  - input: outputA',
                  '    output: output.txt',
                  '    write_meth: invalid'],)
