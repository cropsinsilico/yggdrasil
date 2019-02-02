
function client(iterations)
  
  iterations = str2num(iterations);
  fprintf('Hello from Matlab client: iterations = %d\n', iterations);

  % Set up connections matching yaml
  % RPC client-side connection will be $(server_name)_$(client_name)
  rpc = YggInterface('YggRpcClient', 'server_client', '%d', '%d');
  log = YggInterface('YggOutput', 'output_log', 'fib(%-2d) = %-2d\n');

  % Iterate over Fibonacci sequence
  for i = 1:iterations
    
    % Call the server and receive response
    fprintf('client(Matlab): Calling fib(%d)\n', i);
    [ret, result] = rpc.call(int32(i));
    if (~ret);
      error('client(Matlab): RPC CALL ERROR');
    end;
    fib = result{1};
    fprintf('client(Matlab): Response fib(%d) = %d\n', i, fib);

    % Log result by sending it to the log connection
    ret = log.send(int32(i), fib);
    if (~ret);
      error('client(Matlab): SEND ERROR');
    end;
  end;

  disp('Goodbye from Matlab client');
  
end




