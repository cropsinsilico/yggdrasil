program main
  use fygg

  character(len=32) :: arg
  integer :: msg_count, msg_size
  type(yggcomm) :: outq
  logical :: ret
  integer :: i, count
  integer :: exit_code = 0
  character(len=:), allocatable :: test_msg

  if (command_argument_count().ne.2) then
     write(*, '("Error in Fortran pipe_src: The message count and size &
          &must be provided as input arguments.")')
     stop 1
  end if

  call get_command_argument(1, arg)
  read(arg, *) msg_count
  call get_command_argument(2, arg)
  read(arg, *) msg_size
  write(*, '("Hello from Fortran pipe_src: msg_count = ",i5.1,", &
       &msg_size = ",i5.1)') msg_count, msg_size

  ! Ins/outs matching with the the model yaml
  outq = ygg_output("output_pipe")
  write(*, '("pipe_src(F): Created I/O channels")')

  ! Create test message
  allocate(character(len=(msg_size + 1)) :: test_msg)
  do i = 1, msg_size
     test_msg(i:i) = '0'
  end do
  test_msg((msg_size+1):(msg_size+1)) = c_null_char

  ! Send test message multiple times
  count = 0
  do i = 1, msg_count
     ret = ygg_send(outq, test_msg, msg_size)
     if (.not.ret) then
        write(*, '("pipe_src(F): SEND ERROR ON MSG ",i5.1)') i
        exit_code = -1
        exit
     end if
     count = count + 1
  end do
  
  write(*, '("Goodbye from Fortran source. Sent ",i5.1," messages.")') count
  if (allocated(test_msg)) deallocate(test_msg)
  if (exit_code.lt.0) then
     stop 1
  end if

end program main
