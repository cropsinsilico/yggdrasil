% Initialize input/output channels 
in_channel = YggInterface('YggAsciiTableInput', 'inputA');
out_channel = YggInterface('YggAsciiTableOutput', 'outputA', '%6s\t%d\t%f\n');

flag = true;

% Loop until there is no longer input or the queues are closed
while flag

  % Receive input from input channel
  % If there is an error, the flag will be False.
  [flag, msg] = in_channel.recv();
  if (~flag)
    disp('Model A: No more input.');
    break;
  end;
  name = msg{1};
  count = msg{2};
  size = msg{3};

  % Print received message
  fprintf('Model A: %s, %d, %f\n', name, count, size);

  % Send output to output channel
  % If there is an error, the flag will be False
  flag = out_channel.send(name, count, size);
  if (~flag)
    error('Model A: Error sending output.');
    break;
  end;
  
end;
