
function timesync(t_step, t_units, model)

  t_step = str2num(t_step);
  fprintf('Hello from Matlab timesync: timestep = %f %s\n', t_step, t_units);
  t_step = t_step * str2symunit(t_units);
  t_start = 0.0000000000000001 * str2symunit(t_units);
  t_end = 5.0 * str2symunit('day');
  state = timestep_calc(t_start, model);
    
  % Set up connections matching yaml
  % Timestep synchronization connection will be 'statesync'
  timesync = YggInterface('YggTimesync', 'statesync');
  out = YggInterface('YggOutput', 'output');

  % Initialize state and synchronize with other models
  t = t_start;
  [ret, state] = timesync.call(t, state);
  if (~ret);
    error('timesync(Matlab): Initial sync failed.');
  end;
  [t_data, t_unit] = separateUnits(t);
  fprintf('timesync(Matlab): t = %5.1f %-1s', ...
          t_data, symunit2str(t_unit));
  state_keys = keys(state);
  state_vals = values(state);
  for i = 1:length(state_keys)
    fprintf(', %s = %+ 5.2f', state_keys{i}, state_vals{i});
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
    state = timestep_calc(t, model);

    % Synchronize the state
    [ret, state] = timesync.call(t, state);
    if (~ret);
      error(sprintf('timesync(Matlab): sync for t=%f failed.\n', t));
    end;
    [t_data, t_unit] = separateUnits(t);
    fprintf('timesync(Matlab): t = %5.1f %-1s', ...
            t_data, symunit2str(t_unit));
    state_keys = keys(state);
    state_vals = values(state);
    for i = 1:length(state_keys)
      fprintf(', %s = %+ 5.2f', state_keys{i}, state_vals{i});
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
      error(sprintf('timesync(Matlab): Failed to send output for t=%s.\n', t));
    end;
  end;

  disp('Goodbye from Matlab timesync');
  
end


function state = timestep_calc(t, model)
  state = containers.Map('UniformValues', false, 'ValueType', 'any');
  if (model == 'A')
    state('x') = sin(2.0 * pi * t / (10.0 * str2symunit('day')));
    state('y') = cos(2.0 * pi * t / (5.0 * str2symunit('day')));
    state('z1') = -cos(2.0 * pi * t / (20.0 * str2symunit('day')));
    state('z2') = -cos(2.0 * pi * t / (20.0 * str2symunit('day')));
    state('a') = sin(2.0 * pi * t / (2.5 * str2symunit('day')));
  else
    state('xvar') = sin(2.0 * pi * t / (10.0 * str2symunit('day'))) / 2.0;
    state('yvar') = cos(2.0 * pi * t / (5.0 * str2symunit('day')));
    state('z') = -2.0 * cos(2.0 * pi * t / (20.0 * str2symunit('day')));
    state('b') = cos(2.0 * pi * t / (2.5 * str2symunit('day')));
  end;
end
