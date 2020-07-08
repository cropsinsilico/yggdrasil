program main
  ! Include interface methods
  use fygg

  integer, parameter :: BSIZE = 8192
  logical :: ret
  integer :: error_code = 0
  type(yggcomm) :: file_input, file_output, &
       table_input, table_output, array_input, array_output
  integer(kind=c_size_t), target :: line_size = LINE_SIZE_MAX
  type(yggchar_r) :: line  ! Wrapped to be reallocatable
  character(len=BSIZE), target :: name
  integer(kind=c_size_t), target :: name_siz = BSIZE
  integer(kind=8) :: number
  real(kind=8) :: value
  complex(kind=8) :: comp
  integer(kind=c_size_t), target :: nrows
  type(character_1d), target :: name_arr
  type(integer8_1d), target :: number_arr
  type(real8_1d), target :: value_arr
  type(complex8_1d), target :: comp_arr
  integer(kind=c_size_t) :: i

  ! Input & output to an ASCII file line by line
  file_input = ygg_ascii_file_input("inputF_file")
  file_output = ygg_ascii_file_output("outputF_file")
  ! Input & output from a table row by row
  table_input = ygg_ascii_table_input("inputF_table")
  table_output = ygg_ascii_table_output("outputF_table", &
       "%5s\t%ld\t%3.1f\t%3.1lf%+3.1lfj\n")
  ! Input & output from a table as an array
  array_input = ygg_ascii_array_input("inputF_array")
  array_output = ygg_ascii_array_output("outputF_array", &
       "%5s\t%ld\t%3.1f\t%3.1lf%+3.1lfj\n")

  ! Read lines from ASCII text file until end of file is reached.
  ! As each line is received, it is then sent to the output ASCII file.
  write(*, '("ascii_io(F): Receiving/sending ASCII file.")')
  ret = .true.
  do while (ret)
     line_size = size(line%x)  ! Reset to size of buffer

     ! Receive a single line
     ret = ygg_recv_var_realloc(file_input, &
          [yggarg(line), yggarg(line_size)])
     if (ret) then
        ! If the receive was succesful, send the line to output
        write(*, '("File: ",80A)', advance="no") line%x
        ret = ygg_send_var(file_output, &
             [yggarg(line), yggarg(line_size)])
        if (.not.ret) then
           write(*, '("ascii_io(F): ERROR SENDING LINE")')
           error_code = -1
           exit
        end if
     else
        ! If the receive was not succesful, send the end-of-file message to
        ! close the output file.
        write(*, '("End of file input (F)")')
     end if
  end do

  ! Read rows from ASCII table until end of file is reached.
  ! As each row is received, it is then sent to the output ASCII table
  write(*, '("ascii_io(F): Receiving/sending ASCII table.")')
  ret = .true.
  do while (ret)
     name_siz = BSIZE  ! Reset to size of the buffer

     ! Receive a single row with values stored in scalars declared locally
     ret = ygg_recv_var(table_input, &
          [yggarg(name), yggarg(name_siz), yggarg(number), &
          yggarg(value), yggarg(comp)])

     if (ret) then
        ! If the receive was succesful, send the values to output. Formatting
        ! is taken care of on the output driver side.
        write (*, '("Table: ",A,", ",I7,", ",F10.5,", ",2F10.5)') &
             trim(name), number, value, comp
        ret = ygg_send_var(table_output, &
             [yggarg(name), yggarg(name_siz), yggarg(number), &
             yggarg(value), yggarg(comp)])
        if (.not.ret) then
           write(*, '("ascii_io(F): ERROR SENDING ROW")')
           error_code = -1
           exit
        end if
     else
        ! If the receive was not succesful, send the end-of-file message to
        ! close the output file.
        write(*, '("End of table input (F)")')
     end if
  end do

  ! Read entire array from ASCII table into columns that are dynamically
  ! allocated. The returned values tells us the number of elements in the
  ! columns.
  write(*, '("Receiving/sending ASCII table as array.")')
  ret = .true.
  do while (ret)
     ret = ygg_recv_var_realloc(array_input, [yggarg(nrows), &
          yggarg(name_arr), yggarg(number_arr), &
          yggarg(value_arr), yggarg(comp_arr)])
     if (ret) then
        write(*, '("Array: (",I7," rows)")') nrows
        ! Print each line in the array
        do i = 1, nrows
           write(*, '(5A)', advance="no") name_arr%x(i)%x
           write(*, '(", ",I7,", ",F10.5,", ",2F10.5)') &
                number_arr%x(i), value_arr%x(i), comp_arr%x(i)
        end do
        ! Send the columns in the array to output. Formatting is handled on the
        ! output driver side.
        ret = ygg_send_var(array_output, [yggarg(nrows), &
             yggarg(name_arr), yggarg(number_arr), &
             yggarg(value_arr), yggarg(comp_arr)])
        if (.not.ret) then
           write(*, '("ascii_io(F): ERROR SENDING ARRAY")')
           error_code = -1
           exit
        end if
     else
        write(*, '("End of array input (F)")')
     end if
  end do

  if (error_code.lt.0) then
     stop 1
  end if

end program main
