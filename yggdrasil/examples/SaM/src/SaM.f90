PROGRAM SaM
  USE fygg

  integer :: ret, BSIZE = 1000, a, b, sum
  character(len = 1000) :: adata, bdata, outbuf
  TYPE(yggcomm) :: in1, in2, out1

  ! Get input and output channels matching yaml
  in1 = ygg_input("input1_fortran")
  in2 = ygg_input("static_fortran")
  out1 = ygg_output("output_fortran")

  ! Get input from input1 channel
  ret = ygg_recv(in1, adata, BSIZE)
  IF (ret.lt.0) THEN
     PRINT *, "SaM(Fortran): ERROR RECV from input1"
     CALL EXIT(-1)
  END IF
  READ(adata, '(I4)') a
  PRINT *, "SaM(Fortran): Received ", a, " from input1"

  ! Get input from static channel
  ret = ygg_recv(in2, bdata, BSIZE)
  IF (ret.lt.0) THEN
     PRINT *, "SaM(Fortran): ERROR RECV from static"
     CALL EXIT(-1)
  END IF
  READ(bdata, '(I4)') b
  PRINT *, "SaM(Fortran): Received ", b, " from static"

  ! Compute sum and send message to output channel
  sum = a + b
  WRITE(outbuf, '(I4)') sum
  outbuf = ADJUSTL(outbuf)
  ret = ygg_send(out1, outbuf, LEN_TRIM(outbuf))
  IF (ret.ne.0) THEN
     PRINT *, "SaM(Fortran): ERROR SEND to output"
     CALL EXIT(-1)
  END IF
  PRINT *, "SaM(Fortran): Sent to output"
  
  CALL EXIT(0)

END PROGRAM SaM
