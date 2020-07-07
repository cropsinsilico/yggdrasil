program main
  use fygg

  character(len=32) :: arg
  integer :: iterations
  type(yggcomm) :: rpc
  type(yggcomm) :: log
  logical :: ret
  integer :: fib, i
  integer :: exit_code = 0

  call get_command_argument(1, arg)
  read(arg, *) iterations
  write(*, '("Hello from Fortran client: iterations ",i2)') iterations

  ! Set up connections matching yaml
  ! RPC client-side connection will be $(server_name)_$(client_name)
  rpc = ygg_rpc_client("server_client", "%d", "%d")
  log = ygg_output_fmt("output_log", "fib(%-2d) = %-2d\n")

  ! Initialize variables
  ret = .true.
  fib = -1

  ! Iterate over Fibonacci sequence
  do i = 1, iterations

     ! Call the server and receive response
     write(*, '("client(F): Calling fib(",i2,")")') i
     ret = ygg_rpc_call(rpc, yggarg(i), yggarg(fib))
     if (.not.ret) then
        write(*, '("client(F): RPC CALL ERROR")')
        exit_code = -1;
        exit
     end if
     write(*, '("client(F): Response fib(",i2,") = ",i2)') i, fib

     ! Log result by sending it to the log connection
     ret = ygg_send_var(log, [yggarg(i), yggarg(fib)])
     if (.not.ret) then
        write(*, '("client(F): SEND ERROR")')
        exit_code = -1
        exit
     end if

  end do

  write(*, '("Goodbye from Fortran client")')
  if (exit_code.lt.0) then
     stop 1
  end if

end program main
