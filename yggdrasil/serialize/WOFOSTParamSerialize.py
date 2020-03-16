import re
import json
import numpy as np
from yggdrasil import tools, units
from yggdrasil.serialize.AsciiMapSerialize import AsciiMapSerialize
from yggdrasil.metaschema.encoder import JSONReadableEncoder


class WOFOSTParamSerialize(AsciiMapSerialize):
    r"""Class for serializing/deserializing WOFOST parameter files."""

    _seritype = 'wofost'
    _schema_subtype_description = ('Serialization of mapping between '
                                   'keys and scalar or array values '
                                   'as used in the WOFOST parameter files.')
    _schema_properties = {
        'delimiter': {'type': 'string',
                      'default': ' = '}}
    default_datatype = {'type': 'object'}
    concats_as_str = True
    _delimiter = ' = '
    _array_fmt = '%5.5f, %5.5f'

    def func_serialize(self, args):
        r"""Serialize a message.

        Args:
            args (dict): Python dictionary to be serialized.

        Returns:
            bytes, str: Serialized message.

        """
        lines = []
        for k in args.keys():
            v = args[k]
            if not isinstance(k, (str, bytes)):
                raise ValueError("Serialization of non-string keys not supported.")
            iline = tools.bytes2str(k) + self.delimiter
            if isinstance(v, list):
                indent = ' ' * len(iline)
                arr_lines = []
                assert(len(v) == 2)
                assert(v[0].shape == v[1].shape)
                for i in range(len(v[0])):
                    arr_lines.append(self._array_fmt % (v[0][i], v[1][i]))
                iline += (',\n' + indent).join(arr_lines)
            elif isinstance(v, str):
                iline += "\'%s\'" % v
            else:
                iline += json.dumps(v, cls=JSONReadableEncoder)
            lines.append(iline)
        return tools.str2bytes('\n'.join(lines))

    @classmethod
    def parse_units(cls, x):
        r"""Parse units.

        Args:
            x (str): Unit string.

        Returns:
            str: Propertly formatted units.

        """
        replacements = {"kg N": "kg",
                        "kg P": "kg",
                        "kg-1 dry biomass": "kg-1",
                        "kg CH2O": "kg",
                        "days": "d",
                        "cel": "degC"}
        for k, v in replacements.items():
            x = x.replace(k, v)
        out = units.convert_R_unit_string(x)
        return out
            
    def func_deserialize(self, msg):
        r"""Deserialize a message.

        Args:
            msg (bytes): Message to be deserialized.

        Returns:
            dict: Deserialized Python dictionary.

        """
        regex = (r'(?:(?:(?P<name>[^!]*?)\s*=\s*)|(?:\s+))'
                 r'(?P<value1>(?:-?[\d.]+(?:.[\d+])?)|(?:\'.*?\'))?'
                 r'\s*(?:(?P<unwrapped_units>[^!,\']*?))?'
                 r'(?:,\s+(?P<value2>[^!,]*?)'
                 r'(?:,?))?\s*(?:!\s*(?P<description>.*?)?\s*'
                 r'(?:\[(?P<units>.*?)\])?)?\s*')
        out = dict()
        lines = tools.bytes2str(msg.split(self.newline), recurse=True)
        k = None
        desc = ''
        k_units = ''
        is_arr = False
        for l in lines:
            if (not l.strip()) or l.startswith('**'):
                continue
            match = re.fullmatch(regex, l)
            if not match:  # pragma: debug
                raise Exception("Failed to parse line: '%s'" % l)
            match = match.groupdict()
            if match.get('name', None):
                if is_arr:
                    out[k][0] = np.array(out[k][0])
                    out[k][1] = np.array(out[k][1])
                if k_units:
                    if is_arr:
                        if ';' in k_units:
                            u1, u2 = k_units.split(';')
                            u1 = self.parse_units(u1)
                            u2 = self.parse_units(u2)
                            out[k][0] = units.add_units(out[k][0], u1)
                            out[k][1] = units.add_units(out[k][1], u1)
                        else:
                            out[k][1] = units.add_units(
                                out[k][1], self.parse_units(k_units))
                    else:
                        out[k] = units.add_units(
                            out[k], self.parse_units(k_units))
                if isinstance(match.get('value1', None), str):
                    match['value1'] = match['value1'].strip()
                if isinstance(match.get('value2', None), str):
                    match['value2'] = match['value2'].strip()
                is_arr = bool(match.get('value2', None))
                k = match['name']
                desc = ''
                k_units = ''
                if is_arr:
                    out[k] = [[], []]
            if match.get('description', ''):
                desc += match['description']
            if match.get('units', ''):
                k_units += match['units']
            if match['value1']:
                if match['value1'].startswith('\'') and match['value1'].endswith('\''):
                    v1 = match['value1'].strip('\'')
                else:
                    try:
                        v1 = json.loads(match['value1'])
                    except json.decoder.JSONDecodeError:
                        if match['value1'].endswith('.'):
                            v1 = json.loads(match['value1'] + '0')
                        else:  # pragma: debug
                            raise
                if is_arr:
                    v2 = json.loads(match['value2'])
                    out[k][0].append(v1)
                    out[k][1].append(v2)
                else:
                    out[k] = v1
        return out

    @classmethod
    def concatenate(cls, objects, **kwargs):
        r"""Concatenate objects to get object that would be recieved if
        the concatenated serialization were deserialized.

        Args:
            objects (list): Objects to be concatenated.
            **kwargs: Additional keyword arguments are ignored.

        Returns:
            list: Set of objects that results from concatenating those provided.

        """
        total = dict()
        for x in objects:
            total.update(x)
        return [total]
        
    @classmethod
    def get_testing_options(cls):
        r"""Method to return a dictionary of testing options for this class.

        Returns:
            dict: Dictionary of variables to use for testing.

        """
        out = super(WOFOSTParamSerialize, cls).get_testing_options()
        out['objects'] = [{'CRPNAM': 'Grain maize CSA practicals',
                           'TBASEM': units.add_units(4.0, 'cel'),
                           'TEFFMX': units.add_units(30.0, 'cel'),
                           'TSUMEM': units.add_units(110.0, 'cel*d'),
                           'IDSL': 0,
                           'DLO': units.add_units(-99.0, 'hr'),
                           'DLC': units.add_units(-99.0, 'hr'),
                           'TSUM1': units.add_units(900.0, 'cel*d'),
                           'TSUM2': units.add_units(800.0, 'cel*d'),
                           'DTSMTB': [
                               units.add_units(
                                   np.array([0.0, 10.0, 30.0, 35.0]), 'cel'),
                               units.add_units(
                                   np.array([0.0, 0.0, 24.0, 24.0]), 'cel*d')],
                           'DVSI': 0.0,
                           'DVSEND': 2.0}]
        out['empty'] = dict()
        out['contents'] = (
            b'CRPNAM=\'Grain maize CSA practicals\'\n\n'
            b'** emergence\n'
            b'TBASEM   =   4.0    ! lower threshold temp. for emergence [cel]\n'
            b'TEFFMX   =  30.0    ! max. eff. temp. for emergence [cel]\n'
            b'TSUMEM   = 110.     ! temperature sum from sowing to emergence [cel d]\n\n'
            b'** phenology\n'
            b'IDSL     =   0      ! indicates whether pre-anthesis development depends\n'
            b'                    ! on temp. (=0), daylength (=1) , or both (=2)\n'
            b'DLO      = -99.0    ! optimum daylength for development [hr]\n'
            b'DLC      = -99.0    ! critical daylength (lower threshold) [hr]\n'
            b'TSUM1    = 900.     ! temperature sum from emergence to anthesis [cel d]\n'
            b'TSUM2    = 800.     ! temperature sum from anthesis to maturity [cel d]\n'
            b'DTSMTB   =   0.00,    0.00,     ! daily increase in temp. sum\n'
            b'            10.00,    0.00,     ! as function of av. temp. '
            b'[cel; cel d]\n'
            b'            30.00,   24.00,\n'
            b'            35.00,   24.00\n'
            b'DVSI = 0.           ! initial DVS\n'
            b'DVSEND   =   2.00   ! development stage at harvest (= 2.0 at '
            b'maturity [-]))\n')
        return out
