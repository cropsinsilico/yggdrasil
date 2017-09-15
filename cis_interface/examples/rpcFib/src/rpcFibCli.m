
function rpcFibCli(iterations)
  
  iterations = str2num(iterations);
  fprintf('Hello from Matlab rpcFibCli: iterations = %d\n', iterations);

  % Set up connections matching yaml
  % RPC client-side connection will be $(server_name)_$(client_name)
  ymlfile = PsiInterface('PsiInput', 'yaml_in');
  rpc = PsiInterface('PsiRpcClient', 'rpcFibSrv_rpcFibCli', '%d', '%d %d');
  log = PsiInterface('PsiOutput', 'output_log');

  % Read entire contents of yaml
  input = ymlfile.recv();
  ret = input{1};
  ycontent = char(input{2});
  if (~ret);
    disp('rpcFibCli(M): RECV ERROR');
    exit(-1);
  end
  fprintf('rpcFibCli: yaml has %d lines\n', ...
	  length(strsplit(ycontent, '\n', 'CollapseDelimiters', false)));

  for i = 1:iterations
    
    % Call the server and receive response
    fprintf('rpcFibCli(M):  fib(->%-2d) ::: ', i);
    input = rpc.rpcCall(i);
    ret = input{1};
    fib = input{2};
    if (~ret);
      disp('rpcFibCli(M): RPC CALL ERROR');
      exit(-1);
    end

    % Log result by sending it to the log connection
    s = sprintf('fib(%2d<-) = %-2d<-\n', fib{1}, fib{2});
    fprintf(s);
    ret = log.send(s);
    if (~ret);
      disp('rpcFibCli(M): SEND ERROR');
      exit(-1);
    end
  end

  disp('Goodbye from Matlab rpcFibCli');
  exit(0);
  
end




