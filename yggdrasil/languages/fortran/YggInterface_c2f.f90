function yggptr_c2f(x, realloc) result(flag)
  implicit none
  type(yggptr) :: x
  logical :: realloc
  integer(kind=c_size_t), pointer :: array_len
  integer(kind=c_size_t), pointer :: precision
  integer(kind=8) :: i, j
  integer :: flag
  character(len=500) :: log_msg
  flag = 0
  call ygglog_debug("yggptr_c2f: begin")
  allocate(array_len)
  allocate(precision)
  array_len = 1
  precision = 1
  if (x%array) then
     deallocate(array_len)
     call c_f_pointer(x%len_ptr, array_len)
     write(log_msg, '("array_len = ",i7)'), array_len
     call ygglog_debug(log_msg)
  end if
  if (x%type.eq."character") then
     deallocate(precision)
     call c_f_pointer(x%prec_ptr, precision)
     write(log_msg, '("precision = ",i7)'), precision
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
           write(log_msg, '("yggptr_c2f (realloc array transfer): Unexpected type: ",A)'), x%type
           call ygglog_error(log_msg)
           stop "ERROR"
        end select
     else
        select type(item=>x%item_array)
        type is (integer(kind=2))
           call yggptr_c2f_array_integer(x)
        type is (integer(kind=4))
           call yggptr_c2f_array_integer(x)
        type is (integer(kind=8))
           call yggptr_c2f_array_integer(x)
        type is (real(kind=4))
           call yggptr_c2f_array_real(x)
        type is (real(kind=8))
           call yggptr_c2f_array_real(x)
        type is (real(kind=16))
           call yggptr_c2f_array_real(x)
        type is (complex(kind=4))
           call yggptr_c2f_array_complex(x)
        type is (complex(kind=8))
           call yggptr_c2f_array_complex(x)
        type is (complex(kind=16))
           call yggptr_c2f_array_complex(x)
        type is (logical(kind=1))
           call yggptr_c2f_array_logical(x)
        type is (logical(kind=2))
           call yggptr_c2f_array_logical(x)
        type is (logical(kind=4))
           call yggptr_c2f_array_logical(x)
        type is (logical(kind=8))
           call yggptr_c2f_array_logical(x)
        type is (yggchar_r)
           call yggptr_c2f_array_character(x)
        type is (character(*))
           call yggptr_c2f_array_character(x)
        class default
           write(log_msg, '("yggptr_c2f (realloc transfer): Unexpected type: ",A)'), x%type
           call ygglog_error(log_msg)
           stop "ERROR"
        end select
     end if
  else
     select type(item=>x%item)
     type is (integer(kind=2))
        call yggptr_c2f_scalar_integer(x)
     type is (integer(kind=4))
        call yggptr_c2f_scalar_integer(x)
     type is (integer(kind=8))
        call yggptr_c2f_scalar_integer(x)
     type is (real(kind=4))
        call yggptr_c2f_scalar_real(x)
     type is (real(kind=8))
        call yggptr_c2f_scalar_real(x)
     type is (real(kind=16))
        call yggptr_c2f_scalar_real(x)
     type is (complex(kind=4))
        call yggptr_c2f_scalar_complex(x)
     type is (complex(kind=8))
        call yggptr_c2f_scalar_complex(x)
     type is (complex(kind=16))
        call yggptr_c2f_scalar_complex(x)
     type is (logical(kind=1))
        call yggptr_c2f_scalar_logical(x)
     type is (logical(kind=2))
        call yggptr_c2f_scalar_logical(x)
     type is (logical(kind=4))
        call yggptr_c2f_scalar_logical(x)
     type is (logical(kind=8))
        call yggptr_c2f_scalar_logical(x)
     type is (yggchar_r)
        call yggptr_c2f_scalar_character(x)
     type is (character(*))
        call yggptr_c2f_scalar_character(x)
     class default
        write(log_msg, '("yggptr_c2f (scalar transfer): Unexpected type: ",A)'), x%type
        call ygglog_error(log_msg)
        stop "ERROR"
     end select
  end if
  if (.not.x%array) then
     deallocate(array_len)
  end if
  if (.not.(x%type.eq."character")) then
     deallocate(precision)
  end if
  call ygglog_debug("yggptr_c2f: end")
end function yggptr_c2f


subroutine yggptr_c2f_scalar_integer(x)
  implicit none
  type(yggptr) :: x
  integer(kind=2), pointer :: x_integer2
  integer(kind=4), pointer :: x_integer4
  integer(kind=8), pointer :: x_integer8
  select type(item=>x%item)
  type is (integer(kind=2))
     x_integer2 => item
     call c_f_pointer(x%ptr, x_integer2, [x%len])
  type is (integer(kind=4))
     x_integer4 => item
     call c_f_pointer(x%ptr, x_integer4, [x%len])
  type is (integer(kind=8))
     x_integer8 => item
     ! call c_f_pointer(x%ptr, x_integer8, [x%len])
  class default
     call ygglog_error("yggptr_c2f_scalar_integer: Unexpected type.")
     stop "ERROR"
  end select
end subroutine yggptr_c2f_scalar_integer
subroutine yggptr_c2f_scalar_real(x)
  implicit none
  type(yggptr) :: x
  real(kind=4), pointer :: x_real4
  real(kind=8), pointer :: x_real8
  real(kind=16), pointer :: x_real16
  select type(item=>x%item)
  type is (real(kind=4))
     x_real4 => item
     call c_f_pointer(x%ptr, x_real4, [x%len])
  type is (real(kind=8))
     x_real8 => item
     call c_f_pointer(x%ptr, x_real8, [x%len])
  type is (real(kind=16))
     x_real16 => item
     call c_f_pointer(x%ptr, x_real16, [x%len])
  class default
     call ygglog_error("yggptr_c2f_scalar_real: Unexpected type.")
     stop "ERROR"
  end select
end subroutine yggptr_c2f_scalar_real
subroutine yggptr_c2f_scalar_complex(x)
  implicit none
  type(yggptr) :: x
  complex(kind=4), pointer :: x_complex4
  complex(kind=8), pointer :: x_complex8
  complex(kind=16), pointer :: x_complex16
  select type(item=>x%item)
  type is (complex(kind=4))
     x_complex4 => item
     call c_f_pointer(x%ptr, x_complex4, [x%len])
  type is (complex(kind=8))
     x_complex8 => item
     call c_f_pointer(x%ptr, x_complex8, [x%len])
  type is (complex(kind=16))
     x_complex16 => item
     call c_f_pointer(x%ptr, x_complex16, [x%len])
  class default
     call ygglog_error("yggptr_c2f_scalar_complex: Unexpected type.")
     stop "ERROR"
  end select
end subroutine yggptr_c2f_scalar_complex
subroutine yggptr_c2f_scalar_logical(x)
  implicit none
  type(yggptr) :: x
  logical(kind=1), pointer :: x_logical1
  logical(kind=2), pointer :: x_logical2
  logical(kind=4), pointer :: x_logical4
  logical(kind=8), pointer :: x_logical8
  select type(item=>x%item)
  type is (logical(kind=1))
     x_logical1 => item
     call c_f_pointer(x%ptr, x_logical1, [x%len])
  type is (logical(kind=2))
     x_logical2 => item
     call c_f_pointer(x%ptr, x_logical2, [x%len])
  type is (logical(kind=4))
     x_logical4 => item
     call c_f_pointer(x%ptr, x_logical4, [x%len])
  type is (logical(kind=8))
     x_logical8 => item
     call c_f_pointer(x%ptr, x_logical8, [x%len])
  class default
     call ygglog_error("yggptr_c2f_scalar_logical: Unexpected type.")
     stop "ERROR"
  end select
end subroutine yggptr_c2f_scalar_logical
subroutine yggptr_c2f_scalar_character(x)
  implicit none
  type(yggptr) :: x
  character(len=:), pointer :: x_character
  character, dimension(:), pointer :: xarr_character
  type(yggchar_r), pointer :: x_character_realloc
  integer(kind=8) :: i
  select type(item=>x%item)
  type is (yggchar_r)
     x_character_realloc => item
     call c_f_pointer(x%ptr, xarr_character, [x%prec])
     x_character_realloc%x = xarr_character
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


subroutine yggptr_c2f_array_integer(x)
  implicit none
  type(yggptr) :: x
  integer(kind=2), dimension(:), pointer :: xarr_integer2
  integer(kind=4), dimension(:), pointer :: xarr_integer4
  integer(kind=8), dimension(:), pointer :: xarr_integer8
  select type(item=>x%item_array)
  type is (integer(kind=2))
     xarr_integer2 => item
     call c_f_pointer(x%ptr, xarr_integer2, [x%len])
  type is (integer(kind=4))
     xarr_integer4 => item
     call c_f_pointer(x%ptr, xarr_integer4, [x%len])
  type is (integer(kind=8))
     xarr_integer8 => item
     call c_f_pointer(x%ptr, xarr_integer8, [x%len])
  class default
     call ygglog_error("yggptr_c2f_array_integer: Unexpected type.")
     stop "ERROR"
  end select
end subroutine yggptr_c2f_array_integer
subroutine yggptr_c2f_array_real(x)
  implicit none
  type(yggptr) :: x
  real(kind=4), dimension(:), pointer :: xarr_real4
  real(kind=8), dimension(:), pointer :: xarr_real8
  real(kind=16), dimension(:), pointer :: xarr_real16
  select type(item=>x%item_array)
  type is (real(kind=4))
     xarr_real4 => item
     call c_f_pointer(x%ptr, xarr_real4, [x%len])
  type is (real(kind=8))
     xarr_real8 => item
     call c_f_pointer(x%ptr, xarr_real8, [x%len])
  type is (real(kind=16))
     xarr_real16 => item
     call c_f_pointer(x%ptr, xarr_real16, [x%len])
  class default
     call ygglog_error("yggptr_c2f_array_real: Unexpected type.")
     stop "ERROR"
  end select
end subroutine yggptr_c2f_array_real
subroutine yggptr_c2f_array_complex(x)
  implicit none
  type(yggptr) :: x
  complex(kind=4), dimension(:), pointer :: xarr_complex4
  complex(kind=8), dimension(:), pointer :: xarr_complex8
  complex(kind=16), dimension(:), pointer :: xarr_complex16
  select type(item=>x%item_array)
  type is (complex(kind=4))
     xarr_complex4 => item
     call c_f_pointer(x%ptr, xarr_complex4, [x%len])
  type is (complex(kind=8))
     xarr_complex8 => item
     call c_f_pointer(x%ptr, xarr_complex8, [x%len])
  type is (complex(kind=16))
     xarr_complex16 => item
     call c_f_pointer(x%ptr, xarr_complex16, [x%len])
  class default
     call ygglog_error("yggptr_c2f_array_complex: Unexpected type.")
     stop "ERROR"
  end select
end subroutine yggptr_c2f_array_complex
subroutine yggptr_c2f_array_logical(x)
  implicit none
  type(yggptr) :: x
  logical(kind=1), dimension(:), pointer :: xarr_logical1
  logical(kind=2), dimension(:), pointer :: xarr_logical2
  logical(kind=4), dimension(:), pointer :: xarr_logical4
  logical(kind=8), dimension(:), pointer :: xarr_logical8
  select type(item=>x%item_array)
  type is (logical(kind=1))
     xarr_logical1 => item
     call c_f_pointer(x%ptr, xarr_logical1, [x%len])
  type is (logical(kind=2))
     xarr_logical2 => item
     call c_f_pointer(x%ptr, xarr_logical2, [x%len])
  type is (logical(kind=4))
     xarr_logical4 => item
     call c_f_pointer(x%ptr, xarr_logical4, [x%len])
  type is (logical(kind=8))
     xarr_logical8 => item
     call c_f_pointer(x%ptr, xarr_logical8, [x%len])
  class default
     call ygglog_error("yggptr_c2f_array_logical: Unexpected type.")
     stop "ERROR"
  end select
end subroutine yggptr_c2f_array_logical
subroutine yggptr_c2f_array_character(x)
  implicit none
  type(yggptr) :: x
  type(yggchar_r), pointer :: x_character_realloc
  type(yggchar_r), dimension(:), pointer :: xarr_character_realloc
  character, dimension(:), pointer :: xarr_character, xarr_character0
  integer(kind=8) :: i, j
  select type(item=>x%item_array)
  type is (yggchar_r)
     xarr_character_realloc => item
     x_character_realloc => xarr_character_realloc(1)
     xarr_character0 => x_character_realloc%x
     ! print *, "before pointer (mult) "
     ! call c_f_pointer(x%ptr, xarr_character0, [x%prec*x%len])
     ! print *, "after  pointer (mult) "
     ! do i = 2, x%len
     !    x_character_realloc => xarr_character_realloc(i)
     !    xarr_character => x_character_realloc%x
     !    print *, "before pointer (mult) ", i
     !    xarr_character(1:x%prec) = xarr_character0( &
     !         (1+(i-1)*x%prec):(i*x%prec))
     !    print *, "after  pointer (mult) ", i
     ! end do
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
  integer, dimension(:), pointer :: ptr_c_long
  integer, dimension(:), pointer :: ptr_integer
  integer(kind=2), dimension(:), pointer :: ptr_integer2
  integer(kind=4), dimension(:), pointer :: ptr_integer4
  integer(kind=8), dimension(:), pointer :: ptr_integer8
  select type(item=>x%item)
  type is (c_long_1d)
     x_c_long_1d => item
     call c_f_pointer(x%ptr, ptr_c_long, [x%len])
     x_c_long_1d%x = ptr_c_long
  type is (integer_1d)
     x_integer_1d => item
     call c_f_pointer(x%ptr, ptr_integer, [x%len])
     x_integer_1d%x = ptr_integer
  type is (integer2_1d)
     x_integer2_1d => item
     call c_f_pointer(x%ptr, ptr_integer2, [x%len])
     x_integer2_1d%x = ptr_integer2
  type is (integer4_1d)
     x_integer4_1d => item
     call c_f_pointer(x%ptr, ptr_integer4, [x%len])
     x_integer4_1d%x = ptr_integer4
  type is (integer8_1d)
     x_integer8_1d => item
     call c_f_pointer(x%ptr, ptr_integer8, [x%len])
     x_integer8_1d%x = ptr_integer8
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
  real, dimension(:), pointer :: ptr_real
  real(kind=4), dimension(:), pointer :: ptr_real4
  real(kind=8), dimension(:), pointer :: ptr_real8
  real(kind=16), dimension(:), pointer :: ptr_real16
  select type(item=>x%item)
  type is (real_1d)
     x_real_1d => item
     call c_f_pointer(x%ptr, ptr_real, [x%len])
     x_real_1d%x = ptr_real
  type is (real4_1d)
     x_real4_1d => item
     call c_f_pointer(x%ptr, ptr_real4, [x%len])
     x_real4_1d%x = ptr_real4
  type is (real8_1d)
     x_real8_1d => item
     call c_f_pointer(x%ptr, ptr_real8, [x%len])
     x_real8_1d%x = ptr_real8
  type is (real16_1d)
     x_real16_1d => item
     call c_f_pointer(x%ptr, ptr_real16, [x%len])
     x_real16_1d%x = ptr_real16
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
  complex, dimension(:), pointer :: ptr_complex
  complex(kind=4), dimension(:), pointer :: ptr_complex4
  complex(kind=8), dimension(:), pointer :: ptr_complex8
  complex(kind=16), dimension(:), pointer :: ptr_complex16
  select type(item=>x%item)
  type is (complex_1d)
     x_complex_1d => item
     call c_f_pointer(x%ptr, ptr_complex, [x%len])
     x_complex_1d%x = ptr_complex
  type is (complex4_1d)
     x_complex4_1d => item
     call c_f_pointer(x%ptr, ptr_complex4, [x%len])
     x_complex4_1d%x = ptr_complex4
  type is (complex8_1d)
     x_complex8_1d => item
     call c_f_pointer(x%ptr, ptr_complex8, [x%len])
     x_complex8_1d%x = ptr_complex8
  type is (complex16_1d)
     x_complex16_1d => item
     call c_f_pointer(x%ptr, ptr_complex16, [x%len])
     x_complex16_1d%x = ptr_complex16
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
  logical, dimension(:), pointer :: ptr_logical
  logical(kind=1), dimension(:), pointer :: ptr_logical1
  logical(kind=2), dimension(:), pointer :: ptr_logical2
  logical(kind=4), dimension(:), pointer :: ptr_logical4
  logical(kind=8), dimension(:), pointer :: ptr_logical8
  select type(item=>x%item)
  type is (logical_1d)
     x_logical_1d => item
     call c_f_pointer(x%ptr, ptr_logical, [x%len])
     x_logical_1d%x = ptr_logical
  type is (logical1_1d)
     x_logical1_1d => item
     call c_f_pointer(x%ptr, ptr_logical1, [x%len])
     x_logical1_1d%x = ptr_logical1
  type is (logical2_1d)
     x_logical2_1d => item
     call c_f_pointer(x%ptr, ptr_logical2, [x%len])
     x_logical2_1d%x = ptr_logical2
  type is (logical4_1d)
     x_logical4_1d => item
     call c_f_pointer(x%ptr, ptr_logical4, [x%len])
     x_logical4_1d%x = ptr_logical4
  type is (logical8_1d)
     x_logical8_1d => item
     call c_f_pointer(x%ptr, ptr_logical8, [x%len])
     x_logical8_1d%x = ptr_logical8
  class default
     call ygglog_error("yggptr_c2f_1darray_logical: Unexpected type.")
     stop "ERROR"
  end select
end subroutine yggptr_c2f_1darray_logical
subroutine yggptr_c2f_1darray_character(x)
  implicit none
  type(yggptr) :: x
  integer(kind=c_size_t), pointer :: array_len
  integer(kind=c_size_t), pointer :: precision
  type(yggchar_r), pointer :: x_character_realloc
  type(yggchar_r), dimension(:), pointer :: xarr_character_realloc
  character, dimension(:), pointer :: xarr_character, xarr_character0
  integer(kind=8) :: i, j
  type(character_1d), pointer :: x_character_1d
  select type(item=>x%item)
  type is (character_1d)
     x_character_1d => item
     x_character_realloc => x_character_1d%x(1)
     xarr_character0 => x_character_realloc%x
     ! allocate(x%data_character_unit(x%prec*x%len))
     call c_f_pointer(x%ptr, x%data_character_unit, [x%prec*x%len])
     do i = 1, x%len
        ! x_character_realloc => x_character_1d%x(i)
        ! xarr_character => x_character_realloc%x
        ! xarr_character(1:x%prec) = x%data_character_unit( &
        !      (1+(i-1)*x%prec):(i*x%prec))
        x_character_1d%x(i)%x = x%data_character_unit( &
             (1+(i-1)*x%prec):(i*x%prec))
     end do
     deallocate(x%data_character_unit)
  class default
     call ygglog_error("yggptr_c2f_1darray_character: Unexpected type.")
     stop "ERROR"
  end select
end subroutine yggptr_c2f_1darray_character
