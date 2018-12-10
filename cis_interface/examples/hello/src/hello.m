disp('Hello from Matlab');

% Ins/outs matching with the the model yaml
inf = CisInterface('CisInput', 'inFile');
outf = CisInterface('CisOutput', 'outFile');
inq = CisInterface('CisInput', 'helloQueueIn');
outq = CisInterface('CisOutput', 'helloQueueOut');
disp('hello(M): Created I/O channels');

% Receive input from a local file
[flag, buf] = inf.recv();
if (~flag);
  error('hello(M): ERROR FILE RECV');
end
fprintf('hello(M): Received %d bytes from file: %s\n', ...
	length(buf), buf);

% Send output to the output queue
ret = outq.send(buf);
if (~ret);
  error('hello(M): ERROR QUEUE SEND');
end
disp('hello(M): Sent to outq');
outq.send_eof();

% Receive input form the input queue
[flag, buf] = inq.recv();
if (~flag);
  error('hello(M): ERROR QUEUE RECV');
end
fprintf('hello(M): Received %d bytes from queue: %s\n', ...
	length(buf), buf);

% Send output to a local file
ret = outf.send(buf);
if (~ret);
  error('hello(M): ERROR FILE SEND');
end
disp('hello(M): Sent to outf');

disp('Goodbye from Matlab');
