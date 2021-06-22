using Yggdrasil
using Printf


function main(iterations, client_index)
    
  @printf("Hello from Julia client: iterations = %d\n", iterations)

  # Set up connections matching yaml
  # RPC client-side connection will be $(server_name)_$(client_name)
  rpc = Yggdrasil.YggInterface("YggRpcClient", @sprintf("server_client%d", client_index), "%d", "%d")
  log = Yggdrasil.YggInterface("YggOutput", @sprintf("output_log%d", client_index), "fib(%-2d) = %-2d\n")

  # Iterate over Fibonacci sequence
  for i = 1:iterations
        
    # Call the server and receive response
    @printf("client%d(Julia): Calling fib(%d)\n", client_index, i)
    ret, result = rpc.call(i)
    if (!ret)
      error(@sprintf("client%d(Julia): RPC CALL ERROR", client_index))
    end
    fib = result[1]
    @printf("client%d(Julia): Response fib(%d) = %d\n", client_index, i, fib)

    # Log result by sending it to the log connection
    ret = log.send(i, fib)
    if (!ret)
      error(@sprintf("client%d(Julia): SEND ERROR", client_index))
    end
  end

  @printf("Goodbye from Julia client%d\n", client_index)
end

    
main(parse(Int64, ARGS[1]), parse(Int64, ARGS[2]))
