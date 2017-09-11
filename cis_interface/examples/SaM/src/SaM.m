in = PsiInterface('PsiInput', 'input1');
st = PsiInterface('PsiInput', 'static');
out = PsiInterface('PsiOutput', 'output');

Input = in.recv()
Static = st.recv()
Output = str2num(char(Input{2}))+str2num(char(Static{2}))
sOutput = sprintf('Sum = %d',Output);
out.send(sOutput);

exit();
