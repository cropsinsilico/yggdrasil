PROGRAM hello
  USE fygg

  logical :: ret = .true.
  integer :: bufsiz
  character(len = 512) :: buf = ""
  TYPE(yggcomm) :: inf, outf, inq, outq

  PRINT *, "Hello from Fortran"

  ! Ins/outs matching with the the model yaml
  inf = ygg_input("inFile")
  outf = ygg_output("outFile")
  inq = ygg_input("helloQueueIn")
  outq = ygg_output("helloQueueOut")
  PRINT *, "hello(Fortran): Created I/O channels"

  ! Receive input from a local file
  bufsiz = len(buf)
  ret = ygg_recv(inf, buf, bufsiz)
  IF (.not.ret) THEN
     PRINT *, "hello(Fortran): ERROR FILE RECV"
     STOP 1
  END IF
  PRINT *, "hello(Fortran): Received ", bufsiz, &
       "bytes from file: ", buf

  ! Send output to the output queue
  ret = ygg_send(outq, buf, bufsiz)
  IF (.not.ret) THEN
     PRINT *, "hello(Fortran): ERROR QUEUE SEND"
     STOP 1
  END IF
  PRINT *, "hello(Fortran): Sent to outq"
  
  ! Receive input form the input queue
  bufsiz = len(buf)
  ret = ygg_recv(inq, buf, bufsiz)
  IF (.not.ret) THEN
     PRINT *, "hello(Fortran): ERROR QUEUE RECV"
     STOP 1
  END IF
  PRINT *, "hello(Fortran): Received ", bufsiz, &
       "bytes from queue: ", buf

  ! Send output to a local file
  ret = ygg_send(outf, buf, bufsiz)
  IF (.not.ret) THEN
     PRINT *, "hello(Fortran): ERROR FILE SEND"
     STOP 1
  END IF
  PRINT *, "hello(Fortran): Sent to outf"

  PRINT *, "Goodbye from Fortran"
  
END PROGRAM hello
