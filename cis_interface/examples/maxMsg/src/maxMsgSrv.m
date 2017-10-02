

disp('maxMsgSrv(M): Hello!');
rpc = PsiInterface('PsiRpcServer', 'maxMsgSrv', '%s', '%s');

while (1)
  input = rpc.rpcRecv();
  if (~input{1})
    break;
  end
  fprintf('maxMsgSrv(M): rpcRecv returned %d, input %s\n', ...
	  input{1}, char(input{2}{1}));
  rpc.rpcSend(input{2}{1});
end

disp('maxMsgSrv(M): Goodbye!');

