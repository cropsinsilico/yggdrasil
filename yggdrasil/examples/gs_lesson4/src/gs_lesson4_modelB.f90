PROGRAM main
  ! Include methods for input/output channels
  USE fygg

  ! Declare resulting variables and create buffer for received message
  logical :: flag = .true.
  integer :: bufsiz
  TYPE(yggcomm) :: in_channel, out_channel
  character(len = 1000) :: buf

  ! Initialize input/output channels
  in_channel = ygg_input("inputB")
  out_channel = ygg_output("outputB")

  ! Loop until there is no longer input or the queues are closed
  DO WHILE (flag)
  
     ! Receive input from input channel
     ! If there is an error, the flag will be negative
     ! Otherwise, it is the size of the received message
     bufsiz = len(buf)
     flag = ygg_recv(in_channel, buf, bufsiz)
     IF (.not.flag) THEN
        PRINT *, "Model B: No more input."
        EXIT
     END IF

     ! Print received message
     PRINT *, "Model B: ", buf

     ! Send output to output channel
     ! If there is an error, the flag will be negative
     flag = ygg_send(out_channel, buf, bufsiz)
     IF (.not.flag) THEN
        PRINT *, "Model B: Error sending output."
        EXIT
     END IF

  END DO

END PROGRAM main
