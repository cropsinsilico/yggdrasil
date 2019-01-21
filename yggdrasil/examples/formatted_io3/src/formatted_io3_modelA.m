% Initialize input/output channels 
in_channel = YggInterface('YggAsciiArrayInput', 'inputA');
out_channel = YggInterface('YggAsciiArrayOutput', 'outputA', '%6s\t%d\t%f\n');

flag = true;

% Loop until there is no longer input or the queues are closed
while flag

  % Receive input from input channel
  % If there is an error, the flag will be False.
  [flag, arr] = in_channel.recv_array();
  if (~flag)
    disp('Model A: No more input.');
    break;
  end;

  % Print received message
  nr = size(arr, 1);
  fprintf('Model A: (%d rows)\n', nr);
  for i = 1:nr
    fprintf('   %s, %d, %f\n', arr{i,1}, arr{i,2}, arr{i,3});
  end;

  % Send output to output channel
  % If there is an error, the flag will be False
  flag = out_channel.send_array(arr);
  if (~flag)
    error('Model A: Error sending output.');
    break;
  end;
  
end;
