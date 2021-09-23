import os
import six
import unittest
from yggdrasil import yamlfile, runner, tools
from yggdrasil.components import ComponentMeta, import_component
from yggdrasil.tests import YggTestBase, check_enabled_languages


_demo_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class DemoRun(object):

    def __init__(self, name, yamls):
        self.runner = None
        self.name = name
        self.yamls = yamls
        self.languages = []
        for x in yamlfile.parse_yaml(yamls)['model'].values():
            drv = import_component('model', x['driver'],
                                   without_schema=True)
            if drv.language not in self.languages:
                self.languages.append(drv.language)
        super(DemoRun, self).__init__()

    def run(self):
        r"""Run the integration."""
        if not tools.check_environ_bool('YGG_ENABLE_DEMO_TESTS'):
            raise unittest.SkipTest("Demo tests not enabled.")
        for x in self.languages:
            check_enabled_languages(x)
            if not tools.is_lang_installed(x):
                raise unittest.SkipTest("%s not installed." % x)
        self.runner = runner.get_runner(self.yamls, namespace=self.name,
                                        production_run=True)
        self.runner.run()
        assert(not self.runner.error_flag)
        self.runner = None

    def add_test(self, dct):
        def itest(solf):
            self.run()
        itest.__name__ = 'test_%s' % self.name
        dct[itest.__name__] = itest


class DemoMeta(ComponentMeta):

    def __new__(cls, name, bases, dct):
        runs = dct.get('runs', {})
        for name, yamls in runs.items():
            runs[name] = DemoRun(name, [os.path.join(_demo_dir,
                                                     dct['demo_name'], iyml)
                                        for iyml in yamls])
            runs[name].add_test(dct)
        dct['runs'] = runs
        out = super(DemoMeta, cls).__new__(cls, name, bases, dct)
        return out


@six.add_metaclass(DemoMeta)
class DemoTstBase(YggTestBase, tools.YggClass):
    r"""Base class for running demos."""

    demo_name = None
    runs = {}
