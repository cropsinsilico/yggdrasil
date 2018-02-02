disp('Hello from Matlab pipe_dst');

% Ins/outs matching with the the model yaml
inq = PsiInterface('PsiInput', 'input_pipe');
outf = PsiInterface('PsiOutput', 'output_file');
disp('pipe_dst(M): Created I/O channels');

% Continue receiving input from the queue
count = 0;
while (1);
  res = inq.recv();
  if (~res{1});
    disp('pipe_dst(M): Input channel closed');
    break;
  end;
  buf = char(res{2});
  ret = outf.send(buf);
  if (~ret);
    fprintf('pipe_dst(M): SEND ERROR ON MSG %d\n', count);
    exit(-1);
  end;
  count = count + 1;
end;

fprintf('Goodbye from Matlab destination. Received %d messages.\n', count);

exit(0);
