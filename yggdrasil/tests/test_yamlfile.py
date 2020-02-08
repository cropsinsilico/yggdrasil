import tempfile
import os
import yaml
import io as sio
from jsonschema.exceptions import ValidationError
from yggdrasil import yamlfile
from yggdrasil.tests import YggTestClass, assert_raises, assert_equal
_yaml_env = 'TEST_YAML_FILE'


def direct_translate(msg):  # pragma: no cover
    r"""Test translator that just returns passed message."""
    return msg


def test_load_yaml():
    r"""Test loading yaml."""
    cwd = os.getcwd()
    fname = os.path.join(cwd, 'test_load_yaml.yml')
    dict_write = {'test': 'hello'}
    dict_read = {'test': 'hello',
                 'working_dir': cwd}
    contents = yaml.dump(dict_write)
    with open(fname, 'w') as fd:
        yaml.dump(dict_write, fd)
    try:
        # Dictionary
        out = yamlfile.load_yaml(dict_write)
        assert_equal(out, dict_read)
        # File name
        out = yamlfile.load_yaml(fname)
        assert_equal(out, dict_read)
        # Open file object
        with open(fname, 'r') as fd:
            out = yamlfile.load_yaml(fd)
            assert_equal(out, dict_read)
        # Open stream
        out = yamlfile.load_yaml(sio.StringIO(contents))
        assert_equal(out, dict_read)
    finally:
        # Remove file
        if os.path.isfile(fname):
            os.remove(fname)


def test_load_yaml_error():
    r"""Test error on loading invalid file."""
    assert_raises(IOError, yamlfile.load_yaml, 'invalid')


def test_parse_component_error():
    r"""Test errors in parse_component."""
    assert_raises(TypeError, yamlfile.parse_component,
                  1, 'invalid', 'invalid')
    assert_raises(ValueError, yamlfile.parse_component,
                  {}, 'invalid', 'invalid')


class YamlTestBase(YggTestClass):
    r"""Test base for yamlfile."""
    _contents = tuple()
    _include = tuple()
    _use_json = False

    def __init__(self, *args, **kwargs):
        super(YamlTestBase, self).__init__(*args, **kwargs)
        self.files = []
        self.include_files = []
        for i in range(self.nfiles):
            self.files.append(self.get_fname(i))
        for i in range(len(self.include)):
            self.include_files.append(self.get_fname(i, '_incl'))

    @property
    def nfiles(self):
        r"""int: Number of files."""
        return len(self.contents)

    @property
    def contents(self):
        r"""tuple: Contents of files."""
        return self._contents

    @property
    def include(self):
        r"""tuple: Contents of included files."""
        return self._include

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
        for i, (fname, content) in enumerate(zip(self.include_files,
                                                 self.include)):
            os.environ['%s%d' % (self.yaml_env, i)] = os.path.join(
                '.', os.path.basename(fname))
            with open(fname, 'w') as f:
                f.write('\n'.join(content))

    def teardown(self):
        r"""Remove the temporary file if it exists."""
        for fname in self.files:
            if os.path.isfile(fname):
                os.remove(fname)
        super(YamlTestBase, self).teardown()

    def get_fname(self, idx=0, suffix=''):
        r"""Path to temporary file."""
        if self._use_json:
            ext = '.json'
        else:
            ext = '.yml'
        return os.path.join(tempfile.gettempdir(),
                            '%s_%s_%d%s%s' % (
                                tempfile.gettempprefix(), self.uuid,
                                idx, suffix, ext))

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

    def test_load_yaml_git(self):
        yml = "https://github.com/cropsinsilico/example-fakemodel/fakemodel.yml"
        self.assertRaises(Exception, yamlfile.load_yaml, yml)
        self.assertTrue('model' in yamlfile.load_yaml('git:' + yml))
        yml = "cropsinsilico/example-fakemodel/fakemodel.yml"
        self.assertTrue('model' in yamlfile.load_yaml('git:' + yml))


class YamlTestBaseError(YamlTestBase):
    r"""Test error for yamlfile."""
    _error = None

    def test_parse_yaml(self):
        r"""Test error reading & parsing yaml."""
        if (self._error is None) or (self.nfiles == 0):
            return
        assert_raises(self._error, yamlfile.parse_yaml, self.files)


class TestJSONModelOnly(YamlTestBase):
    r"""Test parsing of different numbers/styles of models from JSON."""
    _use_json = True
    _contents = (['{"models":',
                  '   [{"name": "modelA",',
                  '     "driver": "GCCModelDriver",',
                  '     "args": "./src/modelA.c"}]}'],)
        

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
                  '        translator: %s:direct_translate' % __name__,
                  '        onexit: printStatus',
                  '        args: {{ %s }}' % _yaml_env,
                  '    outputs:',
                  '      - name: outputA',
                  '        driver: FileOutputDriver',
                  '        translator: %s:direct_translate' % __name__,
                  '        onexit: printStatus',
                  '        args: fileA.txt',
                  '      - name: outputA2',
                  '        driver: OutputDriver',
                  '        translator: %s:direct_translate' % __name__,
                  '        onexit: printStatus',
                  '        args: A_to_B'],
                 ['model:',
                  '  - name: modelB',
                  '    driver: GCCModelDriver',
                  '    args: ./src/modelB.c',
                  '    input:',
                  '      - name: inputB',
                  '        driver: FileInputDriver',
                  '        args: {{ %s }}' % _yaml_env,
                  '      - name: inputB2',
                  '        driver: InputDriver',
                  '        args: A_to_B'],
                 ['model:',
                  '  name: modelC',
                  '  driver: GCCModelDriver',
                  '  args: ./src/modelC.c',
                  '  input:',
                  '    name: inputC',
                  '    driver: FileInputDriver',
                  '    args: {{ %s }}' % _yaml_env],
                 ['models:',
                  '  name: modelD',
                  '  driver: GCCModelDriver',
                  '  args: ./src/modelD.c',
                  '  inputs:',
                  '    name: inputD',
                  '    driver: FileInputDriver',
                  '    args: {{ %s }}' % _yaml_env], )


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


class TestYamlInclude(YamlTestBase):
    r"""Test connection between I/O channels in yaml included from one."""
    _contents = (['include: {{ %s0 }}' % _yaml_env,
                  'models:',
                  '  - name: modelA',
                  '    driver: GCCModelDriver',
                  '    args: ./src/modelA.c',
                  '    inputs:',
                  '      - inputA',
                  '',
                  'connections:',
                  '  - input: outputB',
                  '    output: inputA'],)
    _include = (['models:',
                 '  - name: modelB',
                 '    driver: GCCModelDriver',
                 '    args: ./src/modelB.c',
                 '    outputs:',
                 '      - outputB'],)


class TestYamlIODatatype(YamlTestBase):
    r"""Test specification of datatype via schema."""
    _contents = (['models:',
                  '  - name: modelA',
                  '    driver: GCCModelDriver',
                  '    args: ./src/modelA.c',
                  '    inputs:',
                  '      - name: inputA',
                  '        type: object',
                  '        properties:',
                  '          a: int',
                  "          b: {'type': float, 'units': 'cm'}",
                  '',
                  'connections:',
                  "  - from: ['outputB::0', 'outputB::1']",
                  "    to: ['inputA::a', 'inputA::b']"],
                 ['models:',
                  '  - name: modelB',
                  '    driver: GCCModelDriver',
                  '    args: ./src/modelB.c',
                  '    outputs:',
                  '      - name: outputB',
                  '        type: [int, float]'],)


class TestYamlConnectionFork(YamlTestBase):
    r"""Test connection between I/O channels."""
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
                  '  - inputs: ',
                  '      - outputB',
                  '      - outputC',
                  '    output: inputA',
                  '  - input: outputA',
                  '    outputs:',
                  '      - inputB',
                  '      - inputC'],
                 ['models:',
                  '  - name: modelB',
                  '    driver: GCCModelDriver',
                  '    args: ./src/modelB.c',
                  '    inputs:',
                  '      - inputB',
                  '    outputs:',
                  '      - outputB'],
                 ['models:',
                  '  - name: modelC',
                  '    driver: GCCModelDriver',
                  '    args: ./src/modelC.c',
                  '    inputs:',
                  '      - inputC',
                  '    outputs:',
                  '      - outputC'],)


class TestYamlConnectionTranslator(YamlTestBase):
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
                  '    output: inputA',
                  '    translator: %s:direct_translate' % __name__],
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
                  '  - input:',
                  '      - {{ %s }}' % _yaml_env,
                  '    read_meth: all',
                  '    output: inputA',
                  '  - input: outputA',
                  '    output:',
                  '      - output.txt',
                  '    write_meth: all'],)


class TestYamlConnectionInputFile_wait(YamlTestBase):
    r"""Test connection with File where wait_for_creation specified."""
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
                  '  - input:',
                  '      - {{ %s }}' % _yaml_env,
                  '    read_meth: all',
                  '    output: inputA',
                  '  - input: outputA',
                  '    output:',
                  '      - output.txt',
                  '    write_meth: all'],)


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
                  '  - input: invalid.txt',
                  '    output: inputA',
                  '    wait_for_creation: 4',
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


class TestYamlConnectionInputPickle(YamlTestBase):
    r"""Test connection with Pickle."""
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
                  '    read_meth: pickle',
                  '  - input: outputA',
                  '    output: output.txt',
                  '    write_meth: pickle'], )


class TestYamlConnectionInputPandas(YamlTestBase):
    r"""Test connection with Pandas csv."""
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
                  '    read_meth: pandas',
                  '    field_units: name,count,size',
                  '    format_str: "%5s\t%d\t%f\n"',
                  '  - input: outputA',
                  '    output: output.txt',
                  '    write_meth: pandas',
                  '    field_units: name,count,size',
                  '    format_str: "%5s\t%d\t%f\n"'], )


class TestYamlConnectionInputAsciiMap(YamlTestBase):
    r"""Test connection with AsciiMap."""
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
                  '    read_meth: map',
                  '  - input: outputA',
                  '    output: output.txt',
                  '    write_meth: map'], )


class TestYamlConnectionInputPly(YamlTestBase):
    r"""Test connection with Ply file."""
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
                  '    read_meth: ply',
                  '  - input: outputA',
                  '    output: output.ply',
                  '    write_meth: ply'], )


class TestYamlConnectionInputObj(YamlTestBase):
    r"""Test connection with Obj file."""
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
                  '    read_meth: obj',
                  '  - input: outputA',
                  '    output: output.obj',
                  '    write_meth: obj'], )


class TestYamlComponentError(YamlTestBaseError):
    r"""Test error for non-dictionary component."""
    _error = ValidationError
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


class TestYamlConnectionError_forkin(YamlTestBaseError):
    r"""Test error when there is not connection for a fork input channel."""
    _error = RuntimeError
    _contents = (['models:',
                  '  - name: modelA',
                  '    driver: GCCModelDriver',
                  '    args: ./src/modelA.c',
                  '    inputs:',
                  '      - inputA',
                  'connections:',
                  '  - input:',
                  '      - output1',
                  '      - output2',
                  '    output: inputA'],)


# Error not raised as both outputs could be files
# class TestYamlConnectionError_forkout(YamlTestBaseError):
#     r"""Test error when there is not connection for a fork output channel."""
#     _error = RuntimeError
#     _contents = (['models:',
#                   '  - name: modelA',
#                   '    driver: GCCModelDriver',
#                   '    args: ./src/modelA.c',
#                   '    outputs:',
#                   '      - outputA',
#                   'connections:',
#                   '  - input: outputA',
#                   '    output:',
#                   '      - input1',
#                   '      - input2'],)


class TestYamlConnectionError_readmeth(YamlTestBaseError):
    r"""Test error when read_meth is specified for non-file."""
    _error = ValidationError
    _contents = (['models:',
                  '  - name: modelA',
                  '    driver: GCCModelDriver',
                  '    args: ./src/modelA.c',
                  '    inputs:',
                  '      - inputA',
                  '',
                  'connections:',
                  '  - input: outputB',
                  '    output: inputA',
                  '    read_meth: pickle'],
                 ['models:',
                  '  - name: modelB',
                  '    driver: GCCModelDriver',
                  '    args: ./src/modelB.c',
                  '    outputs:',
                  '      - outputB'],)


class TestYamlConnectionError_writemeth(YamlTestBaseError):
    r"""Test error when write_meth is specified for non-file."""
    _error = ValidationError
    _contents = (['models:',
                  '  - name: modelA',
                  '    driver: GCCModelDriver',
                  '    args: ./src/modelA.c',
                  '    inputs:',
                  '      - inputA',
                  '',
                  'connections:',
                  '  - input: outputB',
                  '    output: inputA',
                  '    write_meth: pickle'],
                 ['models:',
                  '  - name: modelB',
                  '    driver: GCCModelDriver',
                  '    args: ./src/modelB.c',
                  '    outputs:',
                  '      - outputB'],)


class TestYamlMissingModelArgsError(YamlTestBaseError):
    r"""Test error when there is a missing arguments to a model."""
    _error = ValidationError
    _contents = (['models:',
                  '  - name: modelA',
                  '    inputs:',
                  '      name: inputA',
                  '      driver: FileInputDriver',
                  '      args: {{ %s }}' % _yaml_env],)


class TestYamlMissingIOArgsError_input(YamlTestBaseError):
    r"""Test error when there is a missing arguments to an input driver."""
    _error = ValidationError
    _contents = (['models:',
                  '  - name: modelA',
                  '    driver: GCCModelDriver',
                  '    args: ./src/modelA.c',
                  '    inputs:',
                  '      name: inputA',
                  '      driver: FileInputDriver'],)


class TestYamlMissingIOArgsError_output(YamlTestBaseError):
    r"""Test error when there is a missing arguments to an output driver."""
    _error = ValidationError
    _contents = (['models:',
                  '  - name: modelA',
                  '    driver: GCCModelDriver',
                  '    args: ./src/modelA.c',
                  '    outputs:',
                  '      name: outputA',
                  '      driver: FileOutputDriver'],)


class TestYamlMissingConnArgsError(YamlTestBaseError):
    r"""Test error when there is a missing arguments to a connection."""
    _error = ValidationError
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
    _error = ValidationError
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
    _error = ValidationError
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
    _error = ValidationError
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
    _error = ValidationError
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
