module fygg
  use iso_c_binding
  implicit none

  integer, parameter :: LINE_SIZE_MAX = 2048

  interface yggarg
     module procedure yggarg_scalar
     module procedure yggarg_array
  end interface yggarg
  interface yggarg_realloc
     module procedure yggarg_realloc_scalar
     module procedure yggarg_realloc_array_integer
     module procedure yggarg_realloc_array_real
     module procedure yggarg_realloc_array_complex
     module procedure yggarg_realloc_array_logical
     module procedure yggarg_realloc_array_character
     module procedure yggarg_realloc_array_size_t
     ! module procedure yggarg_realloc_array
     ! module procedure yggarg_char_realloc
  end interface yggarg_realloc
  type :: yggptr
     type(c_ptr) :: ptr
     class(*), pointer :: item
     class(*), dimension(:), pointer :: item_array
     class(*), allocatable :: item_alloc
     class(*), allocatable, dimension(:) :: item_array_alloc
     character(len=15) :: type
     character, dimension(:), pointer :: item_char_array
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

  public :: yggarg, yggarg_realloc, yggcomm, yggptr, &
       LINE_SIZE_MAX

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
    character, dimension(:), pointer :: xarr_character
    integer(kind=c_size_t), dimension(:), pointer :: xarr_size_t
    integer(kind=c_size_t), pointer :: array_len
    integer(kind=c_size_t), pointer :: precision
    integer(kind=8) :: i, diff
    integer :: flag
    flag = 0
    print *, "begin yggptr_c2f"
    allocate(array_len)
    allocate(precision)
    array_len = 1
    precision = 1
    if (x%array) then
       call c_f_pointer(x%len_ptr, array_len)
       print *, "array_len ", array_len
    else if (x%type.eq."character") then
       call c_f_pointer(x%prec_ptr, precision)
       print *, "precision ", precision
    end if
    if (x%alloc) then
       print *, "begen realloc"
       if ((array_len*precision).gt.x%len) then
          print *, "reallocating ", x%type, x%array
          if (x%array) then
             if (x%type.eq."character") then
                ! xarr_character = x%item_char_array
                print *, "before dealloc"
                deallocate(x%item_char_array)
                ! deallocate(xarr_character)
                print *, "after dealloc, before alloc"
                allocate(x%item_char_array(array_len*precision))
                ! allocate(xarr_character(array_len*precision))
                print *, "after alloc"
             else
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
                   allocate(xarr_character(array_len*precision))
                type is (integer(kind=c_size_t))
                   xarr_size_t => item
                   deallocate(xarr_size_t)
                   allocate(xarr_size_t(array_len))
                class default
                   stop 'Unexpected type.'
                end select
             end if
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
       print *, "done alloc"
    end if
    if ((x%type.eq."character").and.x%array) then
       xarr_character => x%item_char_array
       diff = size(xarr_character) - array_len
       if (diff.lt.0) then
          print *, "Message truncated by ", diff, " characters"
          flag = -1
       else
          do i = 1, array_len
             xarr_character(i) = x%data_character_unit(i)
          end do
          do i = (array_len + 1), size(xarr_character)
             xarr_character(i) = ' '
          end do
       end if
    else
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
          if (x%array) then
             stop "Character array stored as item?"
          else
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
          end if
          deallocate(x%data_character_unit)
       type is (integer(kind=c_size_t))
          x_size_t => item
          call c_f_pointer(x%ptr, x_size_t, [x%len])
       class default
          stop 'Unexpected type.'
       end select
    end if
    if ((x%array).or.(x%type.eq."character")) then
       deallocate(x%len_c)
       deallocate(x%prec_c)
    end if
    deallocate(array_len)
    deallocate(precision)
    print *, "end yggptr_c2f"
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
       allocate(y%data_character_unit(len(x_character)))
       y%data_character_unit = transfer(x_character, &
            y%data_character_unit)
       y%data_character_unit(len_trim(x_character) + 1) = c_null_char
       y%ptr = c_loc(y%data_character_unit(1))
       y%prec = len(x_character)
       allocate(y%len_c)
       allocate(y%prec_c)
       y%len_c = 1
       y%prec_c = 1
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
    character, allocatable, target :: x_character
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
  !   character(len=*), allocatable, target :: x
  !   type(yggptr) :: y
  !   y%type = "character"
  !   if (.not.(allocated(x))) then
  !      allocate(character(len=1) :: x)
  !   end if
  !   y%item => x
  !   allocate(y%data_character_unit(len(x)))
  !   y%data_character_unit = transfer(x, y%data_character_unit)
  !   y%data_character_unit(len_trim(x) + 1) = c_null_char
  !   y%ptr = c_loc(y%data_character_unit(1))
  !   y%len = 1
  !   y%prec = len(x)
  !   y%array = .false.
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
    character, dimension(:), pointer :: x_character
    integer(kind=c_size_t), dimension(:), pointer :: x_size_t
    integer :: i
    y%item => x(1)
    y%item_array => x
    y%array = .true.
    y%alloc = .false.
    y%len = size(x)
    y%prec = 1
    allocate(y%len_c)
    allocate(y%prec_c)
    y%len_c = 1
    y%prec_c = 1
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
       ! do i = 1, size(x_character)
       !    y%data_character_unit(((i - 1) * len(x_character(1))) &
       !         + len_trim(x_character) + 1) = c_null_char
       ! end do
       y%ptr = c_loc(y%data_character_unit(1))
    type is (integer(kind=c_size_t))
       y%type = "size_t"
       x_size_t => item
       y%ptr = c_loc(x_size_t(1))
    class default
       stop 'Unexpected type.'
    end select
  end function yggarg_array
  function yggarg_realloc_array_integer(x) result (y)
    integer, dimension(:), pointer :: x
    type(yggptr) :: y
    nullify(x)
    allocate(x(1))
    y = yggarg(x)
    y%alloc = .true.
  end function yggarg_realloc_array_integer
  function yggarg_realloc_array_real(x) result (y)
    real, dimension(:), pointer :: x
    type(yggptr) :: y
    nullify(x)
    allocate(x(1))
    y = yggarg(x)
    y%alloc = .true.
  end function yggarg_realloc_array_real
  function yggarg_realloc_array_complex(x) result (y)
    complex, dimension(:), pointer :: x
    type(yggptr) :: y
    nullify(x)
    allocate(x(1))
    y = yggarg(x)
    y%alloc = .true.
  end function yggarg_realloc_array_complex
  function yggarg_realloc_array_logical(x) result (y)
    logical, dimension(:), pointer :: x
    type(yggptr) :: y
    nullify(x)
    allocate(x(1))
    y = yggarg(x)
    y%alloc = .true.
  end function yggarg_realloc_array_logical
  function yggarg_realloc_array_character(x) result (y)
    character, dimension(:), pointer :: x
    type(yggptr) :: y
    nullify(x)
    ! allocate(x(1))
    ! y = yggarg(x)
    ! y%item => x(1)
    ! y%item_array = x
    y%item_char_array = x
    allocate(y%item_char_array(1))
    y%array = .true.
    y%len = size(x)
    y%alloc = .true.
    y%type = "character"
    y%prec = len(x(1))
    allocate(y%data_character_unit(y%len * y%prec))
    y%data_character_unit = transfer(x, y%data_character_unit)
    y%ptr = c_loc(y%data_character_unit(1))
    allocate(y%len_c)
    allocate(y%prec_c)
    y%len_c = 1
    y%prec_c = 1
  end function yggarg_realloc_array_character
  function yggarg_realloc_array_size_t(x) result (y)
    integer(kind=c_size_t), dimension(:), pointer :: x
    type(yggptr) :: y
    nullify(x)
    allocate(x(1))
    y = yggarg(x)
    y%alloc = .true.
  end function yggarg_realloc_array_size_t
  ! function yggarg_realloc_array(x) result(y)
  !   class(*), dimension(:), pointer :: x
  !   type(yggptr) :: y
  !   integer, dimension(:), pointer :: x_integer
  !   real, dimension(:), pointer :: x_real
  !   complex, dimension(:), pointer :: x_complex
  !   logical, dimension(:), pointer :: x_logical
  !   character(len=1), dimension(:), pointer :: x_character
  !   integer(kind=c_size_t), dimension(:), pointer :: x_size_t
  !   nullify(x)
  !   ! if (associated(x)) then
  !   !    stop 'Pointer is already associated and so cannot be allocated.'
  !   ! end if
  !   ! if (.not.allocated(x)) then
  !   if (.not.associated(x)) then
  !      select type(x)
  !      type is (integer)
  !         x_integer = x
  !         allocate(x_integer(1))
  !      type is (real)
  !         x_real = x
  !         allocate(x_real(1))
  !      type is (complex)
  !         x_complex = x
  !         allocate(x_complex(1))
  !      type is (logical)
  !         x_logical = x
  !         allocate(x_logical(1))
  !      type is (character(*))
  !         x_character = x
  !         allocate(x_character(1))
  !      type is (integer(kind=c_size_t))
  !         x_size_t = x
  !         allocate(x_size_t(1))
  !      class default
  !         stop 'Unexpected type.'
  !      end select
  !   end if
  !   y = yggarg(x)
  !   y%alloc = .true.
  ! end function yggarg_realloc_array

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
  
  function ygg_ascii_file_output(name) result(channel)
    implicit none
    character(len=*), intent(in) :: name
    character(len=len_trim(name)+1) :: c_name
    type(yggcomm) :: channel
    c_name = trim(name)//c_null_char
    channel%comm = ygg_ascii_file_output_c(c_name)
  end function ygg_ascii_file_output
  
  function ygg_ascii_file_input(name) result(channel)
    implicit none
    character(len=*), intent(in) :: name
    character(len=len_trim(name)+1) :: c_name
    type(yggcomm) :: channel
    c_name = trim(name)//c_null_char
    channel%comm = ygg_ascii_file_input_c(c_name)
  end function ygg_ascii_file_input
  
  function ygg_ascii_table_output(name, format_str) result(channel)
    implicit none
    character(len=*), intent(in) :: name
    character(len=*), intent(in) :: format_str
    character(len=len_trim(name)+1) :: c_name
    character(len=len_trim(format_str)+1) :: c_format_str
    type(yggcomm) :: channel
    c_name = trim(name)//c_null_char
    c_format_str = trim(format_str)//c_null_char
    channel%comm = ygg_ascii_table_output_c(c_name, c_format_str)
  end function ygg_ascii_table_output
  
  function ygg_ascii_table_input(name) result(channel)
    implicit none
    character(len=*), intent(in) :: name
    character(len=len_trim(name)+1) :: c_name
    type(yggcomm) :: channel
    c_name = trim(name)//c_null_char
    channel%comm = ygg_ascii_table_input_c(c_name)
  end function ygg_ascii_table_input
  
  function ygg_ascii_array_output(name, format_str) result(channel)
    implicit none
    character(len=*), intent(in) :: name
    character(len=*), intent(in) :: format_str
    character(len=len_trim(name)+1) :: c_name
    character(len=len_trim(format_str)+1) :: c_format_str
    type(yggcomm) :: channel
    c_name = trim(name)//c_null_char
    c_format_str = trim(format_str)//c_null_char
    channel%comm = ygg_ascii_array_output_c(c_name, c_format_str)
  end function ygg_ascii_array_output
  
  function ygg_ascii_array_input(name) result(channel)
    implicit none
    character(len=*), intent(in) :: name
    character(len=len_trim(name)+1) :: c_name
    type(yggcomm) :: channel
    c_name = trim(name)//c_null_char
    channel%comm = ygg_ascii_array_input_c(c_name)
  end function ygg_ascii_array_input
  
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
    nargs = size(args)
    do i = 1, size(args)
       if (((args(i)%type.eq."character").or. &
            args(i)%array).and. &
            ((i + 1) > size(args)).or. &
            (args(i+1)%type.ne."size_t")) then
          nargs = nargs + 1
       end if
       ! if (args(i)%array) then
       !    nargs = nargs + 1
       ! end if
    end do
    allocate(c_args(nargs))
    j = 1
    do i = 1, size(args)
       c_args(j) = args(i)%ptr
       j = j + 1
       if ((args(i)%type.eq."character").and.(.not.args(i)%array)) then
          if (((i + 1) <= size(args)).and.(args(i+1)%type.eq."size_t")) then
             args(i)%prec_ptr = args(i+1)%ptr
          else
             args(i)%prec_c = args(i)%prec
             args(i)%prec_ptr = c_loc(args(i)%prec_c)
          end if
          c_args(j) = args(i)%prec_ptr
          j = j + 1
       else if ((args(i)%type.eq."character").or.args(i)%array) then
          if (((i + 1) <= size(args)).and.(args(i+1)%type.eq."size_t")) then
             args(i)%len_ptr = args(i+1)%ptr
          else
             args(i)%len_c = args(i)%len
             args(i)%len_ptr = c_loc(args(i)%len_c)
          end if
          c_args(j) = args(i)%len_ptr
          j = j + 1
       end if
       ! if (args(i)%array) then
       !    args(i)%len_c = args(i)%len
       !    args(i)%len_ptr = c_loc(args(i)%len_c)
       !    c_args(j) = args(i)%len_ptr
       !    j = j + 1
       ! end if
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
          if (((args(i)%type.eq."character").or.args(i)%array).and. &
               ((i + 1) > size(args)).or. &
               (args(i+1)%type.ne."size_t")) then
             j = j + 1
          end if
          ! if (args(i)%array) then
          !    j = j + 1
          ! end if
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
    integer :: flag
    integer(kind=c_int) :: c_flag
    c_ygg_q = ygg_q%comm
    call pre_recv(args, c_args)
    c_nargs = size(args)
    c_flag = ygg_recv_var_c(c_ygg_q, c_nargs, c_loc(c_args(1)))
    flag = c_flag
    call post_recv(args, c_args, flag)
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
    print *, "begin ygg_recv_var_realloc"
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
       print *, "pre_recv ygg_recv_var_realloc"
       call pre_recv(args, c_args)
       c_nargs = size(args)
       print *, "call ygg_recv_var_realloc"
       c_flag = ygg_recv_var_realloc_c(c_ygg_q, c_nargs, c_loc(c_args(1)))
       flag = c_flag
    end if
    print *, "post_recv ygg_recv_var_realloc"
    call post_recv(args, c_args, flag)
    print *, "end ygg_recv_var_realloc"
  end function ygg_recv_var_realloc
  
end module fygg
