
function rpcFibCli(iterations)
  PsiInterface = py.importlib.import_module('cis_interface.interface.PsiInterface');
  iterations = str2num(iterations);

  NS = getenv('PSI_NAMESPACE')
  RANK = getenv('PSI_RANK')
  HOST = getenv('PSI_HOST')
  
  fprintf('fibcli(M): hello, system %s, PSI_NAMESPACE %s, PSI_RANK %s, %d iterations', HOST, NS, RANK, iterations);

  rpc = PsiInterface.PsiRpc('cli_fib', '%d', 'cli_fib', '%d %d');

  for i = 1:iterations
    fprintf('fibcli(M):  fib(->%-2d) ::: ', i);
    input = rpc.rpcCall(i);
    if (~input{1}) 
      break
    end
    input = input{2};
    fprintf('fib(%2d<-) = %-2d<-', input{1}, input{2});
    disp(' ');
  end

  disp('fibcli(M) ends');

  exit(0);
end




