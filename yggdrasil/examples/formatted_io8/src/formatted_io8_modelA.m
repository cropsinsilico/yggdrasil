% Initialize input/output channels 
in_channel = YggInterface('YggInput', 'inputA');
out_channel = YggInterface('YggOutput', 'outputA');

flag = true;

% Loop until there is no longer input or the queues are closed
while flag

  % Receive input from input channel
  % If there is an error, the flag will be False.
  [flag, obj] = in_channel.recv();
  if (~flag)
    disp('Model A: No more input.');
    break;
  end;

  % Print received message
  fprintf('Model A:');
  disp(obj);

  % Send output to output channel
  % If there is an error, the flag will be False
  flag = out_channel.send(obj);
  if (~flag)
    error('Model A: Error sending output.');
    break;
  end;
  
end;
