
% Get input and output channels matching yaml
in1 = YggInterface('YggInput', 'input1_matlab');
in2 = YggInterface('YggInput', 'static_matlab');
out1 = YggInterface('YggOutput', 'output_matlab');
disp('SaM(M): Set up I/O channels');

% Get input from input1 channel
[flag, var] = in1.recv();
if (~flag);
  error('SaM(M): ERROR RECV from input1');
end
a = str2num(var);
fprintf('SaM(M): Received %d from input1\n', a);

% Get input from static channel
[flag, var] = in2.recv();
if (~flag);
  error('SaM(M): ERROR RECV from static');
end
b = str2num(var);
fprintf('SaM(M): Received %d from static\n', b);

% Compute sum and send message to output channel
sum = a + b;
ret = out1.send(int2str(sum));
if (~ret);
  error('SaM(M): ERROR SEND to output');
end
disp('SaM(M): Sent to output');
