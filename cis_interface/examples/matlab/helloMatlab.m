PsiInterface = py.importlib.import_module('cis_interface.interface.PsiInterface');

display('hello matlab')

in = PsiInterface.PsiInput('input');
out = PsiInterface.PsiOutput('output');

data = in.recv();
display('received input');
out.send(data);
display('sent output');

display('bye from matlab')
exit(0);



