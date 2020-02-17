module fygg
  use iso_c_binding
  implicit none

  interface yggarg
     module procedure yggarg_int
     module procedure yggarg_real
     module procedure yggarg_complex
     module procedure yggarg_logical
     module procedure yggarg_char
     module procedure yggarg_c_size_t
     module procedure yggarg_int_arr
     module procedure yggarg_real_arr
     module procedure yggarg_complex_arr
     module procedure yggarg_logical_arr
     ! module procedure yggarg_char_arr
     ! module procedure yggarg_c_size_t_arr
  end interface yggarg
  type :: yggptr
     type(c_ptr) :: ptr
     character(len=15) :: type
     integer, pointer :: data_integer
     real, pointer :: data_real
     complex, pointer :: data_complex
     logical, pointer :: data_logical
     character, dimension(:), pointer :: data_character_unit
     character(len=1024), pointer :: data_character_full
     integer(kind=c_size_t), pointer :: data_size_t
     logical :: is_char
     integer :: len
  end type yggptr
  type :: yggcomm
     type(c_ptr) :: comm
  end type yggcomm

  public :: yggarg, yggcomm, yggptr

  INCLUDE "YggInterface_cdef.f90"

contains

  subroutine yggptr_c2f(x)
    implicit none
    type(yggptr) :: x
    character(len=1024), pointer :: temp_char
    integer(kind=c_size_t), pointer :: temp_size_t
    integer :: i
    if (x%type == "integer") then
       call c_f_pointer(x%ptr, x%data_integer, [x%len])
    else if (x%type == "real") then
       call c_f_pointer(x%ptr, x%data_real, [x%len])
    else if (x%type == "complex") then
       call c_f_pointer(x%ptr, x%data_complex, [x%len])
    else if (x%type == "logical") then
       call c_f_pointer(x%ptr, x%data_logical, [x%len])
    else if (x%type == "character") then
       ! call c_f_pointer(x%ptr, x%data_character_full, [x%len])
       ! call c_f_pointer(x%ptr, temp_char) ! , [x%len])
       ! x%data_character_full => temp_char
       ! x%data_character_full = transfer(x%data_character_unit, &
       !      x%data_character_full)
       ! deallocate(x%data_character_unit)
       do i = 1, size(x%data_character_unit)
          x%data_character_full(i:i) = x%data_character_unit(i)
       end do
    else if (x%type == "size_t") then
       call c_f_pointer(x%ptr, x%data_size_t, [x%len])
    end if
  end subroutine yggptr_c2f
  
  ! Scalar versions
  function yggarg_int(x) result(y)
    integer, target :: x
    type(yggptr) :: y
    y%type = "integer"
    y%data_integer => x
    y%ptr = c_loc(x)
    y%is_char = .false.
    y%len = 1
  end function yggarg_int
  function yggarg_real(x) result(y)
    real, target :: x
    type(yggptr) :: y
    y%type = "real"
    y%data_real => x
    y%ptr = c_loc(x)
    y%is_char = .false.
    y%len = 1
  end function yggarg_real
  function yggarg_complex(x) result(y)
    complex, target :: x
    type(yggptr) :: y
    y%type = "complex"
    y%data_complex => x
    y%ptr = c_loc(x)
    y%is_char = .false.
    y%len = 1
  end function yggarg_complex
  function yggarg_logical(x) result(y)
    logical, target :: x
    type(yggptr) :: y
    y%type = "logical"
    y%data_logical => x
    y%ptr = c_loc(x)
    y%is_char = .false.
    y%len = 1
  end function yggarg_logical
  function yggarg_char(x) result(y)
    character(len=*), target :: x
    type(yggptr) :: y
    y%type = "character"
    y%data_character_full => x
    allocate (y%data_character_unit(len(x)))
    y%data_character_unit = transfer(x, y%data_character_unit)
    y%data_character_unit(len_trim(x) + 1) = c_null_char
    y%ptr = c_loc(y%data_character_unit(1))
    y%is_char = .true.
    y%len = len(x)
  end function yggarg_char
  ! function yggarg_char_realloc(x) result(y)
  !   character(len=*), allocatable :: x
  !   type(yggptr) :: y
  !   y%type = "character"
  !   y%data_character_full = x
  !   allocate (y%data_character_unit(len(x)))
  !   y%data_character_unit = transfer(x, y%data_character_unit)
  !   y%data_character_unit(len_trim(x) + 1) = c_null_char
  !   y%ptr = c_loc(y%data_character_unit(1))
  !   y%is_char = .true.
  !   y%len = len(x)
  ! end function yggarg_char_realloc
  function yggarg_c_size_t(x) result(y)
    integer(kind=c_size_t), target :: x
    type(yggptr) :: y
    y%type = "size_t"
    y%data_size_t => x
    y%ptr = c_loc(x)
    y%is_char = .false.
    y%len = 1
  end function yggarg_c_size_t
  
  ! Array versions
  function yggarg_int_arr(x) result(y)
    integer, dimension(:), target :: x
    type(yggptr) :: y
    y%type = "integer"
    y%data_integer => x(1)
    y%ptr = c_loc(y%data_integer)
    y%is_char = .false.
    y%len = size(x)
  end function yggarg_int_arr
  function yggarg_real_arr(x) result(y)
    real, dimension(:), target :: x
    type(yggptr) :: y
    y%type = "real"
    y%data_real => x(1)
    y%ptr = c_loc(y%data_real)
    y%is_char = .false.
    y%len = size(x)
  end function yggarg_real_arr
  function yggarg_complex_arr(x) result(y)
    complex, dimension(:), target :: x
    type(yggptr) :: y
    y%type = "complex"
    y%data_complex => x(1)
    y%ptr = c_loc(y%data_complex)
    y%is_char = .false.
    y%len = size(x)
  end function yggarg_complex_arr
  function yggarg_logical_arr(x) result(y)
    logical, dimension(:), target :: x
    type(yggptr) :: y
    y%type = "logical"
    y%data_logical => x(1)
    y%ptr = c_loc(y%data_logical)
    y%is_char = .false.
    y%len = size(x)
  end function yggarg_logical_arr
  ! function yggarg_char_arr(x) result(y)
  !   character, dimension(:), target :: x
  !   type(yggptr) :: y
  !   y%type = "character"
  !   y%data_character => x(1)
  !   y%ptr = c_loc(y%data_character)
  !   y%is_char = .true.
  !   y%len = size(x)
  ! end function yggarg_char_arr
  ! function yggarg_c_size_t_arr(x) result(y)
  !   integer(kind=c_size_t), dimension(:), target :: x
  !   type(yggptr) :: y
  !   y%type = "c_size_t"
  !   y%data_integer => x(1)
  !   y%ptr = c_loc(y%data_integer)
  !   y%is_char = .false.
  !   y%len = size(x)
  ! end function yggarg_c_size_t_arr

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
  
  function ygg_recv_var(ygg_q, args) result (flag)
    implicit none
    type(yggcomm) :: ygg_q
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
    c_flag = ygg_recv_var_c(c_ygg_q, c_nargs, c_loc(c_args(1)))
    flag = c_flag
    if (flag.ge.0) then
       do i = 1, size(args)
          args(i)%ptr = c_args(i)
          call yggptr_c2f(args(i))
       end do
    end if
  end function ygg_recv_var
  
  function ygg_recv_var_realloc(ygg_q, args) result (flag)
    implicit none
    type(yggcomm) :: ygg_q
    type(c_ptr) :: c_ygg_q
    type(yggptr), target :: args(:)
    type(c_ptr), target :: c_args(size(args))
    integer :: c_nargs
    integer :: flag, i
    integer(kind=c_int) :: c_flag
    c_ygg_q = ygg_q%comm
    c_nargs = size(args)
    flag = 0
    do i = 1, size(args)
       c_args(i) = args(i)%ptr
    end do
    if (flag.ge.0) then
       c_flag = ygg_recv_var_realloc_c(c_ygg_q, c_nargs, c_loc(c_args(1)))
       flag = c_flag
       if (flag.ge.0) then
          do i = 1, size(args)
             args(i)%ptr = c_args(i)
             call yggptr_c2f(args(i))
          end do
       end if
    end if
  end function ygg_recv_var_realloc
  
end module fygg
