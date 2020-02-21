function yggptr_realloc(x, array_len, precision, realloc) result(flag)
  implicit none
  type(yggptr) :: x
  integer(kind=c_size_t), pointer :: array_len
  integer(kind=c_size_t), pointer :: precision
  logical :: realloc
  integer :: flag
  character(len=500) :: log_msg
  flag = 0
  if ((x%array.and.(array_len.gt.x%len)).or. &
       ((x%type.eq."character").and.(precision.gt.x%prec))) then
     if (realloc.and.x%alloc) then
        write(log_msg, '("yggptr_realloc: begin realloc. &
             &size: ",i7,i7," precision: ",i7,i7)'), &
             x%len, array_len, x%prec, precision
        call ygglog_debug(log_msg)
        select type(item=>x%item)
        type is (integer(kind=2))
           call yggptr_realloc_integer(x, array_len)
        type is (integer(kind=4))
           call yggptr_realloc_integer(x, array_len)
        type is (integer(kind=8))
           call yggptr_realloc_integer(x, array_len)
        type is (real(kind=4))
           call yggptr_realloc_real(x, array_len)
        type is (real(kind=8))
           call yggptr_realloc_real(x, array_len)
        type is (real(kind=16))
           call yggptr_realloc_real(x, array_len)
        type is (complex(kind=4))
           call yggptr_realloc_complex(x, array_len)
        type is (complex(kind=8))
           call yggptr_realloc_complex(x, array_len)
        type is (complex(kind=16))
           call yggptr_realloc_complex(x, array_len)
        type is (logical(kind=1))
           call yggptr_realloc_logical(x, array_len)
        type is (logical(kind=2))
           call yggptr_realloc_logical(x, array_len)
        type is (logical(kind=4))
           call yggptr_realloc_logical(x, array_len)
        type is (logical(kind=8))
           call yggptr_realloc_logical(x, array_len)
        type is (yggchar_r)
           call yggptr_realloc_character(x, array_len, precision)
        type is (c_long_1d)
           call yggptr_realloc_1darray_integer(x, array_len, precision)
        type is (integer_1d)
           call yggptr_realloc_1darray_integer(x, array_len, precision)
        type is (integer2_1d)
           call yggptr_realloc_1darray_integer(x, array_len, precision)
        type is (integer4_1d)
           call yggptr_realloc_1darray_integer(x, array_len, precision)
        type is (integer8_1d)
           call yggptr_realloc_1darray_integer(x, array_len, precision)
        type is (real_1d)
           call yggptr_realloc_1darray_real(x, array_len, precision)
        type is (real4_1d)
           call yggptr_realloc_1darray_real(x, array_len, precision)
        type is (real8_1d)
           call yggptr_realloc_1darray_real(x, array_len, precision)
        type is (real16_1d)
           call yggptr_realloc_1darray_real(x, array_len, precision)
        type is (complex_1d)
           call yggptr_realloc_1darray_complex(x, array_len, precision)
        type is (complex4_1d)
           call yggptr_realloc_1darray_complex(x, array_len, precision)
        type is (complex8_1d)
           call yggptr_realloc_1darray_complex(x, array_len, precision)
        type is (complex16_1d)
           call yggptr_realloc_1darray_complex(x, array_len, precision)
        type is (logical_1d)
           call yggptr_realloc_1darray_logical(x, array_len, precision)
        type is (logical1_1d)
           call yggptr_realloc_1darray_logical(x, array_len, precision)
        type is (logical2_1d)
           call yggptr_realloc_1darray_logical(x, array_len, precision)
        type is (logical4_1d)
           call yggptr_realloc_1darray_logical(x, array_len, precision)
        type is (logical8_1d)
           call yggptr_realloc_1darray_logical(x, array_len, precision)
        type is (character_1d)
           call yggptr_realloc_1darray_character(x, array_len, precision)
        class default
           write(log_msg, '("yggptr_realloc: Unexpected type: ",A)'), x%type
           call ygglog_error(log_msg)
           stop "ERROR"
        end select
        if (array_len.gt.x%len) x%len = array_len
        if (precision.gt.x%prec) x%prec = precision
        call ygglog_debug("yggptr_realloc: done alloc")
     else
        flag = -1
        if (x%array.and.(array_len.gt.x%len)) then
           write(log_msg, '("yggptr_realloc: Destination array has ", &
                &i7," elements, but ",i7," elements are expected.")'), &
                x%len, array_len
           call ygglog_error(log_msg)
        end if
        if ((x%type.eq."character").and.(precision.gt.x%prec)) then
           write(log_msg, '("yggptr_realloc: Destination string has ", &
                &i7," elements, but ",i7," elements are expected.")'), &
                x%prec, precision
           call ygglog_error(log_msg)
        end if
        stop "ERROR"
     end if
  end if
end function yggptr_realloc

subroutine yggptr_realloc_integer(x, array_len)
  implicit none
  type(yggptr) :: x
  integer(kind=c_size_t), pointer :: array_len
  integer(kind=2), dimension(:), pointer :: xarr_integer2
  integer(kind=4), dimension(:), pointer :: xarr_integer4
  integer(kind=8), dimension(:), pointer :: xarr_integer8
  if (.not.x%array) then
     stop 'yggptr_realloc_integer: Only arrays can be reallocated.'
  end if
  select type(item=>x%item_array)
  type is (integer(kind=2))
     xarr_integer2 => item
     deallocate(xarr_integer2);
     allocate(xarr_integer2(array_len))
  type is (integer(kind=4))
     xarr_integer4 => item
     deallocate(xarr_integer4);
     allocate(xarr_integer4(array_len))
  type is (integer(kind=8))
     xarr_integer8 => item
     deallocate(xarr_integer8);
     allocate(xarr_integer8(array_len))
  class default
     stop 'yggptr_realloc_integer: Unexpected type.'
  end select
end subroutine yggptr_realloc_integer
subroutine yggptr_realloc_real(x, array_len)
  implicit none
  type(yggptr) :: x
  integer(kind=c_size_t), pointer :: array_len
  real(kind=4), dimension(:), pointer :: xarr_real4
  real(kind=8), dimension(:), pointer :: xarr_real8
  real(kind=16), dimension(:), pointer :: xarr_real16
  if (.not.x%array) then
     stop 'yggptr_realloc_real: Only arrays can be reallocated.'
  end if
  select type(item=>x%item_array)
  type is (real(kind=4))
     xarr_real4 => item
     deallocate(xarr_real4);
     allocate(xarr_real4(array_len))
  type is (real(kind=8))
     xarr_real8 => item
     deallocate(xarr_real8);
     allocate(xarr_real8(array_len))
  type is (real(kind=16))
     xarr_real16 => item
     deallocate(xarr_real16);
     allocate(xarr_real16(array_len))
  class default
     stop 'yggptr_realloc_real: Unexpected type.'
  end select
end subroutine yggptr_realloc_real
subroutine yggptr_realloc_complex(x, array_len)
  implicit none
  type(yggptr) :: x
  integer(kind=c_size_t), pointer :: array_len
  complex(kind=4), dimension(:), pointer :: xarr_complex4
  complex(kind=8), dimension(:), pointer :: xarr_complex8
  complex(kind=16), dimension(:), pointer :: xarr_complex16
  if (.not.x%array) then
     stop 'yggptr_realloc_complex: Only arrays can be reallocated.'
  end if
  select type(item=>x%item_array)
  type is (complex(kind=4))
     xarr_complex4 => item
     deallocate(xarr_complex4);
     allocate(xarr_complex4(array_len))
  type is (complex(kind=8))
     xarr_complex8 => item
     deallocate(xarr_complex8);
     allocate(xarr_complex8(array_len))
  type is (complex(kind=16))
     xarr_complex16 => item
     deallocate(xarr_complex16);
     allocate(xarr_complex16(array_len))
  class default
     stop 'yggptr_realloc_complex: Unexpected type.'
  end select
end subroutine yggptr_realloc_complex
subroutine yggptr_realloc_logical(x, array_len)
  implicit none
  type(yggptr) :: x
  integer(kind=c_size_t), pointer :: array_len
  logical(kind=1), dimension(:), pointer :: xarr_logical1
  logical(kind=2), dimension(:), pointer :: xarr_logical2
  logical(kind=4), dimension(:), pointer :: xarr_logical4
  logical(kind=8), dimension(:), pointer :: xarr_logical8
  if (.not.x%array) then
     stop 'yggptr_realloc_logical: Only arrays can be reallocated.'
  end if
  select type(item=>x%item_array)
  type is (logical(kind=1))
     xarr_logical1 => item
     deallocate(xarr_logical1);
     allocate(xarr_logical1(array_len))
  type is (logical(kind=2))
     xarr_logical2 => item
     deallocate(xarr_logical2);
     allocate(xarr_logical2(array_len))
  type is (logical(kind=4))
     xarr_logical4 => item
     deallocate(xarr_logical4);
     allocate(xarr_logical4(array_len))
  type is (logical(kind=8))
     xarr_logical8 => item
     deallocate(xarr_logical8);
     allocate(xarr_logical8(array_len))
  class default
     stop 'yggptr_realloc_logical: Unexpected type.'
  end select
end subroutine yggptr_realloc_logical
subroutine yggptr_realloc_character(x, array_len, precision)
  implicit none
  type(yggptr) :: x
  integer(kind=c_size_t), pointer :: array_len
  integer(kind=c_size_t), pointer :: precision
  type(yggchar_r), pointer :: x_character_realloc
  type(yggchar_r), dimension(:), pointer :: xarr_character_realloc
  integer(kind=8) :: i
  if (x%array) then
     select type(item=>x%item_array)
     type is (yggchar_r)
        xarr_character_realloc => item
        if (array_len.gt.x%len) then
           deallocate(xarr_character_realloc)
           allocate(xarr_character_realloc(array_len))
        end if
        if ((array_len.gt.x%len).or.(precision.gt.x%prec)) then
           do i = 1, array_len
              x_character_realloc => xarr_character_realloc(i)
              allocate(x_character_realloc%x(precision))
              nullify(x_character_realloc)
           end do
        end if
     class default
        stop 'yggptr_realloc_character (array): Unexpected type.'
     end select
  else
     select type(item=>x%item)
     type is (yggchar_r)
        x_character_realloc => item
        if (allocated(x_character_realloc%x)) deallocate(x_character_realloc%x)
        allocate(x_character_realloc%x(precision))
     class default
        stop 'yggptr_realloc_character (scalar): Unexpected type.'
     end select
  end if
end subroutine yggptr_realloc_character

subroutine yggptr_realloc_1darray_integer(x, array_len, precision)
  implicit none
  type(yggptr) :: x
  integer(kind=c_size_t), pointer :: array_len
  integer(kind=c_size_t), pointer :: precision
  type(c_long_1d), pointer :: x_c_long_1d
  type(integer_1d), pointer :: x_integer_1d
  type(integer2_1d), pointer :: x_integer2_1d
  type(integer4_1d), pointer :: x_integer4_1d
  type(integer8_1d), pointer :: x_integer8_1d
  select type(item=>x%item)
  type is (c_long_1d)
     x_c_long_1d => item
     if (allocated(x_c_long_1d%x)) deallocate(x_c_long_1d%x)
     allocate(x_c_long_1d%x(array_len))
  type is (integer_1d)
     x_integer_1d => item
     if (allocated(x_integer_1d%x)) deallocate(x_integer_1d%x)
     allocate(x_integer_1d%x(array_len))
  type is (integer2_1d)
     x_integer2_1d => item
     if (allocated(x_integer2_1d%x)) deallocate(x_integer2_1d%x)
     allocate(x_integer2_1d%x(array_len))
  type is (integer4_1d)
     x_integer4_1d => item
     if (allocated(x_integer4_1d%x)) deallocate(x_integer4_1d%x)
     allocate(x_integer4_1d%x(array_len))
  type is (integer8_1d)
     x_integer8_1d => item
     if (allocated(x_integer8_1d%x)) deallocate(x_integer8_1d%x)
     allocate(x_integer8_1d%x(array_len))
  class default
     stop 'yggptr_realloc_1darray_integer: Unexpected type.'
  end select
end subroutine yggptr_realloc_1darray_integer
subroutine yggptr_realloc_1darray_real(x, array_len, precision)
  implicit none
  type(yggptr) :: x
  integer(kind=c_size_t), pointer :: array_len
  integer(kind=c_size_t), pointer :: precision
  type(real_1d), pointer :: x_real_1d
  type(real4_1d), pointer :: x_real4_1d
  type(real8_1d), pointer :: x_real8_1d
  type(real16_1d), pointer :: x_real16_1d
  select type(item=>x%item)
  type is (real_1d)
     x_real_1d => item
     if (allocated(x_real_1d%x)) deallocate(x_real_1d%x)
     allocate(x_real_1d%x(array_len))
  type is (real4_1d)
     x_real4_1d => item
     if (allocated(x_real4_1d%x)) deallocate(x_real4_1d%x)
     allocate(x_real4_1d%x(array_len))
  type is (real8_1d)
     x_real8_1d => item
     if (allocated(x_real8_1d%x)) deallocate(x_real8_1d%x)
     allocate(x_real8_1d%x(array_len))
  type is (real16_1d)
     x_real16_1d => item
     if (allocated(x_real16_1d%x)) deallocate(x_real16_1d%x)
     allocate(x_real16_1d%x(array_len))
  class default
     stop 'yggptr_realloc_1darray_real: Unexpected type.'
  end select
end subroutine yggptr_realloc_1darray_real
subroutine yggptr_realloc_1darray_complex(x, array_len, precision)
  implicit none
  type(yggptr) :: x
  integer(kind=c_size_t), pointer :: array_len
  integer(kind=c_size_t), pointer :: precision
  type(complex_1d), pointer :: x_complex_1d
  type(complex4_1d), pointer :: x_complex4_1d
  type(complex8_1d), pointer :: x_complex8_1d
  type(complex16_1d), pointer :: x_complex16_1d
  select type(item=>x%item)
  type is (complex_1d)
     x_complex_1d => item
     if (allocated(x_complex_1d%x)) deallocate(x_complex_1d%x)
     allocate(x_complex_1d%x(array_len))
  type is (complex4_1d)
     x_complex4_1d => item
     if (allocated(x_complex4_1d%x)) deallocate(x_complex4_1d%x)
     allocate(x_complex4_1d%x(array_len))
  type is (complex8_1d)
     x_complex8_1d => item
     if (allocated(x_complex8_1d%x)) deallocate(x_complex8_1d%x)
     allocate(x_complex8_1d%x(array_len))
  type is (complex16_1d)
     x_complex16_1d => item
     if (allocated(x_complex16_1d%x)) deallocate(x_complex16_1d%x)
     allocate(x_complex16_1d%x(array_len))
  class default
     stop 'yggptr_realloc_1darray_complex: Unexpected type.'
  end select
end subroutine yggptr_realloc_1darray_complex
subroutine yggptr_realloc_1darray_logical(x, array_len, precision)
  implicit none
  type(yggptr) :: x
  integer(kind=c_size_t), pointer :: array_len
  integer(kind=c_size_t), pointer :: precision
  type(logical_1d), pointer :: x_logical_1d
  type(logical1_1d), pointer :: x_logical1_1d
  type(logical2_1d), pointer :: x_logical2_1d
  type(logical4_1d), pointer :: x_logical4_1d
  type(logical8_1d), pointer :: x_logical8_1d
  select type(item=>x%item)
  type is (logical_1d)
     x_logical_1d => item
     if (allocated(x_logical_1d%x)) deallocate(x_logical_1d%x)
     allocate(x_logical_1d%x(array_len))
  type is (logical1_1d)
     x_logical1_1d => item
     if (allocated(x_logical1_1d%x)) deallocate(x_logical1_1d%x)
     allocate(x_logical1_1d%x(array_len))
  type is (logical2_1d)
     x_logical2_1d => item
     if (allocated(x_logical2_1d%x)) deallocate(x_logical2_1d%x)
     allocate(x_logical2_1d%x(array_len))
  type is (logical4_1d)
     x_logical4_1d => item
     if (allocated(x_logical4_1d%x)) deallocate(x_logical4_1d%x)
     allocate(x_logical4_1d%x(array_len))
  type is (logical8_1d)
     x_logical8_1d => item
     if (allocated(x_logical8_1d%x)) deallocate(x_logical8_1d%x)
     allocate(x_logical8_1d%x(array_len))
  class default
     stop 'yggptr_realloc_1darray_logical: Unexpected type.'
  end select
end subroutine yggptr_realloc_1darray_logical
subroutine yggptr_realloc_1darray_character(x, array_len, precision)
  implicit none
  type(yggptr) :: x
  integer(kind=c_size_t), pointer :: array_len
  integer(kind=c_size_t), pointer :: precision
  type(yggchar_r), pointer :: x_character_realloc
  type(yggchar_r), dimension(:), pointer :: xarr_character_realloc
  type(character_1d), pointer :: x_character_1d
  integer(kind=8) :: i
  select type(item=>x%item)
  type is (character_1d)
     x_character_1d => item
     if (array_len.gt.x%len) then
        if (allocated(x_character_1d%x)) then
           deallocate(x_character_1d%x)
        end if
        allocate(x_character_1d%x(array_len))
     end if
     if ((array_len.gt.x%len).or.(precision.gt.x%prec)) then
        do i = 1, array_len
           x_character_realloc => x_character_1d%x(i)
           allocate(x_character_realloc%x(precision))
           nullify(x_character_realloc)
        end do
     end if
  class default
     stop 'yggptr_realloc_1darray_character: Unexpected type.'
  end select
end subroutine yggptr_realloc_1darray_character
