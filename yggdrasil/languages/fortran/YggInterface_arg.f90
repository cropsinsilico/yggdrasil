! Scalar versions
function yggarg_scalar_init(x) result (y)
  class(*), target :: x
  type(yggptr) :: y
  y%item => x
  y%array = .false.
  y%alloc = .false.
  y%len = 1
  y%prec = 1
  y%ndim = 1
end function yggarg_scalar_init
function yggarg_scalar_integer2(x) result (y)
  type(yggptr) :: y
  integer(kind=2), target :: x
  integer(kind=2), pointer :: xp
  y = yggarg_scalar_init(x)
  xp => x
  y%type = "integer"
  y%ptr = c_loc(xp)
  y%nbytes = sizeof(x)
end function yggarg_scalar_integer2
function yggarg_scalar_integer4(x) result (y)
  type(yggptr) :: y
  integer(kind=4), target :: x
  integer(kind=4), pointer :: xp
  y = yggarg_scalar_init(x)
  xp => x
  y%type = "integer"
  y%ptr = c_loc(xp)
  y%nbytes = sizeof(x)
end function yggarg_scalar_integer4
function yggarg_scalar_integer8(x) result (y)
  type(yggptr) :: y
  integer(kind=8), target :: x
  integer(kind=8), pointer :: xp
  y = yggarg_scalar_init(x)
  xp => x
  y%type = "integer"
  y%ptr = c_loc(xp)
  y%nbytes = sizeof(x)
end function yggarg_scalar_integer8
function yggarg_scalar_real4(x) result (y)
  type(yggptr) :: y
  real(kind=4), target :: x
  real(kind=4), pointer :: xp
  y = yggarg_scalar_init(x)
  xp => x
  y%type = "real"
  y%ptr = c_loc(xp)
  y%nbytes = sizeof(x)
end function yggarg_scalar_real4
function yggarg_scalar_real8(x) result (y)
  type(yggptr) :: y
  real(kind=8), target :: x
  real(kind=8), pointer :: xp
  y = yggarg_scalar_init(x)
  xp => x
  y%type = "real"
  y%ptr = c_loc(xp)
  y%nbytes = sizeof(x)
end function yggarg_scalar_real8
function yggarg_scalar_real16(x) result (y)
  type(yggptr) :: y
  real(kind=16), target :: x
  real(kind=16), pointer :: xp
  y = yggarg_scalar_init(x)
  xp => x
  y%type = "real"
  y%ptr = c_loc(xp)
  y%nbytes = sizeof(x)
end function yggarg_scalar_real16
function yggarg_scalar_complex4(x) result (y)
  type(yggptr) :: y
  complex(kind=4), target :: x
  complex(kind=4), pointer :: xp
  y = yggarg_scalar_init(x)
  xp => x
  y%type = "complex"
  y%ptr = c_loc(xp)
  y%nbytes = sizeof(x)
end function yggarg_scalar_complex4
function yggarg_scalar_complex8(x) result (y)
  type(yggptr) :: y
  complex(kind=8), target :: x
  complex(kind=8), pointer :: xp
  y = yggarg_scalar_init(x)
  xp => x
  y%type = "complex"
  y%ptr = c_loc(xp)
  y%nbytes = sizeof(x)
end function yggarg_scalar_complex8
function yggarg_scalar_complex16(x) result (y)
  type(yggptr) :: y
  complex(kind=16), target :: x
  complex(kind=16), pointer :: xp
  y = yggarg_scalar_init(x)
  xp => x
  y%type = "complex"
  y%ptr = c_loc(xp)
  y%nbytes = sizeof(x)
end function yggarg_scalar_complex16
function yggarg_scalar_logical1(x) result (y)
  type(yggptr) :: y
  logical(kind=1), target :: x
  logical(kind=1), pointer :: xp
  y = yggarg_scalar_init(x)
  xp => x
  y%type = "logical"
  y%ptr = c_loc(xp)
  y%nbytes = sizeof(x)
end function yggarg_scalar_logical1
function yggarg_scalar_logical2(x) result (y)
  type(yggptr) :: y
  logical(kind=2), target :: x
  logical(kind=2), pointer :: xp
  y = yggarg_scalar_init(x)
  xp => x
  y%type = "logical"
  y%ptr = c_loc(xp)
  y%nbytes = sizeof(x)
end function yggarg_scalar_logical2
function yggarg_scalar_logical4(x) result (y)
  type(yggptr) :: y
  logical(kind=4), target :: x
  logical(kind=4), pointer :: xp
  y = yggarg_scalar_init(x)
  xp => x
  y%type = "logical"
  y%ptr = c_loc(xp)
  y%nbytes = sizeof(x)
end function yggarg_scalar_logical4
function yggarg_scalar_logical8(x) result (y)
  type(yggptr) :: y
  logical(kind=8), target :: x
  logical(kind=8), pointer :: xp
  y = yggarg_scalar_init(x)
  xp => x
  y%type = "logical"
  y%ptr = c_loc(xp)
  y%nbytes = sizeof(x)
end function yggarg_scalar_logical8
function yggarg_scalar_character(x) result (y)
  type(yggptr) :: y
  character(len=*), target :: x
  character(len=len(x)), pointer :: xp
  integer :: i
  y = yggarg_scalar_init(x)
  xp => x
  y%type = "character"
  y%prec = len(x)
  allocate(y%data_character_unit(len(x)))
  do i = 1, len(x)
     y%data_character_unit(i) = x(i:i)
  end do
  if (len_trim(x).lt.len(x)) then
     y%data_character_unit(len_trim(x) + 1) = c_null_char
  end if
  y%ptr = c_loc(y%data_character_unit(1))
  y%nbytes = sizeof(x)
end function yggarg_scalar_character
function yggarg_scalar_yggchar_r(x) result (y)
  type(yggchar_r), target :: x
  type(yggchar_r), pointer :: xp
  type(yggptr) :: y
  y = yggarg_scalar_init(x)
  xp => x
  y%type = "character"
  y%alloc = .true.
  if (associated(xp%x)) then
     y%ptr = c_loc(xp%x(1))
     y%prec = size(xp%x)
  else
     y%ptr = c_null_ptr
  end if
  y%nbytes = sizeof(x%x)
end function yggarg_scalar_yggchar_r
function yggarg_scalar_ply(x) result(y)
  type(yggply), target :: x
  type(yggply), pointer :: xp
  type(yggptr) :: y
  y = yggarg_scalar_init(x)
  xp => x
  y%type = "ply"
  y%ptr = c_loc(xp%material(1))
  y%nbytes = sizeof(x)
end function yggarg_scalar_ply
function yggarg_scalar_obj(x) result(y)
  type(yggobj), target :: x
  type(yggobj), pointer :: xp
  type(yggptr) :: y
  y = yggarg_scalar_init(x)
  xp => x
  y%type = "obj"
  y%ptr = c_loc(xp%material(1))
  y%nbytes = sizeof(x)
end function yggarg_scalar_obj
function yggarg_scalar_null(x) result(y)
  type(yggnull), target :: x
  type(yggnull), pointer :: xp
  type(yggptr) :: y
  y = yggarg_scalar_init(x)
  xp => x
  y%type = "null"
  y%ptr = c_loc(xp%ptr)
  y%nbytes = sizeof(x)
end function yggarg_scalar_null
function yggarg_scalar_generic(x) result(y)
  type(ygggeneric), target :: x
  type(ygggeneric), pointer :: xp
  type(yggptr) :: y
  y = yggarg_scalar_init(x)
  xp => x
  y%type = "generic"
  y%ptr = c_loc(xp%prefix)
  y%nbytes = sizeof(x)
end function yggarg_scalar_generic
function yggarg_scalar_yggarr(x) result(y)
  type(yggarr), target :: x
  type(yggarr), pointer :: xp
  type(yggptr) :: y
  y = yggarg_scalar_init(x)
  xp => x
  y%type = "array"
  y%ptr = c_loc(xp%prefix)
  y%nbytes = sizeof(x)
end function yggarg_scalar_yggarr
function yggarg_scalar_yggmap(x) result(y)
  type(yggmap), target :: x
  type(yggmap), pointer :: xp
  type(yggptr) :: y
  y = yggarg_scalar_init(x)
  xp => x
  y%type = "object"
  y%ptr = c_loc(xp%prefix)
  y%nbytes = sizeof(x)
end function yggarg_scalar_yggmap
function yggarg_scalar_yggschema(x) result(y)
  type(yggschema), target :: x
  type(yggschema), pointer :: xp
  type(yggptr) :: y
  y = yggarg_scalar_init(x)
  xp => x
  y%type = "schema"
  y%ptr = c_loc(xp%prefix)
  y%nbytes = sizeof(x)
end function yggarg_scalar_yggschema
function yggarg_scalar_yggpyinst(x) result(y)
  type(yggpyinst), target :: x
  type(yggpyinst), pointer :: xp
  type(yggptr) :: y
  y = yggarg_scalar_init(x)
  xp => x
  y%type = "instance"
  y%ptr = c_loc(xp%prefix)
  y%nbytes = sizeof(x)
end function yggarg_scalar_yggpyinst
function yggarg_scalar_yggpython(x) result(y)
  type(yggpython), target :: x
  type(yggpython), pointer :: xp
  type(yggptr) :: y
  y = yggarg_scalar_init(x)
  xp => x
  y%type = "python"
  y%ptr = c_loc(xp%name)
  y%nbytes = sizeof(x)
end function yggarg_scalar_yggpython
function yggarg_scalar_yggpyfunc(x) result(y)
  type(yggpyfunc), target :: x
  type(yggpyfunc), pointer :: xp
  type(yggptr) :: y
  y = yggarg_scalar_init(x)
  xp => x
  y%type = "class"
  y%ptr = c_loc(xp%name)
  y%nbytes = sizeof(x)
end function yggarg_scalar_yggpyfunc
function yggarg_scalar_yggptr(x) result(y)
  type(yggptr), target :: x
  type(yggptr) :: y
  y = x
end function yggarg_scalar_yggptr
! function yggarg_scalar_yggptr_arr(x) result(y)
!   ! TODO
!   type(yggptr_arr), target :: x
!   type(yggptr_arr), pointer :: xp
!   type(yggptr) :: y
!   y = yggarg_scalar_init(x)
!   xp => x
!   y%type = "array"
!   y%ptr = c_loc(xp%ptr)
!   y%nbytes = sizeof(x)
!   stop "yggarg_scalar_yggptr_arr: WIP"
! end function yggarg_scalar_yggptr_arr
! function yggarg_scalar_yggptr_map(x) result(y)
!   ! TODO
!   type(yggptr_map), target :: x
!   type(yggptr_map), pointer :: xp
!   type(yggptr) :: y
!   y = yggarg_scalar_init(x)
!   xp => x
!   y%type = "object"
!   y%ptr = c_loc(xp%ptr)
!   y%nbytes = sizeof(x)
!   stop "yggarg_scalar_yggptr_map: WIP"
! end function yggarg_scalar_yggptr_map

  
! 1D Reallocatable array versions
function yggarg_realloc_1darray_init(x) &
     result (y)
  class(*), target :: x
  type(yggptr) :: y
  y%item => x
  y%array = .true.
  y%alloc = .true.
  y%len = 1
  y%prec = 1
  y%ndim = 1
  y%ptr = c_null_ptr
end function yggarg_realloc_1darray_init
function yggarg_realloc_1darray_c_long(x) result (y)
  type(c_long_1d), target :: x
  type(c_long_1d), pointer :: xp
  type(yggptr) :: y
  y = yggarg_realloc_1darray_init(x)
  xp => x
  y%type = "c_long"
  if (associated(xp%x)) then
     y%ptr = c_loc(xp%x(1))
     y%len = size(xp%x)
  end if
end function yggarg_realloc_1darray_c_long
function yggarg_realloc_1darray_integer(x) result (y)
  type(integer_1d), target :: x
  type(integer_1d), pointer :: xp
  type(yggptr) :: y
  y = yggarg_realloc_1darray_init(x)
  xp => x
  y%type = "integer"
  if (associated(xp%x)) then
     y%ptr = c_loc(xp%x(1))
     y%len = size(xp%x)
  end if
end function yggarg_realloc_1darray_integer
function yggarg_realloc_1darray_integer2(x) result (y)
  type(integer2_1d), target :: x
  type(integer2_1d), pointer :: xp
  type(yggptr) :: y
  y = yggarg_realloc_1darray_init(x)
  xp => x
  y%type = "integer"
  if (associated(xp%x)) then
     y%ptr = c_loc(xp%x(1))
     y%len = size(xp%x)
  end if
end function yggarg_realloc_1darray_integer2
function yggarg_realloc_1darray_integer4(x) result (y)
  type(integer4_1d), target :: x
  type(integer4_1d), pointer :: xp
  type(yggptr) :: y
  y = yggarg_realloc_1darray_init(x)
  xp => x
  y%type = "integer"
  if (associated(xp%x)) then
     y%ptr = c_loc(xp%x(1))
     y%len = size(xp%x)
  end if
end function yggarg_realloc_1darray_integer4
function yggarg_realloc_1darray_integer8(x) result (y)
  type(integer8_1d), target :: x
  type(integer8_1d), pointer :: xp
  type(yggptr) :: y
  y = yggarg_realloc_1darray_init(x)
  xp => x
  y%type = "integer"
  if (associated(xp%x)) then
     y%ptr = c_loc(xp%x(1))
     y%len = size(xp%x)
  end if
end function yggarg_realloc_1darray_integer8
function yggarg_realloc_1darray_real(x) result (y)
  type(real_1d), target :: x
  type(real_1d), pointer :: xp
  type(yggptr) :: y
  y = yggarg_realloc_1darray_init(x)
  xp => x
  y%type = "real"
  if (associated(xp%x)) then
     y%ptr = c_loc(xp%x(1))
     y%len = size(xp%x)
  end if
end function yggarg_realloc_1darray_real
function yggarg_realloc_1darray_real4(x) result (y)
  type(real4_1d), target :: x
  type(real4_1d), pointer :: xp
  type(yggptr) :: y
  y = yggarg_realloc_1darray_init(x)
  xp => x
  y%type = "real"
  if (associated(xp%x)) then
     y%ptr = c_loc(xp%x(1))
     y%len = size(xp%x)
  end if
end function yggarg_realloc_1darray_real4
function yggarg_realloc_1darray_real8(x) result (y)
  type(real8_1d), target :: x
  type(real8_1d), pointer :: xp
  type(yggptr) :: y
  y = yggarg_realloc_1darray_init(x)
  xp => x
  y%type = "real"
  if (associated(xp%x)) then
     y%ptr = c_loc(xp%x(1))
     y%len = size(xp%x)
  end if
end function yggarg_realloc_1darray_real8
function yggarg_realloc_1darray_real16(x) result (y)
  type(real16_1d), target :: x
  type(real16_1d), pointer :: xp
  type(yggptr) :: y
  y = yggarg_realloc_1darray_init(x)
  xp => x
  y%type = "real"
  if (associated(xp%x)) then
     y%ptr = c_loc(xp%x(1))
     y%len = size(xp%x)
  end if
end function yggarg_realloc_1darray_real16
function yggarg_realloc_1darray_complex(x) result (y)
  type(complex_1d), target :: x
  type(complex_1d), pointer :: xp
  type(yggptr) :: y
  y = yggarg_realloc_1darray_init(x)
  xp => x
  y%type = "complex"
  if (associated(xp%x)) then
     y%ptr = c_loc(xp%x(1))
     y%len = size(xp%x)
  end if
end function yggarg_realloc_1darray_complex
function yggarg_realloc_1darray_complex4(x) result (y)
  type(complex4_1d), target :: x
  type(complex4_1d), pointer :: xp
  type(yggptr) :: y
  y = yggarg_realloc_1darray_init(x)
  xp => x
  y%type = "complex"
  if (associated(xp%x)) then
     y%ptr = c_loc(xp%x(1))
     y%len = size(xp%x)
  end if
end function yggarg_realloc_1darray_complex4
function yggarg_realloc_1darray_complex8(x) result (y)
  type(complex8_1d), target :: x
  type(complex8_1d), pointer :: xp
  type(yggptr) :: y
  y = yggarg_realloc_1darray_init(x)
  xp => x
  y%type = "complex"
  if (associated(xp%x)) then
     y%ptr = c_loc(xp%x(1))
     y%len = size(xp%x)
  end if
end function yggarg_realloc_1darray_complex8
function yggarg_realloc_1darray_complex16(x) result (y)
  type(complex16_1d), target :: x
  type(complex16_1d), pointer :: xp
  type(yggptr) :: y
  y = yggarg_realloc_1darray_init(x)
  xp => x
  y%type = "complex"
  if (associated(xp%x)) then
     y%ptr = c_loc(xp%x(1))
     y%len = size(xp%x)
  end if
end function yggarg_realloc_1darray_complex16
function yggarg_realloc_1darray_logical(x) result (y)
  type(logical_1d), target :: x
  type(logical_1d), pointer :: xp
  type(yggptr) :: y
  y = yggarg_realloc_1darray_init(x)
  xp => x
  y%type = "logical"
  if (associated(xp%x)) then
     y%ptr = c_loc(xp%x(1))
     y%len = size(xp%x)
  end if
end function yggarg_realloc_1darray_logical
function yggarg_realloc_1darray_logical1(x) result (y)
  type(logical1_1d), target :: x
  type(logical1_1d), pointer :: xp
  type(yggptr) :: y
  y = yggarg_realloc_1darray_init(x)
  xp => x
  y%type = "logical"
  if (associated(xp%x)) then
     y%ptr = c_loc(xp%x(1))
     y%len = size(xp%x)
  end if
end function yggarg_realloc_1darray_logical1
function yggarg_realloc_1darray_logical2(x) result (y)
  type(logical2_1d), target :: x
  type(logical2_1d), pointer :: xp
  type(yggptr) :: y
  y = yggarg_realloc_1darray_init(x)
  xp => x
  y%type = "logical"
  if (associated(xp%x)) then
     y%ptr = c_loc(xp%x(1))
     y%len = size(xp%x)
  end if
end function yggarg_realloc_1darray_logical2
function yggarg_realloc_1darray_logical4(x) result (y)
  type(logical4_1d), target :: x
  type(logical4_1d), pointer :: xp
  type(yggptr) :: y
  y = yggarg_realloc_1darray_init(x)
  xp => x
  y%type = "logical"
  if (associated(xp%x)) then
     y%ptr = c_loc(xp%x(1))
     y%len = size(xp%x)
  end if
end function yggarg_realloc_1darray_logical4
function yggarg_realloc_1darray_logical8(x) result (y)
  type(logical8_1d), target :: x
  type(logical8_1d), pointer :: xp
  type(yggptr) :: y
  y = yggarg_realloc_1darray_init(x)
  xp => x
  y%type = "logical"
  if (associated(xp%x)) then
     y%ptr = c_loc(xp%x(1))
     y%len = size(xp%x)
  end if
end function yggarg_realloc_1darray_logical8
function yggarg_realloc_1darray_character(x) result (y)
  type(character_1d), target :: x
  type(character_1d), pointer :: xp
  type(yggptr) :: y
  integer :: i
  integer(kind=c_size_t) :: j, ilength
  y = yggarg_realloc_1darray_init(x)
  xp => x
  y%type = "character"
  if (associated(xp%x)) then
     y%len = size(xp%x)
     if (associated(xp%x(1)%x)) then
        y%prec = size(xp%x(1)%x)
        allocate(y%data_character_unit(y%len * y%prec))
        do i = 1, size(xp%x)
           ilength = 0
           do j = 1, y%prec
              if (len_trim(xp%x(i)%x(j)) > 0) ilength = j
           end do
           do j = 1, ilength
              y%data_character_unit(((i-1)*y%prec) + j) = xp%x(i)%x(j)
           end do
           if (ilength.lt.y%prec) then
              y%data_character_unit(((i-1)*y%prec) + ilength + 1) = c_null_char
           end if
           do j = (ilength + 2), y%prec
              y%data_character_unit(((i-1)*y%prec) + j) = ' '
           end do
        end do
        y%ptr = c_loc(y%data_character_unit(1))
     end if
  end if
end function yggarg_realloc_1darray_character


! 1D array versions
function yggarg_1darray_init(x) result (y)
  class(*), dimension(:), target :: x
  type(yggptr) :: y
  y%item => x(1)
  y%item_array => x
  y%array = .true.
  y%alloc = .false.
  y%len = size(x)
  y%prec = 1
  y%ptr = c_null_ptr
end function yggarg_1darray_init
function yggarg_1darray_integer2(x) result (y)
  integer(kind=2), dimension(:), target :: x
  integer(kind=2), dimension(:), pointer :: xp
  type(yggptr) :: y
  xp => x
  y = yggarg_1darray_init(x)
  y%type = "integer"
  y%ptr = c_loc(xp(1))
end function yggarg_1darray_integer2
function yggarg_1darray_integer4(x) result (y)
  integer(kind=4), dimension(:), target :: x
  integer(kind=4), dimension(:), pointer :: xp
  type(yggptr) :: y
  xp => x
  y = yggarg_1darray_init(x)
  y%type = "integer"
  y%ptr = c_loc(xp(1))
end function yggarg_1darray_integer4
function yggarg_1darray_integer8(x) result (y)
  integer(kind=8), dimension(:), target :: x
  integer(kind=8), dimension(:), pointer :: xp
  type(yggptr) :: y
  xp => x
  y = yggarg_1darray_init(x)
  y%type = "integer"
  y%ptr = c_loc(xp(1))
end function yggarg_1darray_integer8
function yggarg_1darray_real4(x) result (y)
  real(kind=4), dimension(:), target :: x
  real(kind=4), dimension(:), pointer :: xp
  type(yggptr) :: y
  xp => x
  y = yggarg_1darray_init(x)
  y%type = "real"
  y%ptr = c_loc(xp(1))
end function yggarg_1darray_real4
function yggarg_1darray_real8(x) result (y)
  real(kind=8), dimension(:), target :: x
  real(kind=8), dimension(:), pointer :: xp
  type(yggptr) :: y
  xp => x
  y = yggarg_1darray_init(x)
  y%type = "real"
  y%ptr = c_loc(xp(1))
end function yggarg_1darray_real8
function yggarg_1darray_real16(x) result (y)
  real(kind=16), dimension(:), target :: x
  real(kind=16), dimension(:), pointer :: xp
  type(yggptr) :: y
  xp => x
  y = yggarg_1darray_init(x)
  y%type = "real"
  y%ptr = c_loc(xp(1))
end function yggarg_1darray_real16
function yggarg_1darray_complex4(x) result (y)
  complex(kind=4), dimension(:), target :: x
  complex(kind=4), dimension(:), pointer :: xp
  type(yggptr) :: y
  xp => x
  y = yggarg_1darray_init(x)
  y%type = "complex"
  y%ptr = c_loc(xp(1))
end function yggarg_1darray_complex4
function yggarg_1darray_complex8(x) result (y)
  complex(kind=8), dimension(:), target :: x
  complex(kind=8), dimension(:), pointer :: xp
  type(yggptr) :: y
  xp => x
  y = yggarg_1darray_init(x)
  y%type = "complex"
  y%ptr = c_loc(xp(1))
end function yggarg_1darray_complex8
function yggarg_1darray_complex16(x) result (y)
  complex(kind=16), dimension(:), target :: x
  complex(kind=16), dimension(:), pointer :: xp
  type(yggptr) :: y
  xp => x
  y = yggarg_1darray_init(x)
  y%type = "complex"
  y%ptr = c_loc(xp(1))
end function yggarg_1darray_complex16
function yggarg_1darray_logical1(x) result (y)
  logical(kind=1), dimension(:), target :: x
  logical(kind=1), dimension(:), pointer :: xp
  type(yggptr) :: y
  xp => x
  y = yggarg_1darray_init(x)
  y%type = "logical"
  y%ptr = c_loc(xp(1))
end function yggarg_1darray_logical1
function yggarg_1darray_logical2(x) result (y)
  logical(kind=2), dimension(:), target :: x
  logical(kind=2), dimension(:), pointer :: xp
  type(yggptr) :: y
  xp => x
  y = yggarg_1darray_init(x)
  y%type = "logical"
  y%ptr = c_loc(xp(1))
end function yggarg_1darray_logical2
function yggarg_1darray_logical4(x) result (y)
  logical(kind=4), dimension(:), target :: x
  logical(kind=4), dimension(:), pointer :: xp
  type(yggptr) :: y
  xp => x
  y = yggarg_1darray_init(x)
  y%type = "logical"
  y%ptr = c_loc(xp(1))
end function yggarg_1darray_logical4
function yggarg_1darray_logical8(x) result (y)
  logical(kind=8), dimension(:), target :: x
  logical(kind=8), dimension(:), pointer :: xp
  type(yggptr) :: y
  xp => x
  y = yggarg_1darray_init(x)
  y%type = "logical"
  y%ptr = c_loc(xp(1))
end function yggarg_1darray_logical8
function yggarg_1darray_character(x) result (y)
  character(len=*), dimension(:), target :: x
  character(len=len(x(1))), dimension(:), pointer :: xp
  type(yggptr) :: y
  integer :: i, ilength
  xp => x
  y = yggarg_1darray_init(x)
  y%type = "character"
  y%prec = len(xp(1))
  do i = 1, size(xp)
     ilength = len_trim(xp(i))
     if (ilength.lt.y%prec) then
        xp(i)((ilength+1):(ilength+1)) = c_null_char
     end if
  end do
  allocate(y%data_character_unit(y%len * y%prec))
  y%data_character_unit = transfer(x, y%data_character_unit)
  y%ptr = c_loc(y%data_character_unit(1))
end function yggarg_1darray_character
function yggarg_1darray_yggchar_r(x) result (y)
  type(yggchar_r), dimension(:), target :: x
  type(yggchar_r), dimension(:), pointer :: xp
  type(yggptr) :: y
  integer :: i, j, ilength
  xp => x
  y = yggarg_1darray_init(x)
  y%type = "character"
  if ((associated(xp(1)%x)).and.(size(xp(1)%x).ge.1)) then
     y%prec = size(xp(1)%x)
     allocate(y%data_character_unit(y%len * y%prec))
     do i = 1, size(xp)
        ilength = 0
        do j = 1, ilength
           if (len_trim(xp(i)%x(j)) > 0) ilength = j
        end do
        do j = 1, ilength
           y%data_character_unit(((i-1)*y%prec) + j) = xp(i)%x(j)
        end do
        if (ilength.lt.size(xp(i)%x)) then
           y%data_character_unit(((i-1)*y%prec) + ilength + 1) = c_null_char
        end if
        do j = (ilength + 2), size(xp(i)%x)
           y%data_character_unit(((i-1)*y%prec) + j) = ' '
        end do
     end do
     y%ptr = c_loc(y%data_character_unit(1))
  end if
end function yggarg_1darray_yggchar_r
