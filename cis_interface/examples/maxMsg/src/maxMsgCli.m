
charset = ['0123456789', ...
	   'abcdefghijklmnopqrstuvwxyz', ...
	   'ABCDEFGHIJKLMNOPQRSTUVWXYZ'];


PSI_MSG_MAX = PsiInterface('PSI_MSG_MAX');
fprintf('maxMsgCli(M): Hello PSI_MSG_MAX is %d.\n', PSI_MSG_MAX);

% Create a max message, send/recv and verify
rpc = PsiInterface('PsiRpcClient', 'maxMsgSrv_maxMsgCli', '%s', '%s');

% Create a max message
output = '';
while (length(output) < (PSI_MSG_MAX-1))
  index = ceil(rand() * length(charset));
  output = [output, charset(index)];
end

% Call RPC server
input = rpc.rpcCall(output);
if (~input{1})
  disp('maxMsgCli(M): RPC ERROR');
  exit(-1);
end

% Check to see if response matches
if (input{2}{1} ~= output)
  disp('maxMsgCli(M): ERROR: input/output do not match');
  exit(-1);
else
  disp('maxMsgCli(M): CONFIRM');
end

% All done, say goodbye
disp('maxMsgCli(M): Goodbye!');

