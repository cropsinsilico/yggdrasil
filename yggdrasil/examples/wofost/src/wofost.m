% Initialize input/output channels 
in_channel = YggInterface('YggInput', 'input');
out_channel = YggInterface('YggOutput', 'output');

flag = true;

% Loop until there is no longer input or the queues are closed
while flag

  % Receive input from input channel
  % If there is an error, the flag will be False.
  [flag, obj] = in_channel.recv();
  if (~flag)
    disp('Matlab Model: No more input.');
    break;
  end;

  % Print received message
  fprintf('Matlab Model:');
  disp(obj);

  % Print keys
  fprintf('Matlab Model: keys = ');
  disp(keys(obj));

  % Get floating point element
  co2 = obj('CO2');
  fprintf('Matlab Model: CO2 = %f\n', co2);

  % Get array element
  amaxtb = obj('AMAXTB');
  fprintf('Matlab Model: AMAXTB = \n');
  for i = 1:length(amaxtb{1})
    fprintf('\t%f\t%f\n', amaxtb{1}(i), amaxtb{2}(i));
  end;

  % Send output to output channel
  % If there is an error, the flag will be False
  flag = out_channel.send(obj);
  if (~flag)
    error('Matlab Model: Error sending output.');
    break;
  end;
  
end;
