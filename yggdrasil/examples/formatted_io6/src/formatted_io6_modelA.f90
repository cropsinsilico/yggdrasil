program main
  ! Include methods for input/output channels
  use fygg

  ! Declare resulting variables and create buffer for received message
  logical :: flag = .true.
  type(yggcomm) :: in_channel, out_channel
  type(yggobj) :: p
  p = init_obj()

  ! initialize input/output channels
  in_channel = ygg_obj_input("inputA")
  out_channel = ygg_obj_output("outputA")

  ! Loop until there is no longer input or the queues are closed
  do while (flag)

     ! Receive input from input channel
     ! If there is an error, the flag will be negative
     ! Otherwise, it is the number of variables filled
     flag = ygg_recv_var(in_channel, yggarg(p))
     if (.not.flag) then
        print *, "Model A: No more input."
        exit
     end if

     ! Print received message
     print *, "Model A: (", p%nvert, " verts, ", p%nface, " faces)"
     call display_obj_indent(p, "  ")

     ! Send output to output channel
     ! If there is an error, the flag will be negative
     flag = ygg_send_var(out_channel, yggarg(p))
     if (.not.flag) then
        print *, "Model A: Error sending output."
        exit
     end if

  end do

end program main
