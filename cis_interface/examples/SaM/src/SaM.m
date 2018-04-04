
% Get input and output channels matching yaml
in1 = CisInterface('CisInput', 'input1_matlab', '%d');
in2 = CisInterface('CisInput', 'static_matlab', '%d');
out1 = CisInterface('CisOutput', 'output_matlab', '%d');
disp('SaM(M): Set up I/O channels');

% Get input from input1 channel
[flag, var] = in1.recv();
if (~flag);
  disp('SaM(M): ERROR RECV from input1');
  exit(-1);
end
a = var{1};
fprintf('SaM(M): Received %d from input1\n', a);

% Get input from static channel
[flag, var] = in2.recv();
if (~flag);
  disp('SaM(M): ERROR RECV from static');
  exit(-1);
end
b = var{1};
fprintf('SaM(M): Received %d from static\n', b);

% Compute sum and send message to output channel
sum = a + b;
ret = out1.send(sum);
if (~ret);
  disp('SaM(M): ERROR SEND to output');
  exit(-1);
end
disp('SaM(M): Sent to output');

exit(0);
