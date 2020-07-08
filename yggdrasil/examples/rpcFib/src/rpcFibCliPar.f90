program main
  use fygg

  character(len=32) :: arg
  integer :: iterations
  type(yggcomm) :: rpc
  logical :: ret
  integer :: fib, fibNo, i

  call get_command_argument(1, arg)
  read(arg, *) iterations
  write(*, '("Hello from Fortran rpcFibCliPar: iterations = ",i2)') &
       iterations

  ! Create RPC connection with server
  ! RPC client-side connection will be $(server_name)_$(client_name)
  rpc = ygg_rpc_client("rpcFibSrv_rpcFibCliPar", "%d", "%d %d")

  ! Send all of the requests to the server
  do i = 1, iterations
     write(*, '("rpcFibCliPar(F): fib(->",i2,") ::: ")') i
     ret = ygg_send_var(rpc, yggarg(i))
     if (.not.ret) then
        write(*, '("rpcFibCliPar(F): SEND FAILED")')
        stop 1
     end if
  end do

  ! Receive responses for all requests that were sent
  fib = -1
  fibNo = -1
  do i = 1, iterations
     ret = ygg_recv_var(rpc, [yggarg(fibNo), yggarg(fib)])
     if (.not.ret) then
        write(*, '("rpcFibCliPar(F): RECV FAILED")')
        stop 1
     end if
     write(*, '("rpcFibCliPar(F):  fib(",i2,"<-) = ",i2,"<-")') &
          fibNo, fib
  end do

  write(*, '("Goodbye from Fortran rpcFibCliPar")')

end program main
