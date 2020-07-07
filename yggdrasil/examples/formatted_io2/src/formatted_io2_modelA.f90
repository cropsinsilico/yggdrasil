program main
  ! Include methods for input/output channels
  use fygg

  ! Declare resulting variables and create buffer for received message
  logical :: flag = .true.
  type(yggcomm) :: in_channel, out_channel
  integer(kind=c_size_t), parameter :: MYBUFSIZ = 1000
  character(len=MYBUFSIZ), target :: msg
  integer(kind=c_size_t), target :: msg_siz = 0
  integer, target :: count = 0
  real(kind=8), target :: siz = 0.0
  
  ! Initialize input/output channels
  in_channel = ygg_ascii_table_input("inputA")
  out_channel = ygg_ascii_table_output("outputA", "%6s\t%d\t%f\n")

  ! Loop until there is no longer input or the queues are closed
  do while (flag)
     msg_siz = MYBUFSIZ

     ! Receive input from input channel
     ! If there is an error, the flag will be negative
     ! Otherwise, it is the number of variables filled
     flag = ygg_recv_var(in_channel, [ &
          yggarg(msg), yggarg(msg_siz), yggarg(count), yggarg(siz)])
     if (.not.flag) then
        print *, "Model A: No more input."
        exit
     end if

     ! Print received message
     print *, "Model A: ", msg, count, siz

     ! Send output to output channel
     ! If there is an error, the flag will be negative
     flag = ygg_send_var(out_channel, [ &
          yggarg(msg), yggarg(msg_siz), yggarg(count), yggarg(siz)])
     if (.not.flag) then
        print *, "Model A: Error sending output."
        exit
     end if

  end do

end program main
