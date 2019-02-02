% Initialize input/output channels 
in_channel = YggInterface('YggInput', 'inputB');
out_channel = YggInterface('YggOutput', 'outputB');

flag = true;

% Loop until there is no longer input or the queues are closed
while flag

  % Receive input from input channel
  % If there is an error, the flag will be False.
  [flag, msg] = in_channel.recv();
  if (~flag)
    disp('Model B: No more input.');
    break;
  end;

  % Print received message
  fprintf('Model B: %s\n', char(msg));

  % Send output to output channel
  % If there is an error, the flag will be False
  flag = out_channel.send(msg);
  if (~flag)
    error('Model B: Error sending output.');
    break;
  end;
  
end;
