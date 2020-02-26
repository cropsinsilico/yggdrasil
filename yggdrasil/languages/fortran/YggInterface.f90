module fygg
  ! TODO: Ensure that dynamically allocated C/C++ variables are freed.
  use iso_c_binding
  implicit none

  integer, parameter :: LINE_SIZE_MAX = 2048
  integer, parameter :: YGG_MSG_BUF = 2048

  interface yggarg
     module procedure yggarg_scalar_integer2
     module procedure yggarg_scalar_integer4
     module procedure yggarg_scalar_integer8
     module procedure yggarg_scalar_real4
     module procedure yggarg_scalar_real8
     module procedure yggarg_scalar_real16
     module procedure yggarg_scalar_complex4
     module procedure yggarg_scalar_complex8
     module procedure yggarg_scalar_complex16
     module procedure yggarg_scalar_logical1
     module procedure yggarg_scalar_logical2
     module procedure yggarg_scalar_logical4
     module procedure yggarg_scalar_logical8
     module procedure yggarg_scalar_character
     module procedure yggarg_scalar_yggchar_r
     module procedure yggarg_scalar_ply
     module procedure yggarg_scalar_obj
     module procedure yggarg_scalar_generic
     module procedure yggarg_realloc_1darray_c_long
     module procedure yggarg_realloc_1darray_integer
     module procedure yggarg_realloc_1darray_integer2
     module procedure yggarg_realloc_1darray_integer4
     module procedure yggarg_realloc_1darray_integer8
     module procedure yggarg_realloc_1darray_real
     module procedure yggarg_realloc_1darray_real4
     module procedure yggarg_realloc_1darray_real8
     module procedure yggarg_realloc_1darray_real16
     module procedure yggarg_realloc_1darray_complex
     module procedure yggarg_realloc_1darray_complex4
     module procedure yggarg_realloc_1darray_complex8
     module procedure yggarg_realloc_1darray_complex16
     module procedure yggarg_realloc_1darray_logical
     module procedure yggarg_realloc_1darray_logical1
     module procedure yggarg_realloc_1darray_logical2
     module procedure yggarg_realloc_1darray_logical4
     module procedure yggarg_realloc_1darray_logical8
     module procedure yggarg_realloc_1darray_character
     module procedure yggarg_1darray_integer2
     module procedure yggarg_1darray_integer4
     module procedure yggarg_1darray_integer8
     module procedure yggarg_1darray_real4
     module procedure yggarg_1darray_real8
     module procedure yggarg_1darray_real16
     module procedure yggarg_1darray_complex4
     module procedure yggarg_1darray_complex8
     module procedure yggarg_1darray_complex16
     module procedure yggarg_1darray_logical1
     module procedure yggarg_1darray_logical2
     module procedure yggarg_1darray_logical4
     module procedure yggarg_1darray_logical8
     module procedure yggarg_1darray_character
     module procedure yggarg_1darray_yggchar_r
  end interface yggarg
  interface ygg_send_var
     module procedure ygg_send_var_sing
     module procedure ygg_send_var_mult
  end interface ygg_send_var
  interface ygg_recv_var
     module procedure ygg_recv_var_sing
     module procedure ygg_recv_var_mult
  end interface ygg_recv_var
  interface ygg_recv_var_realloc
     module procedure ygg_recv_var_realloc_sing
     module procedure ygg_recv_var_realloc_mult
  end interface ygg_recv_var_realloc
  interface ygg_rpc_call
     module procedure ygg_rpc_call_1v1
     module procedure ygg_rpc_call_1vm
     module procedure ygg_rpc_call_mv1
     module procedure ygg_rpc_call_mult
  end interface ygg_rpc_call
  interface ygg_rpc_call_realloc
     module procedure ygg_rpc_call_realloc_1v1
     module procedure ygg_rpc_call_realloc_1vm
     module procedure ygg_rpc_call_realloc_mv1
     module procedure ygg_rpc_call_realloc_mult
  end interface ygg_rpc_call_realloc
  type :: yggcomm
     type(c_ptr) :: comm
  end type yggcomm
  type :: yggchar_r
     character, dimension(:), pointer :: x => null()
  end type yggchar_r
  type :: c_long_1d
     integer(kind=c_long), dimension(:), pointer :: x => null()
  end type c_long_1d
  type :: integer_1d
     integer, dimension(:), pointer :: x => null()
  end type integer_1d
  type :: integer2_1d
     integer(kind=2), dimension(:), pointer :: x => null()
  end type integer2_1d
  type :: integer4_1d
     integer(kind=4), dimension(:), pointer :: x => null()
  end type integer4_1d
  type :: integer8_1d
     integer(kind=8), dimension(:), pointer :: x => null()
  end type integer8_1d
  type :: real_1d
     real, dimension(:), pointer :: x => null()
  end type real_1d
  type :: real4_1d
     real(kind=4), dimension(:), pointer :: x => null()
  end type real4_1d
  type :: real8_1d
     real(kind=8), dimension(:), pointer :: x => null()
  end type real8_1d
  type :: real16_1d
     real(kind=16), dimension(:), pointer :: x => null()
  end type real16_1d
  type :: complex_1d
     complex, dimension(:), pointer :: x => null()
  end type complex_1d
  type :: complex4_1d
     complex(kind=4), dimension(:), pointer :: x => null()
  end type complex4_1d
  type :: complex8_1d
     complex(kind=8), dimension(:), pointer :: x => null()
  end type complex8_1d
  type :: complex16_1d
     complex(kind=16), dimension(:), pointer :: x => null()
  end type complex16_1d
  type :: logical_1d
     logical, dimension(:), pointer :: x => null()
  end type logical_1d
  type :: logical1_1d
     logical(kind=1), dimension(:), pointer :: x => null()
  end type logical1_1d
  type :: logical2_1d
     logical(kind=2), dimension(:), pointer :: x => null()
  end type logical2_1d
  type :: logical4_1d
     logical(kind=4), dimension(:), pointer :: x => null()
  end type logical4_1d
  type :: logical8_1d
     logical(kind=8), dimension(:), pointer :: x => null()
  end type logical8_1d
  type :: character_1d
     type(yggchar_r), dimension(:), pointer :: x => null()
  end type character_1d
  type :: integer_2d
     integer, dimension(:, :), pointer :: x => null()
  end type integer_2d
  type :: integer2_2d
     integer(kind=2), dimension(:, :), pointer :: x => null()
  end type integer2_2d
  type :: integer4_2d
     integer(kind=4), dimension(:, :), pointer :: x => null()
  end type integer4_2d
  type :: integer8_2d
     integer(kind=8), dimension(:, :), pointer :: x => null()
  end type integer8_2d
  type :: real_2d
     real, dimension(:, :), pointer :: x => null()
  end type real_2d
  type :: real4_2d
     real(kind=4), dimension(:, :), pointer :: x => null()
  end type real4_2d
  type :: real8_2d
     real(kind=8), dimension(:, :), pointer :: x => null()
  end type real8_2d
  type :: real16_2d
     real(kind=16), dimension(:, :), pointer :: x => null()
  end type real16_2d
  type :: complex_2d
     complex, dimension(:, :), pointer :: x => null()
  end type complex_2d
  type :: complex4_2d
     complex(kind=4), dimension(:, :), pointer :: x => null()
  end type complex4_2d
  type :: complex8_2d
     complex(kind=8), dimension(:, :), pointer :: x => null()
  end type complex8_2d
  type :: complex16_2d
     complex(kind=16), dimension(:, :), pointer :: x => null()
  end type complex16_2d
  type :: logical_2d
     logical, dimension(:, :), pointer :: x => null()
  end type logical_2d
  type :: logical1_2d
     logical(kind=1), dimension(:, :), pointer :: x => null()
  end type logical1_2d
  type :: logical2_2d
     logical(kind=2), dimension(:, :), pointer :: x => null()
  end type logical2_2d
  type :: logical4_2d
     logical(kind=4), dimension(:, :), pointer :: x => null()
  end type logical4_2d
  type :: logical8_2d
     logical(kind=8), dimension(:, :), pointer :: x => null()
  end type logical8_2d
  type :: character_2d
     type(yggchar_r), dimension(:, :), pointer :: x => null()
  end type character_2d
  type :: yggptr
     character(len=15) :: type = "none"
     logical :: array = .false.
     logical :: alloc = .false.
     integer(kind=8) :: len = 0
     integer(kind=8) :: prec = 0
     integer(kind=8) :: nbytes = 0
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
     type(yggptr), dimension(:), pointer :: vals => null()
  end type yggptr_arr
  type :: yggptr_map
     character(len=20), dimension(:), pointer :: keys => null()
     type(yggptr), dimension(:), pointer :: vals => null()
  end type yggptr_map
  type, bind(c) :: ygggeneric
     character(kind=c_char) :: prefix
     type(c_ptr) :: obj
  end type ygggeneric
  type, bind(c) :: yggply
     character(kind=c_char), dimension(100) :: material
     integer(kind=c_int) :: nvert
     integer(kind=c_int) :: nface
     integer(kind=c_int) :: nedge
     type(c_ptr) :: c_vertices
     type(c_ptr) :: c_faces
     type(c_ptr) :: c_edges
     type(c_ptr) :: c_vertex_colors
     type(c_ptr) :: c_edge_colors
     type(c_ptr) :: c_nvert_in_face
  end type yggply
  type, bind(c) :: yggobj
     character(kind=c_char), dimension(100) :: material
     integer(kind=c_int) :: nvert
     integer(kind=c_int) :: ntexc
     integer(kind=c_int) :: nnorm
     integer(kind=c_int) :: nparam
     integer(kind=c_int) :: npoint
     integer(kind=c_int) :: nline
     integer(kind=c_int) :: nface
     integer(kind=c_int) :: ncurve
     integer(kind=c_int) :: ncurve2
     integer(kind=c_int) :: nsurf
     type(c_ptr) :: c_vertices
     type(c_ptr) :: c_vertex_colors
     type(c_ptr) :: c_texcoords
     type(c_ptr) :: c_normals
     type(c_ptr) :: c_params
     type(c_ptr) :: c_points
     type(c_ptr) :: c_nvert_in_point
     type(c_ptr) :: c_lines
     type(c_ptr) :: c_nvert_in_line
     type(c_ptr) :: c_line_texcoords
     type(c_ptr) :: c_faces
     type(c_ptr) :: c_nvert_in_face
     type(c_ptr) :: c_face_texcoords
     type(c_ptr) :: c_face_normals
     type(c_ptr) :: c_curves
     type(c_ptr) :: c_curve_params
     type(c_ptr) :: c_nvert_in_curve
     type(c_ptr) :: c_curves2
     type(c_ptr) :: c_nparam_in_curve2
     type(c_ptr) :: c_surfaces
     type(c_ptr) :: c_nvert_in_surface
     type(c_ptr) :: c_surface_params_u
     type(c_ptr) :: c_surface_params_v
     type(c_ptr) :: c_surface_texcoords
     type(c_ptr) :: c_surface_normals
  end type yggobj

  public :: yggarg, yggchar_r, yggcomm, ygggeneric, &
       yggptr, yggptr_arr, yggptr_map, yggply, yggobj, &
       integer_1d, real_1d, complex_1d, logical_1d, character_1d, &
       LINE_SIZE_MAX

  include "YggInterface_cdef.f90"

contains

  include "YggInterface_realloc.f90"
  include "YggInterface_c2f.f90"
  include "YggInterface_arg.f90"
  
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

  ! Utilities
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

  ! Methods for initializing channels
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
  
  function ygg_ply_output(name) result(channel)
    implicit none
    character(len=*), intent(in) :: name
    character(len=len_trim(name)+1) :: c_name
    type(yggcomm) :: channel
    c_name = trim(name)//c_null_char
    channel%comm = ygg_ply_output_c(c_name)
  end function ygg_ply_output
  
  function ygg_ply_input(name) result(channel)
    implicit none
    character(len=*), intent(in) :: name
    character(len=len_trim(name)+1) :: c_name
    type(yggcomm) :: channel
    c_name = trim(name)//c_null_char
    channel%comm = ygg_ply_input_c(c_name)
  end function ygg_ply_input
  
  function ygg_obj_output(name) result(channel)
    implicit none
    character(len=*), intent(in) :: name
    character(len=len_trim(name)+1) :: c_name
    type(yggcomm) :: channel
    c_name = trim(name)//c_null_char
    channel%comm = ygg_obj_output_c(c_name)
  end function ygg_obj_output
  
  function ygg_obj_input(name) result(channel)
    implicit none
    character(len=*), intent(in) :: name
    character(len=len_trim(name)+1) :: c_name
    type(yggcomm) :: channel
    c_name = trim(name)//c_null_char
    channel%comm = ygg_obj_input_c(c_name)
  end function ygg_obj_input

  function ygg_generic_output(name) result(channel)
    implicit none
    character(len=*), intent(in) :: name
    character(len=len_trim(name)+1) :: c_name
    type(yggcomm) :: channel
    c_name = trim(name)//c_null_char
    channel%comm = ygg_generic_output_c(c_name)
  end function ygg_generic_output
  
  function ygg_generic_input(name) result(channel)
    implicit none
    character(len=*), intent(in) :: name
    character(len=len_trim(name)+1) :: c_name
    type(yggcomm) :: channel
    c_name = trim(name)//c_null_char
    channel%comm = ygg_generic_input_c(c_name)
  end function ygg_generic_input

  function ygg_any_output(name) result(channel)
    implicit none
    character(len=*), intent(in) :: name
    character(len=len_trim(name)+1) :: c_name
    type(yggcomm) :: channel
    c_name = trim(name)//c_null_char
    channel%comm = ygg_any_output_c(c_name)
  end function ygg_any_output
  
  function ygg_any_input(name) result(channel)
    implicit none
    character(len=*), intent(in) :: name
    character(len=len_trim(name)+1) :: c_name
    type(yggcomm) :: channel
    c_name = trim(name)//c_null_char
    channel%comm = ygg_any_input_c(c_name)
  end function ygg_any_input

  function ygg_json_array_output(name) result(channel)
    implicit none
    character(len=*), intent(in) :: name
    character(len=len_trim(name)+1) :: c_name
    type(yggcomm) :: channel
    c_name = trim(name)//c_null_char
    channel%comm = ygg_json_array_output_c(c_name)
  end function ygg_json_array_output
  
  function ygg_json_array_input(name) result(channel)
    implicit none
    character(len=*), intent(in) :: name
    character(len=len_trim(name)+1) :: c_name
    type(yggcomm) :: channel
    c_name = trim(name)//c_null_char
    channel%comm = ygg_json_array_input_c(c_name)
  end function ygg_json_array_input

  function ygg_json_object_output(name) result(channel)
    implicit none
    character(len=*), intent(in) :: name
    character(len=len_trim(name)+1) :: c_name
    type(yggcomm) :: channel
    c_name = trim(name)//c_null_char
    channel%comm = ygg_json_object_output_c(c_name)
  end function ygg_json_object_output
  
  function ygg_json_object_input(name) result(channel)
    implicit none
    character(len=*), intent(in) :: name
    character(len=len_trim(name)+1) :: c_name
    type(yggcomm) :: channel
    c_name = trim(name)//c_null_char
    channel%comm = ygg_json_object_input_c(c_name)
  end function ygg_json_object_input

  function ygg_rpc_client(name, out_fmt, in_fmt) result(channel)
    implicit none
    character(len=*), intent(in) :: name
    character(len=*), intent(in) :: out_fmt
    character(len=*), intent(in) :: in_fmt
    character(len=len_trim(name)+1) :: c_name
    character(len=len_trim(out_fmt)+1) :: c_out_fmt
    character(len=len_trim(in_fmt)+1) :: c_in_fmt
    type(yggcomm) :: channel
    c_name = trim(name)//c_null_char
    c_out_fmt = trim(out_fmt)//c_null_char
    c_in_fmt = trim(in_fmt)//c_null_char
    call fix_format_str(c_out_fmt)
    call fix_format_str(c_in_fmt)
    channel%comm = ygg_rpc_client_c(c_name, c_out_fmt, c_in_fmt)
  end function ygg_rpc_client

  function ygg_rpc_server(name, in_fmt, out_fmt) result(channel)
    implicit none
    character(len=*), intent(in) :: name
    character(len=*), intent(in) :: in_fmt
    character(len=*), intent(in) :: out_fmt
    character(len=len_trim(name)+1) :: c_name
    character(len=len_trim(in_fmt)+1) :: c_in_fmt
    character(len=len_trim(out_fmt)+1) :: c_out_fmt
    type(yggcomm) :: channel
    c_name = trim(name)//c_null_char
    c_in_fmt = trim(in_fmt)//c_null_char
    c_out_fmt = trim(out_fmt)//c_null_char
    call fix_format_str(c_in_fmt)
    call fix_format_str(c_out_fmt)
    channel%comm = ygg_rpc_server_c(c_name, c_in_fmt, c_out_fmt)
  end function ygg_rpc_server

  ! Methods for sending/receiving
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

  function ygg_send_var_sing(ygg_q, arg) result (flag)
    implicit none
    type(yggcomm), intent(in) :: ygg_q
    type(yggptr) :: arg
    integer :: flag
    flag = ygg_send_var_mult(ygg_q, [arg])
  end function ygg_send_var_sing
  function ygg_send_var_mult(ygg_q, args) result (flag)
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
  end function ygg_send_var_mult

  function is_size_t(arg) result(flag)
    type(yggptr), intent(in) :: arg
    logical :: flag
    if (((arg%type.eq."integer").or.(arg%type.eq."size_t")).and. &
         (.not.arg%array).and.(arg%nbytes.eq.8)) then
       flag = .true.
    else
       flag = .false.
    end if
  end function is_size_t

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
            ((i.ge.size(args)).or.(.not.is_size_t(args(i+1))))) then
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
          if ((i.lt.size(args)).and.(is_size_t(args(i+1)))) then
             args(i)%prec_ptr = args(i+1)%ptr
          else
             args(i)%prec_c = args(i)%prec
             args(i)%prec_ptr = c_loc(args(i)%prec_c)
             c_args(j) = args(i)%prec_ptr
             j = j + 1
          end if
       else if ((args(i)%type.eq."character").or.args(i)%array) then
          if ((i.lt.size(args)).and.(is_size_t(args(i+1)))) then
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
               ((i.ge.size(args)).or.(.not.is_size_t(args(i+1))))) then
             j = j + 1
             if ((args(i)%type.eq."character").and.args(i)%array) then
                j = j + 1
             end if
          end if
          deallocate(args(i)%len_c)
          deallocate(args(i)%prec_c)
       end do
    end if
    if (allocated(c_args)) then
       deallocate(c_args)
    end if
    call ygglog_debug("post_recv: end")
  end subroutine post_recv

  function ygg_rpc_call_1v1(ygg_q, oarg, iarg) result (flag)
    implicit none
    type(yggcomm) :: ygg_q
    type(yggptr) :: oarg
    type(yggptr) :: iarg
    integer :: flag
    flag = ygg_rpc_call_mult(ygg_q, [oarg], [iarg])
  end function ygg_rpc_call_1v1
  function ygg_rpc_call_1vm(ygg_q, oarg, iargs) result (flag)
    implicit none
    type(yggcomm) :: ygg_q
    type(yggptr) :: oarg
    type(yggptr) :: iargs(:)
    integer :: flag
    flag = ygg_rpc_call_mult(ygg_q, [oarg], iargs)
  end function ygg_rpc_call_1vm
  function ygg_rpc_call_mv1(ygg_q, oargs, iarg) result (flag)
    implicit none
    type(yggcomm) :: ygg_q
    type(yggptr) :: oargs(:)
    type(yggptr) :: iarg
    integer :: flag
    flag = ygg_rpc_call_mult(ygg_q, oargs, [iarg])
  end function ygg_rpc_call_mv1
  function ygg_rpc_call_mult(ygg_q, oargs, iargs) result (flag)
    implicit none
    type(yggcomm) :: ygg_q
    type(c_ptr) :: c_ygg_q
    type(yggptr) :: oargs(:)
    type(yggptr) :: iargs(:)
    type(c_ptr), allocatable, target :: c_args(:)
    type(c_ptr), allocatable, target :: c_iargs(:)
    integer :: c_nargs
    integer :: flag, i
    integer(kind=c_int) :: c_flag
    c_ygg_q = ygg_q%comm
    call pre_recv(iargs, c_iargs)
    c_nargs = size(oargs) + size(iargs)
    allocate(c_args(size(oargs) + size(c_iargs)))
    do i = 1, size(oargs)
       c_args(i) = oargs(i)%ptr
    end do
    do i = 1, size(c_iargs)
       c_args(i + size(oargs)) = c_iargs(i)
    end do
    c_flag = ygg_rpc_call_c(c_ygg_q, c_nargs, c_loc(c_args(1)))
    flag = c_flag
    do i = 1, size(c_iargs)
       c_iargs(i) = c_args(i + size(oargs))
    end do
    call post_recv(iargs, c_iargs, flag, .false.)
    if (allocated(c_args)) then
       deallocate(c_args)
    end if
  end function ygg_rpc_call_mult
  
  function ygg_rpc_call_realloc_1v1(ygg_q, oarg, iarg) result (flag)
    implicit none
    type(yggcomm) :: ygg_q
    type(yggptr) :: oarg
    type(yggptr) :: iarg
    integer :: flag
    flag = ygg_rpc_call_realloc_mult(ygg_q, [oarg], [iarg])
  end function ygg_rpc_call_realloc_1v1
  function ygg_rpc_call_realloc_1vm(ygg_q, oarg, iargs) result (flag)
    implicit none
    type(yggcomm) :: ygg_q
    type(yggptr) :: oarg
    type(yggptr) :: iargs(:)
    integer :: flag
    flag = ygg_rpc_call_realloc_mult(ygg_q, [oarg], iargs)
  end function ygg_rpc_call_realloc_1vm
  function ygg_rpc_call_realloc_mv1(ygg_q, oargs, iarg) result (flag)
    implicit none
    type(yggcomm) :: ygg_q
    type(yggptr) :: oargs(:)
    type(yggptr) :: iarg
    integer :: flag
    flag = ygg_rpc_call_realloc_mult(ygg_q, oargs, [iarg])
  end function ygg_rpc_call_realloc_mv1
  function ygg_rpc_call_realloc_mult(ygg_q, oargs, iargs) result (flag)
    implicit none
    type(yggcomm) :: ygg_q
    type(c_ptr) :: c_ygg_q
    type(yggptr) :: oargs(:)
    type(yggptr) :: iargs(:)
    type(c_ptr), allocatable, target :: c_args(:)
    type(c_ptr), allocatable, target :: c_iargs(:)
    integer :: c_nargs
    integer :: flag
    integer(kind=c_int) :: c_flag
    integer :: i
    c_ygg_q = ygg_q%comm
    flag = 0
    do i = 1, size(iargs)
       if ((iargs(i)%array.or.(iargs(i)%type.eq."character")).and. &
            (.not.(iargs(i)%alloc))) then
          call ygglog_error("Provided array/string is not allocatable.")
          flag = -1
       end if
    end do
    if (flag.ge.0) then
       call pre_recv(iargs, c_iargs)
       c_nargs = size(oargs) + size(iargs)
       allocate(c_args(size(oargs) + size(c_iargs)))
       do i = 1, size(oargs)
          c_args(i) = oargs(i)%ptr
       end do
       do i = 1, size(c_iargs)
          c_args(i + size(oargs)) = c_iargs(i)
       end do
       c_flag = ygg_rpc_call_realloc_c(c_ygg_q, c_nargs, c_loc(c_args(1)))
       flag = c_flag
       do i = 1, size(c_iargs)
          c_iargs(i) = c_args(i + size(oargs))
       end do
    end if
    call post_recv(iargs, c_iargs, flag, .true.)
    if (allocated(c_args)) then
       deallocate(c_args)
    end if
  end function ygg_rpc_call_realloc_mult
  
  function ygg_recv_var_sing(ygg_q, arg) result (flag)
    implicit none
    type(yggcomm) :: ygg_q
    type(yggptr) :: arg
    integer :: flag
    flag = ygg_recv_var_mult(ygg_q, [arg])
  end function ygg_recv_var_sing
  function ygg_recv_var_mult(ygg_q, args) result (flag)
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
  end function ygg_recv_var_mult

  function ygg_recv_var_realloc_sing(ygg_q, arg) result (flag)
    implicit none
    type(yggcomm) :: ygg_q
    type(yggptr) :: arg
    integer :: flag
    flag = ygg_recv_var_realloc_mult(ygg_q, [arg])
  end function ygg_recv_var_realloc_sing
  function ygg_recv_var_realloc_mult(ygg_q, args) result (flag)
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
       if ((args(i)%array.or.(args(i)%type.eq."character")).and. &
            (.not.(args(i)%alloc))) then
          call ygglog_error("Provided array/string is not allocatable.")
          flag = -1
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
  end function ygg_recv_var_realloc_mult

  ! Ply interface
  function init_ply() result (out)
    implicit none
    type(yggply) :: out
    out = init_ply_c()
  end function init_ply
  subroutine free_ply(pp)
    implicit none
    type(yggply), pointer :: pp
    type(c_ptr) :: c_p
    c_p = c_loc(pp%material(1))
    call free_ply_c(c_p)
    nullify(pp)
  end subroutine free_ply
  subroutine display_ply_indent(p, indent)
    implicit none
    type(yggply), intent(in) :: p
    character(len=*), intent(in) :: indent
    character(len=len(indent)+1) :: c_indent
    c_indent = indent//c_null_char
    call display_ply_indent_c(p, c_indent)
  end subroutine display_ply_indent
  subroutine display_ply(p)
    implicit none
    type(yggply), intent(in) :: p
    call display_ply_c(p)
  end subroutine display_ply
  
  ! Obj interface
  function init_obj() result (out)
    implicit none
    type(yggobj) :: out
    out = init_obj_c()
  end function init_obj
  subroutine free_obj(pp)
    implicit none
    type(yggobj), pointer :: pp
    type(c_ptr) :: c_p
    c_p = c_loc(pp)
    call free_obj_c(c_p)
    nullify(pp)
  end subroutine free_obj
  subroutine display_obj_indent(p, indent)
    implicit none
    type(yggobj), intent(in) :: p
    character(len=*), intent(in) :: indent
    character(len=len(indent)+1) :: c_indent
    c_indent = indent//c_null_char
    call display_obj_indent_c(p, c_indent)
  end subroutine display_obj_indent
  subroutine display_obj(p)
    implicit none
    type(yggobj), intent(in) :: p
    call display_obj_c(p)
  end subroutine display_obj

  ! Generic interface
  function init_generic() result(out)
    implicit none
    type(ygggeneric) :: out
    out = init_generic_c()
  end function init_generic
  function free_generic(x) result(out)
    implicit none
    type(ygggeneric) :: x
    integer(kind=c_int) :: out
    out = free_generic_c(x)
  end function free_generic
  function copy_generic(src) result(out)
    implicit none
    type(ygggeneric), intent(in) :: src
    type(ygggeneric) :: out
    out = copy_generic_c(src)
  end function copy_generic
  subroutine display_generic(x)
    implicit none
    type(ygggeneric), intent(in) :: x
    call display_generic_c(x)
  end subroutine display_generic
  function add_generic_array(arr, x) result(out)
    implicit none
    type(ygggeneric) :: arr
    type(ygggeneric), intent(in) :: x
    integer(kind=c_int) :: out
    out = add_generic_array_c(arr, x)
  end function add_generic_array
  function set_generic_array(arr, i, x) result(out)
    implicit none
    type(ygggeneric) :: arr
    integer(kind=c_size_t), intent(in) :: i
    type(ygggeneric), intent(in) :: x
    integer(kind=c_int) :: out
    out = set_generic_array_c(arr, i, x)
  end function set_generic_array
  function get_generic_array(arr, i, x) result(out)
    implicit none
    type(ygggeneric), intent(in) :: arr
    integer(kind=c_size_t), intent(in) :: i
    type(ygggeneric), pointer :: x
    integer(kind=c_int) :: out
    type(c_ptr) :: c_x
    c_x = c_loc(x) ! Maybe use first element in type
    out = get_generic_array_c(arr, i, c_x)
  end function get_generic_array
  function set_generic_object(arr, k, x) result(out)
    implicit none
    type(ygggeneric) :: arr
    character(len=*), intent(in) :: k
    type(ygggeneric), intent(in) :: x
    integer(kind=c_int) :: out
    character(len=len_trim(k)+1) :: c_k
    c_k = trim(k)//c_null_char
    out = set_generic_object_c(arr, c_k, x)
  end function set_generic_object
  function get_generic_object(arr, k, x) result(out)
    implicit none
    type(ygggeneric) :: arr
    character(len=*), intent(in) :: k
    type(ygggeneric), pointer :: x
    integer(kind=c_int) :: out
    character(len=len_trim(k)+1) :: c_k
    type(c_ptr) :: c_x
    c_k = trim(k)//c_null_char
    c_x = c_loc(x) ! Maybe use first element in type
    out = get_generic_object_c(arr, c_k, c_x)
  end function get_generic_object
  
end module fygg
