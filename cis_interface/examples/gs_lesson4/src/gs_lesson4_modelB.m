% Initialize input/output channels 
in_channel = PsiInterface('PsiInput', 'inputB');
out_channel = PsiInterface('PsiOutput', 'outputB');

% Receive input from input channel
% If there is an error, the flag will be False.
res = in_channel.recv();
flag = res{1};
msg = res{2};

% Print received message
fprintf('%s\n', char(msg));

% Send output to output channel
% If there is an error, the flag will be False
flag = out_channel.send(msg);

exit(0);
