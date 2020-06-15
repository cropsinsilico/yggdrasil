! Interface for getting/setting generic array elements
! Get methods
function generic_array_get_boolean(x, index) result(out)
  implicit none
  type(ygggeneric) :: x
  integer, intent(in) :: index
  logical(kind=1), pointer :: out
  type(c_ptr) :: c_out
  c_out = generic_array_get_item(x, index, "boolean")
  call c_f_pointer(c_out, out)
end function generic_array_get_boolean
function generic_array_get_integer(x, index) result(out)
  implicit none
  type(ygggeneric) :: x
  integer, intent(in) :: index
  integer(kind=c_int), pointer :: out
  type(c_ptr) :: c_out
  c_out = generic_array_get_item(x, index, "integer")
  call c_f_pointer(c_out, out)
end function generic_array_get_integer
function generic_array_get_null(x, index) result(out)
  implicit none
  type(ygggeneric) :: x
  integer, intent(in) :: index
  type(yggnull) :: out
  type(c_ptr) :: c_out
  c_out = generic_array_get_item(x, index, "null")
  ! call c_f_pointer(c_out%ptr, out)
end function generic_array_get_null
function generic_array_get_number(x, index) result(out)
  implicit none
  type(ygggeneric) :: x
  integer, intent(in) :: index
  real(kind=8), pointer :: out
  type(c_ptr) :: c_out
  c_out = generic_array_get_item(x, index, "number")
  call c_f_pointer(c_out, out)
end function generic_array_get_number
function generic_array_get_string(x, index) result(out)
  implicit none
  type(ygggeneric) :: x
  integer, intent(in) :: index
  character(len=:, kind=c_char), pointer :: out
  type(c_ptr) :: c_out
  integer :: nbytes
  c_out = generic_array_get_item(x, index, "string")
  call c_f_pointer(c_out, out)
end function generic_array_get_string
function generic_array_get_map(x, index) result(out)
  implicit none
  type(ygggeneric) :: x
  integer, intent(in) :: index
  type(ygggeneric) :: out
  out = init_generic()
  out%obj = generic_array_get_item(x, index, "object")
end function generic_array_get_map
function generic_array_get_array(x, index) result(out)
  implicit none
  type(ygggeneric) :: x
  integer, intent(in) :: index
  type(ygggeneric) :: out
  out = init_generic()
  out%obj = generic_array_get_item(x, index, "array")
end function generic_array_get_array
function generic_array_get_ply(x, index) result(out)
  implicit none
  type(ygggeneric) :: x
  integer, intent(in) :: index
  type(c_ptr) :: c_out
  type(yggply), pointer :: out
  c_out = generic_array_get_item(x, index, "ply")
  ! Copy?
  call c_f_pointer(c_out, out)
end function generic_array_get_ply
function generic_array_get_obj(x, index) result(out)
  implicit none
  type(ygggeneric) :: x
  integer, intent(in) :: index
  type(c_ptr) :: c_out
  type(yggobj), pointer :: out
  c_out = generic_array_get_item(x, index, "obj")
  ! Copy?
  call c_f_pointer(c_out, out)
end function generic_array_get_obj
function generic_array_get_python_class(x, index) result(out)
  implicit none
  type(ygggeneric) :: x
  integer, intent(in) :: index
  type(c_ptr) :: c_out
  type(yggpython), pointer :: out
  c_out = generic_array_get_item(x, index, "class")
  ! Copy?
  call c_f_pointer(c_out, out)
end function generic_array_get_python_class
function generic_array_get_python_function(x, index) result(out)
  implicit none
  type(ygggeneric) :: x
  integer, intent(in) :: index
  type(c_ptr) :: c_out
  type(yggpython), pointer :: out
  c_out = generic_array_get_item(x, index, "function")
  ! Copy?
  call c_f_pointer(c_out, out)
end function generic_array_get_python_function
function generic_array_get_schema(x, index) result(out)
  implicit none
  type(ygggeneric) :: x
  integer, intent(in) :: index
  type(ygggeneric), pointer :: out
  out = init_generic()
  out%obj = generic_array_get_item(x, index, "schema")
end function generic_array_get_schema
function generic_array_get_any(x, index) result(out)
  implicit none
  type(ygggeneric) :: x
  integer, intent(in) :: index
  type(ygggeneric), pointer :: out
  out = init_generic()
  out%obj = generic_array_get_item(x, index, "any")
end function generic_array_get_any
! Get scalar int
function generic_array_get_integer2(x, index) result(out)
  implicit none
  type(ygggeneric) :: x
  integer, intent(in) :: index
  integer(kind=2), pointer :: out
  type(c_ptr) :: c_out
  c_out = generic_array_get_scalar(x, index, "int", 8 * 2)
  call c_f_pointer(c_out, out)
end function generic_array_get_integer2
function generic_array_get_integer4(x, index) result(out)
  implicit none
  type(ygggeneric) :: x
  integer, intent(in) :: index
  integer(kind=4), pointer :: out
  type(c_ptr) :: c_out
  c_out = generic_array_get_scalar(x, index, "int", 8 * 4)
  call c_f_pointer(c_out, out)
end function generic_array_get_integer4
function generic_array_get_integer8(x, index) result(out)
  implicit none
  type(ygggeneric) :: x
  integer, intent(in) :: index
  integer(kind=8), pointer :: out
  type(c_ptr) :: c_out
  c_out = generic_array_get_scalar(x, index, "int", 8 * 8)
  call c_f_pointer(c_out, out)
end function generic_array_get_integer8
! Get scalar uint
function generic_array_get_unsigned1(x, index) result(out)
  implicit none
  type(ygggeneric) :: x
  integer, intent(in) :: index
  type(ygguint1) :: out
  integer(kind=1), pointer :: temp
  type(c_ptr) :: c_out
  c_out = generic_array_get_scalar(x, index, "uint", 8 * 1)
  call c_f_pointer(c_out, temp)
  out%x = temp
  deallocate(temp)
end function generic_array_get_unsigned1
function generic_array_get_unsigned2(x, index) result(out)
  implicit none
  type(ygggeneric) :: x
  integer, intent(in) :: index
  type(ygguint2) :: out
  integer(kind=2), pointer :: temp
  type(c_ptr) :: c_out
  c_out = generic_array_get_scalar(x, index, "uint", 8 * 2)
  call c_f_pointer(c_out, temp)
  out%x = temp
  deallocate(temp)
end function generic_array_get_unsigned2
function generic_array_get_unsigned4(x, index) result(out)
  implicit none
  type(ygggeneric) :: x
  integer, intent(in) :: index
  type(ygguint4) :: out
  integer(kind=4), pointer :: temp
  type(c_ptr) :: c_out
  c_out = generic_array_get_scalar(x, index, "uint", 8 * 4)
  call c_f_pointer(c_out, temp)
  out%x = temp
  deallocate(temp)
end function generic_array_get_unsigned4
function generic_array_get_unsigned8(x, index) result(out)
  implicit none
  type(ygggeneric) :: x
  integer, intent(in) :: index
  type(ygguint8) :: out
  integer(kind=8), pointer :: temp
  type(c_ptr) :: c_out
  c_out = generic_array_get_scalar(x, index, "uint", 8 * 8)
  call c_f_pointer(c_out, temp)
  out%x = temp
  deallocate(temp)
end function generic_array_get_unsigned8
! Get scalar real
function generic_array_get_real4(x, index) result(out)
  implicit none
  type(ygggeneric) :: x
  integer, intent(in) :: index
  real(kind=4), pointer :: out
  type(c_ptr) :: c_out
  c_out = generic_array_get_scalar(x, index, "float", 8 * 4)
  call c_f_pointer(c_out, out)
end function generic_array_get_real4
function generic_array_get_real8(x, index) result(out)
  implicit none
  type(ygggeneric) :: x
  integer, intent(in) :: index
  real(kind=8), pointer :: out
  type(c_ptr) :: c_out
  c_out = generic_array_get_scalar(x, index, "float", 8 * 8)
  call c_f_pointer(c_out, out)
end function generic_array_get_real8
! Get scalar complex
function generic_array_get_complex4(x, index) result(out)
  implicit none
  type(ygggeneric) :: x
  integer, intent(in) :: index
  complex(kind=4), pointer :: out
  type(c_ptr) :: c_out
  c_out = generic_array_get_scalar(x, index, "complex", 8 * 4)
  call c_f_pointer(c_out, out)
end function generic_array_get_complex4
function generic_array_get_complex8(x, index) result(out)
  implicit none
  type(ygggeneric) :: x
  integer, intent(in) :: index
  complex(kind=8), pointer :: out
  type(c_ptr) :: c_out
  c_out = generic_array_get_scalar(x, index, "complex", 8 * 8)
  call c_f_pointer(c_out, out)
end function generic_array_get_complex8
! Get scalar string
function generic_array_get_bytes(x, index) result(out)
  implicit none
  type(ygggeneric) :: x
  integer, intent(in) :: index
  character(len=:), pointer :: out
  character, dimension(:), pointer :: temp
  type(c_ptr) :: c_out
  integer :: length, i
  c_out = generic_array_get_scalar(x, index, "bytes", 0)
  length = generic_array_get_item_nbytes(x, index)
  call c_f_pointer(c_out, temp, [length])
  allocate(character(len=length) :: out)
  do i = 1, length
     out(i:i) = temp(i)
  end do
  deallocate(temp)
end function generic_array_get_bytes
function generic_array_get_unicode(x, index) result(out)
  implicit none
  type(ygggeneric) :: x
  integer, intent(in) :: index
  character(kind=ucs4, len=:), pointer :: out
  character(kind=ucs4), dimension(:), pointer :: temp
  type(c_ptr) :: c_out
  integer :: length, i
  c_out = generic_array_get_scalar(x, index, "unicode", 0)
  length = generic_array_get_item_nbytes(x, index)/4
  call c_f_pointer(c_out, temp, [length])
  allocate(character(kind=ucs4, len=length) :: out)
  do i = 1, length
     out(i:i) = temp(i)
  end do
  deallocate(temp)
end function generic_array_get_unicode

! Get 1darray int
function generic_array_get_1darray_integer2(x, index) result(out)
  implicit none
  type(ygggeneric) :: x
  integer, intent(in) :: index
  integer(kind=2), dimension(:), pointer :: out
  integer(kind=c_size_t) :: c_length
  type(c_ptr), target :: c_out
  c_length = generic_array_get_1darray(x, index, "int", 8 * 2, c_loc(c_out))
  call c_f_pointer(c_out, out, [c_length])
end function generic_array_get_1darray_integer2
function generic_array_get_1darray_integer4(x, index) result(out)
  implicit none
  type(ygggeneric) :: x
  integer, intent(in) :: index
  integer(kind=4), dimension(:), pointer :: out
  integer(kind=c_size_t) :: c_length
  type(c_ptr), target :: c_out
  c_length = generic_array_get_1darray(x, index, "int", 8 * 4, c_loc(c_out))
  call c_f_pointer(c_out, out, [c_length])
end function generic_array_get_1darray_integer4
function generic_array_get_1darray_integer8(x, index) result(out)
  implicit none
  type(ygggeneric) :: x
  integer, intent(in) :: index
  integer(kind=8), dimension(:), pointer :: out
  integer(kind=c_size_t) :: c_length
  type(c_ptr), target :: c_out
  c_length = generic_array_get_1darray(x, index, "int", 8 * 8, c_loc(c_out))
  call c_f_pointer(c_out, out, [c_length])
end function generic_array_get_1darray_integer8
! Get 1darray uint
function generic_array_get_1darray_unsigned1(x, index) result(out)
  implicit none
  type(ygggeneric) :: x
  integer, intent(in) :: index
  type(ygguint1), dimension(:), pointer :: out
  integer(kind=c_size_t) :: c_length
  type(c_ptr), target :: c_out
  c_length = generic_array_get_1darray(x, index, "uint", 8 * 1, c_loc(c_out))
  call c_f_pointer(c_out, out, [c_length])
end function generic_array_get_1darray_unsigned1
function generic_array_get_1darray_unsigned2(x, index) result(out)
  implicit none
  type(ygggeneric) :: x
  integer, intent(in) :: index
  type(ygguint2), dimension(:), pointer :: out
  integer(kind=c_size_t) :: c_length
  type(c_ptr), target :: c_out
  c_length = generic_array_get_1darray(x, index, "uint", 8 * 2, c_loc(c_out))
  call c_f_pointer(c_out, out, [c_length])
end function generic_array_get_1darray_unsigned2
function generic_array_get_1darray_unsigned4(x, index) result(out)
  implicit none
  type(ygggeneric) :: x
  integer, intent(in) :: index
  type(ygguint4), dimension(:), pointer :: out
  integer(kind=c_size_t) :: c_length
  type(c_ptr), target :: c_out
  c_length = generic_array_get_1darray(x, index, "uint", 8 * 4, c_loc(c_out))
  call c_f_pointer(c_out, out, [c_length])
end function generic_array_get_1darray_unsigned4
function generic_array_get_1darray_unsigned8(x, index) result(out)
  implicit none
  type(ygggeneric) :: x
  integer, intent(in) :: index
  type(ygguint8), dimension(:), pointer :: out
  integer(kind=c_size_t) :: c_length
  type(c_ptr), target :: c_out
  c_length = generic_array_get_1darray(x, index, "uint", 8 * 8, c_loc(c_out))
  call c_f_pointer(c_out, out, [c_length])
end function generic_array_get_1darray_unsigned8
! Get 1darray real
function generic_array_get_1darray_real4(x, index) result(out)
  implicit none
  type(ygggeneric) :: x
  integer, intent(in) :: index
  real(kind=4), dimension(:), pointer :: out
  integer(kind=c_size_t) :: c_length
  type(c_ptr), target :: c_out
  c_length = generic_array_get_1darray(x, index, "float", 8 * 4, c_loc(c_out))
  call c_f_pointer(c_out, out, [c_length])
end function generic_array_get_1darray_real4
function generic_array_get_1darray_real8(x, index) result(out)
  implicit none
  type(ygggeneric) :: x
  integer, intent(in) :: index
  real(kind=8), dimension(:), pointer :: out
  integer(kind=c_size_t) :: c_length
  type(c_ptr), target :: c_out
  c_length = generic_array_get_1darray(x, index, "float", 8 * 8, c_loc(c_out))
  call c_f_pointer(c_out, out, [c_length])
end function generic_array_get_1darray_real8
! Get 1darray complex
function generic_array_get_1darray_complex4(x, index) result(out)
  implicit none
  type(ygggeneric) :: x
  integer, intent(in) :: index
  complex(kind=4), dimension(:), pointer :: out
  integer(kind=c_size_t) :: c_length
  type(c_ptr), target :: c_out
  c_length = generic_array_get_1darray(x, index, "complex", 8 * 4, c_loc(c_out))
  call c_f_pointer(c_out, out, [c_length])
end function generic_array_get_1darray_complex4
function generic_array_get_1darray_complex8(x, index) result(out)
  implicit none
  type(ygggeneric) :: x
  integer, intent(in) :: index
  complex(kind=8), dimension(:), pointer :: out
  integer(kind=c_size_t) :: c_length
  type(c_ptr), target :: c_out
  c_length = generic_array_get_1darray(x, index, "complex", 8 * 8, c_loc(c_out))
  call c_f_pointer(c_out, out, [c_length])
end function generic_array_get_1darray_complex8
! Get 1darray string
function generic_array_get_1darray_bytes(x, index) result(out)
  implicit none
  type(ygggeneric) :: x
  integer, intent(in) :: index
  character(len=:), dimension(:), pointer :: out
  character, dimension(:), pointer :: temp
  type(c_ptr), target :: c_out
  integer(kind=c_size_t) :: c_length, i
  integer :: nbytes, precision, j
  c_length = generic_array_get_1darray(x, index, "bytes", 0, c_loc(c_out))
  nbytes = generic_array_get_item_nbytes(x, index)
  precision = nbytes/int(c_length, kind=4)
  call c_f_pointer(c_out, temp, [nbytes])
  allocate(character(len=precision) :: out(c_length))
  do i = 1, c_length
     do j = 1, precision
        out(i)(j:j) = temp((i-1)*precision + j)
     end do
  end do
  deallocate(temp)
end function generic_array_get_1darray_bytes
function generic_array_get_1darray_unicode(x, index) result(out)
  implicit none
  type(ygggeneric) :: x
  integer, intent(in) :: index
  character(kind=ucs4, len=:), dimension(:), pointer :: out
  character(kind=ucs4), dimension(:), pointer :: temp
  type(c_ptr), target :: c_out
  integer(kind=c_size_t) :: c_length, i
  integer :: nbytes, precision, j
  c_length = generic_array_get_1darray(x, index, "unicode", 0, c_loc(c_out))
  nbytes = generic_array_get_item_nbytes(x, index)
  precision = nbytes/(int(c_length, kind=4)*4)
  call c_f_pointer(c_out, temp, [nbytes/4])
  allocate(character(kind=ucs4, len=precision) :: out(c_length))
  do i = 1, c_length
     do j = 1, precision
        out(i)(j:j) = temp((i-1)*precision + j)
     end do
  end do
  deallocate(temp)
end function generic_array_get_1darray_unicode

! Get ndarray int
function generic_array_get_ndarray_integer2(x, index) result(out)
  implicit none
  type(ygggeneric) :: x
  integer, intent(in) :: index
  type(integer2_nd) :: out
  type(c_ptr), target :: c_out
  out%shape => generic_array_get_ndarray(x, index, "int", 8 * 2, &
       c_loc(c_out))
  call c_f_pointer(c_out, out%x, out%shape)
end function generic_array_get_ndarray_integer2
function generic_array_get_ndarray_integer4(x, index) result(out)
  implicit none
  type(ygggeneric) :: x
  integer, intent(in) :: index
  type(integer4_nd) :: out
  type(c_ptr), target :: c_out
  out%shape => generic_array_get_ndarray(x, index, "int", 8 * 4, &
       c_loc(c_out))
  call c_f_pointer(c_out, out%x, out%shape)
end function generic_array_get_ndarray_integer4
function generic_array_get_ndarray_integer8(x, index) result(out)
  implicit none
  type(ygggeneric) :: x
  integer, intent(in) :: index
  type(integer8_nd) :: out
  type(c_ptr), target :: c_out
  out%shape => generic_array_get_ndarray(x, index, "int", 8 * 8, &
       c_loc(c_out))
  call c_f_pointer(c_out, out%x, out%shape)
end function generic_array_get_ndarray_integer8
! Get ndarray uint
function generic_array_get_ndarray_unsigned1(x, index) result(out)
  implicit none
  type(ygggeneric) :: x
  integer, intent(in) :: index
  type(unsigned1_nd) :: out
  type(c_ptr), target :: c_out
  out%shape => generic_array_get_ndarray(x, index, "uint", 8 * 1, &
       c_loc(c_out))
  call c_f_pointer(c_out, out%x, out%shape)
end function generic_array_get_ndarray_unsigned1
function generic_array_get_ndarray_unsigned2(x, index) result(out)
  implicit none
  type(ygggeneric) :: x
  integer, intent(in) :: index
  type(unsigned2_nd) :: out
  type(c_ptr), target :: c_out
  out%shape => generic_array_get_ndarray(x, index, "uint", 8 * 2, &
       c_loc(c_out))
  call c_f_pointer(c_out, out%x, out%shape)
end function generic_array_get_ndarray_unsigned2
function generic_array_get_ndarray_unsigned4(x, index) result(out)
  implicit none
  type(ygggeneric) :: x
  integer, intent(in) :: index
  type(unsigned4_nd) :: out
  type(c_ptr), target :: c_out
  out%shape => generic_array_get_ndarray(x, index, "uint", 8 * 4, &
       c_loc(c_out))
  call c_f_pointer(c_out, out%x, out%shape)
end function generic_array_get_ndarray_unsigned4
function generic_array_get_ndarray_unsigned8(x, index) result(out)
  implicit none
  type(ygggeneric) :: x
  integer, intent(in) :: index
  type(unsigned8_nd) :: out
  type(c_ptr), target :: c_out
  out%shape => generic_array_get_ndarray(x, index, "uint", 8 * 8, &
       c_loc(c_out))
  call c_f_pointer(c_out, out%x, out%shape)
end function generic_array_get_ndarray_unsigned8
! Get ndarray real
function generic_array_get_ndarray_real4(x, index) result(out)
  implicit none
  type(ygggeneric) :: x
  integer, intent(in) :: index
  type(real4_nd) :: out
  type(c_ptr), target :: c_out
  out%shape => generic_array_get_ndarray(x, index, "float", 8 * 4, &
       c_loc(c_out))
  call c_f_pointer(c_out, out%x, out%shape)
end function generic_array_get_ndarray_real4
function generic_array_get_ndarray_real8(x, index) result(out)
  implicit none
  type(ygggeneric) :: x
  integer, intent(in) :: index
  type(real8_nd) :: out
  type(c_ptr), target :: c_out
  out%shape => generic_array_get_ndarray(x, index, "float", 8 * 8, &
       c_loc(c_out))
  call c_f_pointer(c_out, out%x, out%shape)
end function generic_array_get_ndarray_real8
! Get ndarray complex
function generic_array_get_ndarray_complex4(x, index) result(out)
  implicit none
  type(ygggeneric) :: x
  integer, intent(in) :: index
  type(complex4_nd) :: out
  type(c_ptr), target :: c_out
  out%shape => generic_array_get_ndarray(x, index, "complex", 8 * 4, &
       c_loc(c_out))
  call c_f_pointer(c_out, out%x, out%shape)
end function generic_array_get_ndarray_complex4
function generic_array_get_ndarray_complex8(x, index) result(out)
  implicit none
  type(ygggeneric) :: x
  integer, intent(in) :: index
  type(complex8_nd) :: out
  type(c_ptr), target :: c_out
  out%shape => generic_array_get_ndarray(x, index, "complex", 8 * 8, &
       c_loc(c_out))
  call c_f_pointer(c_out, out%x, out%shape)
end function generic_array_get_ndarray_complex8
! Get ndarray string
function generic_array_get_ndarray_character(x, index) result(out)
  implicit none
  type(ygggeneric) :: x
  integer, intent(in) :: index
  type(character_nd) :: out
  character, dimension(:), pointer :: temp
  type(c_ptr), target :: c_out
  integer(kind=c_size_t) :: precision, nelements, i, j
  integer(kind=c_int) :: nbytes
  out%shape => generic_array_get_ndarray(x, index, "bytes", 0, &
       c_loc(c_out))
  nbytes = generic_array_get_item_nbytes(x, index)
  nelements = 1
  do i = 1, size(out%shape)
     nelements = nelements * out%shape(i)
  end do
  precision = nbytes/nelements
  call c_f_pointer(c_out, temp, [nbytes])
  allocate(out%x(nelements))
  do i = 1, nelements
     allocate(out%x(i)%x(precision))
     do j = 1, precision
        out%x(i)%x(j) = temp(((i-1)*precision) + j)
     end do
  end do
  deallocate(temp)
end function generic_array_get_ndarray_character
function generic_array_get_ndarray_bytes(x, index) result(out)
  implicit none
  type(ygggeneric) :: x
  integer, intent(in) :: index
  type(bytes_nd) :: out
  character, dimension(:), pointer :: temp
  type(c_ptr), target :: c_out
  integer(kind=c_size_t) :: precision, nelements, i, j
  integer(kind=c_int) :: nbytes
  out%shape => generic_array_get_ndarray(x, index, "bytes", 0, &
       c_loc(c_out))
  nbytes = generic_array_get_item_nbytes(x, index)
  nelements = 1
  do i = 1, size(out%shape)
     nelements = nelements * out%shape(i)
  end do
  precision = nbytes/nelements
  call c_f_pointer(c_out, temp, [nbytes])
  allocate(character(len=precision) :: out%x(nelements))
  do i = 1, nelements
     do j = 1, precision
        out%x(i)(j:j) = temp(((i-1)*precision) + j)
     end do
  end do
  deallocate(temp)
end function generic_array_get_ndarray_bytes
function generic_array_get_ndarray_unicode(x, index) result(out)
  implicit none
  type(ygggeneric) :: x
  integer, intent(in) :: index
  type(unicode_nd) :: out
  character(kind=ucs4), dimension(:), pointer :: temp
  type(c_ptr), target :: c_out
  integer(kind=c_size_t) :: precision, nelements, i, j
  integer(kind=c_int) :: nbytes
  out%shape => generic_array_get_ndarray(x, index, "unicode", 0, &
       c_loc(c_out))
  nbytes = generic_array_get_item_nbytes(x, index)
  nelements = 1
  do i = 1, size(out%shape)
     nelements = nelements * out%shape(i)
  end do
  precision = nbytes/(nelements*4)
  call c_f_pointer(c_out, temp, [nbytes/4])
  allocate(character(len=precision, kind=ucs4) :: out%x(nelements))
  do i = 1, nelements
     do j = 1, precision
        out%x(i)(j:j) = temp(((i-1)*precision) + j)
     end do
  end do
end function generic_array_get_ndarray_unicode


! Set methods
subroutine generic_array_set_boolean(x, index, val)
  implicit none
  type(ygggeneric) :: x
  integer, intent(in) :: index
  logical(kind=1), intent(in), target :: val
  type(c_ptr) :: c_val
  c_val = c_loc(val)
  call generic_array_set_item(x, index, "boolean", c_val)
end subroutine generic_array_set_boolean
subroutine generic_array_set_integer(x, index, val)
  implicit none
  type(ygggeneric) :: x
  integer, intent(in) :: index
  integer(kind=c_int), intent(in), target :: val
  type(c_ptr) :: c_val
  c_val = c_loc(val)
  call generic_array_set_item(x, index, "integer", c_val)
end subroutine generic_array_set_integer
subroutine generic_array_set_null(x, index, val)
  implicit none
  type(ygggeneric) :: x
  integer, intent(in) :: index
  type(yggnull), intent(in) :: val
  type(c_ptr) :: c_val
  c_val = c_null_ptr
  call generic_array_set_item(x, index, "null", c_val)
end subroutine generic_array_set_null
subroutine generic_array_set_number(x, index, val)
  implicit none
  type(ygggeneric) :: x
  integer, intent(in) :: index
  real(kind=8), intent(in), target :: val
  type(c_ptr) :: c_val
  c_val = c_loc(val)
  call generic_array_set_item(x, index, "number", c_val)
end subroutine generic_array_set_number
subroutine generic_array_set_array(x, index, val)
  implicit none
  type(ygggeneric) :: x
  integer, intent(in) :: index
  type(yggarr), intent(in), target :: val
  type(c_ptr) :: c_val
  c_val = c_loc(val)
  call generic_array_set_item(x, index, "array", c_val)
end subroutine generic_array_set_array
subroutine generic_array_set_map(x, index, val)
  implicit none
  type(ygggeneric) :: x
  integer, intent(in) :: index
  type(yggmap), intent(in), target :: val
  type(c_ptr) :: c_val
  c_val = c_loc(val)
  call generic_array_set_item(x, index, "object", c_val)
end subroutine generic_array_set_map
subroutine generic_array_set_ply(x, index, val)
  implicit none
  type(ygggeneric) :: x
  integer, intent(in) :: index
  type(yggply), intent(in), target :: val
  type(c_ptr) :: c_val
  c_val = c_loc(val)
  call generic_array_set_item(x, index, "ply", c_val)
end subroutine generic_array_set_ply
subroutine generic_array_set_obj(x, index, val)
  implicit none
  type(ygggeneric) :: x
  integer, intent(in) :: index
  type(yggobj), intent(in), target :: val
  type(c_ptr) :: c_val
  c_val = c_loc(val)
  call generic_array_set_item(x, index, "obj", c_val)
end subroutine generic_array_set_obj
subroutine generic_array_set_python_class(x, index, val)
  implicit none
  type(ygggeneric) :: x
  integer, intent(in) :: index
  type(yggpython), intent(in), target :: val
  type(c_ptr) :: c_val
  c_val = c_loc(val)
  call generic_array_set_item(x, index, "class", c_val)
end subroutine generic_array_set_python_class
subroutine generic_array_set_python_function(x, index, val)
  implicit none
  type(ygggeneric) :: x
  integer, intent(in) :: index
  type(yggpython), intent(in), target :: val
  type(c_ptr) :: c_val
  c_val = c_loc(val)
  call generic_array_set_item(x, index, "function", c_val)
end subroutine generic_array_set_python_function
subroutine generic_array_set_schema(x, index, val)
  implicit none
  type(ygggeneric) :: x
  integer, intent(in) :: index
  type(yggschema), intent(in), target :: val
  type(c_ptr) :: c_val
  c_val = c_loc(val)
  call generic_array_set_item(x, index, "schema", c_val)
end subroutine generic_array_set_schema
subroutine generic_array_set_any(x, index, val)
  implicit none
  type(ygggeneric) :: x
  integer, intent(in) :: index
  type(ygggeneric), intent(in), target :: val
  type(c_ptr) :: c_val
  c_val = c_loc(val)
  call generic_array_set_item(x, index, "any", c_val)
end subroutine generic_array_set_any
! Set scalar int
subroutine generic_array_set_integer2(x, index, val, units_in)
  implicit none
  type(ygggeneric) :: x
  integer, intent(in) :: index
  integer(kind=2), intent(in), target :: val
  character(len=*), intent(in), optional, target :: units_in
  character(len=:), pointer :: units
  type(c_ptr) :: c_val
  if (present(units_in)) then
     units => units_in
  else
     allocate(character(len=0) :: units)
     units = ""
  end if
  c_val = c_loc(val)
  call generic_array_set_scalar(x, index, c_val, "int", 2 * 8, units)
end subroutine generic_array_set_integer2
subroutine generic_array_set_integer4(x, index, val, units_in)
  implicit none
  type(ygggeneric) :: x
  integer, intent(in) :: index
  integer(kind=4), intent(in), target :: val
  character(len=*), intent(in), optional, target :: units_in
  character(len=:), pointer :: units
  type(c_ptr) :: c_val
  if (present(units_in)) then
     units => units_in
  else
     allocate(character(len=0) :: units)
     units = ""
  end if
  c_val = c_loc(val)
  call generic_array_set_scalar(x, index, c_val, "int", 4 * 8, units)
end subroutine generic_array_set_integer4
subroutine generic_array_set_integer8(x, index, val, units_in)
  implicit none
  type(ygggeneric) :: x
  integer, intent(in) :: index
  integer(kind=8), intent(in), target :: val
  character(len=*), intent(in), optional, target :: units_in
  character(len=:), pointer :: units
  type(c_ptr) :: c_val
  if (present(units_in)) then
     units => units_in
  else
     allocate(character(len=0) :: units)
     units = ""
  end if
  c_val = c_loc(val)
  call generic_array_set_scalar(x, index, c_val, "int", 8 * 8, units)
end subroutine generic_array_set_integer8
! Set scalar uint
subroutine generic_array_set_unsigned1(x, index, val, units_in)
  implicit none
  type(ygggeneric) :: x
  integer, intent(in) :: index
  type(ygguint1), intent(in), target :: val
  character(len=*), intent(in), optional, target :: units_in
  character(len=:), pointer :: units
  type(c_ptr) :: c_val
  if (present(units_in)) then
     units => units_in
  else
     allocate(character(len=0) :: units)
     units = ""
  end if
  c_val = c_loc(val%x)
  call generic_array_set_scalar(x, index, c_val, "uint", 1 * 8, units)
end subroutine generic_array_set_unsigned1
subroutine generic_array_set_unsigned2(x, index, val, units_in)
  implicit none
  type(ygggeneric) :: x
  integer, intent(in) :: index
  type(ygguint2), intent(in), target :: val
  character(len=*), intent(in), optional, target :: units_in
  character(len=:), pointer :: units
  type(c_ptr) :: c_val
  if (present(units_in)) then
     units => units_in
  else
     allocate(character(len=0) :: units)
     units = ""
  end if
  c_val = c_loc(val%x)
  call generic_array_set_scalar(x, index, c_val, "uint", 2 * 8, units)
end subroutine generic_array_set_unsigned2
subroutine generic_array_set_unsigned4(x, index, val, units_in)
  implicit none
  type(ygggeneric) :: x
  integer, intent(in) :: index
  type(ygguint4), intent(in), target :: val
  character(len=*), intent(in), optional, target :: units_in
  character(len=:), pointer :: units
  type(c_ptr) :: c_val
  if (present(units_in)) then
     units => units_in
  else
     allocate(character(len=0) :: units)
     units = ""
  end if
  c_val = c_loc(val%x)
  call generic_array_set_scalar(x, index, c_val, "uint", 4 * 8, units)
end subroutine generic_array_set_unsigned4
subroutine generic_array_set_unsigned8(x, index, val, units_in)
  implicit none
  type(ygggeneric) :: x
  integer, intent(in) :: index
  type(ygguint8), intent(in), target :: val
  character(len=*), intent(in), optional, target :: units_in
  character(len=:), pointer :: units
  type(c_ptr) :: c_val
  if (present(units_in)) then
     units => units_in
  else
     allocate(character(len=0) :: units)
     units = ""
  end if
  c_val = c_loc(val%x)
  call generic_array_set_scalar(x, index, c_val, "uint", 8 * 8, units)
end subroutine generic_array_set_unsigned8
! Set scalar real
subroutine generic_array_set_real4(x, index, val, units_in)
  implicit none
  type(ygggeneric) :: x
  integer, intent(in) :: index
  real(kind=4), intent(in), target :: val
  character(len=*), intent(in), optional, target :: units_in
  character(len=:), pointer :: units
  type(c_ptr) :: c_val
  if (present(units_in)) then
     units => units_in
  else
     allocate(character(len=0) :: units)
     units = ""
  end if
  c_val = c_loc(val)
  call generic_array_set_scalar(x, index, c_val, "float", 4 * 8, units)
end subroutine generic_array_set_real4
subroutine generic_array_set_real8(x, index, val, units_in)
  implicit none
  type(ygggeneric) :: x
  integer, intent(in) :: index
  real(kind=8), intent(in), target :: val
  character(len=*), intent(in), optional, target :: units_in
  character(len=:), pointer :: units
  type(c_ptr) :: c_val
  if (present(units_in)) then
     units => units_in
  else
     allocate(character(len=0) :: units)
     units = ""
  end if
  c_val = c_loc(val)
  call generic_array_set_scalar(x, index, c_val, "float", 8 * 8, units)
end subroutine generic_array_set_real8
! Set scalar complex
subroutine generic_array_set_complex4(x, index, val, units_in)
  implicit none
  type(ygggeneric) :: x
  integer, intent(in) :: index
  complex(kind=4), intent(in), target :: val
  character(len=*), intent(in), optional, target :: units_in
  character(len=:), pointer :: units
  type(c_ptr) :: c_val
  if (present(units_in)) then
     units => units_in
  else
     allocate(character(len=0) :: units)
     units = ""
  end if
  c_val = c_loc(val)
  call generic_array_set_scalar(x, index, c_val, "complex", 4 * 8, units)
end subroutine generic_array_set_complex4
subroutine generic_array_set_complex8(x, index, val, units_in)
  implicit none
  type(ygggeneric) :: x
  integer, intent(in) :: index
  complex(kind=8), intent(in), target :: val
  character(len=*), intent(in), optional, target :: units_in
  character(len=:), pointer :: units
  type(c_ptr) :: c_val
  if (present(units_in)) then
     units => units_in
  else
     allocate(character(len=0) :: units)
     units = ""
  end if
  c_val = c_loc(val)
  call generic_array_set_scalar(x, index, c_val, "complex", 8 * 8, units)
end subroutine generic_array_set_complex8
! Set scalar string
subroutine generic_array_set_bytes(x, index, val, units_in)
  implicit none
  type(ygggeneric) :: x
  integer, intent(in) :: index
  character(len=*), intent(in), target :: val
  character(len=*), intent(in), optional, target :: units_in
  character(len=:), pointer :: units
  type(c_ptr) :: c_val
  if (present(units_in)) then
     units => units_in
  else
     allocate(character(len=0) :: units)
     units = ""
  end if
  c_val = c_loc(val)
  ! TODO: Convert to 1d array of characters?
  call generic_array_set_scalar(x, index, c_val, "bytes", 0, units)
end subroutine generic_array_set_bytes
subroutine generic_array_set_unicode(x, index, val, units_in)
  implicit none
  type(ygggeneric) :: x
  integer, intent(in) :: index
  character(kind=ucs4, len=*), intent(in), target :: val
  character(len=*), intent(in), optional, target :: units_in
  character(len=:), pointer :: units
  type(c_ptr) :: c_val
  if (present(units_in)) then
     units => units_in
  else
     allocate(character(len=0) :: units)
     units = ""
  end if
  c_val = c_loc(val)
  ! TODO: Convert to 1d array of characters?
  call generic_array_set_scalar(x, index, c_val, "unicode", 0, units)
end subroutine generic_array_set_unicode

! Set 1darray int
subroutine generic_array_set_1darray_integer2(x, index, val, units_in)
  implicit none
  type(ygggeneric) :: x
  integer, intent(in) :: index
  integer(kind=2), dimension(:), intent(in), target :: val
  character(len=*), intent(in), optional, target :: units_in
  character(len=:), pointer :: units
  type(c_ptr) :: c_val
  if (present(units_in)) then
     units => units_in
  else
     allocate(character(len=0) :: units)
     units = ""
  end if
  c_val = c_loc(val(1))
  call generic_array_set_1darray(x, index, c_val, "int", 2 * 8, &
       size(val), units)
end subroutine generic_array_set_1darray_integer2
subroutine generic_array_set_1darray_integer4(x, index, val, units_in)
  implicit none
  type(ygggeneric) :: x
  integer, intent(in) :: index
  integer(kind=4), dimension(:), intent(in), target :: val
  character(len=*), intent(in), optional, target :: units_in
  character(len=:), pointer :: units
  type(c_ptr) :: c_val
  if (present(units_in)) then
     units => units_in
  else
     allocate(character(len=0) :: units)
     units = ""
  end if
  c_val = c_loc(val(1))
  call generic_array_set_1darray(x, index, c_val, "int", 4 * 8, &
       size(val), units)
end subroutine generic_array_set_1darray_integer4
subroutine generic_array_set_1darray_integer8(x, index, val, units_in)
  implicit none
  type(ygggeneric) :: x
  integer, intent(in) :: index
  integer(kind=8), dimension(:), intent(in), target :: val
  character(len=*), intent(in), optional, target :: units_in
  character(len=:), pointer :: units
  type(c_ptr) :: c_val
  if (present(units_in)) then
     units => units_in
  else
     allocate(character(len=0) :: units)
     units = ""
  end if
  c_val = c_loc(val(1))
  call generic_array_set_1darray(x, index, c_val, "int", 8 * 8, &
       size(val), units)
end subroutine generic_array_set_1darray_integer8
! Set 1darray uint
subroutine generic_array_set_1darray_unsigned1(x, index, val, units_in)
  implicit none
  type(ygggeneric) :: x
  integer, intent(in) :: index
  type(ygguint1), dimension(:), intent(in), target :: val
  character(len=*), intent(in), optional, target :: units_in
  character(len=:), pointer :: units
  type(c_ptr) :: c_val
  if (present(units_in)) then
     units => units_in
  else
     allocate(character(len=0) :: units)
     units = ""
  end if
  c_val = c_loc(val(1))
  call generic_array_set_1darray(x, index, c_val, "uint", 1 * 8, &
       size(val), units)
end subroutine generic_array_set_1darray_unsigned1
subroutine generic_array_set_1darray_unsigned2(x, index, val, units_in)
  implicit none
  type(ygggeneric) :: x
  integer, intent(in) :: index
  type(ygguint2), dimension(:), intent(in), target :: val
  character(len=*), intent(in), optional, target :: units_in
  character(len=:), pointer :: units
  type(c_ptr) :: c_val
  if (present(units_in)) then
     units => units_in
  else
     allocate(character(len=0) :: units)
     units = ""
  end if
  c_val = c_loc(val(1))
  call generic_array_set_1darray(x, index, c_val, "uint", 2 * 8, &
       size(val), units)
end subroutine generic_array_set_1darray_unsigned2
subroutine generic_array_set_1darray_unsigned4(x, index, val, units_in)
  implicit none
  type(ygggeneric) :: x
  integer, intent(in) :: index
  type(ygguint4), dimension(:), intent(in), target :: val
  character(len=*), intent(in), optional, target :: units_in
  character(len=:), pointer :: units
  type(c_ptr) :: c_val
  if (present(units_in)) then
     units => units_in
  else
     allocate(character(len=0) :: units)
     units = ""
  end if
  c_val = c_loc(val(1))
  call generic_array_set_1darray(x, index, c_val, "uint", 4 * 8, &
       size(val), units)
end subroutine generic_array_set_1darray_unsigned4
subroutine generic_array_set_1darray_unsigned8(x, index, val, units_in)
  implicit none
  type(ygggeneric) :: x
  integer, intent(in) :: index
  type(ygguint8), dimension(:), intent(in), target :: val
  character(len=*), intent(in), optional, target :: units_in
  character(len=:), pointer :: units
  type(c_ptr) :: c_val
  if (present(units_in)) then
     units => units_in
  else
     allocate(character(len=0) :: units)
     units = ""
  end if
  c_val = c_loc(val(1))
  call generic_array_set_1darray(x, index, c_val, "uint", 8 * 8, &
       size(val), units)
end subroutine generic_array_set_1darray_unsigned8
! Set 1darray real
subroutine generic_array_set_1darray_real4(x, index, val, units_in)
  implicit none
  type(ygggeneric) :: x
  integer, intent(in) :: index
  real(kind=4), dimension(:), intent(in), target :: val
  character(len=*), intent(in), optional, target :: units_in
  character(len=:), pointer :: units
  type(c_ptr) :: c_val
  if (present(units_in)) then
     units => units_in
  else
     allocate(character(len=0) :: units)
     units = ""
  end if
  c_val = c_loc(val(1))
  call generic_array_set_1darray(x, index, c_val, "float", 4 * 8, &
       size(val), units)
end subroutine generic_array_set_1darray_real4
subroutine generic_array_set_1darray_real8(x, index, val, units_in)
  implicit none
  type(ygggeneric) :: x
  integer, intent(in) :: index
  real(kind=8), dimension(:), intent(in), target :: val
  character(len=*), intent(in), optional, target :: units_in
  character(len=:), pointer :: units
  type(c_ptr) :: c_val
  if (present(units_in)) then
     units => units_in
  else
     allocate(character(len=0) :: units)
     units = ""
  end if
  c_val = c_loc(val(1))
  call generic_array_set_1darray(x, index, c_val, "float", 8 * 8, &
       size(val), units)
end subroutine generic_array_set_1darray_real8
! Set 1darray complex
subroutine generic_array_set_1darray_complex4(x, index, val, units_in)
  implicit none
  type(ygggeneric) :: x
  integer, intent(in) :: index
  complex(kind=4), dimension(:), intent(in), target :: val
  character(len=*), intent(in), optional, target :: units_in
  character(len=:), pointer :: units
  type(c_ptr) :: c_val
  if (present(units_in)) then
     units => units_in
  else
     allocate(character(len=0) :: units)
     units = ""
  end if
  c_val = c_loc(val(1))
  call generic_array_set_1darray(x, index, c_val, "complex", 4 * 8, &
       size(val), units)
end subroutine generic_array_set_1darray_complex4
subroutine generic_array_set_1darray_complex8(x, index, val, units_in)
  implicit none
  type(ygggeneric) :: x
  integer, intent(in) :: index
  complex(kind=8), dimension(:), intent(in), target :: val
  character(len=*), intent(in), optional, target :: units_in
  character(len=:), pointer :: units
  type(c_ptr) :: c_val
  if (present(units_in)) then
     units => units_in
  else
     allocate(character(len=0) :: units)
     units = ""
  end if
  c_val = c_loc(val(1))
  call generic_array_set_1darray(x, index, c_val, "complex", 8 * 8, &
       size(val), units)
end subroutine generic_array_set_1darray_complex8
! Set 1darray string
subroutine generic_array_set_1darray_bytes(x, index, val, units_in)
  implicit none
  type(ygggeneric) :: x
  integer, intent(in) :: index
  character(len=*), dimension(:), intent(in), target :: val
  character(len=*), intent(in), optional, target :: units_in
  character(len=:), pointer :: units
  type(c_ptr) :: c_val
  if (present(units_in)) then
     units => units_in
  else
     allocate(character(len=0) :: units)
     units = ""
  end if
  c_val = c_loc(val(1))
  ! TODO: Convert to 1d array of characters?
  call generic_array_set_1darray(x, index, c_val, "bytes", 0, &
       size(val), units)
end subroutine generic_array_set_1darray_bytes
subroutine generic_array_set_1darray_unicode(x, index, val, units_in)
  implicit none
  type(ygggeneric) :: x
  integer, intent(in) :: index
  character(kind=ucs4, len=*), dimension(:), intent(in), target :: val
  character(len=*), intent(in), optional, target :: units_in
  character(len=:), pointer :: units
  type(c_ptr) :: c_val
  if (present(units_in)) then
     units => units_in
  else
     allocate(character(len=0) :: units)
     units = ""
  end if
  c_val = c_loc(val(1))
  ! TODO: Convert to 1d array of characters?
  call generic_array_set_1darray(x, index, c_val, "unicode", 0, &
       size(val), units)
end subroutine generic_array_set_1darray_unicode

! Set ndarray int
subroutine generic_array_set_ndarray_integer2(x, index, val, units_in)
  implicit none
  type(ygggeneric) :: x
  integer, intent(in) :: index
  type(integer2_nd), intent(in) :: val
  character(len=*), intent(in), optional, target :: units_in
  character(len=:), pointer :: units
  type(c_ptr) :: c_val
  if (present(units_in)) then
     units => units_in
  else
     allocate(character(len=0) :: units)
     units = ""
  end if
  c_val = c_loc(val%x(1))
  call generic_array_set_ndarray(x, index, c_val, "int", 2 * 8, &
       val%shape, units)
end subroutine generic_array_set_ndarray_integer2
subroutine generic_array_set_ndarray_integer4(x, index, val, units_in)
  implicit none
  type(ygggeneric) :: x
  integer, intent(in) :: index
  type(integer4_nd), intent(in) :: val
  character(len=*), intent(in), optional, target :: units_in
  character(len=:), pointer :: units
  type(c_ptr) :: c_val
  if (present(units_in)) then
     units => units_in
  else
     allocate(character(len=0) :: units)
     units = ""
  end if
  c_val = c_loc(val%x(1))
  call generic_array_set_ndarray(x, index, c_val, "int", 4 * 8, &
       val%shape, units)
end subroutine generic_array_set_ndarray_integer4
subroutine generic_array_set_ndarray_integer8(x, index, val, units_in)
  implicit none
  type(ygggeneric) :: x
  integer, intent(in) :: index
  type(integer8_nd), intent(in) :: val
  character(len=*), intent(in), optional, target :: units_in
  character(len=:), pointer :: units
  type(c_ptr) :: c_val
  if (present(units_in)) then
     units => units_in
  else
     allocate(character(len=0) :: units)
     units = ""
  end if
  c_val = c_loc(val%x(1))
  call generic_array_set_ndarray(x, index, c_val, "int", 8 * 8, &
       val%shape, units)
end subroutine generic_array_set_ndarray_integer8
! Get ndarray uint
subroutine generic_array_set_ndarray_unsigned1(x, index, val, units_in)
  implicit none
  type(ygggeneric) :: x
  integer, intent(in) :: index
  type(unsigned1_nd), intent(in) :: val
  character(len=*), intent(in), optional, target :: units_in
  character(len=:), pointer :: units
  type(c_ptr) :: c_val
  if (present(units_in)) then
     units => units_in
  else
     allocate(character(len=0) :: units)
     units = ""
  end if
  c_val = c_loc(val%x(1))
  call generic_array_set_ndarray(x, index, c_val, "uint", 1 * 8, &
       val%shape, units)
end subroutine generic_array_set_ndarray_unsigned1
subroutine generic_array_set_ndarray_unsigned2(x, index, val, units_in)
  implicit none
  type(ygggeneric) :: x
  integer, intent(in) :: index
  type(unsigned2_nd), intent(in) :: val
  character(len=*), intent(in), optional, target :: units_in
  character(len=:), pointer :: units
  type(c_ptr) :: c_val
  if (present(units_in)) then
     units => units_in
  else
     allocate(character(len=0) :: units)
     units = ""
  end if
  c_val = c_loc(val%x(1))
  call generic_array_set_ndarray(x, index, c_val, "uint", 2 * 8, &
       val%shape, units)
end subroutine generic_array_set_ndarray_unsigned2
subroutine generic_array_set_ndarray_unsigned4(x, index, val, units_in)
  implicit none
  type(ygggeneric) :: x
  integer, intent(in) :: index
  type(unsigned4_nd), intent(in) :: val
  character(len=*), intent(in), optional, target :: units_in
  character(len=:), pointer :: units
  type(c_ptr) :: c_val
  if (present(units_in)) then
     units => units_in
  else
     allocate(character(len=0) :: units)
     units = ""
  end if
  c_val = c_loc(val%x(1))
  call generic_array_set_ndarray(x, index, c_val, "uint", 4 * 8, &
       val%shape, units)
end subroutine generic_array_set_ndarray_unsigned4
subroutine generic_array_set_ndarray_unsigned8(x, index, val, units_in)
  implicit none
  type(ygggeneric) :: x
  integer, intent(in) :: index
  type(unsigned8_nd), intent(in) :: val
  character(len=*), intent(in), optional, target :: units_in
  character(len=:), pointer :: units
  type(c_ptr) :: c_val
  if (present(units_in)) then
     units => units_in
  else
     allocate(character(len=0) :: units)
     units = ""
  end if
  c_val = c_loc(val%x(1))
  call generic_array_set_ndarray(x, index, c_val, "uint", 8 * 8, &
       val%shape, units)
end subroutine generic_array_set_ndarray_unsigned8
! Set ndarray real
subroutine generic_array_set_ndarray_real4(x, index, val, units_in)
  implicit none
  type(ygggeneric) :: x
  integer, intent(in) :: index
  type(real4_nd), intent(in) :: val
  character(len=*), intent(in), optional, target :: units_in
  character(len=:), pointer :: units
  type(c_ptr) :: c_val
  if (present(units_in)) then
     units => units_in
  else
     allocate(character(len=0) :: units)
     units = ""
  end if
  c_val = c_loc(val%x(1))
  call generic_array_set_ndarray(x, index, c_val, "float", 4 * 8, &
       val%shape, units)
end subroutine generic_array_set_ndarray_real4
subroutine generic_array_set_ndarray_real8(x, index, val, units_in)
  implicit none
  type(ygggeneric) :: x
  integer, intent(in) :: index
  type(real8_nd), intent(in) :: val
  character(len=*), intent(in), optional, target :: units_in
  character(len=:), pointer :: units
  type(c_ptr) :: c_val
  if (present(units_in)) then
     units => units_in
  else
     allocate(character(len=0) :: units)
     units = ""
  end if
  c_val = c_loc(val%x(1))
  call generic_array_set_ndarray(x, index, c_val, "float", 8 * 8, &
       val%shape, units)
end subroutine generic_array_set_ndarray_real8
! Set ndarray complex
subroutine generic_array_set_ndarray_complex4(x, index, val, units_in)
  implicit none
  type(ygggeneric) :: x
  integer, intent(in) :: index
  type(complex4_nd), intent(in) :: val
  character(len=*), intent(in), optional, target :: units_in
  character(len=:), pointer :: units
  type(c_ptr) :: c_val
  if (present(units_in)) then
     units => units_in
  else
     allocate(character(len=0) :: units)
     units = ""
  end if
  c_val = c_loc(val%x(1))
  call generic_array_set_ndarray(x, index, c_val, "complex", 4 * 8, &
       val%shape, units)
end subroutine generic_array_set_ndarray_complex4
subroutine generic_array_set_ndarray_complex8(x, index, val, units_in)
  implicit none
  type(ygggeneric) :: x
  integer, intent(in) :: index
  type(complex8_nd), intent(in) :: val
  character(len=*), intent(in), optional, target :: units_in
  character(len=:), pointer :: units
  type(c_ptr) :: c_val
  if (present(units_in)) then
     units => units_in
  else
     allocate(character(len=0) :: units)
     units = ""
  end if
  c_val = c_loc(val%x(1))
  call generic_array_set_ndarray(x, index, c_val, "complex", 8 * 8, &
       val%shape, units)
end subroutine generic_array_set_ndarray_complex8
! Set ndarray string
subroutine generic_array_set_ndarray_character(x, index, val, units_in)
  implicit none
  type(ygggeneric) :: x
  integer, intent(in) :: index
  type(character_nd), intent(in) :: val
  character(len=*), intent(in), optional, target :: units_in
  character(len=:), pointer :: units
  type(c_ptr) :: c_val
  if (present(units_in)) then
     units => units_in
  else
     allocate(character(len=0) :: units)
     units = ""
  end if
  c_val = c_loc(val%x(1))
  call generic_array_set_ndarray(x, index, c_val, "bytes", 0, &
       val%shape, units)
end subroutine generic_array_set_ndarray_character
subroutine generic_array_set_ndarray_bytes(x, index, val, units_in)
  implicit none
  type(ygggeneric) :: x
  integer, intent(in) :: index
  type(bytes_nd), intent(in) :: val
  character(len=*), intent(in), optional, target :: units_in
  character(len=:), pointer :: units
  type(c_ptr) :: c_val
  if (present(units_in)) then
     units => units_in
  else
     allocate(character(len=0) :: units)
     units = ""
  end if
  c_val = c_loc(val%x)
  call generic_array_set_ndarray(x, index, c_val, "bytes", 0, &
       val%shape, units)
end subroutine generic_array_set_ndarray_bytes
subroutine generic_array_set_ndarray_unicode(x, index, val, units_in)
  implicit none
  type(ygggeneric) :: x
  integer, intent(in) :: index
  type(unicode_nd), intent(in) :: val
  character(len=*), intent(in), optional, target :: units_in
  character(len=:), pointer :: units
  type(c_ptr) :: c_val
  if (present(units_in)) then
     units => units_in
  else
     allocate(character(len=0) :: units)
     units = ""
  end if
  c_val = c_loc(val%x)
  call generic_array_set_ndarray(x, index, c_val, "unicode", 0, &
       val%shape, units)
end subroutine generic_array_set_ndarray_unicode
