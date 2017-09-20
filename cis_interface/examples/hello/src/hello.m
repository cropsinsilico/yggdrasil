disp('Hello from Matlab');

% Ins/outs matching with the the model yaml
inf = PsiInterface('PsiInput', 'inFile');
outf = PsiInterface('PsiOutput', 'outFile');
inq = PsiInterface('PsiInput', 'helloQueueIn');
outq = PsiInterface('PsiOutput', 'helloQueueOut');
disp('hello(M): Created I/O channels');

% Receive input from a local file
res = inf.recv();
if (~res{1});
  disp('hello(M): ERROR FILE RECV');
  exit(-1);
end
buf = char(res{2});
fprintf('hello(M): Received %d bytes from file: %s\n', ...
	length(buf), buf);

% Send output to the output queue
ret = outq.send(buf);
if (~ret);
  disp('hello(M): ERROR QUEUE SEND');
  exit(-1);
end
disp('hello(M): Sent to outq');

% Receive input form the input queue
res = inq.recv();
if (~res{1});
  disp('hello(M): ERROR QUEUE RECV');
  exit(-1);
end
buf = char(res{2});
fprintf('hello(M): Received %d bytes from queue: %s\n', ...
	length(buf), buf);

% Send output to a local file
ret = outf.send(buf);
if (~ret);
  disp('hello(M): ERROR FILE SEND');
  exit(-1);
end
disp('hello(M): Sent to outf');

disp('Goodbye from Matlab');

exit(0);
