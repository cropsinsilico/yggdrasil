PsiInterface = py.importlib.import_module('cis_interface.interface.PsiInterface');

disp('Hello from Matlab!');
x = onCleanup( @() exit(-1) );

in = PsiInterface.PsiInput('mlinput1');
st = PsiInterface.PsiInput('mlstatic');
out = PsiInterface.PsiOutput('mloutput');
disp('Matlab created channels');

raw_Input = in.recv();
Input = char(raw_Input{2});
disp(['Matlab received ', Input, ' from mlinput1']);
raw_Static = st.recv();

Static = char(raw_Static{2});
disp(['Matlab received ', Static, ' from mlstatic']);
Output = str2num(Input)+str2num(Static);
sOutput = sprintf('%d',Output);
out.send(sOutput);
disp(['Matlab sent ', sOutput, ' to mloutput']);

disp('Goodbye from matlab!');

exit();
