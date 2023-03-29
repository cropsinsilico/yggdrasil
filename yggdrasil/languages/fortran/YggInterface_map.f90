! Interface for getting/setting generic map elements
! Get methods
subroutine generic_map_get_generic(x, key, out)
  implicit none
  type(ygggeneric), intent(in) :: x
  character(len=*), intent(in) :: key
  type(ygggeneric), pointer, intent(out) :: out
  integer(kind=c_int) :: flag
  flag = get_generic_object(x, key, out)
  if (flag.ne.0) then
     stop "generic_map_get_generic: Error extracting generic object."
  end if
end subroutine generic_map_get_generic
subroutine generic_map_get_boolean(x, key, out)
  implicit none
  type(ygggeneric) :: x
  character(len=*) :: key
  logical(kind=1), pointer, intent(out) :: out
  type(c_ptr) :: c_out
  c_out = generic_map_get_item(x, key, "boolean")
  call c_f_pointer(c_out, out)
end subroutine generic_map_get_boolean
subroutine generic_map_get_integer(x, key, out)
  implicit none
  type(ygggeneric) :: x
  character(len=*) :: key
  integer(kind=c_int), pointer, intent(out) :: out
  type(c_ptr) :: c_out
  c_out = generic_map_get_item(x, key, "integer")
  call c_f_pointer(c_out, out)
end subroutine generic_map_get_integer
subroutine generic_map_get_null(x, key, out)
  implicit none
  type(ygggeneric) :: x
  character(len=*) :: key
  type(yggnull), intent(out) :: out
  type(c_ptr) :: c_out
  c_out = generic_map_get_item(x, key, "null")
  ! call c_f_pointer(c_out%ptr, out)
end subroutine generic_map_get_null
subroutine generic_map_get_number(x, key, out)
  implicit none
  type(ygggeneric) :: x
  character(len=*) :: key
  real(kind=8), pointer, intent(out) :: out
  type(c_ptr) :: c_out
  c_out = generic_map_get_item(x, key, "number")
  call c_f_pointer(c_out, out)
end subroutine generic_map_get_number
subroutine generic_map_get_string(x, key, out)
  implicit none
  type(ygggeneric) :: x
  character(len=*) :: key
  character(len=:, kind=c_char), pointer, intent(out) :: out
  type(c_ptr) :: c_out
  c_out = generic_map_get_item(x, key, "string")
  call c_f_pointer(c_out, out)
end subroutine generic_map_get_string
subroutine generic_map_get_map(x, key, out)
  implicit none
  type(ygggeneric) :: x
  character(len=*) :: key
  type(yggmap), pointer, intent(out) :: out
  allocate(out)
  out = yggmap(init_generic())
  out%obj = generic_map_get_item(x, key, "object")
end subroutine generic_map_get_map
subroutine generic_map_get_array(x, key, out)
  implicit none
  type(ygggeneric) :: x
  character(len=*) :: key
  type(yggarr), pointer, intent(out) :: out
  allocate(out)
  out = yggarr(init_generic())
  out%obj = generic_map_get_item(x, key, "array")
end subroutine generic_map_get_array
subroutine generic_map_get_ply(x, key, out)
  implicit none
  type(ygggeneric) :: x
  character(len=*) :: key
  type(c_ptr) :: c_out
  type(yggply), pointer, intent(out) :: out
  integer(kind=c_int) :: copy
  allocate(out)
  out = init_ply()
  ! this returns a copy, is there a way to get a reference?
  c_out = generic_map_get_item(x, key, "ply")
  copy = 0
  call set_ply(out, c_out, copy)
end subroutine generic_map_get_ply
subroutine generic_map_get_obj(x, key, out)
  implicit none
  type(ygggeneric) :: x
  character(len=*) :: key
  type(c_ptr) :: c_out
  type(yggobj), pointer, intent(out) :: out
  integer(kind=c_int) :: copy
  allocate(out)
  out = init_obj()
  ! this returns a copy, is there a way to get a reference?
  c_out = generic_map_get_item(x, key, "obj")
  copy = 0
  call set_obj(out, c_out, copy)
end subroutine generic_map_get_obj
subroutine generic_map_get_python_class(x, key, out)
  implicit none
  type(ygggeneric) :: x
  character(len=*) :: key
  type(yggpython), pointer, intent(out) :: out
  allocate(out)
  out = yggpython(init_python())
  ! this returns a copy, is there a way to get a reference?
  out%obj = generic_map_get_item(x, key, "class")
end subroutine generic_map_get_python_class
subroutine generic_map_get_python_function(x, key, out)
  implicit none
  type(ygggeneric) :: x
  character(len=*) :: key
  type(yggpython), pointer, intent(out) :: out
  allocate(out)
  out = yggpython(init_python())
  ! this returns a copy, is there a way to get a reference?
  out%obj = generic_map_get_item(x, key, "function")
end subroutine generic_map_get_python_function
subroutine generic_map_get_schema(x, key, out)
  implicit none
  type(ygggeneric) :: x
  character(len=*) :: key
  type(yggschema), pointer, intent(out) :: out
  allocate(out)
  out = yggschema(init_generic())
  out%obj = generic_map_get_item(x, key, "schema")
end subroutine generic_map_get_schema
subroutine generic_map_get_any(x, key, out)
  implicit none
  type(ygggeneric) :: x
  character(len=*) :: key
  type(ygggeneric), pointer, intent(out) :: out
  allocate(out)
  out = init_generic()
  out%obj = generic_map_get_item(x, key, "any")
end subroutine generic_map_get_any
! Get scalar int
subroutine generic_map_get_integer2(x, key, out)
  implicit none
  type(ygggeneric) :: x
  character(len=*) :: key
  integer(kind=2), pointer, intent(out) :: out
  type(c_ptr) :: c_out
  c_out = generic_map_get_scalar(x, key, "int", 2)
  call c_f_pointer(c_out, out)
end subroutine generic_map_get_integer2
subroutine generic_map_get_integer4(x, key, out)
  implicit none
  type(ygggeneric) :: x
  character(len=*) :: key
  integer(kind=4), pointer, intent(out) :: out
  type(c_ptr) :: c_out
  c_out = generic_map_get_scalar(x, key, "int", 4)
  call c_f_pointer(c_out, out)
end subroutine generic_map_get_integer4
subroutine generic_map_get_integer8(x, key, out)
  implicit none
  type(ygggeneric) :: x
  character(len=*) :: key
  integer(kind=8), pointer, intent(out) :: out
  type(c_ptr) :: c_out
  c_out = generic_map_get_scalar(x, key, "int", 8)
  call c_f_pointer(c_out, out)
end subroutine generic_map_get_integer8
! Get scalar uint
subroutine generic_map_get_unsigned1(x, key, out)
  implicit none
  type(ygggeneric) :: x
  character(len=*) :: key
  type(ygguint1), intent(out) :: out
  integer(kind=1), pointer :: temp
  type(c_ptr) :: c_out
  c_out = generic_map_get_scalar(x, key, "uint", 1)
  call c_f_pointer(c_out, temp)
  out%x = temp
  deallocate(temp)
end subroutine generic_map_get_unsigned1
subroutine generic_map_get_unsigned2(x, key, out)
  implicit none
  type(ygggeneric) :: x
  character(len=*) :: key
  type(ygguint2), intent(out) :: out
  integer(kind=2), pointer :: temp
  type(c_ptr) :: c_out
  c_out = generic_map_get_scalar(x, key, "uint", 2)
  call c_f_pointer(c_out, temp)
  out%x = temp
  deallocate(temp)
end subroutine generic_map_get_unsigned2
subroutine generic_map_get_unsigned4(x, key, out)
  implicit none
  type(ygggeneric) :: x
  character(len=*) :: key
  type(ygguint4), intent(out) :: out
  integer(kind=4), pointer :: temp
  type(c_ptr) :: c_out
  c_out = generic_map_get_scalar(x, key, "uint", 4)
  call c_f_pointer(c_out, temp)
  out%x = temp
  deallocate(temp)
end subroutine generic_map_get_unsigned4
subroutine generic_map_get_unsigned8(x, key, out)
  implicit none
  type(ygggeneric) :: x
  character(len=*) :: key
  type(ygguint8), intent(out) :: out
  integer(kind=8), pointer :: temp
  type(c_ptr) :: c_out
  c_out = generic_map_get_scalar(x, key, "uint", 8)
  call c_f_pointer(c_out, temp)
  out%x = temp
  deallocate(temp)
end subroutine generic_map_get_unsigned8
! Get scalar real
subroutine generic_map_get_real4(x, key, out)
  implicit none
  type(ygggeneric) :: x
  character(len=*) :: key
  real(kind=4), pointer, intent(out) :: out
  type(c_ptr) :: c_out
  c_out = generic_map_get_scalar(x, key, "float", 4)
  call c_f_pointer(c_out, out)
end subroutine generic_map_get_real4
subroutine generic_map_get_real8(x, key, out)
  implicit none
  type(ygggeneric) :: x
  character(len=*) :: key
  real(kind=8), pointer, intent(out) :: out
  type(c_ptr) :: c_out
  c_out = generic_map_get_scalar(x, key, "float", 8)
  call c_f_pointer(c_out, out)
end subroutine generic_map_get_real8
! Get scalar complex
subroutine generic_map_get_complex4(x, key, out)
  implicit none
  type(ygggeneric) :: x
  character(len=*) :: key
  complex(kind=4), pointer, intent(out) :: out
  type(c_ptr) :: c_out
  c_out = generic_map_get_scalar(x, key, "complex", 4)
  call c_f_pointer(c_out, out)
end subroutine generic_map_get_complex4
subroutine generic_map_get_complex8(x, key, out)
  implicit none
  type(ygggeneric) :: x
  character(len=*) :: key
  complex(kind=8), pointer, intent(out) :: out
  type(c_ptr) :: c_out
  c_out = generic_map_get_scalar(x, key, "complex", 8)
  call c_f_pointer(c_out, out)
end subroutine generic_map_get_complex8
! Get scalar string
subroutine generic_map_get_bytes(x, key, out)
  implicit none
  type(ygggeneric) :: x
  character(len=*) :: key
  character(len=:), pointer, intent(out) :: out
  character, dimension(:), pointer :: temp
  type(c_ptr) :: c_out
  integer :: length, i
  c_out = generic_map_get_scalar(x, key, "bytes", 0)
  length = generic_map_get_item_nbytes(x, key, "bytes")
  call c_f_pointer(c_out, temp, [length])
  allocate(character(len=length) :: out)
  do i = 1, length
     out(i:i) = temp(i)
  end do
  deallocate(temp)
end subroutine generic_map_get_bytes
subroutine generic_map_get_unicode(x, key, out)
  implicit none
  type(ygggeneric) :: x
  character(len=*) :: key
  character(kind=ucs4, len=:), pointer, intent(out) :: out
  character(kind=ucs4), dimension(:), pointer :: temp
  type(c_ptr) :: c_out
  integer :: length, i
  c_out = generic_map_get_scalar(x, key, "unicode", 0)
  length = generic_map_get_item_nbytes(x, key, "unicode")/4
  call c_f_pointer(c_out, temp, [length])
  allocate(character(kind=ucs4, len=length) :: out)
  do i = 1, length
     out(i:i) = temp(i)
  end do
  deallocate(temp)
end subroutine generic_map_get_unicode

! Get 1darray int
subroutine generic_map_get_1darray_integer2(x, key, out)
  implicit none
  type(ygggeneric) :: x
  character(len=*) :: key
  integer(kind=2), dimension(:), pointer, intent(out) :: out
  integer(kind=c_size_t) :: c_length
  type(c_ptr), target :: c_out
  type(c_ptr), pointer :: temp
  type(c_ptr) :: c_out_ptr
  c_out = c_null_ptr
  c_out_ptr = c_loc(c_out)
  c_length = generic_map_get_1darray(x, key, "int", 2, c_out_ptr)
  call c_f_pointer(c_out_ptr, temp)
  call c_f_pointer(temp, out, [c_length])
end subroutine generic_map_get_1darray_integer2
subroutine generic_map_get_1darray_integer4(x, key, out)
  implicit none
  type(ygggeneric) :: x
  character(len=*) :: key
  integer(kind=4), dimension(:), pointer, intent(out) :: out
  integer(kind=c_size_t) :: c_length
  type(c_ptr), target :: c_out
  type(c_ptr), pointer :: temp
  type(c_ptr) :: c_out_ptr
  c_out = c_null_ptr
  c_out_ptr = c_loc(c_out)
  c_length = generic_map_get_1darray(x, key, "int", 4, c_out_ptr)
  call c_f_pointer(c_out_ptr, temp)
  call c_f_pointer(temp, out, [c_length])
end subroutine generic_map_get_1darray_integer4
subroutine generic_map_get_1darray_integer8(x, key, out)
  implicit none
  type(ygggeneric) :: x
  character(len=*) :: key
  integer(kind=8), dimension(:), pointer, intent(out) :: out
  integer(kind=c_size_t) :: c_length
  type(c_ptr), target :: c_out
  type(c_ptr), pointer :: temp
  type(c_ptr) :: c_out_ptr
  c_out = c_null_ptr
  c_out_ptr = c_loc(c_out)
  c_length = generic_map_get_1darray(x, key, "int", 8, c_out_ptr)
  call c_f_pointer(c_out_ptr, temp)
  call c_f_pointer(temp, out, [c_length])
end subroutine generic_map_get_1darray_integer8
! Get 1darray uint
subroutine generic_map_get_1darray_unsigned1(x, key, out)
  implicit none
  type(ygggeneric) :: x
  character(len=*) :: key
  type(ygguint1), dimension(:), pointer, intent(out) :: out
  integer(kind=c_size_t) :: c_length
  type(c_ptr), target :: c_out
  type(c_ptr), pointer :: temp
  type(c_ptr) :: c_out_ptr
  c_out = c_null_ptr
  c_out_ptr = c_loc(c_out)
  c_length = generic_map_get_1darray(x, key, "uint", 1, c_out_ptr)
  call c_f_pointer(c_out_ptr, temp)
  call c_f_pointer(temp, out, [c_length])
end subroutine generic_map_get_1darray_unsigned1
subroutine generic_map_get_1darray_unsigned2(x, key, out)
  implicit none
  type(ygggeneric) :: x
  character(len=*) :: key
  type(ygguint2), dimension(:), pointer, intent(out) :: out
  integer(kind=c_size_t) :: c_length
  type(c_ptr), target :: c_out
  type(c_ptr), pointer :: temp
  type(c_ptr) :: c_out_ptr
  c_out = c_null_ptr
  c_out_ptr = c_loc(c_out)
  c_length = generic_map_get_1darray(x, key, "uint", 2, c_out_ptr)
  call c_f_pointer(c_out_ptr, temp)
  call c_f_pointer(temp, out, [c_length])
end subroutine generic_map_get_1darray_unsigned2
subroutine generic_map_get_1darray_unsigned4(x, key, out)
  implicit none
  type(ygggeneric) :: x
  character(len=*) :: key
  type(ygguint4), dimension(:), pointer, intent(out) :: out
  integer(kind=c_size_t) :: c_length
  type(c_ptr), target :: c_out
  type(c_ptr), pointer :: temp
  type(c_ptr) :: c_out_ptr
  c_out = c_null_ptr
  c_out_ptr = c_loc(c_out)
  c_length = generic_map_get_1darray(x, key, "uint", 4, c_out_ptr)
  call c_f_pointer(c_out_ptr, temp)
  call c_f_pointer(temp, out, [c_length])
end subroutine generic_map_get_1darray_unsigned4
subroutine generic_map_get_1darray_unsigned8(x, key, out)
  implicit none
  type(ygggeneric) :: x
  character(len=*) :: key
  type(ygguint8), dimension(:), pointer, intent(out) :: out
  integer(kind=c_size_t) :: c_length
  type(c_ptr), target :: c_out
  type(c_ptr), pointer :: temp
  type(c_ptr) :: c_out_ptr
  c_out = c_null_ptr
  c_out_ptr = c_loc(c_out)
  c_length = generic_map_get_1darray(x, key, "uint", 8, c_out_ptr)
  call c_f_pointer(c_out_ptr, temp)
  call c_f_pointer(temp, out, [c_length])
end subroutine generic_map_get_1darray_unsigned8
! Get 1darray real
subroutine generic_map_get_1darray_real4(x, key, out)
  implicit none
  type(ygggeneric) :: x
  character(len=*) :: key
  real(kind=4), dimension(:), pointer, intent(out) :: out
  integer(kind=c_size_t) :: c_length
  type(c_ptr), target :: c_out
  type(c_ptr), pointer :: temp
  type(c_ptr) :: c_out_ptr
  c_out = c_null_ptr
  c_out_ptr = c_loc(c_out)
  c_length = generic_map_get_1darray(x, key, "float", 4, c_out_ptr)
  call c_f_pointer(c_out_ptr, temp)
  call c_f_pointer(temp, out, [c_length])
end subroutine generic_map_get_1darray_real4
subroutine generic_map_get_1darray_real8(x, key, out)
  implicit none
  type(ygggeneric) :: x
  character(len=*) :: key
  real(kind=8), dimension(:), pointer, intent(out) :: out
  integer(kind=c_size_t) :: c_length
  type(c_ptr), target :: c_out
  type(c_ptr), pointer :: temp
  type(c_ptr) :: c_out_ptr
  c_out = c_null_ptr
  c_out_ptr = c_loc(c_out)
  c_length = generic_map_get_1darray(x, key, "float", 8, c_out_ptr)
  call c_f_pointer(c_out_ptr, temp)
  call c_f_pointer(temp, out, [c_length])
end subroutine generic_map_get_1darray_real8
! Get 1darray complex
subroutine generic_map_get_1darray_complex4(x, key, out)
  implicit none
  type(ygggeneric) :: x
  character(len=*) :: key
  complex(kind=4), dimension(:), pointer, intent(out) :: out
  integer(kind=c_size_t) :: c_length
  type(c_ptr), target :: c_out
  type(c_ptr), pointer :: temp
  type(c_ptr) :: c_out_ptr
  c_out = c_null_ptr
  c_out_ptr = c_loc(c_out)
  c_length = generic_map_get_1darray(x, key, "complex", 4, c_out_ptr)
  call c_f_pointer(c_out_ptr, temp)
  call c_f_pointer(temp, out, [c_length])
end subroutine generic_map_get_1darray_complex4
subroutine generic_map_get_1darray_complex8(x, key, out)
  implicit none
  type(ygggeneric) :: x
  character(len=*) :: key
  complex(kind=8), dimension(:), pointer, intent(out) :: out
  integer(kind=c_size_t) :: c_length
  type(c_ptr), target :: c_out
  type(c_ptr), pointer :: temp
  type(c_ptr) :: c_out_ptr
  c_out = c_null_ptr
  c_out_ptr = c_loc(c_out)
  c_length = generic_map_get_1darray(x, key, "complex", 8, c_out_ptr)
  call c_f_pointer(c_out_ptr, temp)
  call c_f_pointer(temp, out, [c_length])
end subroutine generic_map_get_1darray_complex8
! Get 1darray string
subroutine generic_map_get_1darray_bytes(x, key, out)
  implicit none
  type(ygggeneric) :: x
  character(len=*) :: key
  character(len=:), dimension(:), pointer, intent(out) :: out
  character, dimension(:), pointer :: temp
  type(c_ptr), target :: c_out
  integer(kind=c_size_t) :: c_length, i
  integer :: nbytes, precision, j
  type(c_ptr), pointer :: temp_ptr
  type(c_ptr) :: c_out_ptr
  c_out = c_null_ptr
  c_out_ptr = c_loc(c_out)
  c_length = generic_map_get_1darray(x, key, "bytes", 0, c_out_ptr)
  nbytes = generic_map_get_item_nbytes(x, key, "bytes")
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
end subroutine generic_map_get_1darray_bytes
subroutine generic_map_get_1darray_unicode(x, key, out)
  implicit none
  type(ygggeneric) :: x
  character(len=*) :: key
  character(kind=ucs4, len=:), dimension(:), pointer, intent(out) :: out
  character(kind=ucs4), dimension(:), pointer :: temp
  type(c_ptr), target :: c_out
  integer(kind=c_size_t) :: c_length, i
  integer :: nbytes, precision, j
  type(c_ptr), pointer :: temp_ptr
  type(c_ptr) :: c_out_ptr
  c_out = c_null_ptr
  c_out_ptr = c_loc(c_out)
  c_length = generic_map_get_1darray(x, key, "unicode", 0, c_out_ptr)
  nbytes = generic_map_get_item_nbytes(x, key, "unicode")
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
end subroutine generic_map_get_1darray_unicode

! Get ndarray int
subroutine generic_map_get_ndarray_integer2(x, key, out)
  implicit none
  type(ygggeneric) :: x
  character(len=*) :: key
  type(integer2_nd), intent(out) :: out
  type(c_ptr), target :: c_out
  type(c_ptr), pointer :: temp
  type(c_ptr) :: c_out_ptr
  c_out = c_null_ptr
  c_out_ptr = c_loc(c_out)
  out%shape => generic_map_get_ndarray(x, key, "int", 2, &
       c_out_ptr)
  call c_f_pointer(c_out_ptr, temp)
  call c_f_pointer(temp, out%x, out%shape)
end subroutine generic_map_get_ndarray_integer2
subroutine generic_map_get_ndarray_integer4(x, key, out)
  implicit none
  type(ygggeneric) :: x
  character(len=*) :: key
  type(integer4_nd), intent(out) :: out
  type(c_ptr), target :: c_out
  type(c_ptr), pointer :: temp
  type(c_ptr) :: c_out_ptr
  c_out = c_null_ptr
  c_out_ptr = c_loc(c_out)
  out%shape => generic_map_get_ndarray(x, key, "int", 4, &
       c_out_ptr)
  call c_f_pointer(c_out_ptr, temp)
  call c_f_pointer(temp, out%x, out%shape)
end subroutine generic_map_get_ndarray_integer4
subroutine generic_map_get_ndarray_integer8(x, key, out)
  implicit none
  type(ygggeneric) :: x
  character(len=*) :: key
  type(integer8_nd), intent(out) :: out
  type(c_ptr), target :: c_out
  type(c_ptr), pointer :: temp
  type(c_ptr) :: c_out_ptr
  c_out = c_null_ptr
  c_out_ptr = c_loc(c_out)
  out%shape => generic_map_get_ndarray(x, key, "int", 8, &
       c_out_ptr)
  call c_f_pointer(c_out_ptr, temp)
  call c_f_pointer(temp, out%x, out%shape)
end subroutine generic_map_get_ndarray_integer8
! Get ndarray uint
subroutine generic_map_get_ndarray_unsigned1(x, key, out)
  implicit none
  type(ygggeneric) :: x
  character(len=*) :: key
  type(unsigned1_nd), intent(out) :: out
  type(c_ptr), target :: c_out
  type(c_ptr), pointer :: temp
  type(c_ptr) :: c_out_ptr
  c_out = c_null_ptr
  c_out_ptr = c_loc(c_out)
  out%shape => generic_map_get_ndarray(x, key, "uint", 1, &
       c_out_ptr)
  call c_f_pointer(c_out_ptr, temp)
  call c_f_pointer(temp, out%x, out%shape)
end subroutine generic_map_get_ndarray_unsigned1
subroutine generic_map_get_ndarray_unsigned2(x, key, out)
  implicit none
  type(ygggeneric) :: x
  character(len=*) :: key
  type(unsigned2_nd), intent(out) :: out
  type(c_ptr), target :: c_out
  type(c_ptr), pointer :: temp
  type(c_ptr) :: c_out_ptr
  c_out = c_null_ptr
  c_out_ptr = c_loc(c_out)
  out%shape => generic_map_get_ndarray(x, key, "uint", 2, &
       c_out_ptr)
  call c_f_pointer(c_out_ptr, temp)
  call c_f_pointer(temp, out%x, out%shape)
end subroutine generic_map_get_ndarray_unsigned2
subroutine generic_map_get_ndarray_unsigned4(x, key, out)
  implicit none
  type(ygggeneric) :: x
  character(len=*) :: key
  type(unsigned4_nd), intent(out) :: out
  type(c_ptr), target :: c_out
  type(c_ptr), pointer :: temp
  type(c_ptr) :: c_out_ptr
  c_out = c_null_ptr
  c_out_ptr = c_loc(c_out)
  out%shape => generic_map_get_ndarray(x, key, "uint", 4, &
       c_out_ptr)
  call c_f_pointer(c_out_ptr, temp)
  call c_f_pointer(temp, out%x, out%shape)
end subroutine generic_map_get_ndarray_unsigned4
subroutine generic_map_get_ndarray_unsigned8(x, key, out)
  implicit none
  type(ygggeneric) :: x
  character(len=*) :: key
  type(unsigned8_nd), intent(out) :: out
  type(c_ptr), target :: c_out
  type(c_ptr), pointer :: temp
  type(c_ptr) :: c_out_ptr
  c_out = c_null_ptr
  c_out_ptr = c_loc(c_out)
  out%shape => generic_map_get_ndarray(x, key, "uint", 8, &
       c_out_ptr)
  call c_f_pointer(c_out_ptr, temp)
  call c_f_pointer(temp, out%x, out%shape)
end subroutine generic_map_get_ndarray_unsigned8
! Get ndarray real
subroutine generic_map_get_ndarray_real4(x, key, out)
  implicit none
  type(ygggeneric) :: x
  character(len=*) :: key
  type(real4_nd), intent(out) :: out
  type(c_ptr), target :: c_out
  type(c_ptr), pointer :: temp
  type(c_ptr) :: c_out_ptr
  c_out = c_null_ptr
  c_out_ptr = c_loc(c_out)
  out%shape => generic_map_get_ndarray(x, key, "float", 4, &
       c_out_ptr)
  call c_f_pointer(c_out_ptr, temp)
  call c_f_pointer(temp, out%x, out%shape)
end subroutine generic_map_get_ndarray_real4
subroutine generic_map_get_ndarray_real8(x, key, out)
  implicit none
  type(ygggeneric) :: x
  character(len=*) :: key
  type(real8_nd), intent(out) :: out
  type(c_ptr), target :: c_out
  type(c_ptr), pointer :: temp
  type(c_ptr) :: c_out_ptr
  c_out = c_null_ptr
  c_out_ptr = c_loc(c_out)
  out%shape => generic_map_get_ndarray(x, key, "float", 8, &
       c_out_ptr)
  call c_f_pointer(c_out_ptr, temp)
  call c_f_pointer(temp, out%x, out%shape)
end subroutine generic_map_get_ndarray_real8
! Get ndarray complex
subroutine generic_map_get_ndarray_complex4(x, key, out)
  implicit none
  type(ygggeneric) :: x
  character(len=*) :: key
  type(complex4_nd), intent(out) :: out
  type(c_ptr), target :: c_out
  type(c_ptr), pointer :: temp
  type(c_ptr) :: c_out_ptr
  c_out = c_null_ptr
  c_out_ptr = c_loc(c_out)
  out%shape => generic_map_get_ndarray(x, key, "complex", 4, &
       c_out_ptr)
  call c_f_pointer(c_out_ptr, temp)
  call c_f_pointer(temp, out%x, out%shape)
end subroutine generic_map_get_ndarray_complex4
subroutine generic_map_get_ndarray_complex8(x, key, out)
  implicit none
  type(ygggeneric) :: x
  character(len=*) :: key
  type(complex8_nd), intent(out) :: out
  type(c_ptr), target :: c_out
  type(c_ptr), pointer :: temp
  type(c_ptr) :: c_out_ptr
  c_out = c_null_ptr
  c_out_ptr = c_loc(c_out)
  out%shape => generic_map_get_ndarray(x, key, "complex", 8, &
       c_out_ptr)
  call c_f_pointer(c_out_ptr, temp)
  call c_f_pointer(temp, out%x, out%shape)
end subroutine generic_map_get_ndarray_complex8
! Get ndarray string
subroutine generic_map_get_ndarray_character(x, key, out)
  implicit none
  type(ygggeneric) :: x
  character(len=*) :: key
  type(character_nd), intent(out) :: out
  character, dimension(:), pointer :: temp
  type(c_ptr), target :: c_out
  integer(kind=c_size_t) :: precision, nelements, i, j
  integer(kind=c_int) :: nbytes
  type(c_ptr), pointer :: temp_ptr
  type(c_ptr) :: c_out_ptr
  c_out = c_null_ptr
  c_out_ptr = c_loc(c_out)
  out%shape => generic_map_get_ndarray(x, key, "bytes", 0, &
       c_out_ptr)
  nbytes = generic_map_get_item_nbytes(x, key, "bytes")
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
        out%x(i)%x(j) = temp((i-1)*precision + j)
     end do
  end do
  deallocate(temp)
end subroutine generic_map_get_ndarray_character
subroutine generic_map_get_ndarray_bytes(x, key, out)
  implicit none
  type(ygggeneric) :: x
  character(len=*) :: key
  type(bytes_nd), intent(out) :: out
  character, dimension(:), pointer :: temp
  type(c_ptr), target :: c_out
  integer(kind=c_size_t) :: precision, nelements, i, j
  integer(kind=c_int) :: nbytes
  type(c_ptr), pointer :: temp_ptr
  type(c_ptr) :: c_out_ptr
  c_out = c_null_ptr
  c_out_ptr = c_loc(c_out)
  out%shape => generic_map_get_ndarray(x, key, "bytes", 0, &
       c_out_ptr)
  nbytes = generic_map_get_item_nbytes(x, key, "bytes")
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
end subroutine generic_map_get_ndarray_bytes
subroutine generic_map_get_ndarray_unicode(x, key, out)
  implicit none
  type(ygggeneric) :: x
  character(len=*) :: key
  type(unicode_nd), intent(out) :: out
  character(kind=ucs4), dimension(:), pointer :: temp
  type(c_ptr), target :: c_out
  integer(kind=c_size_t) :: precision, nelements, i, j
  integer(kind=c_int) :: nbytes
  type(c_ptr), pointer :: temp_ptr
  type(c_ptr) :: c_out_ptr
  c_out = c_null_ptr
  c_out_ptr = c_loc(c_out)
  out%shape => generic_map_get_ndarray(x, key, "unicode", 0, &
       c_out_ptr)
  nbytes = generic_map_get_item_nbytes(x, key, "unicode")
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
end subroutine generic_map_get_ndarray_unicode


! Set methods
subroutine generic_map_set_generic(x, key, val)
  implicit none
  type(ygggeneric) :: x
  character(len=*) :: key
  type(ygggeneric), intent(in) :: val
  integer(kind=c_int) :: flag
  flag = set_generic_object(x, key, val)
  if (flag.ne.0) then
     stop "generic_map_set_generic: Error setting generic object."
  end if
end subroutine generic_map_set_generic
subroutine generic_map_set_boolean(x, key, val)
  implicit none
  type(ygggeneric) :: x
  character(len=*) :: key
  logical(kind=1), intent(in), target :: val
  type(c_ptr) :: c_val
  c_val = c_loc(val)
  call generic_map_set_item(x, key, "boolean", c_val)
end subroutine generic_map_set_boolean
subroutine generic_map_set_integer(x, key, val)
  implicit none
  type(ygggeneric) :: x
  character(len=*) :: key
  integer(kind=c_int), intent(in), target :: val
  type(c_ptr) :: c_val
  c_val = c_loc(val)
  call generic_map_set_item(x, key, "integer", c_val)
end subroutine generic_map_set_integer
subroutine generic_map_set_null(x, key, val)
  implicit none
  type(ygggeneric) :: x
  character(len=*) :: key
  type(yggnull), intent(in) :: val
  type(c_ptr) :: c_val
  c_val = val%ptr
  call generic_map_set_item(x, key, "null", c_val)
end subroutine generic_map_set_null
subroutine generic_map_set_number(x, key, val)
  implicit none
  type(ygggeneric) :: x
  character(len=*) :: key
  real(kind=8), intent(in), target :: val
  type(c_ptr) :: c_val
  c_val = c_loc(val)
  call generic_map_set_item(x, key, "number", c_val)
end subroutine generic_map_set_number
subroutine generic_map_set_array(x, key, val)
  implicit none
  type(ygggeneric) :: x
  character(len=*) :: key
  type(yggarr), intent(in), target :: val
  type(c_ptr) :: c_val
  c_val = c_loc(val)
  call generic_map_set_item(x, key, "array", c_val)
end subroutine generic_map_set_array
subroutine generic_map_set_map(x, key, val)
  implicit none
  type(ygggeneric) :: x
  character(len=*) :: key
  type(yggmap), intent(in), target :: val
  type(c_ptr) :: c_val
  c_val = c_loc(val)
  call generic_map_set_item(x, key, "object", c_val)
end subroutine generic_map_set_map
subroutine generic_map_set_ply(x, key, val)
  implicit none
  type(ygggeneric) :: x
  character(len=*) :: key
  type(yggply), intent(in), target :: val
  type(c_ptr) :: c_val
  c_val = c_loc(val)
  call generic_map_set_item(x, key, "ply", c_val)
end subroutine generic_map_set_ply
subroutine generic_map_set_obj(x, key, val)
  implicit none
  type(ygggeneric) :: x
  character(len=*) :: key
  type(yggobj), intent(in), target :: val
  type(c_ptr) :: c_val
  c_val = c_loc(val)
  call generic_map_set_item(x, key, "obj", c_val)
end subroutine generic_map_set_obj
subroutine generic_map_set_python_class(x, key, val)
  implicit none
  type(ygggeneric) :: x
  character(len=*) :: key
  type(yggpython), intent(in), target :: val
  type(c_ptr) :: c_val
  c_val = c_loc(val)
  call generic_map_set_item(x, key, "class", c_val)
end subroutine generic_map_set_python_class
subroutine generic_map_set_python_function(x, key, val)
  implicit none
  type(ygggeneric) :: x
  character(len=*) :: key
  type(yggpython), intent(in), target :: val
  type(c_ptr) :: c_val
  c_val = c_loc(val)
  call generic_map_set_item(x, key, "function", c_val)
end subroutine generic_map_set_python_function
subroutine generic_map_set_schema(x, key, val)
  implicit none
  type(ygggeneric) :: x
  character(len=*) :: key
  type(yggschema), intent(in), target :: val
  type(c_ptr) :: c_val
  c_val = c_loc(val)
  call generic_map_set_item(x, key, "schema", c_val)
end subroutine generic_map_set_schema
subroutine generic_map_set_any(x, key, val)
  implicit none
  type(ygggeneric) :: x
  character(len=*) :: key
  type(ygggeneric), intent(in), target :: val
  type(c_ptr) :: c_val
  c_val = c_loc(val)
  call generic_map_set_item(x, key, "any", c_val)
end subroutine generic_map_set_any
! Set scalar int
subroutine generic_map_set_integer2(x, key, val, units_in)
  implicit none
  type(ygggeneric) :: x
  character(len=*) :: key
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
  call generic_map_set_scalar(x, key, c_val, "int", 2, units)
end subroutine generic_map_set_integer2
subroutine generic_map_set_integer4(x, key, val, units_in)
  implicit none
  type(ygggeneric) :: x
  character(len=*) :: key
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
  call generic_map_set_scalar(x, key, c_val, "int", 4, units)
end subroutine generic_map_set_integer4
subroutine generic_map_set_integer8(x, key, val, units_in)
  implicit none
  type(ygggeneric) :: x
  character(len=*) :: key
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
  call generic_map_set_scalar(x, key, c_val, "int", 8, units)
end subroutine generic_map_set_integer8
! Set scalar uint
subroutine generic_map_set_unsigned1(x, key, val, units_in)
  implicit none
  type(ygggeneric) :: x
  character(len=*) :: key
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
  call generic_map_set_scalar(x, key, c_val, "uint", 1, units)
end subroutine generic_map_set_unsigned1
subroutine generic_map_set_unsigned2(x, key, val, units_in)
  implicit none
  type(ygggeneric) :: x
  character(len=*) :: key
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
  call generic_map_set_scalar(x, key, c_val, "uint", 2, units)
end subroutine generic_map_set_unsigned2
subroutine generic_map_set_unsigned4(x, key, val, units_in)
  implicit none
  type(ygggeneric) :: x
  character(len=*) :: key
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
  call generic_map_set_scalar(x, key, c_val, "uint", 4, units)
end subroutine generic_map_set_unsigned4
subroutine generic_map_set_unsigned8(x, key, val, units_in)
  implicit none
  type(ygggeneric) :: x
  character(len=*) :: key
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
  call generic_map_set_scalar(x, key, c_val, "uint", 8, units)
end subroutine generic_map_set_unsigned8
! Set scalar real
subroutine generic_map_set_real4(x, key, val, units_in)
  implicit none
  type(ygggeneric) :: x
  character(len=*) :: key
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
  call generic_map_set_scalar(x, key, c_val, "float", 4, units)
end subroutine generic_map_set_real4
subroutine generic_map_set_real8(x, key, val, units_in)
  implicit none
  type(ygggeneric) :: x
  character(len=*) :: key
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
  call generic_map_set_scalar(x, key, c_val, "float", 8, units)
end subroutine generic_map_set_real8
! Set scalar complex
subroutine generic_map_set_complex4(x, key, val, units_in)
  implicit none
  type(ygggeneric) :: x
  character(len=*) :: key
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
  call generic_map_set_scalar(x, key, c_val, "complex", 4, units)
end subroutine generic_map_set_complex4
subroutine generic_map_set_complex8(x, key, val, units_in)
  implicit none
  type(ygggeneric) :: x
  character(len=*) :: key
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
  call generic_map_set_scalar(x, key, c_val, "complex", 8, units)
end subroutine generic_map_set_complex8
! Set scalar string
subroutine generic_map_set_bytes(x, key, val, units_in)
  implicit none
  type(ygggeneric) :: x
  character(len=*) :: key
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
  call generic_map_set_scalar(x, key, c_val, "bytes", 0, units)
end subroutine generic_map_set_bytes
subroutine generic_map_set_unicode(x, key, val, units_in)
  implicit none
  type(ygggeneric) :: x
  character(len=*) :: key
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
  call generic_map_set_scalar(x, key, c_val, "unicode", 0, units)
end subroutine generic_map_set_unicode

! Set 1darray int
subroutine generic_map_set_1darray_integer2(x, key, val, units_in)
  implicit none
  type(ygggeneric) :: x
  character(len=*) :: key
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
  call generic_map_set_1darray(x, key, c_val, "int", 2, &
       size(val), units)
end subroutine generic_map_set_1darray_integer2
subroutine generic_map_set_1darray_integer4(x, key, val, units_in)
  implicit none
  type(ygggeneric) :: x
  character(len=*) :: key
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
  call generic_map_set_1darray(x, key, c_val, "int", 4, &
       size(val), units)
end subroutine generic_map_set_1darray_integer4
subroutine generic_map_set_1darray_integer8(x, key, val, units_in)
  implicit none
  type(ygggeneric) :: x
  character(len=*) :: key
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
  call generic_map_set_1darray(x, key, c_val, "int", 8, &
       size(val), units)
end subroutine generic_map_set_1darray_integer8
! Set 1darray uint
subroutine generic_map_set_1darray_unsigned1(x, key, val, units_in)
  implicit none
  type(ygggeneric) :: x
  character(len=*) :: key
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
  call generic_map_set_1darray(x, key, c_val, "uint", 1, &
       size(val), units)
end subroutine generic_map_set_1darray_unsigned1
subroutine generic_map_set_1darray_unsigned2(x, key, val, units_in)
  implicit none
  type(ygggeneric) :: x
  character(len=*) :: key
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
  call generic_map_set_1darray(x, key, c_val, "uint", 2, &
       size(val), units)
end subroutine generic_map_set_1darray_unsigned2
subroutine generic_map_set_1darray_unsigned4(x, key, val, units_in)
  implicit none
  type(ygggeneric) :: x
  character(len=*) :: key
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
  call generic_map_set_1darray(x, key, c_val, "uint", 4, &
       size(val), units)
end subroutine generic_map_set_1darray_unsigned4
subroutine generic_map_set_1darray_unsigned8(x, key, val, units_in)
  implicit none
  type(ygggeneric) :: x
  character(len=*) :: key
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
  call generic_map_set_1darray(x, key, c_val, "uint", 8, &
       size(val), units)
end subroutine generic_map_set_1darray_unsigned8
! Set 1darray real
subroutine generic_map_set_1darray_real4(x, key, val, units_in)
  implicit none
  type(ygggeneric) :: x
  character(len=*) :: key
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
  call generic_map_set_1darray(x, key, c_val, "float", 4, &
       size(val), units)
end subroutine generic_map_set_1darray_real4
subroutine generic_map_set_1darray_real8(x, key, val, units_in)
  implicit none
  type(ygggeneric) :: x
  character(len=*) :: key
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
  call generic_map_set_1darray(x, key, c_val, "float", 8, &
       size(val), units)
end subroutine generic_map_set_1darray_real8
! Set 1darray complex
subroutine generic_map_set_1darray_complex4(x, key, val, units_in)
  implicit none
  type(ygggeneric) :: x
  character(len=*) :: key
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
  call generic_map_set_1darray(x, key, c_val, "complex", 4, &
       size(val), units)
end subroutine generic_map_set_1darray_complex4
subroutine generic_map_set_1darray_complex8(x, key, val, units_in)
  implicit none
  type(ygggeneric) :: x
  character(len=*) :: key
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
  call generic_map_set_1darray(x, key, c_val, "complex", 8, &
       size(val), units)
end subroutine generic_map_set_1darray_complex8
! Set 1darray string
subroutine generic_map_set_1darray_bytes(x, key, val, units_in)
  implicit none
  type(ygggeneric) :: x
  character(len=*) :: key
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
  call generic_map_set_1darray(x, key, c_val, "bytes", 0, &
       size(val), units)
end subroutine generic_map_set_1darray_bytes
subroutine generic_map_set_1darray_unicode(x, key, val, units_in)
  implicit none
  type(ygggeneric) :: x
  character(len=*) :: key
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
  call generic_map_set_1darray(x, key, c_val, "unicode", 0, &
       size(val), units)
end subroutine generic_map_set_1darray_unicode

! Set ndarray int
subroutine generic_map_set_ndarray_integer2(x, key, val, units_in)
  implicit none
  type(ygggeneric) :: x
  character(len=*) :: key
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
  call generic_map_set_ndarray(x, key, c_val, "int", 2, &
       val%shape, units)
end subroutine generic_map_set_ndarray_integer2
subroutine generic_map_set_ndarray_integer4(x, key, val, units_in)
  implicit none
  type(ygggeneric) :: x
  character(len=*) :: key
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
  call generic_map_set_ndarray(x, key, c_val, "int", 4, &
       val%shape, units)
end subroutine generic_map_set_ndarray_integer4
subroutine generic_map_set_ndarray_integer8(x, key, val, units_in)
  implicit none
  type(ygggeneric) :: x
  character(len=*) :: key
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
  call generic_map_set_ndarray(x, key, c_val, "int", 8, &
       val%shape, units)
end subroutine generic_map_set_ndarray_integer8
! Get ndarray uint
subroutine generic_map_set_ndarray_unsigned1(x, key, val, units_in)
  implicit none
  type(ygggeneric) :: x
  character(len=*) :: key
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
  call generic_map_set_ndarray(x, key, c_val, "uint", 1, &
       val%shape, units)
end subroutine generic_map_set_ndarray_unsigned1
subroutine generic_map_set_ndarray_unsigned2(x, key, val, units_in)
  implicit none
  type(ygggeneric) :: x
  character(len=*) :: key
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
  call generic_map_set_ndarray(x, key, c_val, "uint", 2, &
       val%shape, units)
end subroutine generic_map_set_ndarray_unsigned2
subroutine generic_map_set_ndarray_unsigned4(x, key, val, units_in)
  implicit none
  type(ygggeneric) :: x
  character(len=*) :: key
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
  call generic_map_set_ndarray(x, key, c_val, "uint", 4, &
       val%shape, units)
end subroutine generic_map_set_ndarray_unsigned4
subroutine generic_map_set_ndarray_unsigned8(x, key, val, units_in)
  implicit none
  type(ygggeneric) :: x
  character(len=*) :: key
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
  call generic_map_set_ndarray(x, key, c_val, "uint", 8, &
       val%shape, units)
end subroutine generic_map_set_ndarray_unsigned8
! Set ndarray real
subroutine generic_map_set_ndarray_real4(x, key, val, units_in)
  implicit none
  type(ygggeneric) :: x
  character(len=*) :: key
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
  call generic_map_set_ndarray(x, key, c_val, "float", 4, &
       val%shape, units)
end subroutine generic_map_set_ndarray_real4
subroutine generic_map_set_ndarray_real8(x, key, val, units_in)
  implicit none
  type(ygggeneric) :: x
  character(len=*) :: key
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
  call generic_map_set_ndarray(x, key, c_val, "float", 8, &
       val%shape, units)
end subroutine generic_map_set_ndarray_real8
! Set ndarray complex
subroutine generic_map_set_ndarray_complex4(x, key, val, units_in)
  implicit none
  type(ygggeneric) :: x
  character(len=*) :: key
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
  call generic_map_set_ndarray(x, key, c_val, "complex", 4, &
       val%shape, units)
end subroutine generic_map_set_ndarray_complex4
subroutine generic_map_set_ndarray_complex8(x, key, val, units_in)
  implicit none
  type(ygggeneric) :: x
  character(len=*) :: key
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
  call generic_map_set_ndarray(x, key, c_val, "complex", 8, &
       val%shape, units)
end subroutine generic_map_set_ndarray_complex8
! Set ndarray string
subroutine generic_map_set_ndarray_character(x, key, val, units_in)
  implicit none
  type(ygggeneric) :: x
  character(len=*) :: key
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
  call generic_map_set_ndarray(x, key, c_val, "bytes", 0, &
       val%shape, units)
end subroutine generic_map_set_ndarray_character
subroutine generic_map_set_ndarray_bytes(x, key, val, units_in)
  implicit none
  type(ygggeneric) :: x
  character(len=*) :: key
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
  call generic_map_set_ndarray(x, key, c_val, "bytes", 0, &
       val%shape, units)
end subroutine generic_map_set_ndarray_bytes
subroutine generic_map_set_ndarray_unicode(x, key, val, units_in)
  implicit none
  type(ygggeneric) :: x
  character(len=*) :: key
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
  call generic_map_set_ndarray(x, key, c_val, "unicode", 0, &
       val%shape, units)
end subroutine generic_map_set_ndarray_unicode
