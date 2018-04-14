
function client(iterations)
  
  iterations = str2num(iterations);
  exit_code = 0;
  fprintf('Hello from Matlab client: iterations = %d\n', iterations);

  % Set up connections matching yaml
  % RPC client-side connection will be $(server_name)_$(client_name)
  rpc = CisInterface('CisRpcClient', 'server_client', '%d', '%d');
  log = CisInterface('CisOutput', 'output_log', 'fib(%-2d) = %-2d\n');

  % Iterate over Fibonacci sequence
  for i = 1:iterations
    
    % Call the server and receive response
    fprintf('client(Matlab): Calling fib(%d)\n', i);
    [ret, result] = rpc.call(i);
    if (~ret);
      disp('client(Matlab): RPC CALL ERROR');
      exit_code = -1;
      break;
    end;
    fib = result{1};
    fprintf('client(Matlab): Response fib(%d) = %d\n', i, fib);

    % Log result by sending it to the log connection
    ret = log.send(i, fib);
    if (~ret);
      disp('client(Matlab): SEND ERROR');
      exit_code = -1;
      break;
    end;
  end;

  disp('Goodbye from Matlab client');
  exit(exit_code);
  
end




