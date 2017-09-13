
% Get input and output channels matching yaml
in1 = PsiInterface('PsiInput', 'input1_matlab');
in2 = PsiInterface('PsiInput', 'static_matlab');
out1 = PsiInterface('PsiOutput', 'output_matlab');
disp('SaM(M): Set up I/O channels');

% Get input from input1 channel
res = in1.recv();
if (~res{1});
  disp('SaM(M): ERROR RECV from input1');
  exit(-1);
end
a = str2num(char(res{2}));
fprintf('SaM(M): Received %d from input1\n', a);

% Get input from static channel
res = in2.recv();
if (~res{1});
  disp('SaM(M): ERROR RECV from static');
  exit(-1);
end
b = str2num(char(res{2}));
fprintf('SaM(M): Received %d from static\n', b);

% Compute sum and send message to output channel
sum = a + b;
outdata = sprintf('%d', sum);
ret = out1.send(outdata);
if (~ret);
  disp('SaM(M): ERROR SEND to output');
  exit(-1);
end
disp('SaM(M): Sent to output');

exit(0);
