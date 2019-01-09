% Initialize input/output channels 
in_channel = CisInterface('CisObjInput', 'inputA');
out_channel = CisInterface('CisObjOutput', 'outputA');

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
  fprintf('Model A: (%d verts, %d faces)\n', obj.nvert, obj.nface);
  fprintf('  Vertices:\n');
  for i = 1:int64(obj.nvert)
    fprintf('   %f, %f, %f\n', ...
	    obj{'vertices'}{i}{'x'}, obj{'vertices'}{i}{'y'}, obj{'vertices'}{i}{'z'});
  end;
  fprintf('  Faces:\n');
  for i = 1:int64(obj.nface)
    fprintf('   %ld', int64(py.int(obj{'faces'}{i}{1}{'vertex_index'})));
    for j = 2:size(obj{'faces'}{i})
      fprintf(', %ld', int64(py.int(obj{'faces'}{i}{j}{'vertex_index'})));
    end;
    fprintf('\n');
  end;

  % Send output to output channel
  % If there is an error, the flag will be False
  flag = out_channel.send(obj);
  if (~flag)
    error('Model A: Error sending output.');
    break;
  end;
  
end;
