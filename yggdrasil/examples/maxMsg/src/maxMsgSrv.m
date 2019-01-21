

disp('maxMsgSrv(M): Hello!');

rpc = YggInterface('YggRpcServer', 'maxMsgSrv', '%s', '%s');

while (1)
  [flag, vars] = rpc.recv();
  if (~flag)
    break;
  end
  fprintf('maxMsgSrv(M): rpcRecv returned %d, input %.10s...\n', ...
	  flag, char(vars{1}));
  flag = rpc.send(vars{1});
  if (~flag)
    error('maxMsgSrv(M): Error sending reply.');
  end
end

disp('maxMsgSrv(M): Goodbye!');

