
function rpcFibCli(iterations)
  
  iterations = str2num(iterations);
  fprintf('Hello from Matlab rpcFibCli: iterations = %d', iterations);

  % Set up connections matching yaml
  ymlfile = PsiInterface('PsiInput', 'yaml_in');
  rpc = PsiInterface('PsiRpc', 'cli_fib', '%d', 'cli_fib', '%d %d');
  log = PsiInterface('PsiOutput', 'output_log');

  % Read entire contents of yaml
  input = ymlfile.recv();
  fprintf('rpcFibCli: yaml has %d lines', count(input, '\n'));

  for i = 1:iterations
    
    % Call the server and receive response
    fprintf('rpcFibCli(M):  fib(->%-2d) ::: ', i);
    input = rpc.rpcCall(i);
    if (~input{1}) 
      break
    end

    % Log result by sending it to the log connection
    input = input{2};
    s = sprintf('fib(%2d<-) = %-2d<-\n', input{1}, input{2});
    disp(s);
    log.send(s);
  end

  disp('Goodbye from Python rpcFibCli');
  exit(0);
  
end




