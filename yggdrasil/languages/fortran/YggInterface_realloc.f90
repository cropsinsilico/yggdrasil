  ! BEGIN DOXYGEN_SHOULD_SKIP_THIS
function yggptr_realloc(x, array_shape, precision, realloc) result(flag)
  implicit none
  type(yggptr) :: x
  integer(kind=c_size_t), dimension(:), pointer :: array_shape
  integer(kind=c_size_t), pointer :: precision
  logical :: realloc, flag
  character(len=500) :: log_msg
  integer(kind=c_size_t), pointer :: array_len
  integer(kind=c_size_t) :: old_len = 1
  integer(kind=c_size_t) :: i
  call ygglog_debug("yggptr_realloc: begin")
  allocate(array_len)
  array_len = 1
  if (x%array) then
     if ((x%ndim.gt.1).or.x%ndarray) then
        if (associated(x%shape)) then
           do i = 1, x%ndim
              old_len = old_len * x%shape(i)
           end do
        end if
        do i = 1, size(array_shape)
           array_len = array_len * array_shape(i)
        end do
     else
        old_len = x%len
        array_len = array_shape(1)
     end if
  end if
  call ygglog_debug("yggptr_realloc: set length")
  flag = .true.
  if ((x%array.and.(array_len.gt.old_len)).or. &
       ((x%type.eq."character").and.(precision.gt.x%prec))) then
     if (realloc.and.x%alloc) then
        write(log_msg, '("yggptr_realloc: begin realloc. &
             &size: ",i7,i7," precision: ",i7,i7)') &
             old_len, array_len, x%prec, precision
        call ygglog_debug(log_msg)
        select type(item=>x%item)
        type is (yggchar_r)
           call yggptr_realloc_character(x)
        type is (c_long_1d)
           call yggptr_realloc_1darray_integer(x)
        type is (integer_1d)
           call yggptr_realloc_1darray_integer(x)
        type is (integer2_1d)
           call yggptr_realloc_1darray_integer(x)
        type is (integer4_1d)
           call yggptr_realloc_1darray_integer(x)
        type is (integer8_1d)
           call yggptr_realloc_1darray_integer(x)
        type is (real_1d)
           call yggptr_realloc_1darray_real(x)
        type is (real4_1d)
           call yggptr_realloc_1darray_real(x)
        type is (real8_1d)
           call yggptr_realloc_1darray_real(x)
        type is (real16_1d)
           call yggptr_realloc_1darray_real(x)
        type is (complex_1d)
           call yggptr_realloc_1darray_complex(x)
        type is (complex4_1d)
           call yggptr_realloc_1darray_complex(x)
        type is (complex8_1d)
           call yggptr_realloc_1darray_complex(x)
        type is (complex16_1d)
           call yggptr_realloc_1darray_complex(x)
        type is (logical_1d)
           call yggptr_realloc_1darray_logical(x)
        type is (logical1_1d)
           call yggptr_realloc_1darray_logical(x)
        type is (logical2_1d)
           call yggptr_realloc_1darray_logical(x)
        type is (logical4_1d)
           call yggptr_realloc_1darray_logical(x)
        type is (logical8_1d)
           call yggptr_realloc_1darray_logical(x)
        type is (character_1d)
           call yggptr_realloc_1darray_character(x, array_len, precision)
        type is (c_long_nd)
           call yggptr_realloc_ndarray_integer(x)
        type is (integer_nd)
           call yggptr_realloc_ndarray_integer(x)
        type is (integer2_nd)
           call yggptr_realloc_ndarray_integer(x)
        type is (integer4_nd)
           call yggptr_realloc_ndarray_integer(x)
        type is (integer8_nd)
           call yggptr_realloc_ndarray_integer(x)
        type is (real_nd)
           call yggptr_realloc_ndarray_real(x)
        type is (real4_nd)
           call yggptr_realloc_ndarray_real(x)
        type is (real8_nd)
           call yggptr_realloc_ndarray_real(x)
        type is (real16_nd)
           call yggptr_realloc_ndarray_real(x)
        type is (complex_nd)
           call yggptr_realloc_ndarray_complex(x)
        type is (complex4_nd)
           call yggptr_realloc_ndarray_complex(x)
        type is (complex8_nd)
           call yggptr_realloc_ndarray_complex(x)
        type is (complex16_nd)
           call yggptr_realloc_ndarray_complex(x)
        type is (logical_nd)
           call yggptr_realloc_ndarray_logical(x)
        type is (logical1_nd)
           call yggptr_realloc_ndarray_logical(x)
        type is (logical2_nd)
           call yggptr_realloc_ndarray_logical(x)
        type is (logical4_nd)
           call yggptr_realloc_ndarray_logical(x)
        type is (logical8_nd)
           call yggptr_realloc_ndarray_logical(x)
        type is (character_nd)
           call yggptr_realloc_ndarray_character(x, array_len, precision)
        class default
           write(log_msg, '("yggptr_realloc: Unexpected type: ",A)') x%type
           call ygglog_error(log_msg)
           stop "ERROR"
        end select
        if (.not.associated(x%shape)) then
           allocate(x%shape(size(array_shape)))
           do i = 1, size(array_shape)
              x%shape(i) = array_shape(i)
           end do
           x%ndim = size(array_shape)
        else if (any(array_shape.gt.x%shape)) then
           x%shape = array_shape
           x%ndim = size(array_shape)
        end if
        if (array_len.gt.x%len) x%len = array_len
        if (precision.gt.x%prec) x%prec = precision
        call ygglog_debug("yggptr_realloc: done alloc")
     else
        flag = .false.
        if (.not.associated(x%shape)) then
           stop "Shape not associated"
        end if
        if (x%array.and.any(array_shape.gt.x%shape)) then
           write(log_msg, '("yggptr_realloc: Destination array has ", &
                &i7," elements, but ",i7," elements are expected.")') &
                old_len, array_len
           call ygglog_error(log_msg)
        end if
        if ((x%type.eq."character").and.(precision.gt.x%prec)) then
           write(log_msg, '("yggptr_realloc: Destination string has ", &
                &i7," elements, but ",i7," elements are expected.")') &
                x%prec, precision
           call ygglog_error(log_msg)
        end if
        stop "ERROR"
     end if
  end if
  deallocate(array_len)
  call ygglog_debug("yggptr_realloc: end")
end function yggptr_realloc


subroutine yggptr_realloc_character(x)
  implicit none
  type(yggptr) :: x
  type(yggchar_r), pointer :: x_character_realloc
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


! 1d arrays
subroutine yggptr_realloc_1darray_integer(x)
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
subroutine yggptr_realloc_1darray_real(x)
  implicit none
  type(yggptr) :: x
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
subroutine yggptr_realloc_1darray_complex(x)
  implicit none
  type(yggptr) :: x
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
subroutine yggptr_realloc_1darray_logical(x)
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

! nd arrays
subroutine yggptr_realloc_ndarray_integer(x)
  implicit none
  type(yggptr) :: x
  type(c_long_nd), pointer :: x_c_long_nd
  type(integer_nd), pointer :: x_integer_nd
  type(integer2_nd), pointer :: x_integer2_nd
  type(integer4_nd), pointer :: x_integer4_nd
  type(integer8_nd), pointer :: x_integer8_nd
  select type(item=>x%item)
  type is (c_long_nd)
     x_c_long_nd => item
     if (associated(x_c_long_nd%x)) nullify(x_c_long_nd%x)
     if (associated(x_c_long_nd%shape)) nullify(x_c_long_nd%shape)
  type is (integer_nd)
     x_integer_nd => item
     if (associated(x_integer_nd%x)) nullify(x_integer_nd%x)
     if (associated(x_integer_nd%shape)) nullify(x_integer_nd%shape)
  type is (integer2_nd)
     x_integer2_nd => item
     if (associated(x_integer2_nd%x)) nullify(x_integer2_nd%x)
     if (associated(x_integer2_nd%shape)) nullify(x_integer2_nd%shape)
  type is (integer4_nd)
     x_integer4_nd => item
     if (associated(x_integer4_nd%x)) nullify(x_integer4_nd%x)
     if (associated(x_integer4_nd%shape)) nullify(x_integer4_nd%shape)
  type is (integer8_nd)
     x_integer8_nd => item
     if (associated(x_integer8_nd%x)) nullify(x_integer8_nd%x)
     if (associated(x_integer8_nd%shape)) nullify(x_integer8_nd%shape)
  class default
     stop 'yggptr_realloc_ndarray_integer: Unexpected type.'
  end select
end subroutine yggptr_realloc_ndarray_integer
subroutine yggptr_realloc_ndarray_real(x)
  implicit none
  type(yggptr) :: x
  type(real_nd), pointer :: x_real_nd
  type(real4_nd), pointer :: x_real4_nd
  type(real8_nd), pointer :: x_real8_nd
  type(real16_nd), pointer :: x_real16_nd
  select type(item=>x%item)
  type is (real_nd)
     x_real_nd => item
     if (associated(x_real_nd%x)) nullify(x_real_nd%x)
     if (associated(x_real_nd%shape)) nullify(x_real_nd%shape)
  type is (real4_nd)
     x_real4_nd => item
     if (associated(x_real4_nd%x)) nullify(x_real4_nd%x)
     if (associated(x_real4_nd%shape)) nullify(x_real4_nd%shape)
  type is (real8_nd)
     x_real8_nd => item
     if (associated(x_real8_nd%x)) nullify(x_real8_nd%x)
     if (associated(x_real8_nd%shape)) nullify(x_real8_nd%shape)
  type is (real16_nd)
     x_real16_nd => item
     if (associated(x_real16_nd%x)) nullify(x_real16_nd%x)
     if (associated(x_real16_nd%shape)) nullify(x_real16_nd%shape)
  class default
     stop 'yggptr_realloc_ndarray_real: Unexpected type.'
  end select
end subroutine yggptr_realloc_ndarray_real
subroutine yggptr_realloc_ndarray_complex(x)
  implicit none
  type(yggptr) :: x
  type(complex_nd), pointer :: x_complex_nd
  type(complex4_nd), pointer :: x_complex4_nd
  type(complex8_nd), pointer :: x_complex8_nd
  type(complex16_nd), pointer :: x_complex16_nd
  select type(item=>x%item)
  type is (complex_nd)
     x_complex_nd => item
     if (associated(x_complex_nd%x)) nullify(x_complex_nd%x)
     if (associated(x_complex_nd%shape)) nullify(x_complex_nd%shape)
  type is (complex4_nd)
     x_complex4_nd => item
     if (associated(x_complex4_nd%x)) nullify(x_complex4_nd%x)
     if (associated(x_complex4_nd%shape)) nullify(x_complex4_nd%shape)
  type is (complex8_nd)
     x_complex8_nd => item
     if (associated(x_complex8_nd%x)) nullify(x_complex8_nd%x)
     if (associated(x_complex8_nd%shape)) nullify(x_complex8_nd%shape)
  type is (complex16_nd)
     x_complex16_nd => item
     if (associated(x_complex16_nd%x)) nullify(x_complex16_nd%x)
     if (associated(x_complex16_nd%shape)) nullify(x_complex16_nd%shape)
  class default
     stop 'yggptr_realloc_ndarray_complex: Unexpected type.'
  end select
end subroutine yggptr_realloc_ndarray_complex
subroutine yggptr_realloc_ndarray_logical(x)
  implicit none
  type(yggptr) :: x
  type(logical_nd), pointer :: x_logical_nd
  type(logical1_nd), pointer :: x_logical1_nd
  type(logical2_nd), pointer :: x_logical2_nd
  type(logical4_nd), pointer :: x_logical4_nd
  type(logical8_nd), pointer :: x_logical8_nd
  select type(item=>x%item)
  type is (logical_nd)
     x_logical_nd => item
     if (associated(x_logical_nd%x)) nullify(x_logical_nd%x)
     if (associated(x_logical_nd%shape)) nullify(x_logical_nd%shape)
  type is (logical1_nd)
     x_logical1_nd => item
     if (associated(x_logical1_nd%x)) nullify(x_logical1_nd%x)
     if (associated(x_logical1_nd%shape)) nullify(x_logical1_nd%shape)
  type is (logical2_nd)
     x_logical2_nd => item
     if (associated(x_logical2_nd%x)) nullify(x_logical2_nd%x)
     if (associated(x_logical2_nd%shape)) nullify(x_logical2_nd%shape)
  type is (logical4_nd)
     x_logical4_nd => item
     if (associated(x_logical4_nd%x)) nullify(x_logical4_nd%x)
     if (associated(x_logical4_nd%shape)) nullify(x_logical4_nd%shape)
  type is (logical8_nd)
     x_logical8_nd => item
     if (associated(x_logical8_nd%x)) nullify(x_logical8_nd%x)
     if (associated(x_logical8_nd%shape)) nullify(x_logical8_nd%shape)
  class default
     stop 'yggptr_realloc_ndarray_logical: Unexpected type.'
  end select
end subroutine yggptr_realloc_ndarray_logical
subroutine yggptr_realloc_ndarray_character(x, array_len, precision)
  implicit none
  type(yggptr) :: x
  integer(kind=c_size_t), pointer :: array_len
  integer(kind=c_size_t), pointer :: precision
  type(character_nd), pointer :: x_character_nd
  integer(kind=8) :: i
  select type(item=>x%item)
  type is (character_nd)
     x_character_nd => item
     nullify(x%data_character_unit)
     if (array_len.gt.x%len) then
        if (associated(x_character_nd%x)) then
           deallocate(x_character_nd%x)
        end if
        allocate(x_character_nd%x(array_len))
     end if
     if ((array_len.gt.x%len).or.(precision.gt.x%prec)) then
        do i = 1, size(x_character_nd%x)
           if (associated(x_character_nd%x(i)%x)) then
              deallocate(x_character_nd%x(i)%x)
           end if
           allocate(x_character_nd%x(i)%x(precision))
        end do
     end if
     if (associated(x_character_nd%shape)) nullify(x_character_nd%shape)
  class default
     stop 'yggptr_realloc_ndarray_character: Unexpected type.'
  end select
end subroutine yggptr_realloc_ndarray_character
  ! END DOXYGEN_SHOULD_SKIP_THIS
