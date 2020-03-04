function yggptr_c2f(x, realloc) result(flag)
  implicit none
  type(yggptr) :: x
  logical :: realloc
  integer(kind=c_size_t), pointer :: array_len
  integer(kind=c_size_t), pointer :: precision
  integer(kind=8) :: i, j
  logical :: flag
  character(len=500) :: log_msg
  flag = .true.
  call ygglog_debug("yggptr_c2f: begin")
  allocate(array_len)
  allocate(precision)
  array_len = 1
  precision = 1
  if (x%array) then
     deallocate(array_len)
     call c_f_pointer(x%len_ptr, array_len)
     write(log_msg, '("array_len = ",i7)') array_len
     call ygglog_debug(log_msg)
  end if
  if (x%type.eq."character") then
     deallocate(precision)
     call c_f_pointer(x%prec_ptr, precision)
     write(log_msg, '("precision = ",i7)') precision
     call ygglog_debug(log_msg)
  end if
  flag = yggptr_realloc(x, array_len, precision, realloc)
  if (x%array) then
     if (x%alloc) then
        select type(item=>x%item)
        type is (c_long_1d)
           call yggptr_c2f_1darray_integer(x)
        type is (integer_1d)
           call yggptr_c2f_1darray_integer(x)
        type is (integer2_1d)
           call yggptr_c2f_1darray_integer(x)
        type is (integer4_1d)
           call yggptr_c2f_1darray_integer(x)
        type is (integer8_1d)
           call yggptr_c2f_1darray_integer(x)
        type is (real_1d)
           call yggptr_c2f_1darray_real(x)
        type is (real4_1d)
           call yggptr_c2f_1darray_real(x)
        type is (real8_1d)
           call yggptr_c2f_1darray_real(x)
        type is (real16_1d)
           call yggptr_c2f_1darray_real(x)
        type is (complex_1d)
           call yggptr_c2f_1darray_complex(x)
        type is (complex4_1d)
           call yggptr_c2f_1darray_complex(x)
        type is (complex8_1d)
           call yggptr_c2f_1darray_complex(x)
        type is (complex16_1d)
           call yggptr_c2f_1darray_complex(x)
        type is (logical_1d)
           call yggptr_c2f_1darray_logical(x)
        type is (logical1_1d)
           call yggptr_c2f_1darray_logical(x)
        type is (logical2_1d)
           call yggptr_c2f_1darray_logical(x)
        type is (logical4_1d)
           call yggptr_c2f_1darray_logical(x)
        type is (logical8_1d)
           call yggptr_c2f_1darray_logical(x)
        type is (character_1d)
           call yggptr_c2f_1darray_character(x)
        class default
           write(log_msg, '("yggptr_c2f (realloc array transfer): Unexpected type: ",A)') x%type
           call ygglog_error(log_msg)
           stop "ERROR"
        end select
     else
        select type(item=>x%item_array)
        type is (integer(kind=2))
        type is (integer(kind=4))
        type is (integer(kind=8))
        type is (real(kind=4))
        type is (real(kind=8))
        type is (real(kind=16))
        type is (complex(kind=4))
        type is (complex(kind=8))
        type is (complex(kind=16))
        type is (logical(kind=1))
        type is (logical(kind=2))
        type is (logical(kind=4))
        type is (logical(kind=8))
        type is (yggchar_r)
           call yggptr_c2f_array_character(x)
        type is (character(*))
           call yggptr_c2f_array_character(x)
        class default
           write(log_msg, '("yggptr_c2f (realloc transfer): Unexpected type: ",A)') x%type
           call ygglog_error(log_msg)
           stop "ERROR"
        end select
     end if
  else
     select type(item=>x%item)
     type is (integer(kind=2))
     type is (integer(kind=4))
     type is (integer(kind=8))
     type is (real(kind=4))
     type is (real(kind=8))
     type is (real(kind=16))
     type is (complex(kind=4))
     type is (complex(kind=8))
     type is (complex(kind=16))
     type is (logical(kind=1))
     type is (logical(kind=2))
     type is (logical(kind=4))
     type is (logical(kind=8))
     type is (yggchar_r)
        call yggptr_c2f_scalar_character(x)
     type is (character(*))
        call yggptr_c2f_scalar_character(x)
     class default
        if ((x%type.eq."ply").or.(x%type.eq."obj").or. &
             (x%type.eq."generic")) then
           ! Use pointer
        else
           write(log_msg, '("yggptr_c2f (scalar transfer): Unexpected type: ",A)') x%type
           call ygglog_error(log_msg)
           stop "ERROR"
        end if
     end select
  end if
  if (.not.x%array) then
     deallocate(array_len)
  else
     nullify(array_len)
  end if
  if (.not.(x%type.eq."character")) then
     deallocate(precision)
  else
     nullify(precision)
  end if
  call ygglog_debug("yggptr_c2f: end")
end function yggptr_c2f


subroutine yggptr_c2f_scalar_character(x)
  implicit none
  type(yggptr) :: x
  character(len=:), pointer :: x_character
  type(yggchar_r), pointer :: x_character_realloc
  integer(kind=8) :: i
  select type(item=>x%item)
  type is (yggchar_r)
     x_character_realloc => item
     if (.not.associated(x_character_realloc%x)) then
        call c_f_pointer(x%ptr, x_character_realloc%x, [x%prec])
     end if
     do i = (x%prec + 1), size(x_character_realloc%x)
        x_character_realloc%x(i) = ' '
     end do
  type is (character(*))
     x_character => item
     do i = 1, x%prec
        x_character(i:i) = x%data_character_unit(i)
     end do
     do i = (x%prec + 1), len(x_character)
        x_character(i:i) = ' '
     end do
     deallocate(x%data_character_unit)
  class default
     call ygglog_error("yggptr_c2f_scalar_character: Unexpected type.")
     stop "ERROR"
  end select
end subroutine yggptr_c2f_scalar_character


subroutine yggptr_c2f_array_character(x)
  implicit none
  type(yggptr) :: x
  type(yggchar_r), pointer :: x_character_realloc
  type(yggchar_r), dimension(:), pointer :: xarr_character_realloc
  character, dimension(:), pointer :: xarr_character, xarr_character0
  integer(kind=8) :: i, j
  select type(item=>x%item_array)
  type is (character(*))
     xarr_character => item
     do i = 1, x%len
        do j = 1, x%prec
           xarr_character(i)(j:j) = x%data_character_unit(i)
        end do
        do j = (x%prec + 1), len(xarr_character(i))
           xarr_character(i)(j:j) = ' '
        end do
     end do
     deallocate(x%data_character_unit)
  class default
     call ygglog_error("yggptr_c2f_array_character: Unexpected type.")
     stop "ERROR"
  end select
end subroutine yggptr_c2f_array_character


subroutine yggptr_c2f_1darray_integer(x)
  implicit none
  type(yggptr) :: x
  type(c_long_1d), pointer :: x_c_long_1d
  type(integer_1d), pointer :: x_integer_1d
  type(integer2_1d), pointer :: x_integer2_1d
  type(integer4_1d), pointer :: x_integer4_1d
  type(integer8_1d), pointer :: x_integer8_1d
  select type(item=>x%item)
  type is (c_long_1d)
     x_c_long_1d => item
     if (.not.associated(x_c_long_1d%x)) then
        call c_f_pointer(x%ptr, x_c_long_1d%x, [x%len])
     end if
  type is (integer_1d)
     x_integer_1d => item
     if (.not.associated(x_integer_1d%x)) then
        call c_f_pointer(x%ptr, x_integer_1d%x, [x%len])
     end if
  type is (integer2_1d)
     x_integer2_1d => item
     if (.not.associated(x_integer2_1d%x)) then
        call c_f_pointer(x%ptr, x_integer2_1d%x, [x%len])
     end if
  type is (integer4_1d)
     x_integer4_1d => item
     if (.not.associated(x_integer4_1d%x)) then
        call c_f_pointer(x%ptr, x_integer4_1d%x, [x%len])
     end if
  type is (integer8_1d)
     x_integer8_1d => item
     if (.not.associated(x_integer8_1d%x)) then
        call c_f_pointer(x%ptr, x_integer8_1d%x, [x%len])
     end if
  class default
     call ygglog_error("yggptr_c2f_1darray_integer: Unexpected type.")
     stop "ERROR"
  end select
end subroutine yggptr_c2f_1darray_integer
subroutine yggptr_c2f_1darray_real(x)
  implicit none
  type(yggptr) :: x
  type(real_1d), pointer :: x_real_1d
  type(real4_1d), pointer :: x_real4_1d
  type(real8_1d), pointer :: x_real8_1d
  type(real16_1d), pointer :: x_real16_1d
  select type(item=>x%item)
  type is (real_1d)
     x_real_1d => item
     if (.not.associated(x_real_1d%x)) then
        call c_f_pointer(x%ptr, x_real_1d%x, [x%len])
     end if
  type is (real4_1d)
     x_real4_1d => item
     if (.not.associated(x_real4_1d%x)) then
        call c_f_pointer(x%ptr, x_real4_1d%x, [x%len])
     end if
  type is (real8_1d)
     x_real8_1d => item
     if (.not.associated(x_real8_1d%x)) then
        call c_f_pointer(x%ptr, x_real8_1d%x, [x%len])
     end if
  type is (real16_1d)
     x_real16_1d => item
     if (.not.associated(x_real16_1d%x)) then
        call c_f_pointer(x%ptr, x_real16_1d%x, [x%len])
     end if
  class default
     call ygglog_error("yggptr_c2f_1darray_real: Unexpected type.")
     stop "ERROR"
  end select
end subroutine yggptr_c2f_1darray_real
subroutine yggptr_c2f_1darray_complex(x)
  implicit none
  type(yggptr) :: x
  type(complex_1d), pointer :: x_complex_1d
  type(complex4_1d), pointer :: x_complex4_1d
  type(complex8_1d), pointer :: x_complex8_1d
  type(complex16_1d), pointer :: x_complex16_1d
  select type(item=>x%item)
  type is (complex_1d)
     x_complex_1d => item
     if (.not.associated(x_complex_1d%x)) then
        call c_f_pointer(x%ptr, x_complex_1d%x, [x%len])
     end if
  type is (complex4_1d)
     x_complex4_1d => item
     if (.not.associated(x_complex4_1d%x)) then
        call c_f_pointer(x%ptr, x_complex4_1d%x, [x%len])
     end if
  type is (complex8_1d)
     x_complex8_1d => item
     if (.not.associated(x_complex8_1d%x)) then
        call c_f_pointer(x%ptr, x_complex8_1d%x, [x%len])
     end if
  type is (complex16_1d)
     x_complex16_1d => item
     if (.not.associated(x_complex16_1d%x)) then
        call c_f_pointer(x%ptr, x_complex16_1d%x, [x%len])
     end if
  class default
     call ygglog_error("yggptr_c2f_1darray_complex: Unexpected type.")
     stop "ERROR"
  end select
end subroutine yggptr_c2f_1darray_complex
subroutine yggptr_c2f_1darray_logical(x)
  implicit none
  type(yggptr) :: x
  type(logical_1d), pointer :: x_logical_1d
  type(logical1_1d), pointer :: x_logical1_1d
  type(logical2_1d), pointer :: x_logical2_1d
  type(logical4_1d), pointer :: x_logical4_1d
  type(logical8_1d), pointer :: x_logical8_1d
  select type(item=>x%item)
  type is (logical_1d)
     x_logical_1d => item
     if (.not.associated(x_logical_1d%x)) then
        call c_f_pointer(x%ptr, x_logical_1d%x, [x%len])
     end if
  type is (logical1_1d)
     x_logical1_1d => item
     if (.not.associated(x_logical1_1d%x)) then
        call c_f_pointer(x%ptr, x_logical1_1d%x, [x%len])
     end if
  type is (logical2_1d)
     x_logical2_1d => item
     if (.not.associated(x_logical2_1d%x)) then
        call c_f_pointer(x%ptr, x_logical2_1d%x, [x%len])
     end if
  type is (logical4_1d)
     x_logical4_1d => item
     if (.not.associated(x_logical4_1d%x)) then
        call c_f_pointer(x%ptr, x_logical4_1d%x, [x%len])
     end if
  type is (logical8_1d)
     x_logical8_1d => item
     if (.not.associated(x_logical8_1d%x)) then
        call c_f_pointer(x%ptr, x_logical8_1d%x, [x%len])
     end if
  class default
     call ygglog_error("yggptr_c2f_1darray_logical: Unexpected type.")
     stop "ERROR"
  end select
end subroutine yggptr_c2f_1darray_logical
subroutine yggptr_c2f_1darray_character(x)
  implicit none
  type(yggptr) :: x
  integer(kind=8) :: i, j
  type(character_1d), pointer :: x_character_1d
  select type(item=>x%item)
  type is (character_1d)
     x_character_1d => item
     if (.not.associated(x%data_character_unit)) then
        call c_f_pointer(x%ptr, x%data_character_unit, [x%prec*x%len])
     end if
     do i = 1, x%len
        x_character_1d%x(i)%x = x%data_character_unit( &
             (1+(i-1)*x%prec):(i*x%prec))
     end do
     deallocate(x%data_character_unit)
  class default
     call ygglog_error("yggptr_c2f_1darray_character: Unexpected type.")
     stop "ERROR"
  end select
end subroutine yggptr_c2f_1darray_character
