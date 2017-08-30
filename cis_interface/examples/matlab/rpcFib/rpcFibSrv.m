
function rpcFibSrv(sleeptime)
  PsiInterface = py.importlib.import_module('cis_interface.interface.PsiInterface');
  sleeptime = str2num(sleeptime);
  
  disp('rpcFibSrv starts')

  rpc = PsiInterface.PsiRpc('srv_fib', '%d %d', 'srv_fib', '%d');

  while 1
    input = rpc.rpcRecv();
    if (~input{1})
      D = sprintf('rpcFibSrv(M): end of input');
      disp(D);
      exit(0);
    end
    input = input{2};
    D = sprintf('rpcFibSrv(M): got input %d', input{1});
    disp(D);

    pprev = 0;
    prev = 1;
    result = 1;
    n = 1;
    while n < input{1}
      result = prev + pprev;
      pprev = prev;
      prev = result;
      n = n+1;
    end
    pause(sleeptime);
    D = sprintf('rpcFibSrv(M): sending result %d %d', input{1}, result);
    disp(D);
    rpc.rpcSend(input{1}, result);
  end

  disp('rpcFibSrv: done')
  exit(0);
end



