
function rpcFibCliPar(iterations)
  PsiInterface = py.importlib.import_module('cis_interface.interface.PsiInterface');
  iterations = str2num(iterations);

  fprintf('fibcliPar(M): hello, %d iterations', iterations);

  rpc = PsiInterface.PsiRpc('cli_par_fib', '%d', 'cli_par_fib', '%d %d');

  for i = 1:iterations
    fprintf('fibcli(M):  fib(->%-2d) ::: ', i);
    ret = rpc.rpcSend(i);
    if (~ret)
      disp('send failure');
      exit(-1);
    end
  end

  for i = 1:iterations
    fprintf('fibcli(M):  fib(->%-2d) ::: ', i);
    ret = rpc.rpcRecv();
    if (~ret{1}) 
      disp('end of input');
      exit(-1)
      break;
    end
    ret = ret{2}
    disp(sprintf('fib(%2d<-) = %-2d<-', ret{1}, ret{2}));
  end

  disp('fibcliPar(M) ends');

  exit(0);
end



