import warnings
from yggdrasil.interface import YggInterface
warnings.warn(("YggInterface replaces CisInterface in yggdrasil. "
               "Replace ygg with cis in interface calls."),
              DeprecationWarning, stacklevel=2)


direct_replace = ['maxMsgSize', 'bufMsgSize', 'eof_msg']
upper_replace = ['YGG_MSG_MAX', 'YGG_MSG_EOF', 'YGG_MSG_BUF']
title_replace = ['YggInit', 'YggInput', 'YggOutput',
                 'YggRpcServer', 'YggRpcClient',
                 'YggAsciiFileInput', 'YggAsciiFileOutput',
                 'YggAsciiTableInput', 'YggAsciiTableOutput',
                 'YggAsciiArrayInput', 'YggAsciiArrayOutput',
                 'YggPickleInput', 'YggPickleOutput',
                 'YggPandasInput', 'YggPandasOutput',
                 'YggPlyInput', 'YggPlyOutput',
                 'YggObjInput', 'YggObjOutput']


for x in direct_replace:
    globals()[x] = getattr(YggInterface, x)
for x in upper_replace:
    globals()[x.replace('YGG', 'CIS')] = getattr(YggInterface, x)
for x in title_replace:
    globals()[x.replace('Ygg', 'Cis')] = getattr(YggInterface, x)
