program main
  use fygg

  character(len=32) :: arg
  integer :: iterations
  type(yggcomm) :: ymlfile
  type(yggcomm) :: rpc
  type(yggcomm) :: log
  logical :: ret
  integer, parameter :: msg_len = 2048  ! YGG_MSG_MAX
  character(len=msg_len) :: ycontent
  integer :: fib, fibNo, i, nlines, count_lines
  character(len=msg_len) :: logmsg
  integer :: ycontent_siz, logmsg_siz
  character(len=2) :: fibStr

  call get_command_argument(1, arg)
  read(arg, *) iterations
  write(*, '("Hello from Fortran rpcFibCli: iterations ",i2)') iterations

  ! Set up connections matching yaml
  ! RPC client-side connection will be $(server_name)_$(client_name)
  ymlfile = ygg_input("yaml_in")
  rpc = ygg_rpc_client("rpcFibSrv_rpcFibCli", "%d", "%d %d")
  log = ygg_output("output_log")

  ! Read entire contents of yaml
  ycontent_siz = len(ycontent)
  ret = ygg_recv(ymlfile, ycontent, ycontent_siz)
  if (.not.ret) then
     write(*, '("rpcFibCli(F): RECV ERROR")')
     stop 1
  end if
  nlines = count_lines(ycontent, new_line('A'))
  write(*, '("rpcFibCli: yaml has ",i4," lines")') nlines + 1
  ret = ygg_recv(ymlfile, ycontent, ycontent_siz)

  fib = -1
  fibNo = -1
  do i = 1, iterations

     ! Call the server and receive response
     write(*, '("rpcFibCli(F): fib(->",i2,") ::: ")') i
     ret = ygg_rpc_call(rpc, yggarg(i), [yggarg(fibNo), yggarg(fib)])
     if (.not.ret) then
        write(*, '("rpcFibCli(F): RPC CALL ERROR")')
        stop 1
     end if

     ! Log result by sending it to the log connection
     write(fibStr, '(i2)') fib
     write(logmsg, '("fib(",i2,"<-) = ",A,"<-",A)') fibNo, &
          adjustl(fibStr), new_line('A')
     write(*, '(A)', advance="no") trim(logmsg)
     logmsg_siz = len_trim(logmsg)
     ret = ygg_send(log, logmsg, logmsg_siz)
     if (.not.ret) then
        write(*, '("rpcFibCli(F): SEND ERROR")')
        stop 1
     end if

  end do

  write(*, '("Goodbye from Fortran rpcFibCli")')

end program main

function count_lines(str, substr) result(c)
  implicit none
  character(len=*) :: str
  character(len=*) :: substr
  integer :: c
  integer :: k, inc, idx
  c = 0
  k = 1
  inc = len_trim(substr)
  idx = index(str(k:), substr)
  do while (idx.ne.0)
     c = c + 1
     k = k + inc
     idx = index(str(k:), substr)
  end do
end function count_lines

