program main
  ! Include methods for input/output channels
  use fygg

  ! Declare resulting variables and create buffer for received message
  logical :: flag = .true.
  type(yggcomm) :: in_channel, out_channel
  type(yggchar_r) :: msg  ! Structure wrapping reallocatable string
  integer(kind=c_size_t), target :: msg_siz = 0

  ! Initialize input/output channels
  in_channel = ygg_input("inputB")
  out_channel = ygg_output("outputB")

  ! Loop until there is no longer input or the queues are closed
  do while (flag)

     ! Receive input from input channel
     ! If there is an error, the flag will be negative
     ! Otherwise, it is the number of variables filled
     flag = ygg_recv_var_realloc(in_channel, &
          [yggarg(msg), yggarg(msg_siz)])
     if (.not.flag) then
        print *, "Model B: No more input."
        exit
     end if

     ! Print received message
     print *, "Model B: ", msg%x

     ! Send output to output channel
     ! If there is an error, the flag will be negative
     flag = ygg_send_var(out_channel, &
          [yggarg(msg), yggarg(msg_siz)])
     if (.not.flag) then
        print *, "Model B: Error sending output."
        exit
     end if

  end do

end program main
