disp('Hello from Matlab pipe_dst');

% Ins/outs matching with the the model yaml
inq = YggInterface('YggInput', 'input_pipe');
outf = YggInterface('YggOutput', 'output_file');
disp('pipe_dst(M): Created I/O channels');

% Continue receiving input from the queue
count = 0;
while (1);
  [flag, buf] = inq.recv();
  if (~flag);
    disp('pipe_dst(M): Input channel closed');
    break;
  end;
  ret = outf.send(buf);
  if (~ret);
    error(sprintf('pipe_dst(M): SEND ERROR ON MSG %d\n', count));
  end;
  count = count + 1;
end;

fprintf('Goodbye from Matlab destination. Received %d messages.\n', count);
