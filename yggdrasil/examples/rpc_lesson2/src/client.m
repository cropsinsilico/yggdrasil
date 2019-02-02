
function client(iterations, client_index)
  
  iterations = str2num(iterations);
  client_index = str2num(client_index);
  fprintf('Hello from Matlab client%d: iterations = %d\n', ...
          client_index, iterations);

  % Set up connections matching yaml
  % RPC client-side connection will be $(server_name)_$(client_name)
  rpc_name = sprintf('server_client%d', client_index);
  log_name = sprintf('output_log%d', client_index);
  rpc = YggInterface('YggRpcClient', rpc_name, '%d', '%d');
  log = YggInterface('YggOutput', log_name, 'fib(%-2d) = %-2d\n');

  % Iterate over Fibonacci sequence
  for i = 1:iterations
    
    % Call the server and receive response
    fprintf('client%d(Matlab): Calling fib(%d)\n', client_index, i);
    [ret, result] = rpc.call(int32(i));
    if (~ret);
      error(sprintf('client%d(Matlab): RPC CALL ERROR\n', client_index));
    end;
    fib = result{1};
    fprintf('client%d(Matlab): Response fib(%d) = %d\n', client_index, ...
            i, fib);

    % Log result by sending it to the log connection
    ret = log.send(int32(i), fib);
    if (~ret);
      error(sprintf('client%d(Matlab): SEND ERROR\n', client_index));
    end;
  end;

  fprintf('Goodbye from Matlab client%d\n', client_index);
  
end




