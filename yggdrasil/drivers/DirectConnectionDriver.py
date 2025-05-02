import pprint
import copy
from yggdrasil.drivers.ConnectionDriver import (
    ConnectionDriver, ConnectionError)
from yggdrasil.drivers.DuplicatedModelDriver import DuplicatedModelDriver


class DirectConnectionError(ConnectionError):
    r"""Error when parameters incompatible with a direct conneciton."""


class DirectConnectionDriver(ConnectionDriver):
    r"""Stand-in for connection between models where the models
    have communicators that are directly connected."""

    _connection_type = 'direct'

    def __init__(self, *args, **kwargs):
        kwargs.setdefault('disabled', True)
        super(DirectConnectionDriver, self).__init__(*args, **kwargs)
        assert not self.single_use

    def _init_single_comm(self, io, comm_list):
        r"""Parse keyword arguments for input/output comm."""
        self.debug(f"Creating {io} comm")
        comm_kws = dict()
        assert isinstance(comm_list, list)
        if io == 'input':
            direction = 'send'
            attr_comm = 'icomm'
            comm_type = self._icomm_type
        else:
            direction = 'recv'
            attr_comm = 'ocomm'
            comm_type = self._ocomm_type
        comm_kws['direction'] = direction
        comm_kws['name'] = self.name
        for i, x in enumerate(comm_list):
            if x is None:
                comm_list[i] = dict()
            else:
                assert isinstance(x, dict)
        models = []
        for x in comm_list:
            x.update(
                model=x.pop('partner_model'),
                direct_connection=True,
            )
            models.append(x['model'])
            if 'partner_copies' in x:
                x['model_copies'] = x.pop('partner_copies')
            if 'partner_language' in x:
                x['language'] = x.pop('partner_language')
            if 'filetype' in x:
                # TODO: This is only true for C based interfaces
                x['commtype'] = 'file'
                raise DirectConnectionError(
                    "Cannot make a direct connection to a file.")
            x.setdefault('commtype', comm_type)
            if x['commtype'] == 'mpi':
                raise DirectConnectionError(
                    "Cannot make a direct connection with an MPI comm")
            for k in ['client', 'servier']:
                if x.get(f'is_{k}', False):
                    x.update(
                        request_commtype=x['commtype'],
                        commtype=k,
                    )
                    x.pop(f'is_{k}')
            if direction == 'send' and self._raw_transform:
                x.setdefault('transform', [])
                x['transform'] += self._raw_transform
        comm_kws['commtype'] = copy.deepcopy(comm_list)
        for x in comm_kws['commtype']:
            if isinstance(x.get('datatype', {}), dict):
                if ((x.get('datatype', {}).get('from_function', False)
                     and (x.get('datatype', {}).get('type', None)
                          in ['any', 'instance']))):
                    x['datatype'] = {'type': 'scalar', 'subtype': 'string'}
                x.get('datatype', {}).pop('from_function', False)
        if len(comm_kws['commtype']) == 1:
            comm_kws.update(comm_kws.pop('commtype')[0])
        if len(models) == 1:
            x['model'] = models[0]
        self.debug(f'{attr_comm} comm_kws:\n{self.pprint(comm_kws, 1)}')
        setattr(self, attr_comm, comm_kws)
        setattr(self, '%s_kws' % attr_comm, comm_kws)
        self.models[io] = models

    def _add_partner_single(self, x, x_opp):
        x.update(
            partner_name=x_opp['name'],
            partner_language=x_opp['language'],
        )
        if 'model_copies' in x_opp:
            x['partner_copies'] = x_opp['model_copies']
        x_opp_list = []
        x_pattern = None
        if isinstance(x_opp['commtype'], list):
            assert x_opp.get('model_copies', 1) == 1
            x_opp_list = x_opp['commtype']
            if x_opp['direction'] == 'send':
                x_pattern = self.input_pattern
            else:
                x_pattern = self.output_pattern
        elif (x_opp.get('model_copies', 1) > 1
              and not x.get('dont_copy', False)):
            x_opp_list = [
                dict(x_opp, model=(
                    DuplicatedModelDriver.name_format % (
                        x_opp['model'], idx)))
                for idx in range(x_opp['model_copies'])
            ]
            x_pattern = 'cycle'
        if ((x_opp_list
             and (x_pattern != 'cycle'
                  or x['commtype'] not in ['server', 'client']))):
            if isinstance(x['commtype'], list):
                raise DirectConnectionError(
                    "Cannot handle multiple-to-multiple communication "
                    "pattern without a connection driver")
            assert not isinstance(x['commtype'], list)
            commtype = x['commtype']
            x.update(
                pattern=x_pattern,
                commtype=[dict(x, commtype=commtype) for xx in x_opp_list],
            )
            for xx, xx_opp in zip(x['commtype'], x_opp_list):
                self._add_partner_single(xx, xx_opp)
        else:
            x['partner_model'] = x_opp['model']
            if isinstance(x['commtype'], list):
                for xx in x['commtype']:
                    self._add_partner_single(xx, x_opp)

    def _prune_standalone(self, x, x_opp):
        if not (x['commtype'] == 'default'
                and x_opp['commtype'] in ['file', 'model_function']):
            return
        # TODO: Verify that model_function input & output used by
        # the same model
        # TODO: Import communicator to get keywords
        x.update({k: x_opp[k] for k in ['commtype', 'address']})
        transform_opp = x_opp.pop('transform', [])
        filter_opp = x_opp.pop('filter', [])
        if transform_opp:
            if x['direction'] == 'send':
                x['transform'] = x.get('transform', []) + transform_opp
            else:
                x['transform'] = transform_opp + x.get('transform', [])
        if filter_opp:
            if x['direction'] == 'send':
                x['filter'] = x.get('filter', []) + filter_opp
            else:
                x['filter'] = filter_opp + x.get('filter', [])
        x_opp.update(commtype='dummy')

    def _add_partners(self):
        self._add_partner_single(self.icomm, self.ocomm)
        self._add_partner_single(self.ocomm, self.icomm)
        self._prune_standalone(self.icomm, self.ocomm)
        self._prune_standalone(self.ocomm, self.icomm)

    def _init_comms(self, name, **kwargs):
        r"""Parse keyword arguments for input/output comms."""
        if self.no_direct_connection:
            raise DirectConnectionError("no_direct_connection set")
        self.models = {}
        self.inputs = copy.deepcopy(self.inputs)
        self.outputs = copy.deepcopy(self.outputs)
        self._init_single_comm('input', self.inputs)
        self._init_single_comm('output', self.outputs)
        self._add_partners()

    @property
    def model_env(self):
        r"""dict: Mapping between model name and opposite comm
        environment variables that need to be provided to the model."""
        return {}

    def open_comm(self):
        r"""Open the communicators."""
        pass

    def close_comm(self):
        r"""Close the communicators."""
        pass

    def printStatus(self, beg_msg='', end_msg='',
                    verbose=False, return_str=False):
        r"""Print information on the status of the ConnectionDriver.

        Arguments:
            beg_msg (str, optional): Additional message to print at beginning.
            end_msg (str, optional): Additional message to print at end.
            verbose (bool, optional): If True, the status of
                individual comms will be displayed. Defaults to
                False.
            return_str (bool, optional): If True, the message string is
                returned. Defaults to False.

        """
        msg = beg_msg
        msg += '%-50s' % (self.__module__.split('.')[-1] + '(' + self.name + '): ')
        msg += f'{self.icomm["name"]} => {self.ocomm["name"]}'
        msg += '\n\t'
        msg += '%-30s' % ('last action: ' + self.state)
        msg += end_msg
        if not return_str:
            print(msg)
        if verbose:
            i_msg = pprint.pformat(self.icomm)
            o_msg = pprint.pformat(self.ocomm)
            if return_str:
                msg += '\n%s\n%s' % (i_msg, o_msg)
        return msg
