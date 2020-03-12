module fygg

  ! TODO: Ensure that dynamically allocated C/C++ variables are freed.
  use iso_c_binding
  implicit none

  integer, parameter :: LINE_SIZE_MAX = 2048
  integer, parameter :: YGG_MSG_BUF = 2048
  integer(kind=c_int), bind(c, name="YGG_MSG_MAX_F") :: YGG_MSG_MAX

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
     module procedure yggarg_scalar_null
     module procedure yggarg_scalar_generic
     module procedure yggarg_scalar_yggarr
     module procedure yggarg_scalar_yggmap
     module procedure yggarg_scalar_yggschema
     module procedure yggarg_scalar_yggpython
     module procedure yggarg_scalar_yggpyinst
     module procedure yggarg_scalar_yggpyfunc
     module procedure yggarg_scalar_yggptr
     ! module procedure yggarg_scalar_yggptr_arr
     ! module procedure yggarg_scalar_yggptr_map
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
     module procedure yggarg_2darray_integer2
     module procedure yggarg_2darray_integer4
     module procedure yggarg_2darray_integer8
     module procedure yggarg_2darray_real4
     module procedure yggarg_2darray_real8
     module procedure yggarg_2darray_real16
     module procedure yggarg_2darray_complex4
     module procedure yggarg_2darray_complex8
     module procedure yggarg_2darray_complex16
     module procedure yggarg_2darray_logical1
     module procedure yggarg_2darray_logical2
     module procedure yggarg_2darray_logical4
     module procedure yggarg_2darray_logical8
     module procedure yggarg_2darray_character
     module procedure yggarg_2darray_yggchar_r
  end interface yggarg
  interface yggassign
     module procedure yggassign_yggchar2character
     ! module procedure yggassign_character2yggchar
  end interface yggassign
  interface yggarr
     module procedure ygggeneric2yggarr
  end interface yggarr
  interface yggmap
     module procedure ygggeneric2yggmap
  end interface yggmap
  interface yggschema
     module procedure ygggeneric2yggschema
  end interface yggschema
  interface yggpyinst
     module procedure ygggeneric2yggpyinst
  end interface yggpyinst
  interface ygggeneric
     module procedure yggarr2ygggeneric
     module procedure yggmap2ygggeneric
     module procedure yggschema2ygggeneric
     module procedure yggpyinst2ygggeneric
  end interface ygggeneric
  interface yggpyfunc
     module procedure yggpython2yggpyfunc
  end interface yggpyfunc
  interface yggpython
     module procedure yggpython2yggpython
     module procedure yggpyfunc2yggpython
  end interface yggpython
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
  type :: yggdtype
     type(c_ptr) :: ptr
  end type yggdtype
  type :: yggchar_r
     character, dimension(:), contiguous, pointer :: x => null()
  end type yggchar_r
  type :: c_long_1d
     integer(kind=c_long), dimension(:), contiguous, pointer :: x => null()
  end type c_long_1d
  type :: integer_1d
     integer, dimension(:), contiguous, pointer :: x => null()
  end type integer_1d
  type :: integer2_1d
     integer(kind=2), dimension(:), contiguous, pointer :: x => null()
  end type integer2_1d
  type :: integer4_1d
     integer(kind=4), dimension(:), contiguous, pointer :: x => null()
  end type integer4_1d
  type :: integer8_1d
     integer(kind=8), dimension(:), contiguous, pointer :: x => null()
  end type integer8_1d
  type :: real_1d
     real, dimension(:), contiguous, pointer :: x => null()
  end type real_1d
  type :: real4_1d
     real(kind=4), dimension(:), contiguous, pointer :: x => null()
  end type real4_1d
  type :: real8_1d
     real(kind=8), dimension(:), contiguous, pointer :: x => null()
  end type real8_1d
  type :: real16_1d
     real(kind=16), dimension(:), contiguous, pointer :: x => null()
  end type real16_1d
  type :: complex_1d
     complex, dimension(:), contiguous, pointer :: x => null()
  end type complex_1d
  type :: complex4_1d
     complex(kind=4), dimension(:), contiguous, pointer :: x => null()
  end type complex4_1d
  type :: complex8_1d
     complex(kind=8), dimension(:), contiguous, pointer :: x => null()
  end type complex8_1d
  type :: complex16_1d
     complex(kind=16), dimension(:), contiguous, pointer :: x => null()
  end type complex16_1d
  type :: logical_1d
     logical, dimension(:), contiguous, pointer :: x => null()
  end type logical_1d
  type :: logical1_1d
     logical(kind=1), dimension(:), contiguous, pointer :: x => null()
  end type logical1_1d
  type :: logical2_1d
     logical(kind=2), dimension(:), contiguous, pointer :: x => null()
  end type logical2_1d
  type :: logical4_1d
     logical(kind=4), dimension(:), contiguous, pointer :: x => null()
  end type logical4_1d
  type :: logical8_1d
     logical(kind=8), dimension(:), contiguous, pointer :: x => null()
  end type logical8_1d
  type :: character_1d
     type(yggchar_r), dimension(:), contiguous, pointer :: x => null()
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
     integer(kind=8) :: ndim = 0
     integer(kind=8) :: nbytes = 0
     integer(kind=8), dimension(:), contiguous, pointer :: shape => null()
     type(c_ptr) :: ptr = c_null_ptr
     class(*), pointer :: item => null()
     class(*), dimension(:), pointer :: item_array => null()
     class(*), dimension(:, :), pointer :: item_array_2d => null()
     class(*), dimension(:, :, :), pointer :: item_array_3d => null()
     character, dimension(:), contiguous, pointer :: data_character_unit => null()
     integer(kind=c_size_t), pointer :: len_c => null()
     integer(kind=c_size_t), pointer :: prec_c => null()
     integer(kind=c_size_t), pointer :: ndim_c => null()
     integer(kind=c_size_t), dimension(:), contiguous, pointer :: shape_c => null()
     type(c_ptr) :: len_ptr = c_null_ptr
     type(c_ptr) :: prec_ptr = c_null_ptr
     type(c_ptr) :: ndim_ptr = c_null_ptr
     type(c_ptr) :: shape_ptr = c_null_ptr
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
  type :: yggnull
     type(c_ptr) :: ptr = c_null_ptr
  end type yggnull
  type, bind(c) :: yggarr
     character(kind=c_char) :: prefix
     type(c_ptr) :: obj
  end type yggarr
  type, bind(c) :: yggmap
     character(kind=c_char) :: prefix
     type(c_ptr) :: obj
  end type yggmap
  type, bind(c) :: yggschema
     character(kind=c_char) :: prefix
     type(c_ptr) :: obj
  end type yggschema
  type, bind(c) :: yggpyinst
     character(kind=c_char) :: prefix
     type(c_ptr) :: obj
  end type yggpyinst
  type, bind(c) :: yggpyfunc
     character(kind=c_char, len=1000) :: name = c_null_char
     type(c_ptr) :: args = c_null_ptr
     type(c_ptr) :: kwargs = c_null_ptr
     type(c_ptr) :: obj = c_null_ptr
  end type yggpyfunc
  type, bind(c) :: yggpython
     character(kind=c_char, len=1000) :: name = c_null_char
     type(c_ptr) :: args = c_null_ptr
     type(c_ptr) :: kwargs = c_null_ptr
     type(c_ptr) :: obj = c_null_ptr
  end type yggpython
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
       yggptr, yggnull, yggarr, yggmap, &
       yggschema, yggpython, yggply, yggobj, yggpyinst, yggpyfunc, &
       integer_1d, real_1d, complex_1d, logical_1d, character_1d, &
       LINE_SIZE_MAX

  include "YggInterface_cdef.f90"

contains

  include "YggInterface_realloc.f90"
  include "YggInterface_c2f.f90"
  include "YggInterface_arg.f90"
  include "YggInterface_conv.f90"
  include "YggInterface_assign.f90"
  
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
  function is_comm_format_array_type(x, args) result(out)
    implicit none
    type(yggcomm), intent(in) :: x
    type(yggptr) :: args(:)
    logical :: out
    integer(c_int) :: c_out
    integer :: i
    c_out = is_comm_format_array_type_c(x%comm)
    if (c_out.eq.0) then
       out = .false.
    else if (c_out.eq.1) then
       out = .true.
    else if (size(args).eq.1) then
       out = .false.
    else
       out = .true.
       do i = 2, size(args)
          if (.not.args(i)%array) then
             out = .false.
             exit
          end if
       end do
       if ((out).and.(.not.((args(1)%array).or.(is_size_t(args(1)))))) then
          out = .false.
       end if
       ! stop "is_comm_format_array_type: Error checking type."
    end if
  end function is_comm_format_array_type
  
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

  function ygg_output_type(name, datatype) result(channel)
    implicit none
    character(len=*), intent(in) :: name
    type(yggdtype) :: datatype
    character(len=len_trim(name)+1) :: c_name
    type(c_ptr) :: c_datatype
    type(yggcomm) :: channel
    c_name = trim(name)//c_null_char
    c_datatype = datatype%ptr
    channel%comm = ygg_output_type_c(c_name, c_datatype)
  end function ygg_output_type
  
  function ygg_input_type(name, datatype) result(channel)
    implicit none
    character(len=*), intent(in) :: name
    type(yggdtype) :: datatype
    character(len=len_trim(name)+1) :: c_name
    type(c_ptr) :: c_datatype
    type(yggcomm) :: channel
    c_name = trim(name)//c_null_char
    c_datatype = datatype%ptr
    channel%comm = ygg_input_type_c(c_name, c_datatype)
  end function ygg_input_type
  
  function ygg_output_fmt(name, fmt) result(channel)
    implicit none
    character(len=*), intent(in) :: name
    character(len=*), intent(in) :: fmt
    character(len=len_trim(name)+1) :: c_name
    character(len=len_trim(fmt)+1) :: c_fmt
    type(yggcomm) :: channel
    c_name = trim(name)//c_null_char
    c_fmt = trim(fmt)//c_null_char
    call fix_format_str(c_fmt)
    channel%comm = ygg_output_fmt_c(c_name, c_fmt)
  end function ygg_output_fmt
  
  function ygg_input_fmt(name, fmt) result(channel)
    implicit none
    character(len=*), intent(in) :: name
    character(len=*), intent(in) :: fmt
    character(len=len_trim(name)+1) :: c_name
    character(len=len_trim(fmt)+1) :: c_fmt
    type(yggcomm) :: channel
    c_name = trim(name)//c_null_char
    c_fmt = trim(fmt)//c_null_char
    call fix_format_str(c_fmt)
    channel%comm = ygg_input_fmt_c(c_name, c_fmt)
  end function ygg_input_fmt
  
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

  ! Method for constructing data types
  function is_dtype_format_array(type_struct) result(out)
    implicit none
    type(yggdtype) :: type_struct
    logical :: out
    integer(kind=c_int) :: c_out
    c_out = is_dtype_format_array_c(type_struct%ptr)
    if (c_out.eq.0) then
       out = .false.
    else if (c_out.eq.1) then
       out = .true.
    else
       stop "is_dtype_format_array: Error checking data type"
    end if
  end function is_dtype_format_array
  
  function create_dtype_empty(use_generic) result(out)
    implicit none
    logical, intent(in) :: use_generic
    type(yggdtype) :: out
    out%ptr = create_dtype_empty_c(logical(use_generic, kind=1))
  end function create_dtype_empty

  function create_dtype_python(pyobj, use_generic) result(out)
    implicit none
    type(c_ptr) :: pyobj
    logical, intent(in) :: use_generic
    type(yggdtype) :: out
    out%ptr = create_dtype_python_c(pyobj, logical(use_generic, kind=1))
  end function create_dtype_python

  function create_dtype_direct(use_generic) result(out)
    implicit none
    logical, intent(in) :: use_generic
    type(yggdtype) :: out
    out%ptr = create_dtype_direct_c(logical(use_generic, kind=1))
  end function create_dtype_direct

  function create_dtype_default(typename, use_generic) result(out)
    implicit none
    character(len=*), intent(in) :: typename
    logical, intent(in) :: use_generic
    type(yggdtype) :: out
    character(len=len_trim(typename)+1) :: c_typename
    c_typename = trim(typename)//c_null_char
    out%ptr = create_dtype_default_c(c_typename, logical(use_generic, kind=1))
  end function create_dtype_default

  function create_dtype_scalar(subtype, precision, units, &
       use_generic) result(out)
    implicit none
    character(len=*), intent(in) :: subtype
    integer, intent(in) :: precision
    character(len=*), intent(in) :: units
    logical, intent(in) :: use_generic
    type(yggdtype) :: out
    character(len=len_trim(subtype)+1) :: c_subtype
    integer(kind=c_size_t) :: c_precision
    character(len=len_trim(units)+1) :: c_units
    c_subtype = trim(subtype)//c_null_char
    c_precision = precision
    c_units = trim(units)//c_null_char
    out%ptr = create_dtype_scalar_c(c_subtype, c_precision, c_units, &
         logical(use_generic, kind=1))
  end function create_dtype_scalar

  function create_dtype_1darray(subtype, precision, length, &
       units, use_generic) result(out)
    implicit none
    character(len=*), intent(in) :: subtype
    integer, intent(in) :: precision
    integer, intent(in) :: length
    character(len=*), intent(in) :: units
    logical, intent(in) :: use_generic
    type(yggdtype) :: out
    character(len=len_trim(subtype)+1) :: c_subtype
    integer(kind=c_size_t) :: c_precision
    integer(kind=c_size_t) :: c_length
    character(len=len_trim(units)+1) :: c_units
    c_subtype = trim(subtype)//c_null_char
    c_precision = precision
    c_length = length
    c_units = trim(units)//c_null_char
    out%ptr = create_dtype_1darray_c(c_subtype, c_precision, c_length, &
         c_units, logical(use_generic, kind=1))
  end function create_dtype_1darray

  function create_dtype_ndarray(subtype, precision, ndim, &
       shape, units, use_generic) result(out)
    implicit none
    character(len=*), intent(in) :: subtype
    integer, intent(in) :: precision
    integer, intent(in) :: ndim
    integer(kind=c_size_t), dimension(:), target, intent(in) :: shape
    character(len=*), intent(in) :: units
    logical, intent(in) :: use_generic
    type(yggdtype) :: out
    integer(kind=c_size_t), dimension(:), pointer :: pshape
    character(len=len_trim(subtype)+1) :: c_subtype
    integer(kind=c_size_t) :: c_precision
    integer(kind=c_size_t) :: c_ndim
    type(c_ptr) :: c_shape
    character(len=len_trim(units)+1) :: c_units
    pshape => shape
    c_subtype = trim(subtype)//c_null_char
    c_precision = precision
    c_ndim = ndim
    c_shape = c_loc(shape(1))
    c_units = trim(units)//c_null_char
    out%ptr = create_dtype_ndarray_c(c_subtype, c_precision, c_ndim, &
         c_shape, c_units, logical(use_generic, kind=1))
  end function create_dtype_ndarray

  function create_dtype_json_array(nitems, items, use_generic) &
       result(out)
    implicit none
    integer, intent(in) :: nitems
    type(yggdtype), dimension(:), intent(in) :: items
    logical, intent(in) :: use_generic
    type(yggdtype) :: out
    integer(kind=c_size_t) :: c_nitems
    type(c_ptr), target :: c_items(size(items))
    integer :: i
    c_nitems = nitems
    do i = 1, size(items)
       c_items(i) = items(i)%ptr
    end do
    out%ptr = create_dtype_json_array_c(c_nitems, c_loc(c_items(1)), &
         logical(use_generic, kind=1))
  end function create_dtype_json_array

  function create_dtype_json_object(nitems, keys, values, use_generic) &
       result(out)
    implicit none
    integer, intent(in) :: nitems
    character(len=*), dimension(:), intent(in), target :: keys
    type(yggdtype), dimension(:), intent(in) :: values
    logical, intent(in) :: use_generic
    type(yggdtype) :: out
    integer(kind=c_size_t) :: c_nitems
    type(c_ptr), target :: c_keys(size(keys))
    type(c_ptr), target :: c_values(size(values))
    character(len=len(keys(1))), target :: ikey
    integer :: i
    c_nitems = nitems
    do i = 1, size(keys)
       ikey = keys(i)
       c_keys(i) = c_loc(ikey(i:i))
    end do
    do i = 1, size(values)
       c_values(i) = values(i)%ptr
    end do
    out%ptr = create_dtype_json_object_c(c_nitems, c_loc(c_keys(1)), &
         c_loc(c_values(1)), logical(use_generic, kind=1))
  end function create_dtype_json_object

  function create_dtype_ply(use_generic) result(out)
    implicit none
    logical, intent(in) :: use_generic
    type(yggdtype) :: out
    out%ptr = create_dtype_ply_c(logical(use_generic, kind=1))
  end function create_dtype_ply

  function create_dtype_obj(use_generic) result(out)
    implicit none
    logical, intent(in) :: use_generic
    type(yggdtype) :: out
    out%ptr = create_dtype_obj_c(logical(use_generic, kind=1))
  end function create_dtype_obj

  function create_dtype_format(format_str, as_array, use_generic) &
       result(out)
    implicit none
    character(len=*), intent(in) :: format_str
    integer, intent(in) :: as_array
    logical, intent(in) :: use_generic
    type(yggdtype) :: out
    character(len=len_trim(format_str)+1) :: c_format_str
    c_format_str = trim(format_str)//c_null_char
    call fix_format_str(c_format_str)
    out%ptr = create_dtype_format_c(c_format_str, as_array, logical(use_generic, kind=1))
  end function create_dtype_format

  function create_dtype_pyobj(typename, use_generic) result(out)
    implicit none
    character(len=*), intent(in) :: typename
    logical, intent(in) :: use_generic
    type(yggdtype) :: out
    character(len=len_trim(typename)+1) :: c_typename
    c_typename = trim(typename)//c_null_char
    out%ptr = create_dtype_pyobj_c(c_typename, logical(use_generic, kind=1))
  end function create_dtype_pyobj

  function create_dtype_schema(use_generic) result(out)
    implicit none
    logical, intent(in) :: use_generic
    type(yggdtype) :: out
    out%ptr = create_dtype_schema_c(logical(use_generic, kind=1))
  end function create_dtype_schema

  function create_dtype_any(use_generic) result(out)
    implicit none
    logical, intent(in) :: use_generic
    type(yggdtype) :: out
    out%ptr = create_dtype_any_c(logical(use_generic, kind=1))
  end function create_dtype_any

  ! Methods for sending/receiving
  function ygg_send(ygg_q, data, data_len) result (flag)
    implicit none
    type(yggcomm), intent(in) :: ygg_q
    type(c_ptr) :: c_ygg_q
    character(len=*), intent(in) :: data
    character(len=len(data)+1) :: c_data
    integer, intent(in) :: data_len
    integer(kind=c_int) :: c_data_len
    logical :: flag
    integer(kind=c_int) :: c_flag
    c_ygg_q = ygg_q%comm
    c_data = data//c_null_char
    c_data_len = data_len
    c_flag = ygg_send_c(c_ygg_q, c_data, c_data_len)
    if (c_flag.ge.0) then
       flag = .true.
    else
       flag = .false.
    end if
  end function ygg_send
  
  function ygg_recv(ygg_q, data, data_len) result (flag)
    implicit none
    type(yggcomm) :: ygg_q
    type(c_ptr) :: c_ygg_q
    character(len=*) :: data
    character(len=len(data)+1) :: c_data
    integer :: data_len
    integer(kind=c_int) :: c_data_len
    logical :: flag
    integer(kind=c_int) :: c_flag
    c_ygg_q = ygg_q%comm
    c_data = data//c_null_char
    c_data_len = data_len
    c_flag = ygg_recv_c(c_ygg_q, c_data, c_data_len)
    if (c_flag.ge.0) then
       flag = .true.
       data = c_data(:c_flag)
       data_len = c_flag
    else
       flag = .false.
    end if
  end function ygg_recv

  function ygg_send_nolimit(ygg_q, data, data_len) result (flag)
    implicit none
    type(yggcomm), intent(in) :: ygg_q
    type(yggchar_r) :: data
    integer, intent(in) :: data_len
    logical :: flag
    integer(kind=c_size_t) :: len_used
    len_used = data_len
    flag = ygg_send_var(ygg_q, [yggarg(data), yggarg(len_used)])
  end function ygg_send_nolimit
  
  function ygg_recv_nolimit(ygg_q, data, data_len) result (flag)
    implicit none
    type(yggcomm) :: ygg_q
    type(yggchar_r) :: data
    integer :: data_len
    logical :: flag
    integer(kind=c_size_t) :: len_used
    len_used = data_len
    flag = ygg_recv_var_realloc(ygg_q, [yggarg(data), yggarg(len_used)])
    if (flag) then
       data_len = int(len_used)
    end if
  end function ygg_recv_nolimit

  function ygg_send_var_sing(ygg_q, arg) result (flag)
    implicit none
    type(yggcomm), intent(in) :: ygg_q
    type(yggptr) :: arg
    logical :: flag
    flag = ygg_send_var_mult(ygg_q, [arg])
  end function ygg_send_var_sing
  function ygg_send_var_mult(ygg_q, args) result (flag)
    implicit none
    type(yggcomm), intent(in) :: ygg_q
    type(c_ptr) :: c_ygg_q
    type(yggptr) :: args(:)
    type(c_ptr), allocatable, target :: c_args(:)
    integer :: c_nargs
    integer :: i
    logical :: flag, is_format
    integer(kind=c_int) :: c_flag
    is_format = is_comm_format_array_type(ygg_q, args)
    c_ygg_q = ygg_q%comm
    c_nargs = pre_send(args, c_args, is_format)
    c_flag = ygg_send_var_c(c_ygg_q, c_nargs, c_loc(c_args(1)))
    if (c_flag.ge.0) then
       flag = .true.
    else
       flag = .false.
    end if
    call post_send(args, c_args, flag)
  end function ygg_send_var_mult

  function is_next_size_t(args, i, req_array) result(flag)
    implicit none
    type(yggptr) :: args(:)
    integer :: i
    logical, intent(in), optional :: req_array
    logical :: flag
    if (i.ge.size(args)) then
       flag = .false.
    else
       if (present(req_array)) then
          flag = is_size_t(args(i+1), req_array)
       else
          flag = is_size_t(args(i+1))
       end if
    end if
  end function is_next_size_t

  function is_size_t(arg, req_array_in) result(flag)
    type(yggptr), intent(in) :: arg
    logical, optional :: req_array_in
    logical :: req_array
    logical :: flag
    if (present(req_array_in)) then
       req_array = req_array_in
    else
       req_array = .false.
    end if
    if (((arg%type.eq."integer").or.(arg%type.eq."size_t")).and. &
         (arg%nbytes.eq.8)) then
       flag = .true.
       if (req_array.and.(.not.arg%array)) then
          flag = .false.
       else if ((.not.req_array).and.arg%array) then
          flag = .false.
       end if
    else
       flag = .false.
    end if
  end function is_size_t

  function pre_send(args, c_args, is_format) result(c_nargs)
    implicit none
    type(yggptr) :: args(:)
    type(c_ptr), allocatable, target :: c_args(:)
    logical :: is_format
    integer(kind=c_int) :: c_nargs
    integer(kind=c_size_t) :: k
    integer :: i, j
    integer :: nargs
    nargs = size(args)  ! Number of arguments passed
    c_nargs = nargs  ! Number of arguments that C should be aware of
    if (is_format) then
       if (.not.is_size_t(args(1))) then
          nargs = nargs + 1
          c_nargs = c_nargs + 1
       end if
    end if
    do i = 1, size(args)
       allocate(args(i)%len_c)
       allocate(args(i)%prec_c)
       allocate(args(i)%ndim_c)
       allocate(args(i)%shape_c(args(i)%ndim))
       args(i)%len_c = 1
       args(i)%prec_c = 1
       args(i)%ndim_c = 1
       do k = 1, args(i)%ndim
          args(i)%shape_c(k) = args(i)%shape(k)
       end do
       if (args(i)%array) then
          if (args(i)%ndim.gt.1) then
             if (is_next_size_t(args, i).and.is_next_size_t(args, i+1, req_array=.true.)) then
                ! Do nothing, vars already exist
             else if (is_next_size_t(args, i, req_array=.true.)) then
                if (args(i)%alloc) then
                   nargs = nargs + 1  ! For ndim
                   c_nargs = c_nargs + 1
                end if
             else if (args(i)%alloc) then
                nargs = nargs + 2  ! For ndim and shape
                c_nargs = c_nargs + 2
             end if
          else
             if ((.not.is_format).and.(.not.is_next_size_t(args, i))) then
                if (args(i)%alloc) then
                   nargs = nargs + 1  ! For the array size
                   c_nargs = c_nargs + 1
                end if
             end if
          end if
       else if (args(i)%type.eq."character") then
          if (.not.is_next_size_t(args, i)) then
             nargs = nargs + 1  ! For the string size
             c_nargs = c_nargs + 1
          end if
       end if
    end do
    allocate(c_args(nargs))
    j = 1
    if (is_format) then
       if (.not.is_size_t(args(1))) then
          args(1)%len_c = args(1)%len
          args(1)%len_ptr = c_loc(args(1)%len_c)
          c_args(j) = args(1)%len_ptr
          j = j + 1
       end if
    end if
    do i = 1, size(args)
       c_args(j) = args(i)%ptr
       j = j + 1
       if (args(i)%array) then
          if (args(i)%ndim.gt.1) then
             if (is_next_size_t(args, i).and.is_next_size_t(args, i+1, req_array=.true.)) then
                args(i)%ndim_ptr = args(i+1)%ptr
                args(i)%shape_ptr = args(i+2)%ptr
             else if (is_next_size_t(args, i, req_array=.true.)) then
                args(i)%shape_ptr = args(i+1)%ptr
                if (args(i)%alloc) then
                   args(i)%ndim_c = args(i)%ndim
                   args(i)%ndim_ptr = c_loc(args(i)%ndim_c)
                   c_args(j) = args(i)%ndim_ptr
                   j = j + 1
                end if
             else if (args(i)%alloc) then
                args(i)%ndim_c = args(i)%ndim
                args(i)%ndim_ptr = c_loc(args(i)%ndim_c)
                c_args(j) = args(i)%ndim_ptr
                j = j + 1
                args(i)%shape_ptr = c_loc(args(i)%shape_c(1))
                c_args(j) = args(i)%shape_ptr
                j = j + 1
             end if
          else
             if (is_format) then
                args(i)%len_ptr = c_args(1)
             else if (is_next_size_t(args, i)) then
                args(i)%len_ptr = args(i+1)%ptr
             else if (args(i)%alloc) then
                args(i)%len_c = args(i)%len
                args(i)%len_ptr = c_loc(args(i)%len_c)
                c_args(j) = args(i)%len_ptr
                j = j + 1
             end if
          end if
       else if (args(i)%type.eq."character") then
          if (is_next_size_t(args, i)) then
             args(i)%prec_ptr = args(i+1)%ptr
          else
             args(i)%prec_c = args(i)%prec
             args(i)%prec_ptr = c_loc(args(i)%prec_c)
             c_args(j) = args(i)%prec_ptr
             j = j + 1
          end if
       end if
    end do
  end function pre_send

  function pre_recv(args, c_args, is_format) result(c_nargs)
    implicit none
    type(yggptr) :: args(:)
    type(c_ptr), allocatable, target :: c_args(:)
    logical :: is_format
    integer(kind=c_int) :: c_nargs
    integer(kind=c_size_t) :: k
    integer :: i, j
    integer :: nargs
    nargs = size(args)  ! Number of arguments passed
    c_nargs = nargs  ! Number of arguments that C should be aware of
    if (is_format) then
       if (.not.is_size_t(args(1))) then
          nargs = nargs + 1
          c_nargs = c_nargs + 1
       end if
    end if
    do i = 1, size(args)
       allocate(args(i)%len_c)
       allocate(args(i)%prec_c)
       allocate(args(i)%ndim_c)
       allocate(args(i)%shape_c(args(i)%ndim))
       args(i)%len_c = 1
       args(i)%prec_c = 1
       args(i)%ndim_c = 1
       do k = 1, args(i)%ndim
          args(i)%shape_c(k) = args(i)%shape(k)
       end do
       if (args(i)%array) then
          if (args(i)%ndim.gt.1) then

             if (is_next_size_t(args, i).and.is_next_size_t(args, i+1, req_array=.true.)) then
                ! Do nothing, vars already exist
             else if (is_next_size_t(args, i, req_array=.true.)) then
                nargs = nargs + 1  ! For ndim
                if (args(i)%alloc) then
                   c_nargs = c_nargs + 1
                end if
             else
                nargs = nargs + 2  ! For ndim and shape
                if (args(i)%alloc) then
                   c_nargs = c_nargs + 2
                end if
             end if
          else
             if ((.not.is_format).and.(.not.is_next_size_t(args, i))) then
                nargs = nargs + 1  ! For the array size
                if (args(i)%alloc) then
                   c_nargs = c_nargs + 1
                end if
             end if
          end if
          if (args(i)%type.eq."character") then
             nargs = nargs + 1  ! For the string length
          end if
       else if (args(i)%type.eq."character") then
          if (.not.is_next_size_t(args, i)) then
             nargs = nargs + 1  ! For the string size
             c_nargs = c_nargs + 1
          end if
       end if
    end do
    allocate(c_args(nargs))
    j = 1
    if (is_format) then
       if (.not.is_size_t(args(1))) then
          args(1)%len_c = args(1)%len
          args(1)%len_ptr = c_loc(args(1)%len_c)
          c_args(j) = args(1)%len_ptr
          j = j + 1
       end if
    end if
    do i = 1, size(args)
       c_args(j) = args(i)%ptr
       j = j + 1
       if (args(i)%array) then
          ! TODO: handle case where shape is explicit and ensure
          ! that length of shape variable is not appended
          if (args(i)%ndim.gt.1) then
             if (is_next_size_t(args, i).and.is_next_size_t(args, i+1, req_array=.true.)) then
                args(i)%ndim_ptr = args(i+1)%ptr
                args(i)%shape_ptr = args(i+2)%ptr
             else if (is_next_size_t(args, i, req_array=.true.)) then
                args(i)%shape_ptr = args(i+1)%ptr
                args(i)%ndim_c = args(i)%ndim
                args(i)%ndim_ptr = c_loc(args(i)%ndim_c)
                c_args(j) = args(i)%ndim_ptr
                j = j + 1
             else
                args(i)%ndim_c = args(i)%ndim
                args(i)%ndim_ptr = c_loc(args(i)%ndim_c)
                c_args(j) = args(i)%ndim_ptr
                j = j + 1
                args(i)%shape_ptr = c_loc(args(i)%shape_c(1))
                c_args(j) = args(i)%shape_ptr
                j = j + 1
             end if
          else
             if (is_format) then
                args(i)%len_ptr = c_args(1)
             else if (is_next_size_t(args, i)) then
                args(i)%len_ptr = args(i+1)%ptr
             else
                args(i)%len_c = args(i)%len
                args(i)%len_ptr = c_loc(args(i)%len_c)
                c_args(j) = args(i)%len_ptr
                j = j + 1
             end if
          end if
          if (args(i)%type.eq."character") then
             args(i)%prec_c = args(i)%prec
             args(i)%prec_ptr = c_loc(args(i)%prec_c)
             c_args(j) = args(i)%prec_ptr
             j = j + 1
          end if
       else if (args(i)%type.eq."character") then
          if (is_next_size_t(args, i)) then
             args(i)%prec_ptr = args(i+1)%ptr
          else
             args(i)%prec_c = args(i)%prec
             args(i)%prec_ptr = c_loc(args(i)%prec_c)
             c_args(j) = args(i)%prec_ptr
             j = j + 1
          end if
       end if
    end do
  end function pre_recv

  subroutine post_recv(args, c_args, flag, realloc, is_format)
    implicit none
    type(yggptr) :: args(:)
    type(c_ptr), allocatable, target :: c_args(:)
    logical :: flag
    integer :: i, j
    logical :: realloc, is_format
    call ygglog_debug("post_recv: begin")
    if (flag) then
       j = 1
       if (is_format) then
          if (.not.is_size_t(args(1))) then
             j = j + 1
          end if
       end if
       do i = 1, size(args)
          args(i)%ptr = c_args(j)
          flag = yggptr_c2f(args(i), realloc)
          if (.not.flag) then
             call ygglog_error("Error recovering fortran pointer for variable.")
             exit
          end if
          j = j + 1
          if (args(i)%array) then
             if (args(i)%ndim.gt.1) then
                if (is_next_size_t(args, i).and.is_next_size_t(args, i+1, req_array=.true.)) then
                   ! Do nothing, process variables as normal
                else if (is_next_size_t(args, i, req_array=.true.)) then
                   j = j + 1
                else
                   j = j + 2
                end if
             else
                if ((.not.is_format).and.(.not.is_next_size_t(args, i))) then
                   j = j + 1
                end if
             end if
             if (args(i)%type.eq."character") then
                j = j + 1
             end if
          else if (args(i)%type.eq."character") then
             if (.not.is_next_size_t(args, i)) then
                j = j + 1
             end if
          end if
       end do
    end if
    if (flag) then
       do i = 1, size(args)
          deallocate(args(i)%len_c)
          deallocate(args(i)%prec_c)
          deallocate(args(i)%ndim_c)
          deallocate(args(i)%shape_c)
       end do
    end if
    if (allocated(c_args)) then
       deallocate(c_args)
    end if
    call ygglog_debug("post_recv: end")
  end subroutine post_recv

  subroutine post_send(args, c_args, flag)
    implicit none
    type(yggptr) :: args(:)
    type(c_ptr), allocatable, target :: c_args(:)
    logical :: flag
    integer :: i
    call ygglog_debug("post_send: begin")
    if (flag) then
       do i = 1, size(args)
          deallocate(args(i)%len_c)
          deallocate(args(i)%prec_c)
          deallocate(args(i)%ndim_c)
          deallocate(args(i)%shape_c)
       end do
    end if
    if (allocated(c_args)) then
       deallocate(c_args)
    end if
    call ygglog_debug("post_send: end")
  end subroutine post_send

  function ygg_rpc_call_1v1(ygg_q, oarg, iarg) result (flag)
    implicit none
    type(yggcomm) :: ygg_q
    type(yggptr) :: oarg
    type(yggptr) :: iarg
    logical :: flag
    flag = ygg_rpc_call_mult(ygg_q, [oarg], [iarg])
  end function ygg_rpc_call_1v1
  function ygg_rpc_call_1vm(ygg_q, oarg, iargs) result (flag)
    implicit none
    type(yggcomm) :: ygg_q
    type(yggptr) :: oarg
    type(yggptr) :: iargs(:)
    logical :: flag
    flag = ygg_rpc_call_mult(ygg_q, [oarg], iargs)
  end function ygg_rpc_call_1vm
  function ygg_rpc_call_mv1(ygg_q, oargs, iarg) result (flag)
    implicit none
    type(yggcomm) :: ygg_q
    type(yggptr) :: oargs(:)
    type(yggptr) :: iarg
    logical :: flag
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
    type(c_ptr), allocatable, target :: c_oargs(:)
    integer :: c_nargs
    logical :: flag
    integer :: i
    integer(kind=c_int) :: c_flag
    logical :: iis_format, ois_format
    ois_format = is_comm_format_array_type(ygg_q, oargs)
    iis_format = is_comm_format_array_type(ygg_q, iargs)
    c_ygg_q = ygg_q%comm
    c_nargs = 0
    c_nargs = c_nargs + pre_send(oargs, c_oargs, ois_format)
    c_nargs = c_nargs + pre_recv(iargs, c_iargs, iis_format)
    allocate(c_args(size(c_oargs) + size(c_iargs)))
    do i = 1, size(c_oargs)
       c_args(i) = c_oargs(i)
    end do
    do i = 1, size(c_iargs)
       c_args(i + size(c_oargs)) = c_iargs(i)
    end do
    c_flag = ygg_rpc_call_c(c_ygg_q, c_nargs, c_loc(c_args(1)))
    if (c_flag.ge.0) then
       flag = .true.
    else
       flag = .false.
    end if
    do i = 1, size(c_iargs)
       c_iargs(i) = c_args(i + size(c_oargs))
    end do
    call post_send(oargs, c_oargs, flag)
    call post_recv(iargs, c_iargs, flag, .false., iis_format)
    if (allocated(c_args)) then
       deallocate(c_args)
    end if
  end function ygg_rpc_call_mult
  
  function ygg_rpc_call_realloc_1v1(ygg_q, oarg, iarg) result (flag)
    implicit none
    type(yggcomm) :: ygg_q
    type(yggptr) :: oarg
    type(yggptr) :: iarg
    logical :: flag
    flag = ygg_rpc_call_realloc_mult(ygg_q, [oarg], [iarg])
  end function ygg_rpc_call_realloc_1v1
  function ygg_rpc_call_realloc_1vm(ygg_q, oarg, iargs) result (flag)
    implicit none
    type(yggcomm) :: ygg_q
    type(yggptr) :: oarg
    type(yggptr) :: iargs(:)
    logical :: flag
    flag = ygg_rpc_call_realloc_mult(ygg_q, [oarg], iargs)
  end function ygg_rpc_call_realloc_1vm
  function ygg_rpc_call_realloc_mv1(ygg_q, oargs, iarg) result (flag)
    implicit none
    type(yggcomm) :: ygg_q
    type(yggptr) :: oargs(:)
    type(yggptr) :: iarg
    logical :: flag
    flag = ygg_rpc_call_realloc_mult(ygg_q, oargs, [iarg])
  end function ygg_rpc_call_realloc_mv1
  function ygg_rpc_call_realloc_mult(ygg_q, oargs, iargs) result (flag)
    implicit none
    type(yggcomm) :: ygg_q
    type(c_ptr) :: c_ygg_q
    type(yggptr) :: oargs(:)
    type(yggptr) :: iargs(:)
    type(c_ptr), allocatable, target :: c_args(:)
    type(c_ptr), allocatable, target :: c_oargs(:)
    type(c_ptr), allocatable, target :: c_iargs(:)
    integer :: c_nargs
    logical :: flag, iis_format, ois_format
    integer(kind=c_int) :: c_flag
    integer :: i
    c_ygg_q = ygg_q%comm
    ois_format = is_comm_format_array_type(ygg_q, oargs)
    iis_format = is_comm_format_array_type(ygg_q, iargs)
    flag = .true.
    do i = 1, size(iargs)
       if ((iargs(i)%array.or.(iargs(i)%type.eq."character")).and. &
            (.not.(iargs(i)%alloc))) then
          call ygglog_error("Provided array/string is not allocatable.")
          flag = .false.
       end if
    end do
    if (flag) then
       c_nargs = 0
       c_nargs = c_nargs + pre_send(oargs, c_oargs, ois_format)
       c_nargs = c_nargs + pre_recv(iargs, c_iargs, iis_format)
       allocate(c_args(size(c_oargs) + size(c_iargs)))
       do i = 1, size(c_oargs)
          c_args(i) = c_oargs(i)
       end do
       do i = 1, size(c_iargs)
          c_args(i + size(c_oargs)) = c_iargs(i)
       end do
       c_flag = ygg_rpc_call_realloc_c(c_ygg_q, c_nargs, c_loc(c_args(1)))
       if (c_flag.ge.0) then
          flag = .true.
       else
          flag = .false.
       end if
       do i = 1, size(c_iargs)
          c_iargs(i) = c_args(i + size(c_oargs))
       end do
    end if
    call post_send(oargs, c_oargs, flag)
    call post_recv(iargs, c_iargs, flag, .true., iis_format)
    if (allocated(c_args)) then
       deallocate(c_args)
    end if
  end function ygg_rpc_call_realloc_mult
  
  function ygg_recv_var_sing(ygg_q, arg) result (flag)
    implicit none
    type(yggcomm) :: ygg_q
    type(yggptr) :: arg
    logical :: flag
    flag = ygg_recv_var_mult(ygg_q, [arg])
  end function ygg_recv_var_sing
  function ygg_recv_var_mult(ygg_q, args) result (flag)
    implicit none
    type(yggcomm) :: ygg_q
    type(c_ptr) :: c_ygg_q
    type(yggptr) :: args(:)
    type(c_ptr), allocatable, target :: c_args(:)
    integer :: c_nargs
    logical :: flag, is_format
    integer(kind=c_int) :: c_flag
    is_format = is_comm_format_array_type(ygg_q, args)
    c_ygg_q = ygg_q%comm
    c_nargs = pre_recv(args, c_args, is_format)
    c_flag = ygg_recv_var_c(c_ygg_q, c_nargs, c_loc(c_args(1)))
    if (c_flag.ge.0) then
       flag = .true.
    else
       flag = .false.
    end if
    call post_recv(args, c_args, flag, .false., is_format)
  end function ygg_recv_var_mult

  function ygg_recv_var_realloc_sing(ygg_q, arg) result (flag)
    implicit none
    type(yggcomm) :: ygg_q
    type(yggptr) :: arg
    logical :: flag
    flag = ygg_recv_var_realloc_mult(ygg_q, [arg])
  end function ygg_recv_var_realloc_sing
  function ygg_recv_var_realloc_mult(ygg_q, args) result (flag)
    implicit none
    type(yggcomm) :: ygg_q
    type(c_ptr) :: c_ygg_q
    type(yggptr), target :: args(:)
    type(c_ptr), allocatable, target :: c_args(:)
    integer :: c_nargs
    logical :: flag, is_format
    integer :: i
    integer(kind=c_int) :: c_flag
    call ygglog_debug("ygg_recv_var_realloc: begin")
    is_format = is_comm_format_array_type(ygg_q, args)
    c_ygg_q = ygg_q%comm
    flag = .true.
    do i = 1, size(args)
       if ((args(i)%array.or.(args(i)%type.eq."character")).and. &
            (.not.(args(i)%alloc))) then
          call ygglog_error("Provided array/string is not allocatable.")
          flag = .false.
       end if
    end do
    if (flag) then
       c_nargs = pre_recv(args, c_args, is_format)
       c_flag = ygg_recv_var_realloc_c(c_ygg_q, c_nargs, c_loc(c_args(1)))
       if (c_flag.ge.0) then
          flag = .true.
       else
          flag = .false.
       end if
    end if
    call post_recv(args, c_args, flag, .true., is_format)
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
  function create_generic(type_class, data) result(out)
    implicit none
    type(yggdtype) :: type_class
    type(yggptr) :: data
    integer(kind=c_size_t) :: nbytes
    type(c_ptr) :: c_type_class
    type(c_ptr) :: c_data
    type(ygggeneric) :: out
    c_type_class = type_class%ptr
    c_data = data%ptr
    nbytes = data%nbytes
    out = create_generic_c(c_type_class, c_data, nbytes)
  end function create_generic
  subroutine free_generic(x)
    implicit none
    type(ygggeneric) :: x
    integer(kind=c_int) :: out
    out = free_generic_c(x)
    if (out.ne.0) then
       stop "Error freeing generic object."
    end if
  end subroutine free_generic
  function is_generic_init(x) result(out)
    implicit none
    type(ygggeneric), value, intent(in) :: x
    logical :: out
    integer(kind=c_int) :: c_out
    out = .false.
    c_out = is_generic_init_c(x)
    if (c_out.ne.0) then
       out = .true.
    end if
  end function is_generic_init
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

  ! Python interface
  function init_python() result(out)
    implicit none
    type(yggpython) :: out
    out = init_python_c()
  end function init_python
  subroutine free_python(x)
    implicit none
    type(yggpython), target :: x
    type(yggpython), pointer :: xp
    type(c_ptr) :: c_x
    xp => x
    c_x = c_loc(xp)
    call free_python_c(c_x)
    nullify(xp)
  end subroutine free_python
  function copy_python(x) result(out)
    implicit none
    type(yggpython) :: x
    type(yggpython) :: out
    out = copy_python_c(x)
  end function copy_python
  subroutine display_python(x)
    implicit none
    type(yggpython) :: x
    call display_python_c(x)
  end subroutine display_python
  
end module fygg
