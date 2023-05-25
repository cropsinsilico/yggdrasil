import os
from yggdrasil.drivers.DSLModelDriver import DSLModelDriver
from yggdrasil import rapidjson
# TODO: Allow model to be trained by input and return weights?


class PyTorchModelDriver(DSLModelDriver):
    r"""Class for handling PyTorch models."""

    _schema_subtype_description = 'Model is a PyTorch model'
    _schema_required = ['weights']
    _schema_properties = {
        'weights': {
            'type': 'string',
            'description': ('Path to file where model weights '
                            'are saved')},
        'input_transform': {
            'type': 'function',
            'description': ('Transformation that should be applied to '
                            'input to get it into the format expected by '
                            'the model (including transformation to '
                            'pytorch tensors as necessary). This '
                            'function should return a tuple of '
                            'arguments for the model.')},
        'output_transform': {
            'type': 'function',
            'description': ('Transformation that should be applied to '
                            'model output to get it into a format that '
                            'can be serialized by yggdrasil (i.e. not '
                            'a pytorch Tensor or model sepecific type).')},
    }
    language = 'pytorch'
    language_ext = '.py'  # '.pth'
    interface_dependencies = ['torch']

    @classmethod
    def language_version(cls, **kwargs):
        r"""Determine the version of this language.

        Args:
            **kwargs: Keyword arguments are passed to cls.run_executable.

        Returns:
            str: Version of compiler/interpreter for this language.

        """
        try:
            import torch
            return torch.__version__
        except ImportError:  # pragma: debug
            raise RuntimeError("roadrunner not installed.")

    @property
    def model_wrapper_args(self):
        r"""tuple: Positional arguments for the model wrapper."""
        return (self.model_file, self.weights, )
    
    @property
    def model_wrapper_kwargs(self):
        r"""dict: Keyword arguments for the model wrapper."""
        out = super(PyTorchModelDriver, self).model_wrapper_kwargs
        out.update(
            {'inputs': self.inputs,
             'outputs': self.outputs,
             'working_dir': self.working_dir,
             'input_transform': self.input_transform,
             'output_transform': self.output_transform})
        return out

    @classmethod
    def model_wrapper(cls, model_file, weights_file,
                      inputs=[], outputs=[],
                      env=None, working_dir=None,
                      input_transform=None, output_transform=None):
        r"""Model wrapper."""
        import torch
        from yggdrasil.languages.Python.YggInterface import (
            YggInput, YggOutput)
        if env is not None:
            os.environ.update(env)
        if working_dir is not None:
            os.chdir(working_dir)
        # Create input/output comms
        input_map = {}
        output_map = {}
        input_vars = []
        output_vars = []
        for x in inputs:
            input_map[x['name']] = {
                'vars': [v['name'] for v in x.get('vars', [])],
                'comm': YggInput(x['name'], new_process=True)}
            if not input_map[x['name']]['vars']:
                input_map[x['name']]['vars'].append(x['name'])
            input_vars += input_map[x['name']]['vars']
        for x in outputs:
            x_vars = [v['name'] for v in x.get('vars', [])]
            output_map[x['name']] = {
                'as_array': x.get('as_array', False),
                'vars': x_vars,
                'comm': YggOutput(x['name'], new_process=True,
                                  field_names=x_vars)}
            if not output_map[x['name']]['vars']:
                output_map[x['name']]['vars'].append(x['name'])
            output_vars += output_map[x['name']]['vars']
        # Create model
        model = rapidjson.normalize(model_file, {'type': 'class'})()
        model.load_state_dict(torch.load(weights_file))
        model.eval()
        while True:
            flag = False
            values = {}
            for k, v in input_map.items():
                flag, value = v['comm'].recv_dict(key_order=v['vars'])
                if not flag:
                    print(f"No more input from {k}")
                    break
                values.update(value)
            if not flag:
                break
            args = [values[k] for k in input_vars]
            if input_transform:
                args = input_transform(*args)
            output = model(*args)
            if output_transform:
                output = output_transform(output)
            if len(output_vars) == 1:
                output = [output]
            output = {k: v for k, v in zip(output_vars, output)}
            for k, v in output_map.items():
                iout = {ik: output[ik] for ik in v['vars']}
                flag = v['comm'].send_dict(iout, key_order=v['vars'])
                if not flag:  # pragma: debug
                    raise RuntimeError(f"Error sending to {k}")
                
    @classmethod
    def get_testing_options(cls, **kwargs):
        r"""Method to return a dictionary of testing options for this class.

        Returns:
            dict: Dictionary of variables to use for testing. Key/value pairs:
                kwargs (dict): Keyword arguments for driver instance.
                deps (list): Dependencies to install.

        """
        out = super(PyTorchModelDriver, cls).get_testing_options()
        out['kwargs']['weights'] = 'pytorch_model_weights.pth'
        out['requires_partner'] = True
        return out
