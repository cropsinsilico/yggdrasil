
function rpcFibCliPar(iterations)

  iterations = str2num(iterations);
  fprintf('Hello from Matlab rpcFibCliPar: iterations = %d\n', iterations);

  % Create RPC connection with serover
  % RPC client-side connection will be $(server_name)_$(client_name)
  rpc = CisInterface('CisRpcClient', 'rpcFibSrv_rpcFibCliPar', '%d', '%d %d');

  % Send all of the requests to the server
  for i = 1:iterations
    fprintf('rpcFibCliPar(M): fib(->%-2d) ::: \n', i);
    ret = rpc.send(i);
    if (~ret);
      disp('rpcFibCliPar(M): SEND FAILED');
      exit(-1);
    end
  end

  % Receive responses for all requests that were sent
  for i = 1:iterations
    fprintf('rpcFibCliPar(M): fib(->%-2d) ::: ', i);
    [ret, fib] = rpc.recv();
    if (~ret);
      disp('rpcFibCliPar(M): RECV FAILED')
      exit(-1);
      break;
    end
    fprintf('rpcFibCliPar(M): fib(%2d<-) = %-2d<-\n', fib{1}, fib{2});
  end

  disp('Goodbye from Matlab rpcFibCliPar');
  exit(0);
  
end



