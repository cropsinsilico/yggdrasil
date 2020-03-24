program main
  ! Include methods for input/output channels
  use fygg

  ! Declare resulting variables and create buffer for received message
  logical :: flag = .true.
  type(yggcomm) :: in_channel, out_channel
  integer(kind=c_size_t), target :: nrows
  type(character_1d), target :: name
  type(c_long_1d), target :: count
  type(real8_1d), target :: siz
  integer(kind=c_size_t) :: i

  ! initialize input/output channels
  in_channel = ygg_ascii_array_input("inputA")
  out_channel = ygg_ascii_array_output("outputA", "%6s\t%ld\t%f\n")

  ! Loop until there is no longer input or the queues are closed
  do while (flag)

     ! Receive input from input channel
     ! If there is an error, the flag will be negative
     ! Otherwise, it is the number of variables filled
     flag = ygg_recv_var_realloc(in_channel, [ &
          yggarg(nrows), yggarg(name), yggarg(count), yggarg(siz)])
     if (.not.flag) then
        print *, "Model A: No more input."
        exit
     end if

     ! Print received message
     print *, "Model A: (", nrows, " rows)"
     do i = 1, nrows
        print *, "   ", name%x(i)%x, count%x(i), siz%x(i)
     end do

     ! Send output to output channel
     ! If there is an error, the flag will be negative
     flag = ygg_send_var(out_channel, [ &
          yggarg(nrows), yggarg(name), yggarg(count), yggarg(siz)])
     if (.not.flag) then
        print *, "Model A: Error sending output."
        exit
     end if

  end do

end program main
