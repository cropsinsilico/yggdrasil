PROGRAM main
  ! Include methods for input/output channels
  USE fygg

  ! Declare resulting variables and create buffer
  ! for received message
  integer :: MYBUFSIZ = 1000, flag = 1
  TYPE(yggcomm) :: in_channel, out_channel
  character(len = 1000) :: buf

  ! Initialize input/output channels
  in_channel = ygg_input("input")
  out_channel = ygg_output("output")

  ! Loop until there is no longer input or the queues are closed
  DO WHILE (flag.gt.0)

    ! Receive input from input channel
    ! If there is an error or the queue is closed, the flag will be negative
     ! Otherwise, it is the size of the received message
     flag = ygg_recv(in_channel, buf, MYBUFSIZ)
     IF (ret.lt.0) THEN
        PRINT *, "No more input."
        EXIT
     END IF

     ! Print received message
     PRINT *, buf

     ! Send output to output channel
     ! If there is an error, the flag will be negative
     flag = ygg_send(out_channel, buf, flag)
     IF (ret.lt.0) THEN
        PRINT *, "Error sending output."
        EXIT
     END IF
     
  END DO

  CALL EXIT(0)
  
END PROGRAM main
