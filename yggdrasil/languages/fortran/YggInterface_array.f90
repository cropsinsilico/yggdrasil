! Interface for getting/setting generic array elements
! Get methods
subroutine generic_array_get_generic(x, index, out)
  implicit none
  type(ygggeneric) :: x
  integer, intent(in) :: index
  type(ygggeneric), pointer, intent(out) :: out
  integer(kind=c_int) :: flag
  flag = get_generic_array(x, int(index, c_size_t), out)
  if (flag.ne.0) then
     stop "generic_array_get_generic: Error extracting generic object."
  end if
end subroutine generic_array_get_generic
subroutine generic_array_get_boolean(x, index, out)
  implicit none
  type(ygggeneric) :: x
  integer, intent(in) :: index
  logical(kind=1), pointer, intent(out) :: out
  type(c_ptr) :: c_out
  c_out = generic_array_get_item(x, index, "boolean")
  call c_f_pointer(c_out, out)
end subroutine generic_array_get_boolean
subroutine generic_array_get_integer(x, index, out)
  implicit none
  type(ygggeneric) :: x
  integer, intent(in) :: index
  integer(kind=c_int), pointer, intent(out) :: out
  type(c_ptr) :: c_out
  c_out = generic_array_get_item(x, index, "integer")
  call c_f_pointer(c_out, out)
end subroutine generic_array_get_integer
subroutine generic_array_get_null(x, index, out)
  implicit none
  type(ygggeneric) :: x
  integer, intent(in) :: index
  type(yggnull) :: out
  type(c_ptr) :: c_out
  c_out = generic_array_get_item(x, index, "null")
  out%ptr = c_null_ptr
  ! call c_f_pointer(c_out%ptr, out)
end subroutine generic_array_get_null
subroutine generic_array_get_number(x, index, out)
  implicit none
  type(ygggeneric) :: x
  integer, intent(in) :: index
  real(kind=8), pointer, intent(out) :: out
  type(c_ptr) :: c_out
  c_out = generic_array_get_item(x, index, "number")
  call c_f_pointer(c_out, out)
end subroutine generic_array_get_number
subroutine generic_array_get_string(x, index, out)
  implicit none
  type(ygggeneric) :: x
  integer, intent(in) :: index
  character(len=:, kind=c_char), pointer, intent(out) :: out
  type(c_ptr) :: c_out
  c_out = generic_array_get_item(x, index, "string")
  call c_f_pointer(c_out, out)
end subroutine generic_array_get_string
subroutine generic_array_get_map(x, index, out)
  implicit none
  type(ygggeneric) :: x
  integer, intent(in) :: index
  type(yggmap), pointer, intent(out) :: out
  allocate(out)
  out = yggmap(init_generic())
  out%obj = generic_array_get_item(x, index, "object")
end subroutine generic_array_get_map
subroutine generic_array_get_array(x, index, out)
  implicit none
  type(ygggeneric) :: x
  integer, intent(in) :: index
  type(yggarr), pointer, intent(out) :: out
  allocate(out)
  out = yggarr(init_generic())
  out%obj = generic_array_get_item(x, index, "array")
end subroutine generic_array_get_array
subroutine generic_array_get_ply(x, index, out)
  implicit none
  type(ygggeneric) :: x
  integer, intent(in) :: index
  type(c_ptr) :: c_out
  type(yggply), pointer, intent(out) :: out
  integer(kind=c_int) :: copy
  allocate(out)
  out = init_ply()
  ! this returns a copy, is there a way to get a reference?
  c_out = generic_array_get_item(x, index, "ply")
  copy = 0
  call set_ply(out, c_out, copy)
end subroutine generic_array_get_ply
subroutine generic_array_get_obj(x, index, out)
  implicit none
  type(ygggeneric) :: x
  integer, intent(in) :: index
  type(c_ptr) :: c_out
  type(yggobj), pointer, intent(out) :: out
  integer(kind=c_int) :: copy
  allocate(out)
  out = init_obj()
  ! this returns a copy, is there a way to get a reference?
  c_out = generic_array_get_item(x, index, "obj")
  copy = 0
  call set_obj(out, c_out, copy)
end subroutine generic_array_get_obj
subroutine generic_array_get_python_class(x, index, out)
  implicit none
  type(ygggeneric) :: x
  integer, intent(in) :: index
  type(yggpython), pointer, intent(out) :: out
  allocate(out)
  out = yggpython(init_python())
  ! this returns a copy, is there a way to get a reference?
  out%obj = generic_array_get_item(x, index, "class")
end subroutine generic_array_get_python_class
subroutine generic_array_get_python_function(x, index, out)
  implicit none
  type(ygggeneric) :: x
  integer, intent(in) :: index
  type(yggpython), pointer, intent(out) :: out
  allocate(out)
  out = yggpython(init_python())
  ! this returns a copy, is there a way to get a reference?
  out%obj = generic_array_get_item(x, index, "function")
end subroutine generic_array_get_python_function
subroutine generic_array_get_schema(x, index, out)
  implicit none
  type(ygggeneric) :: x
  integer, intent(in) :: index
  type(yggschema), pointer, intent(out) :: out
  allocate(out)
  out = yggschema(init_generic())
  out%obj = generic_array_get_item(x, index, "schema")
end subroutine generic_array_get_schema
subroutine generic_array_get_any(x, index, out)
  implicit none
  type(ygggeneric) :: x
  integer, intent(in) :: index
  type(ygggeneric), pointer, intent(out) :: out
  allocate(out)
  out = init_generic()
  out%obj = generic_array_get_item(x, index, "any")
end subroutine generic_array_get_any
! Get scalar int
subroutine generic_array_get_integer2(x, index, out)
  implicit none
  type(ygggeneric) :: x
  integer, intent(in) :: index
  integer(kind=2), pointer, intent(out) :: out
  type(c_ptr) :: c_out
  c_out = generic_array_get_scalar(x, index, "int", 2)
  call c_f_pointer(c_out, out)
end subroutine generic_array_get_integer2
subroutine generic_array_get_integer4(x, index, out)
  implicit none
  type(ygggeneric) :: x
  integer, intent(in) :: index
  integer(kind=4), pointer, intent(out) :: out
  type(c_ptr) :: c_out
  c_out = generic_array_get_scalar(x, index, "int", 4)
  call c_f_pointer(c_out, out)
end subroutine generic_array_get_integer4
subroutine generic_array_get_integer8(x, index, out)
  implicit none
  type(ygggeneric) :: x
  integer, intent(in) :: index
  integer(kind=8), pointer, intent(out) :: out
  type(c_ptr) :: c_out
  c_out = generic_array_get_scalar(x, index, "int", 8)
  call c_f_pointer(c_out, out)
end subroutine generic_array_get_integer8
! Get scalar uint
subroutine generic_array_get_unsigned1(x, index, out)
  implicit none
  type(ygggeneric) :: x
  integer, intent(in) :: index
  type(ygguint1) :: out
  integer(kind=1), pointer :: temp
  type(c_ptr) :: c_out
  c_out = generic_array_get_scalar(x, index, "uint", 1)
  call c_f_pointer(c_out, temp)
  out%x = temp
  deallocate(temp)
end subroutine generic_array_get_unsigned1
subroutine generic_array_get_unsigned2(x, index, out)
  implicit none
  type(ygggeneric) :: x
  integer, intent(in) :: index
  type(ygguint2) :: out
  integer(kind=2), pointer :: temp
  type(c_ptr) :: c_out
  c_out = generic_array_get_scalar(x, index, "uint", 2)
  call c_f_pointer(c_out, temp)
  out%x = temp
  deallocate(temp)
end subroutine generic_array_get_unsigned2
subroutine generic_array_get_unsigned4(x, index, out)
  implicit none
  type(ygggeneric) :: x
  integer, intent(in) :: index
  type(ygguint4) :: out
  integer(kind=4), pointer :: temp
  type(c_ptr) :: c_out
  c_out = generic_array_get_scalar(x, index, "uint", 4)
  call c_f_pointer(c_out, temp)
  out%x = temp
  deallocate(temp)
end subroutine generic_array_get_unsigned4
subroutine generic_array_get_unsigned8(x, index, out)
  implicit none
  type(ygggeneric) :: x
  integer, intent(in) :: index
  type(ygguint8) :: out
  integer(kind=8), pointer :: temp
  type(c_ptr) :: c_out
  c_out = generic_array_get_scalar(x, index, "uint", 8)
  call c_f_pointer(c_out, temp)
  out%x = temp
  deallocate(temp)
end subroutine generic_array_get_unsigned8
! Get scalar real
subroutine generic_array_get_real4(x, index, out)
  implicit none
  type(ygggeneric) :: x
  integer, intent(in) :: index
  real(kind=4), pointer, intent(out) :: out
  type(c_ptr) :: c_out
  c_out = generic_array_get_scalar(x, index, "float", 4)
  call c_f_pointer(c_out, out)
end subroutine generic_array_get_real4
subroutine generic_array_get_real8(x, index, out)
  implicit none
  type(ygggeneric) :: x
  integer, intent(in) :: index
  real(kind=8), pointer, intent(out) :: out
  type(c_ptr) :: c_out
  c_out = generic_array_get_scalar(x, index, "float", 8)
  call c_f_pointer(c_out, out)
end subroutine generic_array_get_real8
! Get scalar complex
subroutine generic_array_get_complex4(x, index, out)
  implicit none
  type(ygggeneric) :: x
  integer, intent(in) :: index
  complex(kind=4), pointer, intent(out) :: out
  type(c_ptr) :: c_out
  c_out = generic_array_get_scalar(x, index, "complex", 4)
  call c_f_pointer(c_out, out)
end subroutine generic_array_get_complex4
subroutine generic_array_get_complex8(x, index, out)
  implicit none
  type(ygggeneric) :: x
  integer, intent(in) :: index
  complex(kind=8), pointer, intent(out) :: out
  type(c_ptr) :: c_out
  c_out = generic_array_get_scalar(x, index, "complex", 8)
  call c_f_pointer(c_out, out)
end subroutine generic_array_get_complex8
! Get scalar string
subroutine generic_array_get_bytes(x, index, out)
  implicit none
  type(ygggeneric) :: x
  integer, intent(in) :: index
  character(len=:), pointer, intent(out) :: out
  character, dimension(:), pointer :: temp
  type(c_ptr) :: c_out
  integer :: length, i
  c_out = generic_array_get_scalar(x, index, "bytes", 0)
  length = generic_array_get_item_nbytes(x, index, "bytes")
  call c_f_pointer(c_out, temp, [length])
  allocate(character(len=length) :: out)
  do i = 1, length
     out(i:i) = temp(i)
  end do
  deallocate(temp)
end subroutine generic_array_get_bytes
subroutine generic_array_get_unicode(x, index, out)
  implicit none
  type(ygggeneric) :: x
  integer, intent(in) :: index
  character(kind=ucs4, len=:), pointer, intent(out) :: out
  character(kind=ucs4), dimension(:), pointer :: temp
  type(c_ptr) :: c_out
  integer :: length, i
  c_out = generic_array_get_scalar(x, index, "unicode", 0)
  length = generic_array_get_item_nbytes(x, index, "unicode")/4
  call c_f_pointer(c_out, temp, [length])
  allocate(character(kind=ucs4, len=length) :: out)
  do i = 1, length
     out(i:i) = temp(i)
  end do
  deallocate(temp)
end subroutine generic_array_get_unicode

! Get 1darray int
subroutine generic_array_get_1darray_integer2(x, index, out)
  implicit none
  type(ygggeneric) :: x
  integer, intent(in) :: index
  integer(kind=2), dimension(:), intent(out), pointer :: out
  integer(kind=c_size_t) :: c_length
  type(c_ptr), target :: c_out
  type(c_ptr), pointer :: temp
  type(c_ptr) :: c_out_ptr
  c_out = c_null_ptr
  c_out_ptr = c_loc(c_out)
  c_length = generic_array_get_1darray(x, index, "int", 2, c_out_ptr)
  call c_f_pointer(c_out_ptr, temp)
  call c_f_pointer(temp, out, [c_length])
end subroutine generic_array_get_1darray_integer2
subroutine generic_array_get_1darray_integer4(x, index, out)
  implicit none
  type(ygggeneric) :: x
  integer, intent(in) :: index
  integer(kind=4), dimension(:), pointer, intent(out) :: out
  integer(kind=c_size_t) :: c_length
  type(c_ptr), target :: c_out
  type(c_ptr), pointer :: temp
  type(c_ptr) :: c_out_ptr
  c_out = c_null_ptr
  c_out_ptr = c_loc(c_out)
  c_length = generic_array_get_1darray(x, index, "int", 4, c_out_ptr)
  call c_f_pointer(c_out_ptr, temp)
  call c_f_pointer(temp, out, [c_length])
end subroutine generic_array_get_1darray_integer4
subroutine generic_array_get_1darray_integer8(x, index, out)
  implicit none
  type(ygggeneric) :: x
  integer, intent(in) :: index
  integer(kind=8), dimension(:), pointer, intent(out) :: out
  integer(kind=c_size_t) :: c_length
  type(c_ptr), target :: c_out
  type(c_ptr), pointer :: temp
  type(c_ptr) :: c_out_ptr
  c_out = c_null_ptr
  c_out_ptr = c_loc(c_out)
  c_length = generic_array_get_1darray(x, index, "int", 8, c_out_ptr)
  call c_f_pointer(c_out_ptr, temp)
  call c_f_pointer(temp, out, [c_length])
end subroutine generic_array_get_1darray_integer8
! Get 1darray uint
subroutine generic_array_get_1darray_unsigned1(x, index, out)
  implicit none
  type(ygggeneric) :: x
  integer, intent(in) :: index
  type(ygguint1), dimension(:), pointer, intent(out) :: out
  integer(kind=c_size_t) :: c_length
  type(c_ptr), target :: c_out
  type(c_ptr), pointer :: temp
  type(c_ptr) :: c_out_ptr
  c_out = c_null_ptr
  c_out_ptr = c_loc(c_out)
  c_length = generic_array_get_1darray(x, index, "uint", 1, c_out_ptr)
  call c_f_pointer(c_out_ptr, temp)
  call c_f_pointer(temp, out, [c_length])
end subroutine generic_array_get_1darray_unsigned1
subroutine generic_array_get_1darray_unsigned2(x, index, out)
  implicit none
  type(ygggeneric) :: x
  integer, intent(in) :: index
  type(ygguint2), dimension(:), pointer, intent(out) :: out
  integer(kind=c_size_t) :: c_length
  type(c_ptr), target :: c_out
  type(c_ptr), pointer :: temp
  type(c_ptr) :: c_out_ptr
  c_out = c_null_ptr
  c_out_ptr = c_loc(c_out)
  c_length = generic_array_get_1darray(x, index, "uint", 2, c_out_ptr)
  call c_f_pointer(c_out_ptr, temp)
  call c_f_pointer(temp, out, [c_length])
end subroutine generic_array_get_1darray_unsigned2
subroutine generic_array_get_1darray_unsigned4(x, index, out)
  implicit none
  type(ygggeneric) :: x
  integer, intent(in) :: index
  type(ygguint4), dimension(:), pointer, intent(out) :: out
  integer(kind=c_size_t) :: c_length
  type(c_ptr), target :: c_out
  type(c_ptr), pointer :: temp
  type(c_ptr) :: c_out_ptr
  c_out = c_null_ptr
  c_out_ptr = c_loc(c_out)
  c_length = generic_array_get_1darray(x, index, "uint", 4, c_out_ptr)
  call c_f_pointer(c_out_ptr, temp)
  call c_f_pointer(temp, out, [c_length])
end subroutine generic_array_get_1darray_unsigned4
subroutine generic_array_get_1darray_unsigned8(x, index, out)
  implicit none
  type(ygggeneric) :: x
  integer, intent(in) :: index
  type(ygguint8), dimension(:), pointer, intent(out) :: out
  integer(kind=c_size_t) :: c_length
  type(c_ptr), target :: c_out
  type(c_ptr), pointer :: temp
  type(c_ptr) :: c_out_ptr
  c_out = c_null_ptr
  c_out_ptr = c_loc(c_out)
  c_length = generic_array_get_1darray(x, index, "uint", 8, c_out_ptr)
  call c_f_pointer(c_out_ptr, temp)
  call c_f_pointer(temp, out, [c_length])
end subroutine generic_array_get_1darray_unsigned8
! Get 1darray real
subroutine generic_array_get_1darray_real4(x, index, out)
  implicit none
  type(ygggeneric) :: x
  integer, intent(in) :: index
  real(kind=4), dimension(:), pointer, intent(out) :: out
  integer(kind=c_size_t) :: c_length
  type(c_ptr), target :: c_out
  type(c_ptr), pointer :: temp
  type(c_ptr) :: c_out_ptr
  c_out = c_null_ptr
  c_out_ptr = c_loc(c_out)
  c_length = generic_array_get_1darray(x, index, "float", 4, c_out_ptr)
  call c_f_pointer(c_out_ptr, temp)
  call c_f_pointer(temp, out, [c_length])
end subroutine generic_array_get_1darray_real4
subroutine generic_array_get_1darray_real8(x, index, out)
  implicit none
  type(ygggeneric) :: x
  integer, intent(in) :: index
  real(kind=8), dimension(:), intent(out), pointer :: out
  integer(kind=c_size_t) :: c_length
  type(c_ptr), target :: c_out
  type(c_ptr), pointer :: temp
  type(c_ptr) :: c_out_ptr
  c_out = c_null_ptr
  c_out_ptr = c_loc(c_out)
  c_length = generic_array_get_1darray(x, index, "float", 8, c_out_ptr)
  call c_f_pointer(c_out_ptr, temp)
  call c_f_pointer(temp, out, [c_length])
end subroutine generic_array_get_1darray_real8
! Get 1darray complex
subroutine generic_array_get_1darray_complex4(x, index, out)
  implicit none
  type(ygggeneric) :: x
  integer, intent(in) :: index
  complex(kind=4), dimension(:), pointer, intent(out) :: out
  integer(kind=c_size_t) :: c_length
  type(c_ptr), target :: c_out
  type(c_ptr), pointer :: temp
  type(c_ptr) :: c_out_ptr
  c_out = c_null_ptr
  c_out_ptr = c_loc(c_out)
  c_length = generic_array_get_1darray(x, index, "complex", 4, c_out_ptr)
  call c_f_pointer(c_out_ptr, temp)
  call c_f_pointer(temp, out, [c_length])
end subroutine generic_array_get_1darray_complex4
subroutine generic_array_get_1darray_complex8(x, index, out)
  implicit none
  type(ygggeneric) :: x
  integer, intent(in) :: index
  complex(kind=8), dimension(:), pointer, intent(out) :: out
  integer(kind=c_size_t) :: c_length
  type(c_ptr), target :: c_out
  type(c_ptr), pointer :: temp
  type(c_ptr) :: c_out_ptr
  c_out = c_null_ptr
  c_out_ptr = c_loc(c_out)
  c_length = generic_array_get_1darray(x, index, "complex", 8, c_out_ptr)
  call c_f_pointer(c_out_ptr, temp)
  call c_f_pointer(temp, out, [c_length])
end subroutine generic_array_get_1darray_complex8
! Get 1darray string
subroutine generic_array_get_1darray_bytes(x, index, out)
  implicit none
  type(ygggeneric) :: x
  integer, intent(in) :: index
  character(len=:), dimension(:), pointer, intent(out) :: out
  character, dimension(:), pointer :: temp
  type(c_ptr), target :: c_out
  integer(kind=c_size_t) :: c_length, i
  integer :: nbytes, precision, j
  type(c_ptr), pointer :: temp_ptr
  type(c_ptr) :: c_out_ptr
  c_out = c_null_ptr
  c_out_ptr = c_loc(c_out)
  c_length = generic_array_get_1darray(x, index, "bytes", 0, c_out_ptr)
  nbytes = generic_array_get_item_nbytes(x, index, "bytes")
  precision = nbytes/int(c_length, kind=4)
  call c_f_pointer(c_out_ptr, temp_ptr)
  call c_f_pointer(temp_ptr, temp, [nbytes])
  allocate(character(len=precision) :: out(c_length))
  do i = 1, c_length
     do j = 1, precision
        out(i)(j:j) = temp((i-1)*precision + j)
     end do
  end do
  deallocate(temp)
end subroutine generic_array_get_1darray_bytes
subroutine generic_array_get_1darray_unicode(x, index, out)
  implicit none
  type(ygggeneric) :: x
  integer, intent(in) :: index
  character(kind=ucs4, len=:), dimension(:), pointer, intent(out) :: out
  character(kind=ucs4), dimension(:), pointer :: temp
  type(c_ptr), target :: c_out
  integer(kind=c_size_t) :: c_length, i
  integer :: nbytes, precision, j
  type(c_ptr), pointer :: temp_ptr
  type(c_ptr) :: c_out_ptr
  c_out = c_null_ptr
  c_out_ptr = c_loc(c_out)
  c_length = generic_array_get_1darray(x, index, "unicode", 0, c_out_ptr)
  nbytes = generic_array_get_item_nbytes(x, index, "unicode")
  precision = nbytes/(int(c_length, kind=4)*4)
  call c_f_pointer(c_out_ptr, temp_ptr)
  call c_f_pointer(temp_ptr, temp, [nbytes/4])
  allocate(character(kind=ucs4, len=precision) :: out(c_length))
  do i = 1, c_length
     do j = 1, precision
        out(i)(j:j) = temp((i-1)*precision + j)
     end do
  end do
  deallocate(temp)
end subroutine generic_array_get_1darray_unicode

! Get ndarray int
subroutine generic_array_get_ndarray_integer2(x, index, out)
  implicit none
  type(ygggeneric) :: x
  integer, intent(in) :: index
  type(integer2_nd), intent(out) :: out
  type(c_ptr), target :: c_out
  type(c_ptr), pointer :: temp
  type(c_ptr) :: c_out_ptr
  c_out = c_null_ptr
  c_out_ptr = c_loc(c_out)
  out%shape => generic_array_get_ndarray(x, index, "int", 2, &
       c_out_ptr)
  call c_f_pointer(c_out_ptr, temp)
  call c_f_pointer(temp, out%x, out%shape)
end subroutine generic_array_get_ndarray_integer2
subroutine generic_array_get_ndarray_integer4(x, index, out)
  implicit none
  type(ygggeneric) :: x
  integer, intent(in) :: index
  type(integer4_nd), intent(out) :: out
  type(c_ptr), target :: c_out
  type(c_ptr), pointer :: temp
  type(c_ptr) :: c_out_ptr
  c_out = c_null_ptr
  c_out_ptr = c_loc(c_out)
  out%shape => generic_array_get_ndarray(x, index, "int", 4, &
       c_out_ptr)
  call c_f_pointer(c_out_ptr, temp)
  call c_f_pointer(temp, out%x, out%shape)
end subroutine generic_array_get_ndarray_integer4
subroutine generic_array_get_ndarray_integer8(x, index, out)
  implicit none
  type(ygggeneric) :: x
  integer, intent(in) :: index
  type(integer8_nd), intent(out) :: out
  type(c_ptr), target :: c_out
  type(c_ptr), pointer :: temp
  type(c_ptr) :: c_out_ptr
  c_out = c_null_ptr
  c_out_ptr = c_loc(c_out)
  out%shape => generic_array_get_ndarray(x, index, "int", 8, &
       c_out_ptr)
  call c_f_pointer(c_out_ptr, temp)
  call c_f_pointer(temp, out%x, out%shape)
end subroutine generic_array_get_ndarray_integer8
! Get ndarray uint
subroutine generic_array_get_ndarray_unsigned1(x, index, out)
  implicit none
  type(ygggeneric) :: x
  integer, intent(in) :: index
  type(unsigned1_nd), intent(out) :: out
  type(c_ptr), target :: c_out
  type(c_ptr), pointer :: temp
  type(c_ptr) :: c_out_ptr
  c_out = c_null_ptr
  c_out_ptr = c_loc(c_out)
  out%shape => generic_array_get_ndarray(x, index, "uint", 1, &
       c_out_ptr)
  call c_f_pointer(c_out_ptr, temp)
  call c_f_pointer(temp, out%x, out%shape)
end subroutine generic_array_get_ndarray_unsigned1
subroutine generic_array_get_ndarray_unsigned2(x, index, out)
  implicit none
  type(ygggeneric) :: x
  integer, intent(in) :: index
  type(unsigned2_nd), intent(out) :: out
  type(c_ptr), target :: c_out
  type(c_ptr), pointer :: temp
  type(c_ptr) :: c_out_ptr
  c_out = c_null_ptr
  c_out_ptr = c_loc(c_out)
  out%shape => generic_array_get_ndarray(x, index, "uint", 2, &
       c_out_ptr)
  call c_f_pointer(c_out_ptr, temp)
  call c_f_pointer(temp, out%x, out%shape)
end subroutine generic_array_get_ndarray_unsigned2
subroutine generic_array_get_ndarray_unsigned4(x, index, out)
  implicit none
  type(ygggeneric) :: x
  integer, intent(in) :: index
  type(unsigned4_nd), intent(out) :: out
  type(c_ptr), target :: c_out
  type(c_ptr), pointer :: temp
  type(c_ptr) :: c_out_ptr
  c_out = c_null_ptr
  c_out_ptr = c_loc(c_out)
  out%shape => generic_array_get_ndarray(x, index, "uint", 4, &
       c_out_ptr)
  call c_f_pointer(c_out_ptr, temp)
  call c_f_pointer(temp, out%x, out%shape)
end subroutine generic_array_get_ndarray_unsigned4
subroutine generic_array_get_ndarray_unsigned8(x, index, out)
  implicit none
  type(ygggeneric) :: x
  integer, intent(in) :: index
  type(unsigned8_nd), intent(out) :: out
  type(c_ptr), target :: c_out
  type(c_ptr), pointer :: temp
  type(c_ptr) :: c_out_ptr
  c_out = c_null_ptr
  c_out_ptr = c_loc(c_out)
  out%shape => generic_array_get_ndarray(x, index, "uint", 8, &
       c_out_ptr)
  call c_f_pointer(c_out_ptr, temp)
  call c_f_pointer(temp, out%x, out%shape)
end subroutine generic_array_get_ndarray_unsigned8
! Get ndarray real
subroutine generic_array_get_ndarray_real4(x, index, out)
  implicit none
  type(ygggeneric) :: x
  integer, intent(in) :: index
  type(real4_nd), intent(out) :: out
  type(c_ptr), target :: c_out
  type(c_ptr), pointer :: temp
  type(c_ptr) :: c_out_ptr
  c_out = c_null_ptr
  c_out_ptr = c_loc(c_out)
  out%shape => generic_array_get_ndarray(x, index, "float", 4, &
       c_out_ptr)
  call c_f_pointer(c_out_ptr, temp)
  call c_f_pointer(temp, out%x, out%shape)
end subroutine generic_array_get_ndarray_real4
subroutine generic_array_get_ndarray_real8(x, index, out)
  implicit none
  type(ygggeneric) :: x
  integer, intent(in) :: index
  type(real8_nd), intent(out) :: out
  type(c_ptr), target :: c_out
  type(c_ptr), pointer :: temp
  type(c_ptr) :: c_out_ptr
  c_out = c_null_ptr
  c_out_ptr = c_loc(c_out)
  out%shape => generic_array_get_ndarray(x, index, "float", 8, &
       c_out_ptr)
  call c_f_pointer(c_out_ptr, temp)
  call c_f_pointer(temp, out%x, out%shape)
end subroutine generic_array_get_ndarray_real8
! Get ndarray complex
subroutine generic_array_get_ndarray_complex4(x, index, out)
  implicit none
  type(ygggeneric) :: x
  integer, intent(in) :: index
  type(complex4_nd), intent(out) :: out
  type(c_ptr), target :: c_out
  type(c_ptr), pointer :: temp
  type(c_ptr) :: c_out_ptr
  c_out = c_null_ptr
  c_out_ptr = c_loc(c_out)
  out%shape => generic_array_get_ndarray(x, index, "complex", 4, &
       c_out_ptr)
  call c_f_pointer(c_out_ptr, temp)
  call c_f_pointer(temp, out%x, out%shape)
end subroutine generic_array_get_ndarray_complex4
subroutine generic_array_get_ndarray_complex8(x, index, out)
  implicit none
  type(ygggeneric) :: x
  integer, intent(in) :: index
  type(complex8_nd), intent(out) :: out
  type(c_ptr), target :: c_out
  type(c_ptr), pointer :: temp
  type(c_ptr) :: c_out_ptr
  c_out = c_null_ptr
  c_out_ptr = c_loc(c_out)
  out%shape => generic_array_get_ndarray(x, index, "complex", 8, &
       c_out_ptr)
  call c_f_pointer(c_out_ptr, temp)
  call c_f_pointer(temp, out%x, out%shape)
end subroutine generic_array_get_ndarray_complex8
! Get ndarray string
subroutine generic_array_get_ndarray_character(x, index, out)
  implicit none
  type(ygggeneric) :: x
  integer, intent(in) :: index
  type(character_nd), intent(out) :: out
  character, dimension(:), pointer :: temp
  type(c_ptr), target :: c_out
  integer(kind=c_size_t) :: precision, nelements, i, j
  integer(kind=c_int) :: nbytes
  type(c_ptr), pointer :: temp_ptr
  type(c_ptr) :: c_out_ptr
  c_out = c_null_ptr
  c_out_ptr = c_loc(c_out)
  out%shape => generic_array_get_ndarray(x, index, "bytes", 0, &
       c_out_ptr)
  nbytes = generic_array_get_item_nbytes(x, index, "bytes")
  nelements = 1
  do i = 1, size(out%shape)
     nelements = nelements * out%shape(i)
  end do
  precision = nbytes/nelements
  call c_f_pointer(c_out_ptr, temp_ptr)
  call c_f_pointer(temp_ptr, temp, [nbytes])
  allocate(out%x(nelements))
  do i = 1, nelements
     allocate(out%x(i)%x(precision))
     do j = 1, precision
        out%x(i)%x(j) = temp(((i-1)*precision) + j)
     end do
  end do
  deallocate(temp)
end subroutine generic_array_get_ndarray_character
subroutine generic_array_get_ndarray_bytes(x, index, out)
  implicit none
  type(ygggeneric) :: x
  integer, intent(in) :: index
  type(bytes_nd), intent(out) :: out
  character, dimension(:), pointer :: temp
  type(c_ptr), target :: c_out
  integer(kind=c_size_t) :: precision, nelements, i, j
  integer(kind=c_int) :: nbytes
  type(c_ptr), pointer :: temp_ptr
  type(c_ptr) :: c_out_ptr
  c_out = c_null_ptr
  c_out_ptr = c_loc(c_out)
  out%shape => generic_array_get_ndarray(x, index, "bytes", 0, &
       c_out_ptr)
  nbytes = generic_array_get_item_nbytes(x, index, "bytes")
  nelements = 1
  do i = 1, size(out%shape)
     nelements = nelements * out%shape(i)
  end do
  precision = nbytes/nelements
  call c_f_pointer(c_out_ptr, temp_ptr)
  call c_f_pointer(temp_ptr, temp, [nbytes])
  allocate(character(len=precision) :: out%x(nelements))
  do i = 1, nelements
     do j = 1, precision
        out%x(i)(j:j) = temp(((i-1)*precision) + j)
     end do
  end do
  deallocate(temp)
end subroutine generic_array_get_ndarray_bytes
subroutine generic_array_get_ndarray_unicode(x, index, out)
  implicit none
  type(ygggeneric) :: x
  integer, intent(in) :: index
  type(unicode_nd), intent(out) :: out
  character(kind=ucs4), dimension(:), pointer :: temp
  type(c_ptr), target :: c_out
  integer(kind=c_size_t) :: precision, nelements, i, j
  integer(kind=c_int) :: nbytes
  type(c_ptr), pointer :: temp_ptr
  type(c_ptr) :: c_out_ptr
  c_out = c_null_ptr
  c_out_ptr = c_loc(c_out)
  out%shape => generic_array_get_ndarray(x, index, "unicode", 0, &
       c_out_ptr)
  nbytes = generic_array_get_item_nbytes(x, index, "unicode")
  nelements = 1
  do i = 1, size(out%shape)
     nelements = nelements * out%shape(i)
  end do
  precision = nbytes/(nelements*4)
  call c_f_pointer(c_out_ptr, temp_ptr)
  call c_f_pointer(temp_ptr, temp, [nbytes/4])
  allocate(character(len=precision, kind=ucs4) :: out%x(nelements))
  do i = 1, nelements
     do j = 1, precision
        out%x(i)(j:j) = temp(((i-1)*precision) + j)
     end do
  end do
end subroutine generic_array_get_ndarray_unicode


! Set methods
subroutine generic_array_set_generic(x, index, val)
  implicit none
  type(ygggeneric) :: x
  integer, intent(in) :: index
  type(ygggeneric), intent(in) :: val
  integer(kind=c_int) :: flag
  flag = set_generic_array(x, int(index, c_size_t), val)
  if (flag.ne.0) then
     stop "generic_array_get_generic: Error setting generic object."
  end if
end subroutine generic_array_set_generic
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
  c_val = val%ptr
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
  call generic_array_set_scalar(x, index, c_val, "int", 2, units)
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
  call generic_array_set_scalar(x, index, c_val, "int", 4, units)
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
  call generic_array_set_scalar(x, index, c_val, "int", 8, units)
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
  call generic_array_set_scalar(x, index, c_val, "uint", 1, units)
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
  call generic_array_set_scalar(x, index, c_val, "uint", 2, units)
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
  call generic_array_set_scalar(x, index, c_val, "uint", 4, units)
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
  call generic_array_set_scalar(x, index, c_val, "uint", 8, units)
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
  call generic_array_set_scalar(x, index, c_val, "float", 4, units)
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
  call generic_array_set_scalar(x, index, c_val, "float", 8, units)
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
  call generic_array_set_scalar(x, index, c_val, "complex", 4, units)
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
  call generic_array_set_scalar(x, index, c_val, "complex", 8, units)
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
  call generic_array_set_1darray(x, index, c_val, "int", 2, &
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
  call generic_array_set_1darray(x, index, c_val, "int", 4, &
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
  call generic_array_set_1darray(x, index, c_val, "int", 8, &
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
  call generic_array_set_1darray(x, index, c_val, "uint", 1, &
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
  call generic_array_set_1darray(x, index, c_val, "uint", 2, &
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
  call generic_array_set_1darray(x, index, c_val, "uint", 4, &
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
  call generic_array_set_1darray(x, index, c_val, "uint", 8, &
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
  call generic_array_set_1darray(x, index, c_val, "float", 4, &
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
  call generic_array_set_1darray(x, index, c_val, "float", 8, &
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
  call generic_array_set_1darray(x, index, c_val, "complex", 4, &
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
  call generic_array_set_1darray(x, index, c_val, "complex", 8, &
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
  call generic_array_set_ndarray(x, index, c_val, "int", 2, &
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
  call generic_array_set_ndarray(x, index, c_val, "int", 4, &
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
  call generic_array_set_ndarray(x, index, c_val, "int", 8, &
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
  call generic_array_set_ndarray(x, index, c_val, "uint", 1, &
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
  call generic_array_set_ndarray(x, index, c_val, "uint", 2, &
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
  call generic_array_set_ndarray(x, index, c_val, "uint", 4, &
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
  call generic_array_set_ndarray(x, index, c_val, "uint", 8, &
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
  call generic_array_set_ndarray(x, index, c_val, "float", 4, &
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
  call generic_array_set_ndarray(x, index, c_val, "float", 8, &
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
  call generic_array_set_ndarray(x, index, c_val, "complex", 4, &
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
  call generic_array_set_ndarray(x, index, c_val, "complex", 8, &
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
