program main
  use fygg

  character(len=32) :: arg
  integer :: msg_count, msg_size
  type(yggcomm) :: inq, outf
  logical :: ret
  integer :: i, count
  integer :: exit_code = 0
  integer :: bufsiz = 0, old_bufsiz = 0
  type(yggchar_r) :: buf

  write(*, '("Hello from Fortran pipe_dst")')

  ! Ins/outs matching with the the model yaml
  inq = ygg_input("input_pipe")
  outf = ygg_output("output_file")
  write(*, '("pipe_dst(F): Created I/O channels")')

  ! Continue receiving input from the queue
  count = 0
  do while(.true.)
     bufsiz = size(buf%x)
     old_bufsiz = bufsiz
     ret = ygg_recv_nolimit(inq, buf, bufsiz)
     if (.not.ret) then
        write(*, '("pipe_dst(F): Input channel closed")')
        exit
     end if
     if (bufsiz.gt.old_bufsiz) then
        write(*, '("pipe_dst(F): Buffer increased from ",&
             &i5.1," to ",i5.1," bytes")') old_bufsiz, bufsiz
     end if
     ret = ygg_send_nolimit(outf, buf, bufsiz)
     if (.not.ret) then
        write(*, '("pipe_dst(F): SEND ERROR ON MSG ",i5.1)') count
        exit_code = -1
        exit
     end if
     count = count + 1
  end do

  write(*, '("Goodbye from Fortran destination. Received ",&
       &i5.1," messages.")') count
  if (exit_code.lt.0) then
     stop 1
  end if

end program main
