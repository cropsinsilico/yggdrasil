
function rpcFibCliPar(iterations)

  iterations = str2num(iterations);
  fprintf('Hello from Python rpcFibCliPar: iterations = %d', iterations);

  % Create RPC connection with serover
  rpc = PsiInterface('PsiRpc', 'cli_par_fib', '%d', 'cli_par_fib', '%d %d');

  % Send all of the requests to the server
  for i = 1:iterations
    fprintf('Pfibcli(M):  fib(->%-2d) ::: \n', i);
    ret = rpc.rpcSend(i);
    if (~ret)
      disp('SEND FAILED');
      exit(-1);
    end
  end

  % Receive responses for all requests that were sent
  for i = 1:iterations
    fprintf('Pfibcli(M):  fib(->%-2d) ::: ', i);
    ret = rpc.rpcRecv();
    if (~ret{1}) 
      disp('end of input');
      exit(-1);
      break;
    end
    ret = ret{2};
    fprintf('Pfibcli(M): fib(%2d<-) = %-2d<-\n', ret{1}, ret{2});
  end

  disp('Goodbye from Python rpcFibCliPar');
  exit(0);
  
end



