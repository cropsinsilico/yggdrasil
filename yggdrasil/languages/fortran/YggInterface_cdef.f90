  interface
     ! function ygg_output_type_c(name, datatype) result(channel) &
     !      bind(c, name="yggoutputtype")
     !   use, intrinsic :: iso_c_binding, only: c_ptr, c_char
     !   implicit none
     !   character(kind=c_char), intent(in) :: name(*)
     !   type(c_ptr), intent(in) :: datatype
     !   type(c_ptr) :: channel
     ! end function ygg_output_type_c
  
     ! function ygg_input_type_c(name, datatype) result(channel) &
     !      bind(c, name="ygginputtype")
     !   use, intrinsic :: iso_c_binding, only: c_ptr, c_char
     !   implicit none
     !   character(kind=c_char), intent(in) :: name(*)
     !   type(c_ptr), intent(in) :: datatype
     !   type(c_ptr) :: channel
     ! end function ygg_input_type_c
  
     ! function ygg_output_fmt_c(name, fmt_string) result(channel) &
     !      bind(c, name="yggoutputfmt")
     !   use, intrinsic :: iso_c_binding, only: c_ptr, c_char
     !   implicit none
     !   character(kind=c_char), intent(in) :: name(*)
     !   character(kind=c_char), intent(in) :: fmt_string(*)
     !   type(c_ptr) :: channel
     ! end function ygg_output_fmt_c
  
     ! function ygg_input_fmt_c(name, fmt_string) result(channel) &
     !      bind(c, name="ygginputfmt")
     !   use, intrinsic :: iso_c_binding, only: c_ptr, c_char
     !   implicit none
     !   character(kind=c_char), intent(in) :: name(*)
     !   character(kind=c_char), intent(in) :: fmt_string(*)
     !   type(c_ptr) :: channel
     ! end function ygg_input_fmt_c
  
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
     
  end interface
