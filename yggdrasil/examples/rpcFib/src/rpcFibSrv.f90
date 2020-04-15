program main
  use fygg

  type(yggcomm) :: rpc
  character(len=32) :: arg
  real :: time_sleep
  integer :: input
  integer :: result0, prevResult, prevPrev, idx
  logical :: ret

  call get_command_argument(1, arg)
  read(arg, *) time_sleep
  write(*, '("Hello from Fortran rpcFibSrv: sleeptime = ",f10.4)') time_sleep

  ! Create server-side rpc conneciton using model name
  rpc = ygg_rpc_server("rpcFibSrv", "%d", "%d %d")

  ! Continue receiving requests until error occurs (the connection is
  ! closed by all clients that have connected).
  do while (.true.)
     write(*, '("rpcFibSrv(F): receiving...")')

     ret = ygg_recv_var(rpc, yggarg(input))
     if (.not.ret) then
        write(*, '("rpcFibSrv(F): end of input")')
        exit
     end if

     ! Compute fibonacci number
     result0 = 1
     prevResult = 1
     prevPrev = 0
     idx = 1
     do while (idx.lt.input)
        result0 = prevResult + prevPrev
        prevPrev = prevResult
        prevResult = result0
        idx = idx + 1
     end do
     write(*, '("rpcFibSrv(F): <- input ",i2," ::: ->(",i2," ",i2,")")') &
          input, input, result0

     ! Sleep and then send response back
     if (time_sleep.gt.0) call fsleep(int(time_sleep))
     ret = ygg_send_var(rpc, [yggarg(input), yggarg(result0)])
     if (.not.ret) then
        write(*, '("rpcFibSrv(F): ERROR sending")')
        exit
     end if

  end do

  write(*, '("Goodbye from Fortran rpcFibSrv")')

end program main
