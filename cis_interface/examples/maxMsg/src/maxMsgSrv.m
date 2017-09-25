

disp('maxMsgSrv(M): Hello!');
rpc = PsiInterface('PsiRpcServer', 'maxMsgSrv', '%s', '%s');

input = rpc.rpcRecv();
fprintf('maxMsgSrv(M): rpcRecv returned %d, input %s\n', ...
	input{1}, char(input{2}{1}));
rpc.rpcSend(input{2}{1});

disp('maxMsgSrv(M): Goodbye!');

