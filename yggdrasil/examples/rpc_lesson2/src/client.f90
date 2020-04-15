program main
  use fygg

  character(len=32) :: arg
  integer :: iterations, client_index
  type(yggcomm) :: rpc
  type(yggcomm) :: log
  logical :: ret
  integer :: fib, i
  integer :: exit_code = 0
  character(len=100) :: rpc_name
  character(len=100) :: log_name

  call get_command_argument(1, arg)
  read(arg, *) iterations
  call get_command_argument(2, arg)
  read(arg, *) client_index
  write(*, '("Hello from Fortran client",i1,": iterations ",i2)') &
       client_index, iterations

  ! Set up connections matching yaml
  ! RPC client-side connection will be $(server_name)_$(client_name)
  write(rpc_name, '("server_client",i1)') client_index
  write(log_name, '("output_log",i1)') client_index
  rpc = ygg_rpc_client(trim(rpc_name), "%d", "%d")
  log = ygg_output_fmt(trim(log_name), "fib(%-2d) = %-2d\n")

  ! Initialize variables
  ret = .true.
  fib = -1

  ! Iterate over Fibonacci sequence
  do i = 1, iterations

     ! Call the server and receive response
     write(*, '("client",i1,"(F): Calling fib(",i2,")")') &
          client_index, i
     ret = ygg_rpc_call(rpc, yggarg(i), yggarg(fib))
     if (.not.ret) then
        write(*, '("client",i1,"(F): RPC CALL ERROR")') client_index
        exit_code = -1;
        exit
     end if
     write(*, '("client",i1,"(F): Response fib(",i2,") = ",i2)') &
          client_index, i, fib

     ! Log result by sending it to the log connection
     ret = ygg_send_var(log, [yggarg(i), yggarg(fib)])
     if (.not.ret) then
        write(*, '("client",i1,"(F): SEND ERROR")') client_index
        exit_code = -1
        exit
     end if

  end do

  write(*, '("Goodbye from Fortran client",i1)') client_index
  if (exit_code.lt.0) then
     stop 1
  end if

end program main
