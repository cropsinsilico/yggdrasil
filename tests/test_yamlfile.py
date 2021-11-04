import pytest
import tempfile
import os
import yaml
import flaky
import io as sio
from jsonschema.exceptions import ValidationError
from yggdrasil import yamlfile
from yaml.constructor import ConstructorError
from tests import TestBase as base_class
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
        assert(out == dict_read)
        # File name
        out = yamlfile.load_yaml(fname)
        assert(out == dict_read)
        # Open file object
        with open(fname, 'r') as fd:
            out = yamlfile.load_yaml(fd)
            assert(out == dict_read)
        # Open stream
        out = yamlfile.load_yaml(sio.StringIO(contents))
        assert(out == dict_read)
    finally:
        # Remove file
        if os.path.isfile(fname):
            os.remove(fname)


def test_load_yaml_error():
    r"""Test error on loading invalid file."""
    with pytest.raises(IOError):
        yamlfile.load_yaml('invalid')


def test_parse_component_error():
    r"""Test errors in parse_component."""
    with pytest.raises(yamlfile.YAMLSpecificationError):
        yamlfile.parse_component(1, 'invalid', 'invalid')
    with pytest.raises(yamlfile.YAMLSpecificationError):
        yamlfile.parse_component({}, 'invalid', 'invalid')


@flaky.flaky(max_runs=3)
def test_load_yaml_git():
    r"""Test loading a yaml from a remote git repository."""
    import git
    yml = "https://github.com/cropsinsilico/example-fakemodel/fakemodel.yml"
    with pytest.raises(Exception):
        yamlfile.load_yaml(yml)
    assert('model' in yamlfile.load_yaml('git:' + yml))
    yml = "cropsinsilico/example-fakemodel/fakemodel.yml"
    assert('model' in yamlfile.load_yaml('git:' + yml))
    git.rmtree("cropsinsilico")
    

class YamlTestBase(base_class):
    r"""Test base for yamlfile."""
    
    _contents = tuple()
    _include = tuple()
    _use_json = False
    _parse_kwargs = dict()

    @pytest.fixture(scope="class")
    def contents(self):
        r"""tuple: Contents of files."""
        return self._contents

    @pytest.fixture(scope="class")
    def nfiles(self, contents):
        r"""int: Number of files created for the test."""
        return len(contents)

    @pytest.fixture(scope="class")
    def use_json(self):
        r"""bool: Whether or not to use JSON for the test."""
        return self._use_json

    @pytest.fixture(scope="class")
    def parse_kwargs(self):
        r"""dict: Keyword arguments for the parse call."""
        return self._parse_kwargs

    @pytest.fixture(scope="class")
    def include(self):
        r"""tuple: Contents of included files."""
        return self._include

    @pytest.fixture(scope="class")
    def yaml_env(self):
        r"""str: Environment variable where file path is stored."""
        return _yaml_env

    @pytest.fixture
    def files(self, nfiles, get_fname):
        r"""list: Name of test files."""
        return [get_fname(i) for i in range(nfiles)]

    @pytest.fixture
    def include_files(self, include, get_fname):
        r"""list: Names of test include files."""
        return [get_fname(i, '_incl') for i in range(len(include))]

    @pytest.fixture(autouse=True)
    def create_files(self, files, contents, yaml_env,
                     include_files, include, nfiles):
        r"""Write contents to temp file."""
        if nfiles > 0:
            os.environ[yaml_env] = files[0]
        for fname, content in zip(files, contents):
            with open(fname, 'w') as f:
                f.write('\n'.join(content))
        for i, (fname, content) in enumerate(zip(include_files,
                                                 include)):
            os.environ['%s%d' % (yaml_env, i)] = os.path.join(
                '.', os.path.basename(fname))
            with open(fname, 'w') as f:
                f.write('\n'.join(content))
        yield
        for fname in files + include_files:
            if os.path.isfile(fname):
                os.remove(fname)

    @pytest.fixture
    def get_fname(self, uuid, use_json):
        r"""Path to temporary file."""
        def wrapped_get_fname(idx=0, suffix=''):
            if use_json:
                ext = '.json'
            else:
                ext = '.yml'
            return os.path.join(tempfile.gettempdir(),
                                '%s_%s_%d%s%s' % (
                                    tempfile.gettempprefix(), uuid,
                                    idx, suffix, ext))
        return wrapped_get_fname

    def test_parse_yaml(self, parse_kwargs, nfiles, files):
        r"""Test successfully reading & parsing yaml."""
        if nfiles == 0:
            pass
        elif nfiles == 1:
            yamlfile.parse_yaml(files[0], **parse_kwargs)
        else:
            yamlfile.parse_yaml(files, **parse_kwargs)


class YamlTestBaseError(YamlTestBase):
    r"""Test error for yamlfile."""
    
    _error = None

    @pytest.fixture(scope="class")
    def error(self):
        return self._error

    def test_parse_yaml(self, parse_kwargs, error, nfiles, files):
        r"""Test error reading & parsing yaml."""
        if (error is None) or (nfiles == 0):
            return
        with pytest.raises(error):
            yamlfile.parse_yaml(files, parse_kwargs)


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
                  '  args: ./src/modelD.c',
                  '  env:',
                  '    TEST_VAR: 1'], )


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


class TestYamlModelFunction(YamlTestBase):
    r"""Test when missing input/output connections should be routed to a function."""
    _parse_kwargs = {'complete_partial': True}
    _contents = (['models:',
                  '  - name: modelA',
                  '    language: c',
                  '    args: ./src/modelA.c',
                  '    inputs:',
                  '      - inputA',
                  '    outputs:',
                  '      - outputA',
                  '',
                  '  - name: modelB',
                  '    language: c',
                  '    args: ./src/modelB.c',
                  '    inputs:',
                  '      - inputB',
                  '    outputs:',
                  '      - outputB',
                  '',
                  'connections:',
                  '  - input: outputA',
                  '    output: inputB'], )


class TestYamlConnectionDefaultValue(YamlTestBase):
    r"""Test use of default_value parameter."""
    _contents = (['models:',
                  '  - name: modelA',
                  '    driver: GCCModelDriver',
                  '    args: ./src/modelA.c',
                  '    inputs:',
                  '      - name: inputA',
                  '        default_value: test'],)


class TestYamlModelOnlyKwarg(YamlTestBase):
    r"""Test parsing with model_only=True."""
    _parse_kwargs = {'model_only': True}
    _contents = (['models:',
                  '  - name: modelA',
                  '    driver: GCCModelDriver',
                  '    args: ./src/modelA.c',
                  '    inputs:',
                  '      - name: inputA'],)


class TestYamlModelSubmission(YamlTestBase):
    r"""Test parsing with model_submission=True."""
    _parse_kwargs = {'model_submission': True}
    _contents = (['model:',
                  '  - name: FakeModel',
                  '    repository_url: https://github.com/cropsinsilico/'
                  'example-fakemodel',
                  '    repository_commit: e4bc7932c3c0c68fb3852cfb864777ca64cba448',
                  '    description: Example model submission',
                  '    language: python',
                  '    args:',
                  '      - ./src/fakemodel.py',
                  '      - --yggdrasil',
                  '    inputs:',
                  '      - name: photosynthesis_rate',
                  '        default_file:',
                  '          name: ./Input/input.txt',
                  '          filetype: table',
                  '        datatype:',
                  '          type: bytes',
                  '    outputs:',
                  '      - name: growth_rate',
                  '        default_file:',
                  '          name: ./Output/output.txt',
                  '          filetype: table',
                  '        datatype:',
                  '          type: bytes',
                  ],)

    @pytest.fixture(autouse=True)
    def cleanup_git_repo(self):
        r"""Remove the git repository."""
        yield
        import git
        git.rmtree("cropsinsilico")


class TestYamlServerNoClient(YamlTestBaseError):
    r"""Test error when is_server is set but there arn't any clients."""
    _error = yamlfile.YAMLSpecificationError
    _contents = (['models:',
                  '  - name: modelA',
                  '    driver: GCCModelDriver',
                  '    args: ./src/modelA.c',
                  '    is_server: True'],)


class TestYamlClientNoServer(YamlTestBaseError):
    r"""Test error when client_of is set but there arn't any servers by that name."""
    _error = yamlfile.YAMLSpecificationError
    _contents = (['models:',
                  '  - name: modelA',
                  '    driver: GCCModelDriver',
                  '    args: ./src/modelA.c',
                  '    client_of: modelB'],)


class TestYamlServerFunction(YamlTestBaseError):
    r"""Test error raised when both is_server and function are set, but
    there is more than one input/output."""
    _error = yamlfile.YAMLSpecificationError
    _contents = (['models:',
                  '  - name: modelA',
                  '    driver: GCCModelDriver',
                  '    args: ./src/modelA.c',
                  '    function: fake',
                  '    is_server: True',
                  '    inputs: [inputA, inputB]'],
                 ['model:',
                  '  - name: modelB',
                  '    driver: GCCModelDriver',
                  '    args: ./src/modelB.c',
                  '    client_of: modelA'],)


class TestYamlServerDictNoInput(YamlTestBaseError):
    r"""Test error raised when is_server is a dictionary but the referenced
    input channel cannot be located."""
    _error = yamlfile.YAMLSpecificationError
    _contents = (['models:',
                  '  - name: modelA',
                  '    driver: GCCModelDriver',
                  '    args: ./src/modelA.c',
                  '    function: fake',
                  '    is_server:',
                  '      input: A',
                  '      output: B',
                  '    outputs: B'],
                 ['model:',
                  '  - name: modelB',
                  '    driver: GCCModelDriver',
                  '    args: ./src/modelB.c',
                  '    client_of: modelA'],)


class TestYamlServerDictNoOutput(YamlTestBaseError):
    r"""Test error raised when is_server is a dictionary but the referenced
    output channel cannot be located."""
    _error = yamlfile.YAMLSpecificationError
    _contents = (['models:',
                  '  - name: modelA',
                  '    driver: GCCModelDriver',
                  '    args: ./src/modelA.c',
                  '    function: fake',
                  '    is_server:',
                  '      input: A',
                  '      output: B',
                  '    inputs: A'],
                 ['model:',
                  '  - name: modelB',
                  '    driver: GCCModelDriver',
                  '    args: ./src/modelB.c',
                  '    client_of: modelA'],)


class TestYamlComponentError(YamlTestBaseError):
    r"""Test error for non-dictionary component."""
    _error = ValidationError
    _contents = (['models: error'],)


class TestYamlDuplicateKeyError(YamlTestBaseError):
    r"""Test error when there are duplicates of the same key in a map."""
    _error = ConstructorError
    _contents = (['model:',
                  '  name: modelA',
                  '  driver: GCCModelDriver',
                  '  args: ./src/modelA.c',
                  '  inputs:',
                  '    - inputA',
                  '',
                  'connections:',
                  '  - input: outputB',
                  '    output: inputA',
                  '',
                  'model:',
                  '  name: modelB',
                  '  driver: GCCModelDriver',
                  '  args: ./src/modelB.c',
                  '  outputs:',
                  '    - outputB'],)


class TestYamlDuplicateError(YamlTestBaseError):
    r"""Test error when there are two components with the same name."""
    _error = yamlfile.YAMLSpecificationError
    _contents = (['models:',
                  '  - name: modelA',
                  '    driver: GCCModelDriver',
                  '    args: ./src/modelA.c',
                  '  - name: modelA',
                  '    driver: GCCModelDriver',
                  '    args: ./src/modelA.c'],)


class TestYamlConnectionError(YamlTestBaseError):
    r"""Test error when there is not connection for a model I/O channel."""
    _error = yamlfile.YAMLSpecificationError
    _contents = (['models:',
                  '  - name: modelA',
                  '    driver: GCCModelDriver',
                  '    args: ./src/modelA.c',
                  '    inputs:',
                  '      - inputA'],)


class TestYamlConnectionError_forkin(YamlTestBaseError):
    r"""Test error when there is not connection for a fork input channel."""
    _error = yamlfile.YAMLSpecificationError
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
