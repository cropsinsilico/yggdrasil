module fygg
  use iso_c_binding
  implicit none

  interface yggarg
     module procedure yggarg_scalar
     module procedure yggarg_array
  end interface yggarg
  interface yggarg_realloc
     module procedure yggarg_realloc_scalar
     ! module procedure yggarg_realloc_array
  end interface yggarg_realloc
  type :: yggptr
     type(c_ptr) :: ptr
     class(*), pointer :: item
     class(*), dimension(:), pointer :: item_array
     class(*), allocatable :: item_alloc
     class(*), allocatable, dimension(:) :: item_array_alloc
     character(len=15) :: type
     character, dimension(:), pointer :: data_character_unit
     logical :: array
     logical :: alloc
     integer :: len
     integer :: prec
     integer(kind=c_size_t), pointer :: len_c
     type(c_ptr) :: len_ptr
     integer(kind=c_size_t), pointer :: prec_c
     type(c_ptr) :: prec_ptr
  end type yggptr
  type :: yggcomm
     type(c_ptr) :: comm
  end type yggcomm

  public :: yggarg, yggcomm, yggptr

  INCLUDE "YggInterface_cdef.f90"

contains

  function yggptr_c2f(x) result(flag)
    implicit none
    type(yggptr) :: x
    integer, pointer :: x_integer
    real, pointer :: x_real
    complex, pointer :: x_complex
    logical, pointer :: x_logical
    character(len=:), pointer :: x_character
    integer(kind=c_size_t), pointer :: x_size_t
    integer, dimension(:), pointer :: xarr_integer
    real, dimension(:), pointer :: xarr_real
    complex, dimension(:), pointer :: xarr_complex
    logical, dimension(:), pointer :: xarr_logical
    character(len=:), dimension(:), pointer :: xarr_character
    integer(kind=c_size_t), dimension(:), pointer :: xarr_size_t
    integer(kind=c_size_t), pointer :: array_len
    integer(kind=c_size_t), pointer :: precision
    integer(kind=8) :: i, diff
    integer :: flag
    flag = 0
    allocate(array_len)
    allocate(precision)
    array_len = 1
    precision = 1
    if (x%array) then
       call c_f_pointer(x%len_ptr, array_len)
       print *, "array_len ", array_len
    end if
    if (x%type.eq."character") then
       call c_f_pointer(x%prec_ptr, precision)
       print *, "precision ", precision
    end if
    if (x%alloc) then
       print *, "allocated missing logic"
       if ((array_len.gt.x%len).or.(precision.gt.x%prec)) then
          print *, array_len, x%len
          if (x%array) then
             select type(item=>x%item_array)
             type is (integer)
                xarr_integer => item
                deallocate(xarr_integer);
                allocate(xarr_integer(array_len))
             type is (real)
                xarr_real => item
                deallocate(xarr_real)
                allocate(xarr_real(array_len))
             type is (complex)
                xarr_complex => item
                deallocate(xarr_complex)
                allocate(xarr_complex(array_len))
             type is (logical)
                xarr_logical => item
                deallocate(xarr_logical)
                allocate(xarr_logical(array_len))
             type is (character(*))
                xarr_character => item
                deallocate(xarr_character)
                allocate(character(len=precision) :: xarr_character(array_len))
             type is (integer(kind=c_size_t))
                xarr_size_t => item
                deallocate(xarr_size_t)
                allocate(xarr_size_t(array_len))
             class default
                stop 'Unexpected type.'
             end select
          else
             select type(item=>x%item)
             type is (character(*))
                x_character => item
                deallocate(x_character)
                allocate(character(len=precision) :: x_character)
             class default
                stop 'Unexpected type.'
             end select
          end if
       end if
    end if
    select type(item=>x%item)
    type is (integer)
       x_integer => item
       call c_f_pointer(x%ptr, x_integer, [x%len])
    type is (real)
       x_real => item
       call c_f_pointer(x%ptr, x_real, [x%len])
    type is (complex)
       x_complex => item
       call c_f_pointer(x%ptr, x_complex, [x%len])
    type is (logical)
       x_logical => item
       call c_f_pointer(x%ptr, x_logical, [x%len])
    type is (character(*))
       ! TODO: Array
       x_character => item
       diff = len(x_character) - precision
       if (diff.lt.0) then
          print *, "Message truncated by ", diff, " characters"
          flag = -1
       else
          do i = 1, precision
             x_character(i:i) = x%data_character_unit(i)
          end do
          do i = (precision + 1), len(x_character)
             x_character(i:i) = ' '
          end do
       end if
       deallocate(x%data_character_unit)
    type is (integer(kind=c_size_t))
       x_size_t => item
       call c_f_pointer(x%ptr, x_size_t, [x%len])
    class default
       stop 'Unexpected type.'
    end select
  end function yggptr_c2f
  
  ! Scalar versions
  function yggarg_scalar(x) result(y)
    class(*), target :: x
    type(yggptr) :: y
    integer, pointer :: x_integer
    real, pointer :: x_real
    complex, pointer :: x_complex
    logical, pointer :: x_logical
    character(len=:), pointer :: x_character
    integer(kind=c_size_t), pointer :: x_size_t
    y%item => x
    y%array = .false.
    y%alloc = .false.
    y%len = 1
    y%prec = 1
    select type(x)
    type is (integer)
       y%type = "integer"
       x_integer => x
       y%ptr = c_loc(x_integer)
    type is (real)
       y%type = "real"
       x_real => x
       y%ptr = c_loc(x_real)
    type is (complex)
       y%type = "complex"
       x_complex => x
       y%ptr = c_loc(x_complex)
    type is (logical)
       y%type = "logical"
       x_logical => x
       y%ptr = c_loc(x_logical)
    type is (character(*))
       y%type = "character"
       x_character => x
       allocate (y%data_character_unit(len(x_character)))
       y%data_character_unit = transfer(x_character, &
            y%data_character_unit)
       y%data_character_unit(len_trim(x_character) + 1) = c_null_char
       y%ptr = c_loc(y%data_character_unit(1))
       y%prec = len(x_character)
    type is (integer(kind=c_size_t))
       y%type = "size_t"
       x_size_t => x
       y%ptr = c_loc(x_size_t)
    class default
       stop 'Unexpected type.'
    end select
  end function yggarg_scalar
  function yggarg_realloc_scalar(x) result(y)
    class(*), allocatable, target :: x
    type(yggptr) :: y
    integer, allocatable, target :: x_integer
    real, allocatable, target :: x_real
    complex, allocatable, target :: x_complex
    logical, allocatable, target :: x_logical
    character(len=1), allocatable, target :: x_character
    integer(kind=c_size_t), allocatable, target :: x_size_t
    if (.not.allocated(x)) then
       select type(x)
       type is (integer)
          x_integer = x
          allocate(x_integer)
       type is (real)
          x_real = x
          allocate(x_real)
       type is (complex)
          x_complex = x
          allocate(x_complex)
       type is (logical)
          x_logical = x
          allocate(x_logical)
       type is (character(*))
          x_character = x
          allocate(x_character)
       type is (integer(kind=c_size_t))
          x_size_t = x
          allocate(x_size_t)
       class default
          stop 'Unexpected type.'
       end select
    end if
    y = yggarg(x)
    y%alloc = .true.
  end function yggarg_realloc_scalar
  ! function yggarg_char_realloc(x) result(y)
  !   character(len=:), allocatable, target :: x
  !   type(yggptr) :: y
  !   y%type = "character"
  !   if (.not.(allocated(x))) then
  !      allocate(character(len=1) :: x)
  !   end if
  !   y%data_character_full => x
  !   ! if (allocated(x)) then
  !   allocate(y%data_character_unit(len(x)))
  !   y%data_character_unit = transfer(x, y%data_character_unit)
  !   y%data_character_unit(len_trim(x) + 1) = c_null_char
  !   y%ptr = c_loc(y%data_character_unit(1))
  !   y%len = len(x)
  !   ! else
  !   !    y%ptr = c_null_ptr
  !   !    y%len = 0
  !   ! end if
  !   y%array = .true.
  !   y%alloc = .true.
  ! end function yggarg_char_realloc
  
  ! Array versions
  function yggarg_array(x) result(y)
    class(*), dimension(:), target :: x
    type(yggptr) :: y
    integer, dimension(:), pointer :: x_integer
    real, dimension(:), pointer :: x_real
    complex, dimension(:), pointer :: x_complex
    logical, dimension(:), pointer :: x_logical
    character(len=:), dimension(:), pointer :: x_character
    integer(kind=c_size_t), dimension(:), pointer :: x_size_t
    integer :: i
    y%item => x(1)
    y%item_array => x
    y%array = .true.
    y%alloc = .false.
    y%len = size(x)
    y%prec = 1
    select type(item=>y%item_array)
    type is (integer)
       y%type = "integer"
       x_integer => item
       y%ptr = c_loc(x_integer(1))
    type is (real)
       y%type = "real"
       x_real => item
       y%ptr = c_loc(x_real(1))
    type is (complex)
       y%type = "complex"
       x_complex => item
       y%ptr = c_loc(x_complex(1))
    type is (logical)
       y%type = "logical"
       x_logical => item
       y%ptr = c_loc(x_logical(1))
    type is (character(*))
       y%type = "character"
       x_character => item
       y%prec = len(x_character(1))
       allocate(y%data_character_unit(y%len * y%prec))
       y%data_character_unit = transfer(x_character, &
            y%data_character_unit)
       do i = 1, size(x_character)
          y%data_character_unit(((i - 1) * len(x_character(1))) &
               + len_trim(x_character) + 1) = c_null_char
       end do
       y%ptr = c_loc(y%data_character_unit(1))
    type is (integer(kind=c_size_t))
       y%type = "size_t"
       x_size_t => item
       y%ptr = c_loc(x_size_t(1))
    class default
       stop 'Unexpected type.'
    end select
  end function yggarg_array

  ! YggInterface
  function ygg_output(name) result(channel)
    implicit none
    character(len=*), intent(in) :: name
    character(len=len_trim(name)+1) :: c_name
    type(yggcomm) :: channel
    c_name = trim(name)//c_null_char
    channel%comm = ygg_output_c(c_name)
  end function ygg_output
  
  function ygg_input(name) result(channel)
    implicit none
    character(len=*), intent(in) :: name
    character(len=len_trim(name)+1) :: c_name
    type(yggcomm) :: channel
    c_name = trim(name)//c_null_char
    channel%comm = ygg_input_c(c_name)
  end function ygg_input
  
  function ygg_send(ygg_q, data, data_len) result (flag)
    implicit none
    type(yggcomm), intent(in) :: ygg_q
    type(c_ptr) :: c_ygg_q
    character(len=*), intent(in) :: data
    character(len=len(data)+1) :: c_data
    integer, intent(in) :: data_len
    integer(kind=c_int) :: c_data_len
    integer :: flag
    integer(kind=c_int) :: c_flag
    c_ygg_q = ygg_q%comm
    c_data = data//c_null_char
    c_data_len = data_len
    c_flag = ygg_send_c(c_ygg_q, c_data, c_data_len)
    flag = c_flag
  end function ygg_send
  
  function ygg_recv(ygg_q, data, data_len) result (flag)
    implicit none
    type(yggcomm) :: ygg_q
    type(c_ptr) :: c_ygg_q
    character(len=*) :: data
    character(len=len(data)+1) :: c_data
    integer, intent(in) :: data_len
    integer(kind=c_int) :: c_data_len
    integer :: flag
    integer(kind=c_int) :: c_flag
    c_ygg_q = ygg_q%comm
    c_data = data//c_null_char
    c_data_len = data_len
    c_flag = ygg_recv_c(c_ygg_q, c_data, c_data_len)
    flag = c_flag
    data = c_data(:flag)
  end function ygg_recv

  function ygg_send_var(ygg_q, args) result (flag)
    implicit none
    type(yggcomm), intent(in) :: ygg_q
    type(c_ptr) :: c_ygg_q
    type(yggptr) :: args(:)
    type(c_ptr), target :: c_args(size(args))
    integer :: c_nargs
    integer :: flag, i
    integer(kind=c_int) :: c_flag
    c_ygg_q = ygg_q%comm
    c_nargs = size(args)
    do i = 1, size(args)
       c_args(i) = args(i)%ptr
    end do
    c_flag = ygg_send_var_c(c_ygg_q, c_nargs, c_loc(c_args(1)))
    flag = c_flag
  end function ygg_send_var

  subroutine pre_recv(args, c_args)
    implicit none
    type(yggptr) :: args(:)
    type(c_ptr), allocatable, target :: c_args(:)
    integer :: i, j
    integer :: nargs
    integer(kind=c_size_t) :: len_args(size(args))
    nargs = size(args)
    do i = 1, size(args)
       if ((args(i)%type.eq."character").and. &
            ((i + 1) > size(args)).or. &
            (args(i+1)%type.ne."size_t")) then
          nargs = nargs + 1
       end if
       if (args(i)%array) then
          nargs = nargs + 1
       end if
    end do
    allocate(c_args(nargs))
    j = 1
    do i = 1, size(args)
       c_args(j) = args(i)%ptr
       j = j + 1
       if (args(i)%type.eq."character") then
          if (((i + 1) <= size(args)).and.(args(i+1)%type.eq."size_t")) then
             args(i)%prec_ptr = args(i+1)%ptr
          else
             args(i)%prec_c = args(i)%prec
             args(i)%prec_ptr = c_loc(args(i)%prec_c)
          end if
          c_args(j) = args(i)%prec_ptr
          j = j + 1
       end if
       if (args(i)%array) then
          args(i)%len_c = args(i)%len
          args(i)%len_ptr = c_loc(args(i)%len_c)
          c_args(j) = args(i)%len_ptr
          j = j + 1
       end if
    end do
  end subroutine pre_recv

  subroutine post_recv(args, c_args, flag)
    implicit none
    type(yggptr) :: args(:)
    type(c_ptr), allocatable, target :: c_args(:)
    integer :: flag, i, j
    if (flag.ge.0) then
       j = 1
       do i = 1, size(args)
          args(i)%ptr = c_args(j)
          flag = yggptr_c2f(args(i))
          if (flag.lt.0) then
             print *, "Error recovering fortran pointer for ", i, &
                  "th variable."
             exit
          end if
          j = j + 1
          if ((args(i)%type.eq."character").and. &
               ((i + 1) > size(args)).or. &
               (args(i+1)%type.ne."size_t")) then
             j = j + 1
          end if
          if (args(i)%array) then
             j = j + 1
          end if
       end do
    end if
    if (allocated(c_args)) then
       deallocate(c_args)
    end if
  end subroutine post_recv
  
  function ygg_recv_var(ygg_q, args) result (flag)
    implicit none
    type(yggcomm) :: ygg_q
    type(c_ptr) :: c_ygg_q
    type(yggptr) :: args(:)
    type(c_ptr), allocatable, target :: c_args(:)
    integer :: c_nargs
    integer :: flag, i
    integer(kind=c_int) :: c_flag
    c_ygg_q = ygg_q%comm
    call pre_recv(args, c_args)
    c_nargs = size(args)
    print *, "before call"
    c_flag = ygg_recv_var_c(c_ygg_q, c_nargs, c_loc(c_args(1)))
    print *, "after call"
    flag = c_flag
    call post_recv(args, c_args, flag)
    print *, "after post"
  end function ygg_recv_var
  
  function ygg_recv_var_realloc(ygg_q, args) result (flag)
    implicit none
    type(yggcomm) :: ygg_q
    type(c_ptr) :: c_ygg_q
    type(yggptr), target :: args(:)
    type(c_ptr), allocatable, target :: c_args(:)
    integer :: c_nargs
    integer :: flag, i
    integer(kind=c_int) :: c_flag
    c_ygg_q = ygg_q%comm
    flag = 0
    do i = 1, size(args)
       if ((args(i)%array.or.(args(i)%type.eq."character")) &
            .and.(.not.(args(i)%alloc))) then
          print *, "Array provided as element ", i, " is not allocatable."
          flag = -1
       end if
    end do
    if (flag.ge.0) then
       call pre_recv(args, c_args)
       c_nargs = size(args)
       c_flag = ygg_recv_var_realloc_c(c_ygg_q, c_nargs, c_loc(c_args(1)))
       flag = c_flag
    end if
    call post_recv(args, c_args, flag)
  end function ygg_recv_var_realloc
  
end module fygg
