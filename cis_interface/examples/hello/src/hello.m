display('hello matlab')

in = PsiInterface('PsiInput', 'input');
out = PsiInterface('PsiOutput', 'output');

data = in.recv();
display('received input');
out.send(data{2});
display('sent output');

display('bye from matlab')
exit(0);



