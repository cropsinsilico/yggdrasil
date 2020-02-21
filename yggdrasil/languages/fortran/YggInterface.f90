module fygg
  ! TODO: Ensure that dynamically allocated C/C++ variables are freed.
  use iso_c_binding
  implicit none

  integer, parameter :: LINE_SIZE_MAX = 2048

  interface yggarg
     module procedure yggarg_scalar
     module procedure yggarg_array
  end interface yggarg
  type :: yggcomm
     type(c_ptr) :: comm
  end type yggcomm
  type :: yggchar_r
     character, dimension(:), allocatable :: x
  end type yggchar_r
  type :: yggarr_r
     class(*), dimension(:), allocatable :: x
  end type yggarr_r
  type :: c_long_1d
     integer(kind=c_long), dimension(:), allocatable :: x
  end type c_long_1d
  type :: integer_1d
     integer, dimension(:), allocatable :: x
  end type integer_1d
  type :: integer2_1d
     integer(kind=2), dimension(:), allocatable :: x
  end type integer2_1d
  type :: integer4_1d
     integer(kind=4), dimension(:), allocatable :: x
  end type integer4_1d
  type :: integer8_1d
     integer(kind=8), dimension(:), allocatable :: x
  end type integer8_1d
  type :: real_1d
     real, dimension(:), allocatable :: x
  end type real_1d
  type :: real4_1d
     real(kind=4), dimension(:), allocatable :: x
  end type real4_1d
  type :: real8_1d
     real(kind=8), dimension(:), allocatable :: x
  end type real8_1d
  type :: real16_1d
     real(kind=16), dimension(:), allocatable :: x
  end type real16_1d
  type :: complex_1d
     complex, dimension(:), allocatable :: x
  end type complex_1d
  type :: complex4_1d
     complex(kind=4), dimension(:), allocatable :: x
  end type complex4_1d
  type :: complex8_1d
     complex(kind=8), dimension(:), allocatable :: x
  end type complex8_1d
  type :: complex16_1d
     complex(kind=16), dimension(:), allocatable :: x
  end type complex16_1d
  type :: logical_1d
     logical, dimension(:), allocatable :: x
  end type logical_1d
  type :: logical1_1d
     logical(kind=1), dimension(:), allocatable :: x
  end type logical1_1d
  type :: logical2_1d
     logical(kind=2), dimension(:), allocatable :: x
  end type logical2_1d
  type :: logical4_1d
     logical(kind=4), dimension(:), allocatable :: x
  end type logical4_1d
  type :: logical8_1d
     logical(kind=8), dimension(:), allocatable :: x
  end type logical8_1d
  type :: character_1d
     type(yggchar_r), dimension(:), allocatable :: x
  end type character_1d
  type :: integer_2d
     integer, dimension(:, :), allocatable :: x
  end type integer_2d
  type :: integer2_2d
     integer(kind=2), dimension(:, :), allocatable :: x
  end type integer2_2d
  type :: integer4_2d
     integer(kind=4), dimension(:, :), allocatable :: x
  end type integer4_2d
  type :: integer8_2d
     integer(kind=8), dimension(:, :), allocatable :: x
  end type integer8_2d
  type :: real_2d
     real, dimension(:, :), allocatable :: x
  end type real_2d
  type :: real4_2d
     real(kind=4), dimension(:, :), allocatable :: x
  end type real4_2d
  type :: real8_2d
     real(kind=8), dimension(:, :), allocatable :: x
  end type real8_2d
  type :: real16_2d
     real(kind=16), dimension(:, :), allocatable :: x
  end type real16_2d
  type :: complex_2d
     complex, dimension(:, :), allocatable :: x
  end type complex_2d
  type :: complex4_2d
     complex(kind=4), dimension(:, :), allocatable :: x
  end type complex4_2d
  type :: complex8_2d
     complex(kind=8), dimension(:, :), allocatable :: x
  end type complex8_2d
  type :: complex16_2d
     complex(kind=16), dimension(:, :), allocatable :: x
  end type complex16_2d
  type :: logical_2d
     logical, dimension(:, :), allocatable :: x
  end type logical_2d
  type :: logical1_2d
     logical(kind=1), dimension(:, :), allocatable :: x
  end type logical1_2d
  type :: logical2_2d
     logical(kind=2), dimension(:, :), allocatable :: x
  end type logical2_2d
  type :: logical4_2d
     logical(kind=4), dimension(:, :), allocatable :: x
  end type logical4_2d
  type :: logical8_2d
     logical(kind=8), dimension(:, :), allocatable :: x
  end type logical8_2d
  type :: character_2d
     type(yggchar_r), dimension(:, :), allocatable :: x
  end type character_2d
  type :: yggptr
     character(len=15) :: type = "none"
     logical :: array = .false.
     logical :: alloc = .false.
     integer(kind=8) :: len = 0
     integer(kind=8) :: prec = 0
     type(c_ptr) :: ptr = c_null_ptr
     class(*), pointer :: item => null()
     class(*), dimension(:), pointer :: item_array => null()
     character, dimension(:), pointer :: data_character_unit => null()
     integer(kind=c_size_t), pointer :: len_c => null()
     type(c_ptr) :: len_ptr = c_null_ptr
     integer(kind=c_size_t), pointer :: prec_c => null()
     type(c_ptr) :: prec_ptr = c_null_ptr
  end type yggptr
  type :: yggptr_arr
     type(yggptr), dimension(:), allocatable :: vals
  end type yggptr_arr
  type :: yggptr_map
     character(len=20), dimension(:), allocatable :: keys
     type(yggptr), dimension(:), allocatable :: vals
  end type yggptr_map

  public :: yggarg, yggchar_r, yggarr_r, yggcomm, &
       yggptr, yggptr_arr, yggptr_map, &
       integer_1d, real_1d, complex_1d, logical_1d, character_1d, &
       LINE_SIZE_MAX

  include "YggInterface_cdef.f90"

contains

  include "YggInterface_realloc.f90"

  
  subroutine yggptr_c2f_array_transfer_integer(x)
    implicit none
    type(yggptr) :: x
    integer(kind=2), dimension(:), pointer :: xarr_integer2
    integer(kind=4), dimension(:), pointer :: xarr_integer4
    integer(kind=8), dimension(:), pointer :: xarr_integer8
    select type(item=>x%item_array)
    type is (integer(kind=2))
       xarr_integer2 => item
       call c_f_pointer(x%ptr, xarr_integer2, [x%len])
    type is (integer(kind=4))
       xarr_integer4 => item
       call c_f_pointer(x%ptr, xarr_integer4, [x%len])
    type is (integer(kind=8))
       xarr_integer8 => item
       call c_f_pointer(x%ptr, xarr_integer8, [x%len])
    class default
       call ygglog_error("yggptr_c2f_array_transfer_integer: Unexpected type.")
       stop "ERROR"
    end select
  end subroutine yggptr_c2f_array_transfer_integer
  subroutine yggptr_c2f_array_transfer_real(x)
    implicit none
    type(yggptr) :: x
    real(kind=4), dimension(:), pointer :: xarr_real4
    real(kind=8), dimension(:), pointer :: xarr_real8
    real(kind=16), dimension(:), pointer :: xarr_real16
    select type(item=>x%item_array)
    type is (real(kind=4))
       xarr_real4 => item
       call c_f_pointer(x%ptr, xarr_real4, [x%len])
    type is (real(kind=8))
       xarr_real8 => item
       call c_f_pointer(x%ptr, xarr_real8, [x%len])
    type is (real(kind=16))
       xarr_real16 => item
       call c_f_pointer(x%ptr, xarr_real16, [x%len])
    class default
       call ygglog_error("yggptr_c2f_array_transfer_real: Unexpected type.")
       stop "ERROR"
    end select
  end subroutine yggptr_c2f_array_transfer_real
  subroutine yggptr_c2f_array_transfer_complex(x)
    implicit none
    type(yggptr) :: x
    complex(kind=4), dimension(:), pointer :: xarr_complex4
    complex(kind=8), dimension(:), pointer :: xarr_complex8
    complex(kind=16), dimension(:), pointer :: xarr_complex16
    select type(item=>x%item_array)
    type is (complex(kind=4))
       xarr_complex4 => item
       call c_f_pointer(x%ptr, xarr_complex4, [x%len])
    type is (complex(kind=8))
       xarr_complex8 => item
       call c_f_pointer(x%ptr, xarr_complex8, [x%len])
    type is (complex(kind=16))
       xarr_complex16 => item
       call c_f_pointer(x%ptr, xarr_complex16, [x%len])
    class default
       call ygglog_error("yggptr_c2f_array_transfer_complex: Unexpected type.")
       stop "ERROR"
    end select
  end subroutine yggptr_c2f_array_transfer_complex
  subroutine yggptr_c2f_array_transfer_logical(x)
    implicit none
    type(yggptr) :: x
    logical(kind=1), dimension(:), pointer :: xarr_logical1
    logical(kind=2), dimension(:), pointer :: xarr_logical2
    logical(kind=4), dimension(:), pointer :: xarr_logical4
    logical(kind=8), dimension(:), pointer :: xarr_logical8
    select type(item=>x%item_array)
    type is (logical(kind=1))
       xarr_logical1 => item
       call c_f_pointer(x%ptr, xarr_logical1, [x%len])
    type is (logical(kind=2))
       xarr_logical2 => item
       call c_f_pointer(x%ptr, xarr_logical2, [x%len])
    type is (logical(kind=4))
       xarr_logical4 => item
       call c_f_pointer(x%ptr, xarr_logical4, [x%len])
    type is (logical(kind=8))
       xarr_logical8 => item
       call c_f_pointer(x%ptr, xarr_logical8, [x%len])
    class default
       call ygglog_error("yggptr_c2f_array_transfer_logical: Unexpected type.")
       stop "ERROR"
    end select
  end subroutine yggptr_c2f_array_transfer_logical
  subroutine yggptr_c2f_array_transfer_character(x)
    implicit none
    type(yggptr) :: x
    type(yggchar_r), pointer :: x_character_realloc
    type(yggchar_r), dimension(:), pointer :: xarr_character_realloc
    character, dimension(:), pointer :: xarr_character, xarr_character0
    integer(kind=8) :: i, j
    select type(item=>x%item_array)
    type is (yggchar_r)
       xarr_character_realloc => item
       x_character_realloc => xarr_character_realloc(1)
       xarr_character0 => x_character_realloc%x
       ! print *, "before pointer (mult) "
       ! call c_f_pointer(x%ptr, xarr_character0, [x%prec*x%len])
       ! print *, "after  pointer (mult) "
       ! do i = 2, x%len
       !    x_character_realloc => xarr_character_realloc(i)
       !    xarr_character => x_character_realloc%x
       !    print *, "before pointer (mult) ", i
       !    xarr_character(1:x%prec) = xarr_character0( &
       !         (1+(i-1)*x%prec):(i*x%prec))
       !    print *, "after  pointer (mult) ", i
       ! end do
    type is (character(*))
       xarr_character => item
       do i = 1, x%len
          do j = 1, x%prec
             xarr_character(i)(j:j) = x%data_character_unit(i)
          end do
          do j = (x%prec + 1), len(xarr_character(i))
             xarr_character(i)(j:j) = ' '
          end do
       end do
       deallocate(x%data_character_unit)
    class default
       call ygglog_error("yggptr_c2f_array_transfer_character: Unexpected type.")
       stop "ERROR"
    end select
  end subroutine yggptr_c2f_array_transfer_character
  subroutine yggptr_c2f_array_transfer_1darray(x)
    implicit none
    type(yggptr) :: x
    integer(kind=c_size_t), pointer :: array_len
    integer(kind=c_size_t), pointer :: precision
    type(yggchar_r), pointer :: x_character_realloc
    type(yggchar_r), dimension(:), pointer :: xarr_character_realloc
    character, dimension(:), pointer :: xarr_character, xarr_character0
    integer(kind=8) :: i, j
    type(c_long_1d), pointer :: x_c_long_1d
    type(integer_1d), pointer :: x_integer_1d
    type(integer2_1d), pointer :: x_integer2_1d
    type(integer4_1d), pointer :: x_integer4_1d
    type(integer8_1d), pointer :: x_integer8_1d
    type(real_1d), pointer :: x_real_1d
    type(real4_1d), pointer :: x_real4_1d
    type(real8_1d), pointer :: x_real8_1d
    type(real16_1d), pointer :: x_real16_1d
    type(complex_1d), pointer :: x_complex_1d
    type(complex4_1d), pointer :: x_complex4_1d
    type(complex8_1d), pointer :: x_complex8_1d
    type(complex16_1d), pointer :: x_complex16_1d
    type(logical_1d), pointer :: x_logical_1d
    type(logical1_1d), pointer :: x_logical1_1d
    type(logical2_1d), pointer :: x_logical2_1d
    type(logical4_1d), pointer :: x_logical4_1d
    type(logical8_1d), pointer :: x_logical8_1d
    type(character_1d), pointer :: x_character_1d
    integer, dimension(:), pointer :: ptr_c_long
    integer, dimension(:), pointer :: ptr_integer
    integer(kind=2), dimension(:), pointer :: ptr_integer2
    integer(kind=4), dimension(:), pointer :: ptr_integer4
    integer(kind=8), dimension(:), pointer :: ptr_integer8
    real, dimension(:), pointer :: ptr_real
    real(kind=4), dimension(:), pointer :: ptr_real4
    real(kind=8), dimension(:), pointer :: ptr_real8
    real(kind=16), dimension(:), pointer :: ptr_real16
    complex, dimension(:), pointer :: ptr_complex
    complex(kind=4), dimension(:), pointer :: ptr_complex4
    complex(kind=8), dimension(:), pointer :: ptr_complex8
    complex(kind=16), dimension(:), pointer :: ptr_complex16
    logical, dimension(:), pointer :: ptr_logical
    logical(kind=1), dimension(:), pointer :: ptr_logical1
    logical(kind=2), dimension(:), pointer :: ptr_logical2
    logical(kind=4), dimension(:), pointer :: ptr_logical4
    logical(kind=8), dimension(:), pointer :: ptr_logical8
    select type(item=>x%item)
    type is (c_long_1d)
       x_c_long_1d => item
       call c_f_pointer(x%ptr, ptr_c_long, [x%len])
       x_c_long_1d%x = ptr_c_long
    type is (integer_1d)
       x_integer_1d => item
       call c_f_pointer(x%ptr, ptr_integer, [x%len])
       x_integer_1d%x = ptr_integer
    type is (integer2_1d)
       x_integer2_1d => item
       call c_f_pointer(x%ptr, ptr_integer2, [x%len])
       x_integer2_1d%x = ptr_integer2
    type is (integer4_1d)
       x_integer4_1d => item
       call c_f_pointer(x%ptr, ptr_integer4, [x%len])
       x_integer4_1d%x = ptr_integer4
    type is (integer8_1d)
       x_integer8_1d => item
       call c_f_pointer(x%ptr, ptr_integer8, [x%len])
       x_integer8_1d%x = ptr_integer8
    type is (real_1d)
       x_real_1d => item
       call c_f_pointer(x%ptr, ptr_real, [x%len])
       x_real_1d%x = ptr_real
    type is (real4_1d)
       x_real4_1d => item
       call c_f_pointer(x%ptr, ptr_real4, [x%len])
       x_real4_1d%x = ptr_real4
    type is (real8_1d)
       x_real8_1d => item
       call c_f_pointer(x%ptr, ptr_real8, [x%len])
       x_real8_1d%x = ptr_real8
    type is (real16_1d)
       x_real16_1d => item
       call c_f_pointer(x%ptr, ptr_real16, [x%len])
       x_real16_1d%x = ptr_real16
    type is (complex_1d)
       x_complex_1d => item
       call c_f_pointer(x%ptr, ptr_complex, [x%len])
       x_complex_1d%x = ptr_complex
    type is (complex4_1d)
       x_complex4_1d => item
       call c_f_pointer(x%ptr, ptr_complex4, [x%len])
       x_complex4_1d%x = ptr_complex4
    type is (complex8_1d)
       x_complex8_1d => item
       call c_f_pointer(x%ptr, ptr_complex8, [x%len])
       x_complex8_1d%x = ptr_complex8
    type is (complex16_1d)
       x_complex16_1d => item
       call c_f_pointer(x%ptr, ptr_complex16, [x%len])
       x_complex16_1d%x = ptr_complex16
    type is (logical_1d)
       x_logical_1d => item
       call c_f_pointer(x%ptr, ptr_logical, [x%len])
       x_logical_1d%x = ptr_logical
    type is (logical1_1d)
       x_logical1_1d => item
       call c_f_pointer(x%ptr, ptr_logical1, [x%len])
       x_logical1_1d%x = ptr_logical1
    type is (logical2_1d)
       x_logical2_1d => item
       call c_f_pointer(x%ptr, ptr_logical2, [x%len])
       x_logical2_1d%x = ptr_logical2
    type is (logical4_1d)
       x_logical4_1d => item
       call c_f_pointer(x%ptr, ptr_logical4, [x%len])
       x_logical4_1d%x = ptr_logical4
    type is (logical8_1d)
       x_logical8_1d => item
       call c_f_pointer(x%ptr, ptr_logical8, [x%len])
       x_logical8_1d%x = ptr_logical8
    type is (character_1d)
       x_character_1d => item
       x_character_realloc => x_character_1d%x(1)
       xarr_character0 => x_character_realloc%x
       ! allocate(x%data_character_unit(x%prec*x%len))
       call c_f_pointer(x%ptr, x%data_character_unit, [x%prec*x%len])
       do i = 1, x%len
          ! x_character_realloc => x_character_1d%x(i)
          ! xarr_character => x_character_realloc%x
          ! xarr_character(1:x%prec) = x%data_character_unit( &
          !      (1+(i-1)*x%prec):(i*x%prec))
          x_character_1d%x(i)%x = x%data_character_unit( &
               (1+(i-1)*x%prec):(i*x%prec))
       end do
       deallocate(x%data_character_unit)
    class default
       call ygglog_error("yggarg_c2f_array_transfer_1darray: Unexpected type.")
       stop "ERROR"
    end select
  end subroutine yggptr_c2f_array_transfer_1darray
  
  subroutine yggptr_c2f_scalar_transfer_integer(x)
    implicit none
    type(yggptr) :: x
    integer(kind=2), pointer :: x_integer2
    integer(kind=4), pointer :: x_integer4
    integer(kind=8), pointer :: x_integer8
    select type(item=>x%item)
    type is (integer(kind=2))
       x_integer2 => item
       call c_f_pointer(x%ptr, x_integer2, [x%len])
    type is (integer(kind=4))
       x_integer4 => item
       call c_f_pointer(x%ptr, x_integer4, [x%len])
    type is (integer(kind=8))
       x_integer8 => item
       ! call c_f_pointer(x%ptr, x_integer8, [x%len])
    class default
       call ygglog_error("yggptr_c2f_scalar_transfer_integer: Unexpected type.")
       stop "ERROR"
    end select
  end subroutine yggptr_c2f_scalar_transfer_integer
  subroutine yggptr_c2f_scalar_transfer_real(x)
    implicit none
    type(yggptr) :: x
    real(kind=4), pointer :: x_real4
    real(kind=8), pointer :: x_real8
    real(kind=16), pointer :: x_real16
    select type(item=>x%item)
    type is (real(kind=4))
       x_real4 => item
       call c_f_pointer(x%ptr, x_real4, [x%len])
    type is (real(kind=8))
       x_real8 => item
       call c_f_pointer(x%ptr, x_real8, [x%len])
    type is (real(kind=16))
       x_real16 => item
       call c_f_pointer(x%ptr, x_real16, [x%len])
    class default
       call ygglog_error("yggptr_c2f_scalar_transfer_real: Unexpected type.")
       stop "ERROR"
    end select
  end subroutine yggptr_c2f_scalar_transfer_real
  subroutine yggptr_c2f_scalar_transfer_complex(x)
    implicit none
    type(yggptr) :: x
    complex(kind=4), pointer :: x_complex4
    complex(kind=8), pointer :: x_complex8
    complex(kind=16), pointer :: x_complex16
    select type(item=>x%item)
    type is (complex(kind=4))
       x_complex4 => item
       call c_f_pointer(x%ptr, x_complex4, [x%len])
    type is (complex(kind=8))
       x_complex8 => item
       call c_f_pointer(x%ptr, x_complex8, [x%len])
    type is (complex(kind=16))
       x_complex16 => item
       call c_f_pointer(x%ptr, x_complex16, [x%len])
    class default
       call ygglog_error("yggptr_c2f_scalar_transfer_complex: Unexpected type.")
       stop "ERROR"
    end select
  end subroutine yggptr_c2f_scalar_transfer_complex
  subroutine yggptr_c2f_scalar_transfer_logical(x)
    implicit none
    type(yggptr) :: x
    logical(kind=1), pointer :: x_logical1
    logical(kind=2), pointer :: x_logical2
    logical(kind=4), pointer :: x_logical4
    logical(kind=8), pointer :: x_logical8
    select type(item=>x%item)
    type is (logical(kind=1))
       x_logical1 => item
       call c_f_pointer(x%ptr, x_logical1, [x%len])
    type is (logical(kind=2))
       x_logical2 => item
       call c_f_pointer(x%ptr, x_logical2, [x%len])
    type is (logical(kind=4))
       x_logical4 => item
       call c_f_pointer(x%ptr, x_logical4, [x%len])
    type is (logical(kind=8))
       x_logical8 => item
       call c_f_pointer(x%ptr, x_logical8, [x%len])
    class default
       call ygglog_error("yggptr_c2f_scalar_transfer_logical: Unexpected type.")
       stop "ERROR"
    end select
  end subroutine yggptr_c2f_scalar_transfer_logical
  subroutine yggptr_c2f_scalar_transfer_character(x)
    implicit none
    type(yggptr) :: x
    character(len=:), pointer :: x_character
    character, dimension(:), pointer :: xarr_character
    type(yggchar_r), pointer :: x_character_realloc
    integer(kind=8) :: i
    select type(item=>x%item)
    type is (yggchar_r)
       x_character_realloc => item
       call c_f_pointer(x%ptr, xarr_character, [x%prec])
       x_character_realloc%x = xarr_character
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
       call ygglog_error("yggptr_c2f_scalar_transfer_character: Unexpected type.")
       stop "ERROR"
    end select
  end subroutine yggptr_c2f_scalar_transfer_character
  
  function yggptr_c2f(x, realloc) result(flag)
    implicit none
    type(yggptr) :: x
    logical :: realloc
    integer(kind=c_size_t), pointer :: array_len
    integer(kind=c_size_t), pointer :: precision
    integer(kind=8) :: i, j
    integer :: flag
    character(len=500) :: log_msg
    flag = 0
    call ygglog_debug("yggptr_c2f: begin")
    allocate(array_len)
    allocate(precision)
    array_len = 1
    precision = 1
    if (x%array) then
       deallocate(array_len)
       call c_f_pointer(x%len_ptr, array_len)
       write(log_msg, '("array_len = ",i7)'), array_len
       call ygglog_debug(log_msg)
    end if
    if (x%type.eq."character") then
       deallocate(precision)
       call c_f_pointer(x%prec_ptr, precision)
       write(log_msg, '("precision = ",i7)'), precision
       call ygglog_debug(log_msg)
    end if
    flag = yggptr_realloc(x, array_len, precision, realloc)
    if (x%array) then
       if (x%alloc) then
          select type(item=>x%item)
          type is (c_long_1d)
             call yggptr_c2f_array_transfer_1darray(x)
          type is (integer_1d)
             call yggptr_c2f_array_transfer_1darray(x)
          type is (integer2_1d)
             call yggptr_c2f_array_transfer_1darray(x)
          type is (integer4_1d)
             call yggptr_c2f_array_transfer_1darray(x)
          type is (integer8_1d)
             call yggptr_c2f_array_transfer_1darray(x)
          type is (real_1d)
             call yggptr_c2f_array_transfer_1darray(x)
          type is (real4_1d)
             call yggptr_c2f_array_transfer_1darray(x)
          type is (real8_1d)
             call yggptr_c2f_array_transfer_1darray(x)
          type is (real16_1d)
             call yggptr_c2f_array_transfer_1darray(x)
          type is (complex_1d)
             call yggptr_c2f_array_transfer_1darray(x)
          type is (complex4_1d)
             call yggptr_c2f_array_transfer_1darray(x)
          type is (complex8_1d)
             call yggptr_c2f_array_transfer_1darray(x)
          type is (complex16_1d)
             call yggptr_c2f_array_transfer_1darray(x)
          type is (logical_1d)
             call yggptr_c2f_array_transfer_1darray(x)
          type is (logical1_1d)
             call yggptr_c2f_array_transfer_1darray(x)
          type is (logical2_1d)
             call yggptr_c2f_array_transfer_1darray(x)
          type is (logical4_1d)
             call yggptr_c2f_array_transfer_1darray(x)
          type is (logical8_1d)
             call yggptr_c2f_array_transfer_1darray(x)
          type is (character_1d)
             call yggptr_c2f_array_transfer_1darray(x)
          class default
             write(log_msg, '("yggptr_c2f (realloc array transfer): Unexpected type: ",A)'), x%type
             call ygglog_error(log_msg)
             stop "ERROR"
          end select
       else
          select type(item=>x%item_array)
          type is (integer(kind=2))
             call yggptr_c2f_array_transfer_integer(x)
          type is (integer(kind=4))
             call yggptr_c2f_array_transfer_integer(x)
          type is (integer(kind=8))
             call yggptr_c2f_array_transfer_integer(x)
          type is (real(kind=4))
             call yggptr_c2f_array_transfer_real(x)
          type is (real(kind=8))
             call yggptr_c2f_array_transfer_real(x)
          type is (real(kind=16))
             call yggptr_c2f_array_transfer_real(x)
          type is (complex(kind=4))
             call yggptr_c2f_array_transfer_complex(x)
          type is (complex(kind=8))
             call yggptr_c2f_array_transfer_complex(x)
          type is (complex(kind=16))
             call yggptr_c2f_array_transfer_complex(x)
          type is (logical(kind=1))
             call yggptr_c2f_array_transfer_logical(x)
          type is (logical(kind=2))
             call yggptr_c2f_array_transfer_logical(x)
          type is (logical(kind=4))
             call yggptr_c2f_array_transfer_logical(x)
          type is (logical(kind=8))
             call yggptr_c2f_array_transfer_logical(x)
          type is (yggchar_r)
             call yggptr_c2f_array_transfer_character(x)
          type is (character(*))
             call yggptr_c2f_array_transfer_character(x)
          class default
             write(log_msg, '("yggptr_c2f (realloc transfer): Unexpected type: ",A)'), x%type
             call ygglog_error(log_msg)
             stop "ERROR"
          end select
       end if
    else
       select type(item=>x%item)
       type is (integer(kind=2))
          call yggptr_c2f_scalar_transfer_integer(x)
       type is (integer(kind=4))
          call yggptr_c2f_scalar_transfer_integer(x)
       type is (integer(kind=8))
          call yggptr_c2f_scalar_transfer_integer(x)
       type is (real(kind=4))
          call yggptr_c2f_scalar_transfer_real(x)
       type is (real(kind=8))
          call yggptr_c2f_scalar_transfer_real(x)
       type is (real(kind=16))
          call yggptr_c2f_scalar_transfer_real(x)
       type is (complex(kind=4))
          call yggptr_c2f_scalar_transfer_complex(x)
       type is (complex(kind=8))
          call yggptr_c2f_scalar_transfer_complex(x)
       type is (complex(kind=16))
          call yggptr_c2f_scalar_transfer_complex(x)
       type is (logical(kind=1))
          call yggptr_c2f_scalar_transfer_logical(x)
       type is (logical(kind=2))
          call yggptr_c2f_scalar_transfer_logical(x)
       type is (logical(kind=4))
          call yggptr_c2f_scalar_transfer_logical(x)
       type is (logical(kind=8))
          call yggptr_c2f_scalar_transfer_logical(x)
       type is (yggchar_r)
          call yggptr_c2f_scalar_transfer_character(x)
       type is (character(*))
          call yggptr_c2f_scalar_transfer_character(x)
       class default
          write(log_msg, '("yggptr_c2f (scalar transfer): Unexpected type: ",A)'), x%type
          call ygglog_error(log_msg)
          stop "ERROR"
       end select
    end if
    if (.not.x%array) then
       deallocate(array_len)
    end if
    if (.not.(x%type.eq."character")) then
       deallocate(precision)
    end if
    call ygglog_debug("yggptr_c2f: end")
  end function yggptr_c2f
  
  ! Scalar versions
  subroutine yggarg_scalar_integer(y)
    type(yggptr) :: y
    integer(kind=2), pointer :: x_integer2
    integer(kind=4), pointer :: x_integer4
    integer(kind=8), pointer :: x_integer8
    y%type = "integer"
    select type(x=>y%item)
    type is (integer(kind=2))
       x_integer2 => x
       y%ptr = c_loc(x_integer2)
    type is (integer(kind=4))
       x_integer4 => x
       y%ptr = c_loc(x_integer4)
    type is (integer(kind=8))
       y%type = "size_t"
       x_integer8 => x
       y%ptr = c_loc(x_integer8)
    class default
       stop 'yggarg_scalar_integer: Unexpected type.'
    end select
  end subroutine yggarg_scalar_integer
  subroutine yggarg_scalar_real(y)
    type(yggptr) :: y
    real(kind=4), pointer :: x_real4
    real(kind=8), pointer :: x_real8
    real(kind=16), pointer :: x_real16
    y%type = "real"
    select type(x=>y%item)
    type is (real(kind=4))
       x_real4 => x
       y%ptr = c_loc(x_real4)
    type is (real(kind=8))
       x_real8 => x
       y%ptr = c_loc(x_real8)
    type is (real(kind=16))
       x_real16 => x
       y%ptr = c_loc(x_real16)
    class default
       stop 'yggarg_scalar_real: Unexpected type.'
    end select
  end subroutine yggarg_scalar_real
  subroutine yggarg_scalar_complex(y)
    type(yggptr) :: y
    complex, pointer :: x_complex
    complex(kind=4), pointer :: x_complex4
    complex(kind=8), pointer :: x_complex8
    complex(kind=16), pointer :: x_complex16
    y%type = "complex"
    select type(x=>y%item)
    type is (complex(kind=4))
       x_complex4 => x
       y%ptr = c_loc(x_complex4)
    type is (complex(kind=8))
       x_complex8 => x
       y%ptr = c_loc(x_complex8)
    type is (complex(kind=16))
       x_complex16 => x
       y%ptr = c_loc(x_complex16)
    class default
       stop 'yggarg_scalar_complex: Unexpected type.'
    end select
  end subroutine yggarg_scalar_complex
  subroutine yggarg_scalar_logical(y)
    type(yggptr) :: y
    logical(kind=1), pointer :: x_logical1
    logical(kind=2), pointer :: x_logical2
    logical(kind=4), pointer :: x_logical4
    logical(kind=8), pointer :: x_logical8
    y%type = "logical"
    select type(x=>y%item)
    type is (logical(kind=1))
       x_logical1 => x
       y%ptr = c_loc(x_logical1)
    type is (logical(kind=2))
       x_logical2 => x
       y%ptr = c_loc(x_logical2)
    type is (logical(kind=4))
       x_logical4 => x
       y%ptr = c_loc(x_logical4)
    type is (logical(kind=8))
       x_logical8 => x
       y%ptr = c_loc(x_logical8)
    class default
       stop 'yggarg_scalar_logical: Unexpected type.'
    end select
  end subroutine yggarg_scalar_logical
  subroutine yggarg_scalar_character(y)
    type(yggptr) :: y
    character(len=:), pointer :: x_character
    type(yggchar_r), pointer :: x_character_realloc
    integer :: i
    y%type = "character"
    select type(x=>y%item)
    type is (character(*))
       x_character => x
       allocate(y%data_character_unit(len(x_character)))
       do i = 1, len(x_character)
          y%data_character_unit(i) = x_character(i:i)
       end do
       if (len_trim(x_character).lt.len(x_character)) then
          y%data_character_unit(len_trim(x_character) + 1) = c_null_char
       end if
       y%ptr = c_loc(y%data_character_unit(1))
       y%prec = len(x_character)
    type is (yggchar_r)
       x_character_realloc => x
       if (allocated(x_character_realloc%x)) then
          y%ptr = c_loc(x_character_realloc%x(1))
          y%prec = size(x_character_realloc%x)
       else
          y%ptr = c_null_ptr
       end if
       y%alloc = .true.
    class default
       stop 'yggarg_scalar_character: Unexpected type.'
    end select
  end subroutine yggarg_scalar_character
  function yggarg_scalar(x) result(y)
    class(*), target :: x
    type(yggptr) :: y
    y%item => x
    y%array = .false.
    y%alloc = .false.
    y%len = 1
    y%prec = 1
    select type(x)
    type is (integer(kind=2))
       call yggarg_scalar_integer(y)
    type is (integer(kind=4))
       call yggarg_scalar_integer(y)
    type is (integer(kind=8))
       call yggarg_scalar_integer(y)
    type is (real(kind=4))
       call yggarg_scalar_real(y)
    type is (real(kind=8))
       call yggarg_scalar_real(y)
    type is (real(kind=16))
       call yggarg_scalar_real(y)
    type is (complex(kind=4))
       call yggarg_scalar_complex(y)
    type is (complex(kind=8))
       call yggarg_scalar_complex(y)
    type is (complex(kind=16))
       call yggarg_scalar_complex(y)
    type is (logical(kind=1))
       call yggarg_scalar_logical(y)
    type is (logical(kind=2))
       call yggarg_scalar_logical(y)
    type is (logical(kind=4))
       call yggarg_scalar_logical(y)
    type is (logical(kind=8))
       call yggarg_scalar_logical(y)
    type is (character(*))
       call yggarg_scalar_character(y)
    type is (yggchar_r)
       call yggarg_scalar_character(y)
    type is (c_long_1d)
       call yggarg_realloc_1darray(y)
    type is (integer_1d)
       call yggarg_realloc_1darray(y)
    type is (integer2_1d)
       call yggarg_realloc_1darray(y)
    type is (integer4_1d)
       call yggarg_realloc_1darray(y)
    type is (integer8_1d)
       call yggarg_realloc_1darray(y)
    type is (real_1d)
       call yggarg_realloc_1darray(y)
    type is (real4_1d)
       call yggarg_realloc_1darray(y)
    type is (real8_1d)
       call yggarg_realloc_1darray(y)
    type is (real16_1d)
       call yggarg_realloc_1darray(y)
    type is (complex_1d)
       call yggarg_realloc_1darray(y)
    type is (complex4_1d)
       call yggarg_realloc_1darray(y)
    type is (complex8_1d)
       call yggarg_realloc_1darray(y)
    type is (complex16_1d)
       call yggarg_realloc_1darray(y)
    type is (logical_1d)
       call yggarg_realloc_1darray(y)
    type is (logical1_1d)
       call yggarg_realloc_1darray(y)
    type is (logical2_1d)
       call yggarg_realloc_1darray(y)
    type is (logical4_1d)
       call yggarg_realloc_1darray(y)
    type is (logical8_1d)
       call yggarg_realloc_1darray(y)
    type is (character_1d)
       call yggarg_realloc_1darray(y)
    class default
       stop 'yggarg_scalar: Unexpected type.'
    end select
  end function yggarg_scalar
  
  ! Array versions
  subroutine yggarg_realloc_1darray(y)
    type(yggptr) :: y
    type(c_long_1d), pointer :: x_c_long_1d
    type(integer_1d), pointer :: x_integer_1d
    type(integer2_1d), pointer :: x_integer2_1d
    type(integer4_1d), pointer :: x_integer4_1d
    type(integer8_1d), pointer :: x_integer8_1d
    type(real_1d), pointer :: x_real_1d
    type(real4_1d), pointer :: x_real4_1d
    type(real8_1d), pointer :: x_real8_1d
    type(real16_1d), pointer :: x_real16_1d
    type(complex_1d), pointer :: x_complex_1d
    type(complex4_1d), pointer :: x_complex4_1d
    type(complex8_1d), pointer :: x_complex8_1d
    type(complex16_1d), pointer :: x_complex16_1d
    type(logical_1d), pointer :: x_logical_1d
    type(logical1_1d), pointer :: x_logical1_1d
    type(logical2_1d), pointer :: x_logical2_1d
    type(logical4_1d), pointer :: x_logical4_1d
    type(logical8_1d), pointer :: x_logical8_1d
    type(character_1d), pointer :: x_character_1d
    integer(kind=8) :: i, j, ilength
    call ygglog_debug("yggarg_realloc_1darray: begin")
    y%array = .true.
    y%alloc = .true.
    y%len = 1
    y%prec = 1
    y%ptr = c_null_ptr
    select type(x=>y%item)
    type is (c_long_1d)
       y%type = "c_long"
       x_c_long_1d => x
       if (allocated(x_c_long_1d%x)) then
          y%ptr = c_loc(x_c_long_1d%x(1))
          y%len = size(x_c_long_1d%x)
       end if
    type is (integer_1d)
       y%type = "integer"
       x_integer_1d => x
       if (allocated(x_integer_1d%x)) then
          y%ptr = c_loc(x_integer_1d%x(1))
          y%len = size(x_integer_1d%x)
       end if
    type is (integer2_1d)
       y%type = "integer"
       x_integer2_1d => x
       if (allocated(x_integer2_1d%x)) then
          y%ptr = c_loc(x_integer2_1d%x(1))
          y%len = size(x_integer2_1d%x)
       end if
    type is (integer4_1d)
       y%type = "integer"
       x_integer4_1d => x
       if (allocated(x_integer4_1d%x)) then
          y%ptr = c_loc(x_integer4_1d%x(1))
          y%len = size(x_integer4_1d%x)
       end if
    type is (integer8_1d)
       y%type = "integer"
       x_integer8_1d => x
       if (allocated(x_integer8_1d%x)) then
          y%ptr = c_loc(x_integer8_1d%x(1))
          y%len = size(x_integer8_1d%x)
       end if
    type is (real_1d)
       y%type = "real"
       x_real_1d => x
       if (allocated(x_real_1d%x)) then
          y%ptr = c_loc(x_real_1d%x(1))
          y%len = size(x_real_1d%x)
       end if
    type is (real4_1d)
       y%type = "real"
       x_real4_1d => x
       if (allocated(x_real4_1d%x)) then
          y%ptr = c_loc(x_real4_1d%x(1))
          y%len = size(x_real4_1d%x)
       end if
    type is (real8_1d)
       y%type = "real"
       x_real8_1d => x
       if (allocated(x_real8_1d%x)) then
          y%ptr = c_loc(x_real8_1d%x(1))
          y%len = size(x_real8_1d%x)
       end if
    type is (real16_1d)
       y%type = "real"
       x_real16_1d => x
       if (allocated(x_real16_1d%x)) then
          y%ptr = c_loc(x_real16_1d%x(1))
          y%len = size(x_real16_1d%x)
       end if
    type is (complex_1d)
       y%type = "complex"
       x_complex_1d => x
       if (allocated(x_complex_1d%x)) then
          y%ptr = c_loc(x_complex_1d%x(1))
          y%len = size(x_complex_1d%x)
       end if
    type is (complex4_1d)
       y%type = "complex"
       x_complex4_1d => x
       if (allocated(x_complex4_1d%x)) then
          y%ptr = c_loc(x_complex4_1d%x(1))
          y%len = size(x_complex4_1d%x)
       end if
    type is (complex8_1d)
       y%type = "complex"
       x_complex8_1d => x
       if (allocated(x_complex8_1d%x)) then
          y%ptr = c_loc(x_complex8_1d%x(1))
          y%len = size(x_complex8_1d%x)
       end if
    type is (complex16_1d)
       y%type = "complex"
       x_complex16_1d => x
       if (allocated(x_complex16_1d%x)) then
          y%ptr = c_loc(x_complex16_1d%x(1))
          y%len = size(x_complex16_1d%x)
       end if
    type is (logical_1d)
       y%type = "logical"
       x_logical_1d => x
       if (allocated(x_logical_1d%x)) then
          y%ptr = c_loc(x_logical_1d%x(1))
          y%len = size(x_logical_1d%x)
       end if
    type is (logical1_1d)
       y%type = "logical"
       x_logical1_1d => x
       if (allocated(x_logical1_1d%x)) then
          y%ptr = c_loc(x_logical1_1d%x(1))
          y%len = size(x_logical1_1d%x)
       end if
    type is (logical2_1d)
       y%type = "logical"
       x_logical2_1d => x
       if (allocated(x_logical2_1d%x)) then
          y%ptr = c_loc(x_logical2_1d%x(1))
          y%len = size(x_logical2_1d%x)
       end if
    type is (logical4_1d)
       y%type = "logical"
       x_logical4_1d => x
       if (allocated(x_logical4_1d%x)) then
          y%ptr = c_loc(x_logical4_1d%x(1))
          y%len = size(x_logical4_1d%x)
       end if
    type is (logical8_1d)
       y%type = "logical"
       x_logical8_1d => x
       if (allocated(x_logical8_1d%x)) then
          y%ptr = c_loc(x_logical8_1d%x(1))
          y%len = size(x_logical8_1d%x)
       end if
    type is (character_1d)
       y%type = "character"
       x_character_1d => x
       if (allocated(x_character_1d%x)) then
          y%len = size(x_character_1d%x)
          if (allocated(x_character_1d%x(1)%x)) then
             y%prec = size(x_character_1d%x(1)%x)
             allocate(y%data_character_unit(y%len * y%prec))
             do i = 1, size(x_character_1d%x)
                ilength = 0
                do j = 1, y%prec
                   if (len_trim(x_character_1d%x(i)%x(j)) > 0) ilength = j
                end do
                do j = 1, ilength
                   y%data_character_unit(((i-1)*y%prec) + j) = x_character_1d%x(i)%x(j)
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
    class default
       call ygglog_error("yggarg_realloc_1darray: Unexpected type.")
       stop "ERROR"
    end select
    call ygglog_debug("yggarg_realloc_1darray: end")
  end subroutine yggarg_realloc_1darray
    
  subroutine yggarg_array_integer(y)
    type(yggptr) :: y
    integer(kind=2), dimension(:), pointer :: x_integer2
    integer(kind=4), dimension(:), pointer :: x_integer4
    integer(kind=8), dimension(:), pointer :: x_integer8
    y%type = "integer"
    select type(x=>y%item_array)
    type is (integer(kind=2))
       x_integer2 => x
       y%ptr = c_loc(x_integer2(1))
    type is (integer(kind=4))
       x_integer4 => x
       y%ptr = c_loc(x_integer4(1))
    type is (integer(kind=8))
       y%type = "size_t"
       x_integer8 => x
       y%ptr = c_loc(x_integer8(1))
    class default
       stop 'yggarg_array_integer: Unexpected type.'
    end select
  end subroutine yggarg_array_integer
  subroutine yggarg_array_real(y)
    type(yggptr) :: y
    real(kind=4), dimension(:), pointer :: x_real4
    real(kind=8), dimension(:), pointer :: x_real8
    real(kind=16), dimension(:), pointer :: x_real16
    y%type = "real"
    select type(x=>y%item_array)
    type is (real(kind=4))
       x_real4 => x
       y%ptr = c_loc(x_real4(1))
    type is (real(kind=8))
       x_real8 => x
       y%ptr = c_loc(x_real8(1))
    type is (real(kind=16))
       x_real16 => x
       y%ptr = c_loc(x_real16(1))
    class default
       stop 'yggarg_array_real: Unexpected type.'
    end select
  end subroutine yggarg_array_real
  subroutine yggarg_array_complex(y)
    type(yggptr) :: y
    complex(kind=4), dimension(:), pointer :: x_complex4
    complex(kind=8), dimension(:), pointer :: x_complex8
    complex(kind=16), dimension(:), pointer :: x_complex16
    y%type = "complex"
    select type(x=>y%item_array)
    type is (complex(kind=4))
       x_complex4 => x
       y%ptr = c_loc(x_complex4(1))
    type is (complex(kind=8))
       x_complex8 => x
       y%ptr = c_loc(x_complex8(1))
    type is (complex(kind=16))
       x_complex16 => x
       y%ptr = c_loc(x_complex16(1))
    class default
       stop 'yggarg_array_complex: Unexpected type.'
    end select
  end subroutine yggarg_array_complex
  subroutine yggarg_array_logical(y)
    type(yggptr) :: y
    logical(kind=1), dimension(:), pointer :: x_logical1
    logical(kind=2), dimension(:), pointer :: x_logical2
    logical(kind=4), dimension(:), pointer :: x_logical4
    logical(kind=8), dimension(:), pointer :: x_logical8
    y%type = "logical"
    select type(x=>y%item_array)
    type is (logical(kind=1))
       x_logical1 => x
       y%ptr = c_loc(x_logical1(1))
    type is (logical(kind=2))
       x_logical2 => x
       y%ptr = c_loc(x_logical2(1))
    type is (logical(kind=4))
       x_logical4 => x
       y%ptr = c_loc(x_logical4(1))
    type is (logical(kind=8))
       x_logical8 => x
       y%ptr = c_loc(x_logical8(1))
    class default
       stop 'yggarg_array_logical: Unexpected type.'
    end select
  end subroutine yggarg_array_logical
  subroutine yggarg_array_character(y)
    type(yggptr) :: y
    character(len=:), dimension(:), pointer :: x_character
    type(yggchar_r), dimension(:), pointer :: x_character_realloc
    integer :: i, j, ilength
    y%type = "character"
    select type(x=>y%item_array)
    type is (yggchar_r)
       x_character_realloc => x
       if ((allocated(x_character_realloc(1)%x)).and. &
            (size(x_character_realloc(1)%x).ge.1)) then
          ! y%ptr = c_loc(x_character_realloc(1)%x(1))
          y%prec = size(x_character_realloc(1)%x)
          allocate(y%data_character_unit(y%len * y%prec))
          do i = 1, size(x_character_realloc)
             ilength = 0
             do j = 1, ilength
                if (len_trim(x_character_realloc(i)%x(j)) > 0) ilength = j
             end do
             do j = 1, ilength
                y%data_character_unit(((i-1)*y%prec) + j) = x_character_realloc(i)%x(j)
             end do
             if (ilength.lt.size(x_character_realloc(i)%x)) then
                y%data_character_unit(((i-1)*y%prec) + ilength + 1) = c_null_char
             end if
             do j = (ilength + 2), size(x_character_realloc(i)%x)
                y%data_character_unit(((i-1)*y%prec) + j) = ' '
             end do
          end do
          y%ptr = c_loc(y%data_character_unit(1))
       else
          y%ptr = c_null_ptr
       end if
    type is (character(*))
       x_character => x
       y%prec = len(x_character(1))
       do i = 1, size(x_character)
          ilength = len_trim(x_character(i))
          if (ilength.lt.y%prec) then
             x_character(i)((ilength+1):(ilength+1)) = c_null_char
          end if
       end do
       allocate(y%data_character_unit(y%len * y%prec))
       y%data_character_unit = transfer(x_character, &
            y%data_character_unit)
       y%ptr = c_loc(y%data_character_unit(1))
    class default
       stop 'yggarg_array_character: Unexpected type.'
    end select
  end subroutine yggarg_array_character
  function yggarg_array(x) result(y)
    class(*), dimension(:), target :: x
    type(yggptr) :: y
    y%item => x(1)
    y%item_array => x
    y%array = .true.
    y%alloc = .false.
    y%len = size(x)
    y%prec = 1
    select type(item=>y%item_array)
    type is (integer(kind=2))
       call yggarg_array_integer(y)
    type is (integer(kind=4))
       call yggarg_array_integer(y)
    type is (integer(kind=8))
       call yggarg_array_integer(y)
    type is (real(kind=4))
       call yggarg_array_real(y)
    type is (real(kind=8))
       call yggarg_array_real(y)
    type is (real(kind=16))
       call yggarg_array_real(y)
    type is (complex(kind=4))
       call yggarg_array_complex(y)
    type is (complex(kind=8))
       call yggarg_array_complex(y)
    type is (complex(kind=16))
       call yggarg_array_complex(y)
    type is (logical(kind=1))
       call yggarg_array_logical(y)
    type is (logical(kind=2))
       call yggarg_array_logical(y)
    type is (logical(kind=4))
       call yggarg_array_logical(y)
    type is (logical(kind=8))
       call yggarg_array_logical(y)
    type is (character(*))
       call yggarg_array_character(y)
    type is (yggchar_r)
       call yggarg_array_character(y)
    class default
       stop 'yggarg_array: Unexpected type.'
    end select
  end function yggarg_array
  
  ! Utilities
  subroutine fix_format_str(x)
    implicit none
    character(len=*) :: x
    integer :: i, length
    length = len(x)
    i = index(x, "\t")
    do while (i.ne.0)
       x(i:i) = char(9)
       x((i+1):length) = x((i+2):length)
       length = len(x)
       i = index(x, "\t")
    end do
    i = index(x, "\n")
    do while (i.ne.0)
       x(i:i) = NEW_LINE('c')
       x((i+1):length) = x((i+2):length)
       length = len(x)
       i = index(x, "\n")
    end do
  end subroutine fix_format_str

  ! YggInterface
  subroutine ygglog_info(fmt)
    implicit none
    character(len=*), intent(in) :: fmt
    character(len=len_trim(fmt)+1) :: c_fmt
    type(yggcomm) :: channel
    c_fmt = trim(fmt)//c_null_char
    call ygglog_info_c(c_fmt)
  end subroutine ygglog_info
  subroutine ygglog_debug(fmt)
    implicit none
    character(len=*), intent(in) :: fmt
    character(len=len_trim(fmt)+1) :: c_fmt
    type(yggcomm) :: channel
    c_fmt = trim(fmt)//c_null_char
    call ygglog_debug_c(c_fmt)
  end subroutine ygglog_debug
  subroutine ygglog_error(fmt)
    implicit none
    character(len=*), intent(in) :: fmt
    character(len=len_trim(fmt)+1) :: c_fmt
    type(yggcomm) :: channel
    c_fmt = trim(fmt)//c_null_char
    call ygglog_error_c(c_fmt)
  end subroutine ygglog_error
  
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
    call fix_format_str(c_format_str)
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
    call fix_format_str(c_format_str)
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
       allocate(args(i)%len_c)
       allocate(args(i)%prec_c)
       args(i)%len_c = 1
       args(i)%prec_c = 1
       if (((args(i)%type.eq."character").or. &
            args(i)%array).and. &
            (i.ge.size(args)).or.(args(i+1)%array).or. &
            (args(i+1)%type.ne."size_t")) then
          nargs = nargs + 1
          if ((args(i)%type.eq."character").and.args(i)%array) then
             nargs = nargs + 1
          end if
       end if
    end do
    allocate(c_args(nargs))
    j = 1
    do i = 1, size(args)
       c_args(j) = args(i)%ptr
       j = j + 1
       if ((args(i)%type.eq."character").and.(.not.args(i)%array)) then
          if ((i.lt.size(args)).and.(.not.args(i+1)%array).and. &
               (args(i+1)%type.eq."size_t")) then
             args(i)%prec_ptr = args(i+1)%ptr
          else
             args(i)%prec_c = args(i)%prec
             args(i)%prec_ptr = c_loc(args(i)%prec_c)
             c_args(j) = args(i)%prec_ptr
             j = j + 1
          end if
       else if ((args(i)%type.eq."character").or.args(i)%array) then
          if ((i.lt.size(args)).and.(.not.args(i+1)%array).and. &
               (args(i+1)%type.eq."size_t")) then
             args(i)%len_ptr = args(i+1)%ptr
          else
             args(i)%len_c = args(i)%len
             args(i)%len_ptr = c_loc(args(i)%len_c)
             c_args(j) = args(i)%len_ptr
             j = j + 1
          end if
          if ((args(i)%type.eq."character").and.args(i)%array) then
             args(i)%prec_c = args(i)%prec
             args(i)%prec_ptr = c_loc(args(i)%prec_c)
             c_args(j) = args(i)%prec_ptr
             j = j + 1
          end if
       end if
    end do
  end subroutine pre_recv

  subroutine post_recv(args, c_args, flag, realloc)
    implicit none
    type(yggptr) :: args(:)
    type(c_ptr), allocatable, target :: c_args(:)
    integer :: flag, i, j
    logical :: realloc
    call ygglog_debug("post_recv: begin")
    if (flag.ge.0) then
       j = 1
       do i = 1, size(args)
          args(i)%ptr = c_args(j)
          flag = yggptr_c2f(args(i), realloc)
          if (flag.lt.0) then
             call ygglog_error("Error recovering fortran pointer for variable.")
             exit
          end if
          j = j + 1
          if (((args(i)%type.eq."character").or.args(i)%array).and. &
               ((i.ge.size(args)).or.(args(i+1)%array).or. &
               (args(i+1)%type.ne."size_t"))) then
             j = j + 1
             if ((args(i)%type.eq."character").and.args(i)%array) then
                j = j + 1
             end if
          end if
          ! deallocate(args(i)%len_c)
          ! deallocate(args(i)%prec_c)
       end do
    end if
    if (allocated(c_args)) then
       deallocate(c_args)
    end if
    call ygglog_debug("post_recv: end")
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
    call post_recv(args, c_args, flag, .false.)
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
    call ygglog_debug("ygg_recv_var_realloc: begin")
    c_ygg_q = ygg_q%comm
    flag = 0
    do i = 1, size(args)
       if (args(i)%array.or.(args(i)%type.eq."character")) then
          if (.not.(args(i)%alloc)) then
             call ygglog_error("Provided array/string is not allocatable.")
             flag = -1
          else
             ! TODO: Find a way to nullify pointer so that memory
             ! is "surrendered" to C when it is reallocated C side
             args(i)%ptr = c_null_ptr
          end if
       end if
    end do
    if (flag.ge.0) then
       call pre_recv(args, c_args)
       c_nargs = size(args)
       c_flag = ygg_recv_var_realloc_c(c_ygg_q, c_nargs, c_loc(c_args(1)))
       flag = c_flag
    end if
    call post_recv(args, c_args, flag, .true.)
    call ygglog_debug("ygg_recv_var_realloc: end")
  end function ygg_recv_var_realloc
  
end module fygg
