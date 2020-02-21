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


subroutine yggptr_realloc_character(x, array_len, precision)
  implicit none
  type(yggptr) :: x
  integer(kind=c_size_t), pointer :: array_len
  integer(kind=c_size_t), pointer :: precision
  type(yggchar_r), pointer :: x_character_realloc
  type(yggchar_r), dimension(:), pointer :: xarr_character_realloc
  integer(kind=8) :: i
  if (x%array) then
     stop 'yggptr_realloc_character (array): Unexpected type.'
  else
     select type(item=>x%item)
     type is (yggchar_r)
        x_character_realloc => item
        if (associated(x_character_realloc%x)) nullify(x_character_realloc%x)
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
     if (associated(x_c_long_1d%x)) nullify(x_c_long_1d%x)
  type is (integer_1d)
     x_integer_1d => item
     if (associated(x_integer_1d%x)) nullify(x_integer_1d%x)
  type is (integer2_1d)
     x_integer2_1d => item
     if (associated(x_integer2_1d%x)) nullify(x_integer2_1d%x)
  type is (integer4_1d)
     x_integer4_1d => item
     if (associated(x_integer4_1d%x)) nullify(x_integer4_1d%x)
  type is (integer8_1d)
     x_integer8_1d => item
     if (associated(x_integer8_1d%x)) nullify(x_integer8_1d%x)
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
     if (associated(x_real_1d%x)) nullify(x_real_1d%x)
  type is (real4_1d)
     x_real4_1d => item
     if (associated(x_real4_1d%x)) nullify(x_real4_1d%x)
  type is (real8_1d)
     x_real8_1d => item
     if (associated(x_real8_1d%x)) nullify(x_real8_1d%x)
  type is (real16_1d)
     x_real16_1d => item
     if (associated(x_real16_1d%x)) nullify(x_real16_1d%x)
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
     if (associated(x_complex_1d%x)) nullify(x_complex_1d%x)
  type is (complex4_1d)
     x_complex4_1d => item
     if (associated(x_complex4_1d%x)) nullify(x_complex4_1d%x)
  type is (complex8_1d)
     x_complex8_1d => item
     if (associated(x_complex8_1d%x)) nullify(x_complex8_1d%x)
  type is (complex16_1d)
     x_complex16_1d => item
     if (associated(x_complex16_1d%x)) nullify(x_complex16_1d%x)
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
     if (associated(x_logical_1d%x)) nullify(x_logical_1d%x)
  type is (logical1_1d)
     x_logical1_1d => item
     if (associated(x_logical1_1d%x)) nullify(x_logical1_1d%x)
  type is (logical2_1d)
     x_logical2_1d => item
     if (associated(x_logical2_1d%x)) nullify(x_logical2_1d%x)
  type is (logical4_1d)
     x_logical4_1d => item
     if (associated(x_logical4_1d%x)) nullify(x_logical4_1d%x)
  type is (logical8_1d)
     x_logical8_1d => item
     if (associated(x_logical8_1d%x)) nullify(x_logical8_1d%x)
  class default
     stop 'yggptr_realloc_1darray_logical: Unexpected type.'
  end select
end subroutine yggptr_realloc_1darray_logical
subroutine yggptr_realloc_1darray_character(x, array_len, precision)
  implicit none
  type(yggptr) :: x
  integer(kind=c_size_t), pointer :: array_len
  integer(kind=c_size_t), pointer :: precision
  type(character_1d), pointer :: x_character_1d
  integer(kind=8) :: i
  select type(item=>x%item)
  type is (character_1d)
     x_character_1d => item
     nullify(x%data_character_unit)
     if (array_len.gt.x%len) then
        if (associated(x_character_1d%x)) then
           deallocate(x_character_1d%x)
        end if
        allocate(x_character_1d%x(array_len))
     end if
     if ((array_len.gt.x%len).or.(precision.gt.x%prec)) then
        do i = 1, size(x_character_1d%x)
           if (associated(x_character_1d%x(i)%x)) then
              deallocate(x_character_1d%x(i)%x)
           end if
           allocate(x_character_1d%x(i)%x(precision))
        end do
     end if
  class default
     stop 'yggptr_realloc_1darray_character: Unexpected type.'
  end select
end subroutine yggptr_realloc_1darray_character
