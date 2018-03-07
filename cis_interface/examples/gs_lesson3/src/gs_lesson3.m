% Initialize input/output channels 
in_channel = PsiInterface('PsiInput', 'input');
out_channel = PsiInterface('PsiOutput', 'output');

flag = true;

% Loop until there is no longer input or the queues are closed
while flag

  % Receive input from input channel 
  % If there is an error, the flag will be False.
  res = in_channel.recv();
  flag = res{1};
  msg = res{2};
  if (~flag)
    disp('No more input.');
    break
  end

  % Print received message
  fprintf('%s\n', char(msg));

  % Send output to output channel
  % If there is an error, the flag will be False
  flag = out_channel.send(msg);
  if (~flag)
    disp('Error sending output.');
    break
  end
  
end

exit(0);
