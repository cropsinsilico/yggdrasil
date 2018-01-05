
charset = ['0123456789', ...
	   'abcdefghijklmnopqrstuvwxyz', ...
	   'ABCDEFGHIJKLMNOPQRSTUVWXYZ'];


PSI_MSG_MAX = PsiInterface('PSI_MSG_MAX');
fprintf('maxMsgCli(M): Hello PSI_MSG_MAX is %d.\n', PSI_MSG_MAX);

% Create a max message, send/recv and verify
rpc = PsiInterface('PsiRpcClient', 'maxMsgSrv_maxMsgCli', '%s', '%s');

% Create a max message
output = randsample(charset, PSI_MSG_MAX-1, true);

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
