function convert_string_f2c(f_message) result(c_message)
  implicit none
  character(len=*), intent(in) :: f_message
  character(kind=c_char), allocatable :: c_message(:)
  integer :: i
  allocate(c_message(len(f_message)+1))
  do i = 1, len(f_message)
     c_message(i) = f_message(i:i)
  end do
  c_message(len(f_message)+1) = c_null_char
end function convert_string_f2c
function convert_format_f2c(f_fmt) result(c_fmt)
  implicit none
  character(len=*), intent(in) :: f_fmt
  character(kind=c_char), allocatable :: c_fmt(:)
  integer :: i, j, length
  allocate(c_fmt(len(f_fmt)+1))
  length = len(f_fmt)
  j = 1
  i = 1
  do while ((i.LE.length).AND.(j.LE.len(f_fmt)))
     if (j.LT.len(f_fmt)) then
        if (f_fmt(j:(j+1)).EQ."\t") then
           c_fmt(i) = char(9)
           j = j + 1
           length = length - 1
        else if (f_fmt(j:(j+1)).EQ."\n") then
           c_fmt(i) = NEW_LINE('c')
           j = j + 1
           length = length - 1
        else
           c_fmt(i) = f_fmt(j:j)
        end if
     else if (j.EQ.len(f_fmt)) then
        c_fmt(i) = f_fmt(j:j)
     end if
     i = i + 1
     j = j + 1
  end do
  do i = (length+1), (len(f_fmt)+1)
     c_fmt(i) = c_null_char
  end do
end function convert_format_f2c
function yggptr_c2f(x, realloc) result(flag)
  implicit none
  type(yggptr) :: x
  logical :: realloc
  integer(kind=c_size_t), pointer :: array_len
  integer(kind=c_size_t), pointer :: array_ndim
  integer(kind=c_size_t), dimension(:), pointer :: array_shape
  integer(kind=c_size_t), pointer :: precision
  integer(kind=8) :: i
  logical :: flag
  character(len=500) :: log_msg
  flag = .true.
  call ygglog_debug("yggptr_c2f: begin")
  allocate(array_len)
  allocate(array_ndim)
  allocate(array_shape(1))
  allocate(precision)
  array_len = 1
  array_ndim = 1
  array_shape(1) = 1
  precision = 1
  if (x%array) then
     if ((x%ndim.gt.1).or.x%ndarray) then
        deallocate(array_ndim)
        deallocate(array_shape)
        call c_f_pointer(x%ndim_ptr, array_ndim)
        call c_f_pointer(x%shape_ptr, array_shape, [array_ndim])
        do i = 1, array_ndim
           array_len = array_len * array_shape(i)
        end do
        write(log_msg, '("array_ndim = ",i7)') array_ndim
        call ygglog_debug(log_msg)
     else
        deallocate(array_len)
        call c_f_pointer(x%len_ptr, array_len)
        array_shape(1) = array_len
     end if
     write(log_msg, '("array_len = ",i7)') array_len
     call ygglog_debug(log_msg)
  end if
  if ((x%type.eq."character").or.(x%type.eq."unicode")) then
     deallocate(precision)
     call c_f_pointer(x%prec_ptr, precision)
     write(log_msg, '("precision = ",i7)') precision
     call ygglog_debug(log_msg)
  end if
  flag = yggptr_realloc(x, array_shape, precision, realloc)
  if (x%array) then
     if (x%alloc) then
        select type(item=>x%item)
        type is (unsigned1_1d)
           call yggptr_c2f_1darray_realloc_unsigned(x)
        type is (unsigned2_1d)
           call yggptr_c2f_1darray_realloc_unsigned(x)
        type is (unsigned4_1d)
           call yggptr_c2f_1darray_realloc_unsigned(x)
        type is (unsigned8_1d)
           call yggptr_c2f_1darray_realloc_unsigned(x)
        type is (c_long_1d)
           call yggptr_c2f_1darray_realloc_integer(x)
        type is (integer_1d)
           call yggptr_c2f_1darray_realloc_integer(x)
        type is (integer2_1d)
           call yggptr_c2f_1darray_realloc_integer(x)
        type is (integer4_1d)
           call yggptr_c2f_1darray_realloc_integer(x)
        type is (integer8_1d)
           call yggptr_c2f_1darray_realloc_integer(x)
        type is (real_1d)
           call yggptr_c2f_1darray_realloc_real(x)
        type is (real4_1d)
           call yggptr_c2f_1darray_realloc_real(x)
        type is (real8_1d)
           call yggptr_c2f_1darray_realloc_real(x)
        type is (real16_1d)
           call yggptr_c2f_1darray_realloc_real(x)
        type is (complex_1d)
           call yggptr_c2f_1darray_realloc_complex(x)
        type is (complex4_1d)
           call yggptr_c2f_1darray_realloc_complex(x)
        type is (complex8_1d)
           call yggptr_c2f_1darray_realloc_complex(x)
        type is (complex16_1d)
           call yggptr_c2f_1darray_realloc_complex(x)
        type is (logical_1d)
           call yggptr_c2f_1darray_realloc_logical(x)
        type is (logical1_1d)
           call yggptr_c2f_1darray_realloc_logical(x)
        type is (logical2_1d)
           call yggptr_c2f_1darray_realloc_logical(x)
        type is (logical4_1d)
           call yggptr_c2f_1darray_realloc_logical(x)
        type is (logical8_1d)
           call yggptr_c2f_1darray_realloc_logical(x)
        type is (character_1d)
           call yggptr_c2f_1darray_realloc_character(x)
        type is (unsigned1_nd)
           call yggptr_c2f_ndarray_realloc_unsigned(x)
        type is (unsigned2_nd)
           call yggptr_c2f_ndarray_realloc_unsigned(x)
        type is (unsigned4_nd)
           call yggptr_c2f_ndarray_realloc_unsigned(x)
        type is (unsigned8_nd)
           call yggptr_c2f_ndarray_realloc_unsigned(x)
        type is (c_long_nd)
           call yggptr_c2f_ndarray_realloc_integer(x)
        type is (integer_nd)
           call yggptr_c2f_ndarray_realloc_integer(x)
        type is (integer2_nd)
           call yggptr_c2f_ndarray_realloc_integer(x)
        type is (integer4_nd)
           call yggptr_c2f_ndarray_realloc_integer(x)
        type is (integer8_nd)
           call yggptr_c2f_ndarray_realloc_integer(x)
        type is (real_nd)
           call yggptr_c2f_ndarray_realloc_real(x)
        type is (real4_nd)
           call yggptr_c2f_ndarray_realloc_real(x)
        type is (real8_nd)
           call yggptr_c2f_ndarray_realloc_real(x)
        type is (real16_nd)
           call yggptr_c2f_ndarray_realloc_real(x)
        type is (complex_nd)
           call yggptr_c2f_ndarray_realloc_complex(x)
        type is (complex4_nd)
           call yggptr_c2f_ndarray_realloc_complex(x)
        type is (complex8_nd)
           call yggptr_c2f_ndarray_realloc_complex(x)
        type is (complex16_nd)
           call yggptr_c2f_ndarray_realloc_complex(x)
        type is (logical_nd)
           call yggptr_c2f_ndarray_realloc_logical(x)
        type is (logical1_nd)
           call yggptr_c2f_ndarray_realloc_logical(x)
        type is (logical2_nd)
           call yggptr_c2f_ndarray_realloc_logical(x)
        type is (logical4_nd)
           call yggptr_c2f_ndarray_realloc_logical(x)
        type is (logical8_nd)
           call yggptr_c2f_ndarray_realloc_logical(x)
        type is (character_nd)
           call yggptr_c2f_ndarray_realloc_character(x)
        class default
           write(log_msg, '("yggptr_c2f (realloc array transfer): Unexpected type: ",A)') x%type
           call ygglog_error(log_msg)
           stop "ERROR"
        end select
     else
        if (x%ndim.gt.1) then
           select type(item=>x%item_array)
           type is (ygguint1)
              call yggptr_c2f_ndarray_unsigned(x)
           type is (ygguint2)
              call yggptr_c2f_ndarray_unsigned(x)
           type is (ygguint4)
              call yggptr_c2f_ndarray_unsigned(x)
           type is (ygguint8)
              call yggptr_c2f_ndarray_unsigned(x)
           type is (integer(kind=2))
              call yggptr_c2f_ndarray_integer(x)
           type is (integer(kind=4))
              call yggptr_c2f_ndarray_integer(x)
           type is (integer(kind=8))
              call yggptr_c2f_ndarray_integer(x)
           type is (real(kind=4))
              call yggptr_c2f_ndarray_real(x)
           type is (real(kind=8))
              call yggptr_c2f_ndarray_real(x)
           ! type is (real(kind=16))
           !    call yggptr_c2f_ndarray_real(x)
           type is (complex(kind=4))
              call yggptr_c2f_ndarray_complex(x)
           type is (complex(kind=8))
              call yggptr_c2f_ndarray_complex(x)
           ! type is (complex(kind=16))
           !    call yggptr_c2f_ndarray_complex(x)
           type is (logical(kind=1))
              call yggptr_c2f_ndarray_logical(x)
           type is (logical(kind=2))
              call yggptr_c2f_ndarray_logical(x)
           type is (logical(kind=4))
              call yggptr_c2f_ndarray_logical(x)
           type is (logical(kind=8))
              call yggptr_c2f_ndarray_logical(x)
           type is (character(*))
              call yggptr_c2f_ndarray_character(x)
           class default
              write(log_msg, '("yggptr_c2f (",i2,"D array transfer): Unexpected type: ",A)') x%ndim, x%type
              call ygglog_error(log_msg)
              stop "ERROR"
           end select
        else
           select type(item=>x%item_array)
           type is (ygguint1)
           type is (ygguint2)
           type is (ygguint4)
           type is (ygguint8)
           type is (integer(kind=2))
           type is (integer(kind=4))
           type is (integer(kind=8))
           type is (real(kind=4))
           type is (real(kind=8))
           ! type is (real(kind=16))
           type is (complex(kind=4))
           type is (complex(kind=8))
           ! type is (complex(kind=16))
           type is (logical(kind=1))
           type is (logical(kind=2))
           type is (logical(kind=4))
           type is (logical(kind=8))
           type is (yggchar_r)
              call yggptr_c2f_array_character(x)
           type is (character(*))
              call yggptr_c2f_array_character(x)
           class default
              write(log_msg, '("yggptr_c2f (1d array transfer): Unexpected type: ",A)') x%type
              call ygglog_error(log_msg)
              stop "ERROR"
           end select
        end if
     end if
  else
     select type(item=>x%item)
     type is (ygguint1)
     type is (ygguint2)
     type is (ygguint4)
     type is (ygguint8)
     type is (integer(kind=2))
     type is (integer(kind=4))
     type is (integer(kind=8))
     type is (real(kind=4))
     type is (real(kind=8))
     ! type is (real(kind=16))
     type is (complex(kind=4))
     type is (complex(kind=8))
     ! type is (complex(kind=16))
     type is (logical(kind=1))
     type is (logical(kind=2))
     type is (logical(kind=4))
     type is (logical(kind=8))
     type is (yggnull)
     type is (yggchar_r)
        call yggptr_c2f_scalar_character(x)
     type is (character(*))
        call yggptr_c2f_scalar_character(x)
     class default
        if ((x%type.eq."ply").or.(x%type.eq."obj").or. &
             (x%type.eq."generic").or.(x%type.eq."object").or. &
             (x%type.eq."array").or.(x%type.eq."schema").or. &
             (x%type.eq."python").or.(x%type.eq."class").or. &
             (x%type.eq."instance").or.(x%type.eq."function")) then
           ! Use pointer        
        else
           select type(item=>x%item)
           type is (character(kind=ucs4, len=*))
              call yggptr_c2f_scalar_character(x)
           class default
              write(log_msg, '("yggptr_c2f (scalar transfer): Unexpected type: ",A)') x%type
              call ygglog_error(log_msg)
              stop "ERROR"
           end select
        end if
     end select
  end if
  if (.not.x%array) then
     deallocate(array_len)
     deallocate(array_ndim)
     deallocate(array_shape)
  else
     if (x%ndim.gt.1) then
        deallocate(array_len)
        nullify(array_ndim)
        nullify(array_shape)
     else
        nullify(array_len)
        deallocate(array_ndim)
        deallocate(array_shape)
     end if
  end if
  if (.not.((x%type.eq."character").or.(x%type.eq."unicode"))) then
     deallocate(precision)
  else
     nullify(precision)
  end if
  call ygglog_debug("yggptr_c2f: end")
end function yggptr_c2f


subroutine yggptr_c2f_scalar_character(x)
  implicit none
  type(yggptr) :: x
  character(kind=ucs4, len=:), &
       pointer :: x_unicode
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
     select type(item=>x%item)
     type is (character(kind=ucs4, len=*))
        x_unicode => item
        do i = 1, (x%prec / 4)
           x_unicode(i:i) = x%data_unicode_unit(i)
        end do
        do i = ((x%prec / 4) + 1), len(x_unicode)
           x_unicode(i:i) = ' '
        end do
        deallocate(x%data_unicode_unit)
     class default
        call ygglog_error("yggptr_c2f_scalar_character: Unexpected type.")
        stop "ERROR"
     end select
  end select
end subroutine yggptr_c2f_scalar_character


subroutine yggptr_c2f_array_character(x)
  implicit none
  type(yggptr) :: x
  character(len=x%prec), dimension(:), pointer :: item
  ! integer(kind=8) :: i, j, k
  item => x%item_array_char
  ! select type(item=>x%item_array)
  ! type is (character(*))
  if ((size(item).GT.0).AND.(len(item).GT.0)) then
     item = transfer(x%data_character_unit, item)
  end if
  ! do i = 1, x%len
  !    do j = 1, x%prec
  !       k = (i - 1) * x%prec + j
  !       item(i)(j:j) = x%data_character_unit(k)
  !    end do
  !    do j = (x%prec + 1), len(item(i))
  !       item(i)(j:j) = ' '
  !    end do
  ! end do
     deallocate(x%data_character_unit)
  ! class default
  !    call ygglog_error("yggptr_c2f_array_character: Unexpected type.")
  !    stop "ERROR"
  ! end select
end subroutine yggptr_c2f_array_character


! ND not reallocatable
subroutine yggptr_c2f_ndarray_unsigned(x)
  implicit none
  type(yggptr) :: x
  type(ygguint1), dimension(:), pointer :: x1
  type(ygguint2), dimension(:), pointer :: x2
  type(ygguint4), dimension(:), pointer :: x4
  type(ygguint8), dimension(:), pointer :: x8
  type(ygguint1), dimension(:, :), pointer :: x1_2d
  type(ygguint2), dimension(:, :), pointer :: x2_2d
  type(ygguint4), dimension(:, :), pointer :: x4_2d
  type(ygguint8), dimension(:, :), pointer :: x8_2d
  select type(item_2d=>x%item_array_2d)
  type is (ygguint1)
     x1_2d => item_2d
     select type(item_1d=>x%item_array)
     type is (ygguint1)
        x1 => item_1d
        x1_2d = reshape(x1, [x%shape(1), x%shape(2)])
        nullify(x%item_array)
        deallocate(x1)
     class default
        call ygglog_error("yggptr_c2f_ndarray_unsigned: types do not match")
        stop "ERROR"
     end select
  type is (ygguint2)
     x2_2d => item_2d
     select type(item_1d=>x%item_array)
     type is (ygguint2)
        x2 => item_1d
        x2_2d = reshape(x2, [x%shape(1), x%shape(2)])
        nullify(x%item_array)
        deallocate(x2)
     class default
        call ygglog_error("yggptr_c2f_ndarray_unsigned: types do not match")
        stop "ERROR"
     end select
  type is (ygguint4)
     x4_2d => item_2d
     select type(item_1d=>x%item_array)
     type is (ygguint4)
        x4 => item_1d
        x4_2d = reshape(x4, [x%shape(1), x%shape(2)])
        nullify(x%item_array)
        deallocate(x4)
     class default
        call ygglog_error("yggptr_c2f_ndarray_unsigned: types do not match")
        stop "ERROR"
     end select
  type is (ygguint8)
     x8_2d => item_2d
     select type(item_1d=>x%item_array)
     type is (ygguint8)
        x8 => item_1d
        x8_2d = reshape(x8, [x%shape(1), x%shape(2)])
        nullify(x%item_array)
        deallocate(x8)
     class default
        call ygglog_error("yggptr_c2f_ndarray_unsigned: types do not match")
        stop "ERROR"
     end select
  class default
     call ygglog_error("yggptr_c2f_ndarray_unsigned: Unexpected type.")
     stop "ERROR"
  end select
end subroutine yggptr_c2f_ndarray_unsigned
subroutine yggptr_c2f_ndarray_integer(x)
  implicit none
  type(yggptr) :: x
  integer(kind=2), dimension(:), pointer :: x2
  integer(kind=4), dimension(:), pointer :: x4
  integer(kind=8), dimension(:), pointer :: x8
  integer(kind=2), dimension(:, :), pointer :: x2_2d
  integer(kind=4), dimension(:, :), pointer :: x4_2d
  integer(kind=8), dimension(:, :), pointer :: x8_2d
  select type(item_2d=>x%item_array_2d)
  type is (integer(kind=2))
     x2_2d => item_2d
     select type(item_1d=>x%item_array)
     type is (integer(kind=2))
        x2 => item_1d
        x2_2d = reshape(x2, [x%shape(1), x%shape(2)])
        nullify(x%item_array)
        deallocate(x2)
     class default
        call ygglog_error("yggptr_c2f_ndarray_integer: types do not match")
        stop "ERROR"
     end select
  type is (integer(kind=4))
     x4_2d => item_2d
     select type(item_1d=>x%item_array)
     type is (integer(kind=4))
        x4 => item_1d
        x4_2d = reshape(x4, [x%shape(1), x%shape(2)])
        nullify(x%item_array)
        deallocate(x4)
     class default
        call ygglog_error("yggptr_c2f_ndarray_integer: types do not match")
        stop "ERROR"
     end select
  type is (integer(kind=8))
     x8_2d => item_2d
     select type(item_1d=>x%item_array)
     type is (integer(kind=8))
        x8 => item_1d
        x8_2d = reshape(x8, [x%shape(1), x%shape(2)])
        nullify(x%item_array)
        deallocate(x8)
     class default
        call ygglog_error("yggptr_c2f_ndarray_integer: types do not match")
        stop "ERROR"
     end select
  class default
     call ygglog_error("yggptr_c2f_ndarray_integer: Unexpected type.")
     stop "ERROR"
  end select
end subroutine yggptr_c2f_ndarray_integer
subroutine yggptr_c2f_ndarray_real(x)
  implicit none
  type(yggptr) :: x
  real(kind=4), dimension(:), pointer :: x4
  real(kind=8), dimension(:), pointer :: x8
  ! real(kind=16), dimension(:), pointer :: x16
  real(kind=4), dimension(:, :), pointer :: x4_2d
  real(kind=8), dimension(:, :), pointer :: x8_2d
  ! real(kind=16), dimension(:, :), pointer :: x16_2d
  select type(item_2d=>x%item_array_2d)
  type is (real(kind=4))
     x4_2d => item_2d
     select type(item_1d=>x%item_array)
     type is (real(kind=4))
        x4 => item_1d
        x4_2d = reshape(x4, [x%shape(1), x%shape(2)])
        nullify(x%item_array)
        deallocate(x4)
     class default
        call ygglog_error("yggptr_c2f_ndarray_real: types do not match")
        stop "ERROR"
     end select
  type is (real(kind=8))
     x8_2d => item_2d
     select type(item_1d=>x%item_array)
     type is (real(kind=8))
        x8 => item_1d
        x8_2d = reshape(x8, [x%shape(1), x%shape(2)])
        nullify(x%item_array)
        deallocate(x8)
     class default
        call ygglog_error("yggptr_c2f_ndarray_real: types do not match")
        stop "ERROR"
     end select
  ! type is (real(kind=16))
  !    x16_2d => item_2d
  !    select type(item_1d=>x%item_array)
  !    type is (real(kind=16))
  !       x16 => item_1d
  !       x16_2d = reshape(x16, [x%shape(1), x%shape(2)])
  !       nullify(x%item_array)
  !       deallocate(x16)
  !    class default
  !       call ygglog_error("yggptr_c2f_ndarray_real: types do not match")
  !       stop "ERROR"
  !    end select
  class default
     call ygglog_error("yggptr_c2f_ndarray_real: Unexpected type.")
     stop "ERROR"
  end select
end subroutine yggptr_c2f_ndarray_real
subroutine yggptr_c2f_ndarray_complex(x)
  implicit none
  type(yggptr) :: x
  complex(kind=4), dimension(:), pointer :: x4
  complex(kind=8), dimension(:), pointer :: x8
  ! complex(kind=16), dimension(:), pointer :: x16
  complex(kind=4), dimension(:, :), pointer :: x4_2d
  complex(kind=8), dimension(:, :), pointer :: x8_2d
  ! complex(kind=16), dimension(:, :), pointer :: x16_2d
  select type(item_2d=>x%item_array_2d)
  type is (complex(kind=4))
     x4_2d => item_2d
     select type(item_1d=>x%item_array)
     type is (complex(kind=4))
        x4 => item_1d
        x4_2d = reshape(x4, [x%shape(1), x%shape(2)])
        nullify(x%item_array)
        deallocate(x4)
     class default
        call ygglog_error("yggptr_c2f_ndarray_complex: types do not match")
        stop "ERROR"
     end select
  type is (complex(kind=8))
     x8_2d => item_2d
     select type(item_1d=>x%item_array)
     type is (complex(kind=8))
        x8 => item_1d
        x8_2d = reshape(x8, [x%shape(1), x%shape(2)])
        nullify(x%item_array)
        deallocate(x8)
     class default
        call ygglog_error("yggptr_c2f_ndarray_complex: types do not match")
        stop "ERROR"
     end select
  ! type is (complex(kind=16))
  !    x16_2d => item_2d
  !    select type(item_1d=>x%item_array)
  !    type is (complex(kind=16))
  !       x16 => item_1d
  !       x16_2d = reshape(x16, [x%shape(1), x%shape(2)])
  !       nullify(x%item_array)
  !       deallocate(x16)
  !    class default
  !       call ygglog_error("yggptr_c2f_ndarray_complex: types do not match")
  !       stop "ERROR"
  !    end select
  class default
     call ygglog_error("yggptr_c2f_ndarray_complex: Unexpected type.")
     stop "ERROR"
  end select
end subroutine yggptr_c2f_ndarray_complex
subroutine yggptr_c2f_ndarray_logical(x)
  implicit none
  type(yggptr) :: x
  logical(kind=1), dimension(:), pointer :: x1
  logical(kind=2), dimension(:), pointer :: x2
  logical(kind=4), dimension(:), pointer :: x4
  logical(kind=8), dimension(:), pointer :: x8
  logical(kind=1), dimension(:, :), pointer :: x1_2d
  logical(kind=2), dimension(:, :), pointer :: x2_2d
  logical(kind=4), dimension(:, :), pointer :: x4_2d
  logical(kind=8), dimension(:, :), pointer :: x8_2d
  select type(item_2d=>x%item_array_2d)
  type is (logical(kind=1))
     x1_2d => item_2d
     select type(item_1d=>x%item_array)
     type is (logical(kind=1))
        x1 => item_1d
        x1_2d = reshape(x1, [x%shape(1), x%shape(2)])
        nullify(x%item_array)
        deallocate(x1)
     class default
        call ygglog_error("yggptr_c2f_ndarray_logical: types do not match")
        stop "ERROR"
     end select
  type is (logical(kind=2))
     x2_2d => item_2d
     select type(item_1d=>x%item_array)
     type is (logical(kind=2))
        x2 => item_1d
        x2_2d = reshape(x2, [x%shape(1), x%shape(2)])
        nullify(x%item_array)
        deallocate(x2)
     class default
        call ygglog_error("yggptr_c2f_ndarray_logical: types do not match")
        stop "ERROR"
     end select
  type is (logical(kind=4))
     x4_2d => item_2d
     select type(item_1d=>x%item_array)
     type is (logical(kind=4))
        x4 => item_1d
        x4_2d = reshape(x4, [x%shape(1), x%shape(2)])
        nullify(x%item_array)
        deallocate(x4)
     class default
        call ygglog_error("yggptr_c2f_ndarray_logical: types do not match")
        stop "ERROR"
     end select
  type is (logical(kind=8))
     x8_2d => item_2d
     select type(item_1d=>x%item_array)
     type is (logical(kind=8))
        x8 => item_1d
        x8_2d = reshape(x8, [x%shape(1), x%shape(2)])
        nullify(x%item_array)
        deallocate(x8)
     class default
        call ygglog_error("yggptr_c2f_ndarray_logical: types do not match")
        stop "ERROR"
     end select
  class default
     call ygglog_error("yggptr_c2f_ndarray_logical: Unexpected type.")
     stop "ERROR"
  end select
end subroutine yggptr_c2f_ndarray_logical
subroutine yggptr_c2f_ndarray_character(x)
  implicit none
  type(yggptr) :: x
  character(len=:), dimension(:), pointer :: xc
  character(len=:), dimension(:, :), pointer :: xc_2d
  integer(kind=c_size_t) :: i, j
  select type(item_2d=>x%item_array_2d)
  type is (character(*))
     xc_2d => item_2d
     select type(item_1d=>x%item_array)
     type is (character(*))
        xc => item_1d
        allocate(character(len=x%prec) :: xc_2d(x%shape(1), x%shape(2)))
        do i = 1, x%shape(1)
           do j = 1, x%shape(2)
              xc_2d(i, j) = xc(i + (j-1)*(x%shape(1)))
           enddo
        enddo
        ! xc_2d = reshape(xc, [x%shape(1), x%shape(2)])
        nullify(x%item_array)
        deallocate(xc)
     class default
        call ygglog_error("yggptr_c2f_ndarray_logical: types do not match")
        stop "ERROR"
     end select
  class default
     call ygglog_error("yggptr_c2f_ndarray_character: Unexpected type.")
     stop "ERROR"
  end select
end subroutine yggptr_c2f_ndarray_character


! 1D reallocatable
subroutine yggptr_c2f_1darray_realloc_unsigned(x)
  implicit none
  type(yggptr) :: x
  type(unsigned1_1d), pointer :: x_unsigned1_1d
  type(unsigned2_1d), pointer :: x_unsigned2_1d
  type(unsigned4_1d), pointer :: x_unsigned4_1d
  type(unsigned8_1d), pointer :: x_unsigned8_1d
  select type(item=>x%item)
  type is (unsigned1_1d)
     x_unsigned1_1d => item
     if (.not.associated(x_unsigned1_1d%x)) then
        call c_f_pointer(x%ptr, x_unsigned1_1d%x, [x%len])
     end if
  type is (unsigned2_1d)
     x_unsigned2_1d => item
     if (.not.associated(x_unsigned2_1d%x)) then
        call c_f_pointer(x%ptr, x_unsigned2_1d%x, [x%len])
     end if
  type is (unsigned4_1d)
     x_unsigned4_1d => item
     if (.not.associated(x_unsigned4_1d%x)) then
        call c_f_pointer(x%ptr, x_unsigned4_1d%x, [x%len])
     end if
  type is (unsigned8_1d)
     x_unsigned8_1d => item
     if (.not.associated(x_unsigned8_1d%x)) then
        call c_f_pointer(x%ptr, x_unsigned8_1d%x, [x%len])
     end if
  class default
     call ygglog_error("yggptr_c2f_1darray_realloc_unsigned: Unexpected type.")
     stop "ERROR"
  end select
end subroutine yggptr_c2f_1darray_realloc_unsigned
subroutine yggptr_c2f_1darray_realloc_integer(x)
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
     call ygglog_error("yggptr_c2f_1darray_realloc_integer: Unexpected type.")
     stop "ERROR"
  end select
end subroutine yggptr_c2f_1darray_realloc_integer
subroutine yggptr_c2f_1darray_realloc_real(x)
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
     call ygglog_error("yggptr_c2f_1darray_realloc_real: Unexpected type.")
     stop "ERROR"
  end select
end subroutine yggptr_c2f_1darray_realloc_real
subroutine yggptr_c2f_1darray_realloc_complex(x)
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
     call ygglog_error("yggptr_c2f_1darray_realloc_complex: Unexpected type.")
     stop "ERROR"
  end select
end subroutine yggptr_c2f_1darray_realloc_complex
subroutine yggptr_c2f_1darray_realloc_logical(x)
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
     call ygglog_error("yggptr_c2f_1darray_realloc_logical: Unexpected type.")
     stop "ERROR"
  end select
end subroutine yggptr_c2f_1darray_realloc_logical
subroutine yggptr_c2f_1darray_realloc_character(x)
  implicit none
  type(yggptr) :: x
  integer(kind=8) :: i
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
     call ygglog_error("yggptr_c2f_1darray_realloc_character: Unexpected type.")
     stop "ERROR"
  end select
end subroutine yggptr_c2f_1darray_realloc_character


! ND reallocatable
subroutine yggptr_c2f_ndarray_realloc_unsigned(x)
  implicit none
  type(yggptr) :: x
  type(unsigned1_nd), pointer :: x_unsigned1_nd
  type(unsigned2_nd), pointer :: x_unsigned2_nd
  type(unsigned4_nd), pointer :: x_unsigned4_nd
  type(unsigned8_nd), pointer :: x_unsigned8_nd
  select type(item=>x%item)
  type is (unsigned1_nd)
     x_unsigned1_nd => item
     if (.not.associated(x_unsigned1_nd%x)) then
        call c_f_pointer(x%ptr, x_unsigned1_nd%x, [x%len])
     end if
     if (.not.associated(x_unsigned1_nd%shape)) then
        call c_f_pointer(x%shape_ptr, x_unsigned1_nd%shape, [x%ndim])
     end if
  type is (unsigned2_nd)
     x_unsigned2_nd => item
     if (.not.associated(x_unsigned2_nd%x)) then
        call c_f_pointer(x%ptr, x_unsigned2_nd%x, [x%len])
     end if
     if (.not.associated(x_unsigned2_nd%shape)) then
        call c_f_pointer(x%shape_ptr, x_unsigned2_nd%shape, [x%ndim])
     end if
  type is (unsigned4_nd)
     x_unsigned4_nd => item
     if (.not.associated(x_unsigned4_nd%x)) then
        call c_f_pointer(x%ptr, x_unsigned4_nd%x, [x%len])
     end if
     if (.not.associated(x_unsigned4_nd%shape)) then
        call c_f_pointer(x%shape_ptr, x_unsigned4_nd%shape, [x%ndim])
     end if
  type is (unsigned8_nd)
     x_unsigned8_nd => item
     if (.not.associated(x_unsigned8_nd%x)) then
        call c_f_pointer(x%ptr, x_unsigned8_nd%x, [x%len])
     end if
     if (.not.associated(x_unsigned8_nd%shape)) then
        call c_f_pointer(x%shape_ptr, x_unsigned8_nd%shape, [x%ndim])
     end if
  class default
     call ygglog_error("yggptr_c2f_ndarray_realloc_unsigned: Unexpected type.")
     stop "ERROR"
  end select
end subroutine yggptr_c2f_ndarray_realloc_unsigned
subroutine yggptr_c2f_ndarray_realloc_integer(x)
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
     if (.not.associated(x_c_long_nd%x)) then
        call c_f_pointer(x%ptr, x_c_long_nd%x, [x%len])
     end if
     if (.not.associated(x_c_long_nd%shape)) then
        call c_f_pointer(x%shape_ptr, x_c_long_nd%shape, [x%ndim])
     end if
  type is (integer_nd)
     x_integer_nd => item
     if (.not.associated(x_integer_nd%x)) then
        call c_f_pointer(x%ptr, x_integer_nd%x, [x%len])
     end if
     if (.not.associated(x_integer_nd%shape)) then
        call c_f_pointer(x%shape_ptr, x_integer_nd%shape, [x%ndim])
     end if
  type is (integer2_nd)
     x_integer2_nd => item
     if (.not.associated(x_integer2_nd%x)) then
        call c_f_pointer(x%ptr, x_integer2_nd%x, [x%len])
     end if
     if (.not.associated(x_integer2_nd%shape)) then
        call c_f_pointer(x%shape_ptr, x_integer2_nd%shape, [x%ndim])
     end if
  type is (integer4_nd)
     x_integer4_nd => item
     if (.not.associated(x_integer4_nd%x)) then
        call c_f_pointer(x%ptr, x_integer4_nd%x, [x%len])
     end if
     if (.not.associated(x_integer4_nd%shape)) then
        call c_f_pointer(x%shape_ptr, x_integer4_nd%shape, [x%ndim])
     end if
  type is (integer8_nd)
     x_integer8_nd => item
     if (.not.associated(x_integer8_nd%x)) then
        call c_f_pointer(x%ptr, x_integer8_nd%x, [x%len])
     end if
     if (.not.associated(x_integer8_nd%shape)) then
        call c_f_pointer(x%shape_ptr, x_integer8_nd%shape, [x%ndim])
     end if
  class default
     call ygglog_error("yggptr_c2f_ndarray_realloc_integer: Unexpected type.")
     stop "ERROR"
  end select
end subroutine yggptr_c2f_ndarray_realloc_integer
subroutine yggptr_c2f_ndarray_realloc_real(x)
  implicit none
  type(yggptr) :: x
  type(real_nd), pointer :: x_real_nd
  type(real4_nd), pointer :: x_real4_nd
  type(real8_nd), pointer :: x_real8_nd
  type(real16_nd), pointer :: x_real16_nd
  select type(item=>x%item)
  type is (real_nd)
     x_real_nd => item
     if (.not.associated(x_real_nd%x)) then
        call c_f_pointer(x%ptr, x_real_nd%x, [x%len])
     end if
     if (.not.associated(x_real_nd%shape)) then
        call c_f_pointer(x%shape_ptr, x_real_nd%shape, [x%ndim])
     end if
  type is (real4_nd)
     x_real4_nd => item
     if (.not.associated(x_real4_nd%x)) then
        call c_f_pointer(x%ptr, x_real4_nd%x, [x%len])
     end if
     if (.not.associated(x_real4_nd%shape)) then
        call c_f_pointer(x%shape_ptr, x_real4_nd%shape, [x%ndim])
     end if
  type is (real8_nd)
     x_real8_nd => item
     if (.not.associated(x_real8_nd%x)) then
        call c_f_pointer(x%ptr, x_real8_nd%x, [x%len])
     end if
     if (.not.associated(x_real8_nd%shape)) then
        call c_f_pointer(x%shape_ptr, x_real8_nd%shape, [x%ndim])
     end if
  type is (real16_nd)
     x_real16_nd => item
     if (.not.associated(x_real16_nd%x)) then
        call c_f_pointer(x%ptr, x_real16_nd%x, [x%len])
     end if
     if (.not.associated(x_real16_nd%shape)) then
        call c_f_pointer(x%shape_ptr, x_real16_nd%shape, [x%ndim])
     end if
  class default
     call ygglog_error("yggptr_c2f_ndarray_realloc_real: Unexpected type.")
     stop "ERROR"
  end select
end subroutine yggptr_c2f_ndarray_realloc_real
subroutine yggptr_c2f_ndarray_realloc_complex(x)
  implicit none
  type(yggptr) :: x
  type(complex_nd), pointer :: x_complex_nd
  type(complex4_nd), pointer :: x_complex4_nd
  type(complex8_nd), pointer :: x_complex8_nd
  type(complex16_nd), pointer :: x_complex16_nd
  select type(item=>x%item)
  type is (complex_nd)
     x_complex_nd => item
     if (.not.associated(x_complex_nd%x)) then
        call c_f_pointer(x%ptr, x_complex_nd%x, [x%len])
     end if
     if (.not.associated(x_complex_nd%shape)) then
        call c_f_pointer(x%shape_ptr, x_complex_nd%shape, [x%ndim])
     end if
  type is (complex4_nd)
     x_complex4_nd => item
     if (.not.associated(x_complex4_nd%x)) then
        call c_f_pointer(x%ptr, x_complex4_nd%x, [x%len])
     end if
     if (.not.associated(x_complex4_nd%shape)) then
        call c_f_pointer(x%shape_ptr, x_complex4_nd%shape, [x%ndim])
     end if
  type is (complex8_nd)
     x_complex8_nd => item
     if (.not.associated(x_complex8_nd%x)) then
        call c_f_pointer(x%ptr, x_complex8_nd%x, [x%len])
     end if
     if (.not.associated(x_complex8_nd%shape)) then
        call c_f_pointer(x%shape_ptr, x_complex8_nd%shape, [x%ndim])
     end if
  type is (complex16_nd)
     x_complex16_nd => item
     if (.not.associated(x_complex16_nd%x)) then
        call c_f_pointer(x%ptr, x_complex16_nd%x, [x%len])
     end if
     if (.not.associated(x_complex16_nd%shape)) then
        call c_f_pointer(x%shape_ptr, x_complex16_nd%shape, [x%ndim])
     end if
  class default
     call ygglog_error("yggptr_c2f_ndarray_realloc_complex: Unexpected type.")
     stop "ERROR"
  end select
end subroutine yggptr_c2f_ndarray_realloc_complex
subroutine yggptr_c2f_ndarray_realloc_logical(x)
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
     if (.not.associated(x_logical_nd%x)) then
        call c_f_pointer(x%ptr, x_logical_nd%x, [x%len])
     end if
     if (.not.associated(x_logical_nd%shape)) then
        call c_f_pointer(x%shape_ptr, x_logical_nd%shape, [x%ndim])
     end if
  type is (logical1_nd)
     x_logical1_nd => item
     if (.not.associated(x_logical1_nd%x)) then
        call c_f_pointer(x%ptr, x_logical1_nd%x, [x%len])
     end if
     if (.not.associated(x_logical1_nd%shape)) then
        call c_f_pointer(x%shape_ptr, x_logical1_nd%shape, [x%ndim])
     end if
  type is (logical2_nd)
     x_logical2_nd => item
     if (.not.associated(x_logical2_nd%x)) then
        call c_f_pointer(x%ptr, x_logical2_nd%x, [x%len])
     end if
     if (.not.associated(x_logical2_nd%shape)) then
        call c_f_pointer(x%shape_ptr, x_logical2_nd%shape, [x%ndim])
     end if
  type is (logical4_nd)
     x_logical4_nd => item
     if (.not.associated(x_logical4_nd%x)) then
        call c_f_pointer(x%ptr, x_logical4_nd%x, [x%len])
     end if
     if (.not.associated(x_logical4_nd%shape)) then
        call c_f_pointer(x%shape_ptr, x_logical4_nd%shape, [x%ndim])
     end if
  type is (logical8_nd)
     x_logical8_nd => item
     if (.not.associated(x_logical8_nd%x)) then
        call c_f_pointer(x%ptr, x_logical8_nd%x, [x%len])
     end if
     if (.not.associated(x_logical8_nd%shape)) then
        call c_f_pointer(x%shape_ptr, x_logical8_nd%shape, [x%ndim])
     end if
  class default
     call ygglog_error("yggptr_c2f_ndarray_realloc_logical: Unexpected type.")
     stop "ERROR"
  end select
end subroutine yggptr_c2f_ndarray_realloc_logical
subroutine yggptr_c2f_ndarray_realloc_character(x)
  implicit none
  type(yggptr) :: x
  integer(kind=8) :: i
  type(character_nd), pointer :: x_character_nd
  select type(item=>x%item)
  type is (character_nd)
     x_character_nd => item
     if (.not.associated(x%data_character_unit)) then
        call c_f_pointer(x%ptr, x%data_character_unit, [x%prec*x%len])
     end if
     do i = 1, x%len
        x_character_nd%x(i)%x = x%data_character_unit( &
             (1+(i-1)*x%prec):(i*x%prec))
     end do
     deallocate(x%data_character_unit)
     if (.not.associated(x_character_nd%shape)) then
        call c_f_pointer(x%shape_ptr, x_character_nd%shape, [x%ndim])
     end if
  class default
     call ygglog_error("yggptr_c2f_ndarray_realloc_character: Unexpected type.")
     stop "ERROR"
  end select
end subroutine yggptr_c2f_ndarray_realloc_character
