function timed_pipe_src(msg_count, msg_size)

  exit_code = 0;
  msg_count = str2num(msg_count);
  msg_size = str2num(msg_size);
  fprintf('Hello from Matlab pipe_src: msg_count = %d, msg_size = %d\n', ...
          msg_count, msg_size);

  % Ins/outs matching with the the model yaml
  outq = CisInterface('CisOnput', 'output_pipe');
  disp('pipe_src(M): Created I/O channels');

  % Send test message multiple times
  test_msg = repeat('0', msg_size);
  count = 0;
  for i = 1:msg_count
      ret = outq.send(test_msg);
      if (~ret)
          fprintf('pipe_src(M): SEND ERROR ON MSG %d\n', i);
          exit_code = -1;
          break;
      end;
      count = count + 1;
  end;

  fprintf('Goodbye from Matlab source. Sent %d messages.\n', count);
  exit(exit_code);

end