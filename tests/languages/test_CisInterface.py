import copy
from yggdrasil.languages.Python import test_YggInterface


title_replace = ['TestYggInput', 'TestYggInputMatlab',
                 'TestYggRpcClient', 'TestYggRpcClientMatlab',
                 'TestYggAsciiFileInput', 'TestYggAsciiTableInput',
                 'TestYggAsciiTableOutputMatlab',
                 'TestYggAsciiArrayInput', 'TestYggPickleInput',
                 'TestYggPandasInput', 'TestYggPlyInput',
                 'TestYggObjInput']
for x in copy.deepcopy(title_replace):
    if 'Input' in x:
        title_replace.append(x.replace('Input', 'Output'))
    elif 'Client' in x:
        title_replace.append(x.replace('Client', 'Server'))
for x in title_replace:
    globals()[x.replace('Ygg', 'Cis')] = type(
        x.replace('Ygg', 'Cis'), (getattr(test_YggInterface, x), ),
        {'_mod': 'yggdrasil.interface.CisInterface',
         '_cls': getattr(test_YggInterface, x)._cls.replace('Ygg', 'Cis')})
