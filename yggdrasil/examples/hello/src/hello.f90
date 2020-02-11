PROGRAM hello
  USE ygg
  USE ISO_C_BINDING
  IMPLICIT none

  integer :: BSIZE = 512 ! the max
  integer :: ret = 0
  integer :: bufsiz
  character(len = 512) :: buf
  TYPE(yggcomm) :: inf, outf, inq, outq

  PRINT *, "Hello from Fortran"

  ! Ins/outs matching with the the model yaml
  inf = ygg_input("inFile")
  outf = ygg_output("outFile")
  inq = ygg_input("helloQueueIn")
  outq = ygg_output("helloQueueOut")
  PRINT *, "hello(Fortran): Created I/O channels"

  ! Receive input from a local file
  ret = ygg_recv(inf, buf, BSIZE)
  IF (ret.lt.0) THEN
     PRINT *, "hello(Fortran): ERROR FILE RECV"
     CALL EXIT(-1)
  END IF
  bufsiz = ret
  PRINT *, "hello(Fortran): Received", bufsiz, "bytes from file:", buf

  ! Send output to the output queue
  ret = ygg_send(outq, buf, bufsiz)
  IF (ret.lt.0) THEN
     PRINT *, "hello(Fortran): ERROR QUEUE SEND"
     CALL EXIT(-1)
  END IF
  PRINT *, "hello(Fortran): Sent to outq"
  
  ! Receive input form the input queue
  ret = ygg_recv(inq, buf, BSIZE)
  IF (ret.lt.0) THEN
     PRINT *, "hello(Fortran): ERROR QUEUE RECV"
     CALL EXIT(-1)
  END IF
  bufsiz = ret
  PRINT *, "hello(Fortran): Received", bufsiz, "bytes from queue:", buf

  ! Send output to a local file
  ret = ygg_send(outf, buf, bufsiz)
  IF (ret.ne.0) THEN
     PRINT *, "hello(Fortran): ERROR FILE SEND"
     CALL EXIT(-1)
  END IF
  PRINT *, "hello(Fortran): Sent to outf"

  PRINT *, "Goodbye from Fortran"
  CALL EXIT(0)
  
END PROGRAM hello
