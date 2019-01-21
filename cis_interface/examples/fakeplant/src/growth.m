input = CisInterface('CisInput', 'photosynthesis_rate');
output = CisInterface('CisOutput', 'growth_rate', '%f\n');

while (1)
  [flag, prate] = input.recv();
  if (~flag)
    disp('growth: No more input.');
    break;
  end;
  grate = 0.5 * prate{1};
  fprintf('growth: photosynthesis rate = %f ---> growth rate = %f\n', ...
          prate{1}, grate);
  flag = output.send(grate);
  if (~flag)
    error('growth: Error sending growth rate.');
  end;
end;
