function out_buf = client(in_buf)
  % The global_scope keyword is required to ensure that the comm persists
  % between function calls
  rpc = YggInterface('YggRpcClient', 'server_client', 'global_scope', true);
  disp(sprintf('client(Matlab): %s', in_buf));
  [ret, result] = rpc.call(in_buf);
  if (~ret);
    error('client(Matlab): RPC CALL ERROR');
  end;
  out_buf = result;
end
