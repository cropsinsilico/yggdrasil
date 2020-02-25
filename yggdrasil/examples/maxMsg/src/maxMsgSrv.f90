program main
  use fygg

  type(yggcomm) :: rpc
  integer(kind=c_size_t) :: input_size
  type(yggchar_r) :: input
  integer :: ret

  print *, "maxMsgSrv(F): Hello!"
  rpc = ygg_rpc_server("maxMsgSrv", "%s", "%s")

  do while (.true.)
     ! Reset to size of buffer if not all utilized
     input_size = size(input%x)

     ret = ygg_recv_var_realloc(rpc, [yggarg(input), yggarg(input_size)])
     if (ret.lt.0) exit
     print *, "maxMsgSrv(F): rpcRecv returned ", ret, ", input (size=", &
          input_size, ") ", input%x(1:10)
     ret = ygg_send_var(rpc, [yggarg(input), yggarg(input_size)])
     if (ret.lt.0) then
        print *, "maxMsgSrv(F): SEND ERROR"
        exit
     end if

  end do

  print *, "maxMsgSrv(F): Goodbye!"
  call exit(0)

end program main
