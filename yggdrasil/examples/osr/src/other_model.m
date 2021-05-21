
function timesync(t_step, t_units)

  t_step = str2num(t_step);
  fprintf('Hello from Matlab other_model: timestep = %f %s\n', t_step, t_units);
  t_step = t_step * str2symunit(t_units);
  t_start = 0.0000000000000001 * str2symunit(t_units);
  t_end = 1.0 * str2symunit('day');
  state = containers.Map('UniformValues', false, 'ValueType', 'any');
  state('carbonAllocation2Roots') = 10.0 * str2symunit('g');
  state('saturatedConductivity') = 10.0 * str2symunit('cm/day');

  % Set up connections matching yaml
  % Timestep synchonization connection will default to 'timesync'
  timesync = YggInterface('YggTimesync', 'timesync');
  out = YggInterface('YggOutput', 'output');

  % Initialize state and synchronize with other models
  t = t_start;
  [ret, state] = timesync.call(t, state);
  if (~ret);
    error('other_model(Matlab): Initial sync failed.');
  end;
  [t_data, t_unit] = separateUnits(t);
  fprintf('other_model(Matlab): t = %5.1f %-1s', ...
	  t_data, symunit2str(t_unit));
  for k = keys(state)
    fprintf(', %s = %+ 5.2f', k{1}, state(k{1}));
  end;
  fprintf('\n');

  % Send initial state to output
  msg_keys = keys(state);
  msg_keys{length(msg_keys) + 1} = 'time';
  msg_vals = values(state);
  msg_vals{length(msg_vals) + 1} = t;
  msg = containers.Map(msg_keys, msg_vals, 'UniformValues', false);
  flag = out.send(msg);

  % Iterate until end
  while (simplify(t/t_end) < 1)

    % Perform calculations to update the state
    t = t + t_step;
    state = containers.Map('UniformValues', false, 'ValueType', 'any');
    state('carbonAllocation2Roots') = 10.0 * str2symunit('g');
    state('saturatedConductivity') = 10.0 * str2symunit('cm/day');

    % Synchronize the state
    [ret, state] = timesync.call(t, state);
    if (~ret);
      error(sprintf('other_model(Matlab): sync for t=%f failed.\n', t));
    end;
    [t_data, t_unit] = separateUnits(t);
    fprintf('other_model(Matlab): t = %5.1f %-1s', ...
            t_data, symunit2str(t_unit));
    for k = keys(state)
      fprintf(', %s = %+ 5.2f', k{1}, state(k{1}));
    end;
    fprintf('\n');

    % Send output
    msg_keys = keys(state);
    msg_keys{length(msg_keys) + 1} = 'time';
    msg_vals = values(state);
    msg_vals{length(msg_vals) + 1} = t;
    msg = containers.Map(msg_keys, msg_vals, 'UniformValues', false);
    flag = out.send(msg);
    if (~flag);
      error(sprintf('other_model(Matlab): Failed to send output for t=%s.\n', t));
    end;
  end;

  disp('Goodbye from Matlab other_model');
  
end




