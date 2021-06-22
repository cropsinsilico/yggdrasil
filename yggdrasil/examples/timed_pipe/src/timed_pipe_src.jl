using Yggdrasil
using Printf


function run(args)
  msg_count = parse(Int64, args[1])
  msg_size = parse(Int64, args[2])
  @printf("Hello from Julia pipe_src: msg_count = %d, msg_size = %d\n",
          msg_count, msg_size)

  # Ins/outs matching with the the model yaml
  outq = Yggdrasil.YggInterface("YggOutput", "output_pipe")
  println("pipe_src(Julia): Created I/O channels")

  # Send test message multiple times
  test_msg = "0"^msg_size
  global count = 0
  for i = 1:msg_count
    ret = outq.send(test_msg)
    if (!ret)
      error(@sprintf("pipe_src(Julia): SEND ERROR ON MSG %d", i))
    end
    global count = count + 1
  end

  @printf("Goodbye from Julia source. Sent %d messages.\n", count)
end
    

run(ARGS)
