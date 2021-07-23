import copy
from yggdrasil.drivers import create_driver
from yggdrasil.drivers.Driver import Driver
        

class DuplicatedModelDriver(Driver):
    r"""Base class for Model drivers and for running executable based models.

    Args:
        name (str): Unique name used to identify the model. This will
            be used to report errors associated with the model.
        *args: Additional arguments are passed to the models in the set.
        **kwargs: Additional keyword arguments are passed to the models in
            the set.

    Attributes:

    Raises:
        RuntimeError: If both with_strace and with_valgrind are True.

    """

    name_format = "%s_copy%d"

    def __init__(self, yml, duplicates=None, **kwargs):
        kwargs.update(yml)
        self.copies = []
        if duplicates is not None:
            for x in duplicates:
                ienv = copy.deepcopy(yml.get('env', {}))
                ienv.update(yml.pop('env_%s' % x['name'], {}))
                ienv.update(x.pop('env', {}))
                x['env'] = ienv
                ikws = copy.deepcopy(kwargs)
                ikws.update(x)
                self.copies.append(create_driver(yml=x, **ikws))
        else:
            for iyml in self.get_yaml_copies(yml):
                ikws = copy.deepcopy(kwargs)
                ikws.update(iyml)
                self.copies.append(create_driver(yml=iyml, **ikws))
        super(DuplicatedModelDriver, self).__init__(**kwargs)

    @classmethod
    def get_base_name(cls, name):
        r"""Get the name of the base model.

        Args:
            name (str): Model name.

        Returns:
            str: Base model name.

        """
        assert('_copy' in name)
        return name.split('_copy')[0]

    @classmethod
    def get_yaml_copies(cls, yml):
        r"""Get a list of yamls for creating duplicate models for the model
        described by the provided yaml.

        Args:
            yml (dict): Input parameters for creating a model driver.

        Returns:
            list: Copies of input parameters for creating duplicate models.

        """
        env_copy_specific = {}
        for i in range(yml['copies']):
            iname = cls.name_format % (yml['name'], i)
            env_copy_specific[iname] = yml.pop('env_%s' % iname, {})
        copies = []
        for i in range(yml['copies']):
            iyml = copy.deepcopy(yml)
            iyml['name'] = cls.name_format % (yml['name'], i)
            iyml['copy_index'] = i
            iyml['input_drivers'] = yml['input_drivers']
            iyml['output_drivers'] = yml['output_drivers']
            # Update environment to reflect addition of suffix
            iyml['env'] = yml.get('env', {}).copy()
            iyml['env'].update(env_copy_specific.get(iyml['name'], {}))
            copies.append(iyml)
        return copies

    def cleanup(self, *args, **kwargs):
        r"""Actions to perform to clean up the thread after it has stopped."""
        for x in self.copies:
            x.cleanup(*args, **kwargs)
        super(DuplicatedModelDriver, self).cleanup(*args, **kwargs)

    def start(self, *args, **kwargs):
        r"""Start thread/process and print info."""
        # self.delay_start(*args, **kwargs)
        input_drivers = self.yml.get('input_drivers', [])
        output_drivers = self.yml.get('output_drivers', [])
        for x in self.copies:
            x.env.update(x.get_io_env(input_drivers=input_drivers,
                                      output_drivers=output_drivers))
            x.start(*args, **kwargs)
        super(DuplicatedModelDriver, self).start(*args, **kwargs)

    # def delay_start(self, *args, **kwargs):
    #     r"""This method should not be called in production and is only
    #     used for local testing to simulation a delayed start for some
    #     copies."""
    #     self.copies[0].start(*args, **kwargs)
    #     def start_remainder():
    #         for x in self.copies[1:]:
    #             x.start(*args, **kwargs)
    #     self.sched_task(0.4, start_remainder)
    #     super(DuplicatedModelDriver, self).start(*args, **kwargs)

    def stop(self, *args, **kwargs):
        r"""Stop the driver."""
        for x in self.copies:
            x.stop(*args, **kwargs)
        super(DuplicatedModelDriver, self).stop(*args, **kwargs)
        
    def graceful_stop(self, *args, **kwargs):
        r"""Gracefully stop the driver."""
        for x in self.copies:
            x.graceful_stop(*args, **kwargs)
        super(DuplicatedModelDriver, self).graceful_stop(*args, **kwargs)
        
    def terminate(self, *args, **kwargs):
        r"""Set the terminate event and wait for the thread/process to stop."""
        for x in self.copies:
            x.terminate(*args, **kwargs)
        super(DuplicatedModelDriver, self).terminate(*args, **kwargs)
        
    def run_loop(self):
        r"""Loop to check if model is still running and forward output."""
        # TODO: Stop if there is an error on one?
        if any([x.is_alive() for x in self.copies]):
            self.sleep()
            return
        else:
            self.set_break_flag()

    def after_loop(self, *args, **kwargs):
        r"""Actions to perform after run_loop has finished."""
        for x in self.copies:
            x.terminate()
        super(DuplicatedModelDriver, self).after_loop(*args, **kwargs)

    def printStatus(self, *args, **kwargs):
        r"""Print the class status."""
        out_copies = []
        for x in self.copies:
            out_copies.append(x.printStatus(*args, **kwargs))
        out = super(DuplicatedModelDriver, self).printStatus(*args, **kwargs)
        if kwargs.get('return_str', False):
            out = '\n'.join(out_copies + [out])
        return out

    @property
    def io_errors(self):
        r"""list: Errors produced by input/output drivers to this model."""
        errors = []
        for x in self.copies:
            errors += x.io_errors
        return errors
        
    @property
    def errors(self):
        r"""list: Errors returned by model copies."""
        out = []
        for x in self.copies:
            out += x.errors
        return out

    @errors.setter
    def errors(self, val):
        pass
