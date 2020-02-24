  interface
     ! Utilities
     subroutine c_free(x) bind(c, name="ygg_c_free")
       use, intrinsic :: iso_c_binding, only: c_ptr
       implicit none
       type(c_ptr) :: x
     end subroutine c_free

     subroutine ygglog_info_c(fmt) bind(c, name="ygg_log_info_f")
       use, intrinsic :: iso_c_binding, only: c_char
       implicit none
       character(kind=c_char), dimension(*), intent(in) :: fmt
     end subroutine ygglog_info_c
     subroutine ygglog_debug_c(fmt) bind(c, name="ygg_log_debug_f")
       use, intrinsic :: iso_c_binding, only: c_char
       implicit none
       character(kind=c_char), dimension(*), intent(in) :: fmt
     end subroutine ygglog_debug_c
     subroutine ygglog_error_c(fmt) bind(c, name="ygg_log_error_f")
       use, intrinsic :: iso_c_binding, only: c_char
       implicit none
       character(kind=c_char), dimension(*), intent(in) :: fmt
     end subroutine ygglog_error_c
  
     ! Methods for initializing channels
     function ygg_output_c(name) result(channel) &
          bind(c, name="ygg_output_f")
       use, intrinsic :: iso_c_binding, only: c_ptr, c_char
       implicit none
       character(kind=c_char), dimension(*), intent(in) :: name
       type(c_ptr) :: channel
     end function ygg_output_c
  
     function ygg_input_c(name) result(channel) &
          bind(c, name="ygg_input_f")
       use, intrinsic :: iso_c_binding, only: c_ptr, c_char
       implicit none
       character(kind=c_char), dimension(*), intent(in) :: name
       type(c_ptr) :: channel
     end function ygg_input_c
  
     function ygg_ascii_file_output_c(name) result(channel) &
          bind(c, name="yggAsciiFileOutput_f")
       use, intrinsic :: iso_c_binding, only: c_ptr, c_char
       implicit none
       character(kind=c_char), dimension(*), intent(in) :: name
       type(c_ptr) :: channel
     end function ygg_ascii_file_output_c
  
     function ygg_ascii_file_input_c(name) result(channel) &
          bind(c, name="yggAsciiFileInput_f")
       use, intrinsic :: iso_c_binding, only: c_ptr, c_char
       implicit none
       character(kind=c_char), dimension(*), intent(in) :: name
       type(c_ptr) :: channel
     end function ygg_ascii_file_input_c
  
     function ygg_ascii_table_output_c(name, format_str) &
          result(channel) bind(c, name="yggAsciiTableOutput_f")
       use, intrinsic :: iso_c_binding, only: c_ptr, c_char
       implicit none
       character(kind=c_char), dimension(*), intent(in) :: name
       character(kind=c_char), dimension(*), intent(in) :: format_str
       type(c_ptr) :: channel
     end function ygg_ascii_table_output_c
  
     function ygg_ascii_table_input_c(name) result(channel) &
          bind(c, name="yggAsciiTableInput_f")
       use, intrinsic :: iso_c_binding, only: c_ptr, c_char
       implicit none
       character(kind=c_char), dimension(*), intent(in) :: name
       type(c_ptr) :: channel
     end function ygg_ascii_table_input_c
  
     function ygg_ascii_array_output_c(name, format_str) &
          result(channel) bind(c, name="yggAsciiArrayOutput_f")
       use, intrinsic :: iso_c_binding, only: c_ptr, c_char
       implicit none
       character(kind=c_char), dimension(*), intent(in) :: name
       character(kind=c_char), dimension(*), intent(in) :: format_str
       type(c_ptr) :: channel
     end function ygg_ascii_array_output_c
  
     function ygg_ascii_array_input_c(name) result(channel) &
          bind(c, name="yggAsciiArrayInput_f")
       use, intrinsic :: iso_c_binding, only: c_ptr, c_char
       implicit none
       character(kind=c_char), dimension(*), intent(in) :: name
       type(c_ptr) :: channel
     end function ygg_ascii_array_input_c
  
     function ygg_ply_output_c(name) result(channel) &
          bind(c, name="yggPlyOutput_f")
       use, intrinsic :: iso_c_binding, only: c_ptr, c_char
       implicit none
       character(kind=c_char), dimension(*), intent(in) :: name
       type(c_ptr) :: channel
     end function ygg_ply_output_c
  
     function ygg_ply_input_c(name) result(channel) &
          bind(c, name="yggPlyInput_f")
       use, intrinsic :: iso_c_binding, only: c_ptr, c_char
       implicit none
       character(kind=c_char), dimension(*), intent(in) :: name
       type(c_ptr) :: channel
     end function ygg_ply_input_c
  
     function ygg_obj_output_c(name) result(channel) &
          bind(c, name="yggObjOutput_f")
       use, intrinsic :: iso_c_binding, only: c_ptr, c_char
       implicit none
       character(kind=c_char), dimension(*), intent(in) :: name
       type(c_ptr) :: channel
     end function ygg_obj_output_c
  
     function ygg_obj_input_c(name) result(channel) &
          bind(c, name="yggObjInput_f")
       use, intrinsic :: iso_c_binding, only: c_ptr, c_char
       implicit none
       character(kind=c_char), dimension(*), intent(in) :: name
       type(c_ptr) :: channel
     end function ygg_obj_input_c
  
     ! Methods for sending/receiving
     function ygg_send_c(ygg_q, data, data_len) result (flag) &
          bind(c, name="ygg_send_f")
       use, intrinsic :: iso_c_binding, only: c_ptr, c_char, &
            c_int
       implicit none
       type(c_ptr), value, intent(in) :: ygg_q
       character(kind=c_char), dimension(*), intent(in) :: data
       integer(kind=c_int), value, intent(in) :: data_len
       integer(kind=c_int) :: flag
     end function ygg_send_c
  
     function ygg_recv_c(ygg_q, data, data_len) result (flag) &
          bind(c, name="ygg_recv_f")
       use, intrinsic :: iso_c_binding, only: c_ptr, c_char, &
            c_int
       implicit none
       type(c_ptr), value :: ygg_q
       character(kind=c_char), dimension(*) :: data
       integer(kind=c_int), value, intent(in) :: data_len
       integer(kind=c_int) :: flag
     end function ygg_recv_c

     function ygg_send_var_c(ygg_q, nargs, args) result (flag) &
          bind(c, name="ygg_send_var_f")
       use, intrinsic :: iso_c_binding, only: c_ptr, c_int
       implicit none
       type(c_ptr), value, intent(in) :: ygg_q
       integer(kind=c_int), value :: nargs
       type(c_ptr), value :: args
       integer(kind=c_int) :: flag
     end function ygg_send_var_c

     function ygg_recv_var_c(ygg_q, nargs, args) result (flag) &
          bind(c, name="ygg_recv_var_f")
       use, intrinsic :: iso_c_binding, only: c_ptr, c_int
       implicit none
       type(c_ptr), value :: ygg_q
       integer(kind=c_int), value :: nargs
       type(c_ptr), value :: args
       integer(kind=c_int) :: flag
     end function ygg_recv_var_c

     function ygg_recv_var_realloc_c(ygg_q, nargs, args) &
          result (flag) bind(c, name="ygg_recv_var_realloc_f")
       use, intrinsic :: iso_c_binding, only: c_ptr, c_int
       implicit none
       type(c_ptr), value :: ygg_q
       integer(kind=c_int), value :: nargs
       type(c_ptr), value :: args
       integer(kind=c_int) :: flag
     end function ygg_recv_var_realloc_c
     
     ! Ply interface
     function init_ply_c() result(out) bind(c, name="init_ply_f")
       import :: yggply
       implicit none
       type(yggply) :: out
     end function init_ply_c
     subroutine free_ply_c(p) bind(c, name="free_ply_f")
       use, intrinsic :: iso_c_binding, only: c_ptr
       implicit none
       type(c_ptr), value :: p
     end subroutine free_ply_c
     subroutine display_ply_indent_c(p, indent) bind(c, name="display_ply_indent_f")
       use, intrinsic :: iso_c_binding, only: c_char
       import :: yggply
       implicit none
       type(yggply), value, intent(in) :: p
       character(kind=c_char), dimension(*), intent(in) :: indent
     end subroutine display_ply_indent_c
     subroutine display_ply_c(p) bind(c, name="display_ply_f")
       import :: yggply
       implicit none
       type(yggply), value, intent(in) :: p
     end subroutine display_ply_c

     ! Obj interface
     function init_obj_c() result(out) bind(c, name="init_obj_f")
       import :: yggobj
       implicit none
       type(yggobj) :: out
     end function init_obj_c
     subroutine free_obj_c(p) bind(c, name="free_obj_f")
       use, intrinsic :: iso_c_binding, only: c_ptr
       implicit none
       type(c_ptr), value :: p
     end subroutine free_obj_c
     subroutine display_obj_indent_c(p, indent) bind(c, name="display_obj_indent_f")
       use, intrinsic :: iso_c_binding, only: c_char
       import :: yggobj
       implicit none
       type(yggobj), value, intent(in) :: p
       character(kind=c_char), dimension(*), intent(in) :: indent
     end subroutine display_obj_indent_c
     subroutine display_obj_c(p) bind(c, name="display_obj_f")
       import :: yggobj
       implicit none
       type(yggobj), value, intent(in) :: p
     end subroutine display_obj_c

  end interface
