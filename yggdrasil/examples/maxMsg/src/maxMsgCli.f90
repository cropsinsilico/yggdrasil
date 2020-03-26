program main
  use fygg

  integer(kind=c_size_t) :: msg_size_output = YGG_MSG_BUF
  integer(kind=c_size_t) :: msg_size_input = YGG_MSG_BUF
  character, dimension(YGG_MSG_BUF) :: output
  type(yggchar_r) :: input
  type(yggcomm) :: rpc
  logical :: ret

  print *, "maxMsgCli(F): Hello message size is ", msg_size_output

  ! Create a max message, send/recv and verify
  rpc = ygg_rpc_client("maxMsgSrv_maxMsgCli", "%s", "%s")

  ! Create a max message
  call rand_str(output, msg_size_output)
  print *, "maxMsgCli(F): sending ", output(1:10), "..."

  ! Call RPC server
  msg_size_input = size(input%x)
  ret = ygg_rpc_call_realloc(rpc, &
       [yggarg(output), yggarg(msg_size_output)], &
       [yggarg(input), yggarg(msg_size_input)])
  if (.not.ret) then
     print *, "maxMsgCli(F): RPC ERROR"
     stop 1
  end if
  print *, "maxMsgCli(F): received ", msg_size_input, " bytes: ", &
       input%x(1:10), "..."

  ! Check to see if response matches
  if (.not.all(output.eq.(input%x))) then
     print *, "maxMsgCli(F): ERROR: input/output do not match"
     stop 1
  else
     print *, "maxMsgCli(F): CONFIRM"
  end if

  ! All done, free and say goodbye
  print *, "maxMsgCli(F): Goodbye!"

end program main

subroutine rand_str(x, x_siz)
  use fygg
  character, dimension(*) :: x
  real :: x_rand
  integer(kind=c_size_t) :: x_siz, i, index
  character(len=62) :: charset
  charset = "0123456789&
       &abcdefghijklmnopqrstuvwxyz&
       &ABCDEFGHIJKLMNOPQRSTUVWXYZ"
  do i = 1, x_siz
     call random_number(x_rand)
     index = int(x_rand * (len(charset) - 1), c_size_t) + 1
     x(i) = charset(index:index)
  end do
  ! do i = (x_siz+1), size(x)
  !    x(i) = ' '
  ! end do
end subroutine rand_str

