
charset = ['0123456789', ...
	   'abcdefghijklmnopqrstuvwxyz', ...
	   'ABCDEFGHIJKLMNOPQRSTUVWXYZ'];


msg_size = PsiInterface('PSI_MSG_BUF');
fprintf('maxMsgCli(M): Hello message size is %d.\n', msg_size);

% Create a max message, send/recv and verify
rpc = PsiInterface('PsiRpcClient', 'maxMsgSrv_maxMsgCli', '%s', '%s');

% Create a max message
output = randsample(charset, msg_size-1, true);

% Call RPC server
input = rpc.rpcCall(output);
if (~input{1})
  error('maxMsgCli(M): RPC ERROR');
  exit(-1);
end

% Check to see if response matches
if (input{2}{1} ~= output)
  error('maxMsgCli(M): ERROR: input/output do not match');
  exit(-1);
else
  disp('maxMsgCli(M): CONFIRM');
end

% All done, say goodbye
disp('maxMsgCli(M): Goodbye!');
exit(0);
