library(yggdrasil)


run <- function(args) {
  msg_count <- strtoi(args[[1]])
  msg_size <- strtoi(args[[2]])
  fprintf('Hello from R pipe_src: msg_count = %d, msg_size = %d',
          msg_count, msg_size)

  # Ins/outs matching with the the model yaml
  outq <- YggInterface('YggOutput', 'output_pipe')
  print("pipe_src(R): Created I/O channels")

  # Send test message multiple times
  test_msg <- paste(replicate(msg_size, '0'), collapse="")
  count <- 0
  for (i in 1:msg_count) {
    ret <- outq$send(test_msg)
    if (!ret) {
      stop(sprintf('pipe_src(R): SEND ERROR ON MSG %d', i))
    }
    count <- count + 1
  }

  fprintf('Goodbye from R source. Sent %d messages.', count)
}
    

args <- commandArgs(trailingOnly=TRUE)
run(args)
