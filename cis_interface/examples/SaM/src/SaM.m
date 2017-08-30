PsiInterface = py.importlib.import_module('cis_interface.interface.PsiInterface');

in = PsiInterface.PsiInput('input1');
st = PsiInterface.PsiInput('static');
out = PsiInterface.PsiOutput('output');

Input = in.recv()
Static = st.recv()
Output = str2num(char(Input))+str2num(char(Static))
sOutput = sprintf('Sum = %d',Output);
out.send(sOutput);

exit();
