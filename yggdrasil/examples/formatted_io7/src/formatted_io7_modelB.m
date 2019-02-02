% Initialize input/output channels 
in_channel = YggInterface('YggInput', 'inputB');
out_channel = YggInterface('YggOutput', 'outputB');

flag = true;

% Loop until there is no longer input or the queues are closed
while flag

  % Receive input from input channel
  % If there is an error, the flag will be False.
  [flag, obj] = in_channel.recv();
  if (~flag)
    disp('Model B: No more input.');
    break;
  end;

  % Print received message
  fprintf('Model B:');
  disp(obj);

  % Send output to output channel
  % If there is an error, the flag will be False
  flag = out_channel.send(obj);
  if (~flag)
    error('Model B: Error sending output.');
    break;
  end;
  
end;
