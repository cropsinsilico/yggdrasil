% Initialize input/output channels 
in_channel = CisInterface('CisPlyInput', 'inputA');
out_channel = CisInterface('CisPlyOutput', 'outputA');

flag = true;

% Loop until there is no longer input or the queues are closed
while flag

  % Receive input from input channel
  % If there is an error, the flag will be False.
  [flag, ply] = in_channel.recv();
  if (~flag)
    disp('Model A: No more input.');
    break;
  end;

  % Print received message
  fprintf('Model A: (%d verts, %d faces)\n', ply.nvert, ply.nface);
  fprintf('  Vertices:\n');
  for i = 1:int64(ply.nvert)
    fprintf('   %f, %f, %f\n', ...
            ply{'vertices'}{i}{'x'}, ply{'vertices'}{i}{'y'}, ply{'vertices'}{i}{'z'});
  end;
  fprintf('  Faces:\n');
  for i = 1:int64(ply.nface)
    fprintf('   %d', ply{'faces'}{i}{'vertex_index'}{1});
    for j = 2:size(ply{'faces'}{i}{'vertex_index'})
      fprintf(', %d', ply{'faces'}{i}{'vertex_index'}{j});
    end;
    fprintf('\n');
  end;

  % Send output to output channel
  % If there is an error, the flag will be False
  flag = out_channel.send(ply);
  if (~flag)
    error('Model A: Error sending output.');
    break;
  end;
  
end;
