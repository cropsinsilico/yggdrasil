function modelD_function(in_val1, in_val2, in_val1_copy, in_val2_copy, out_val) result(out)
  real(kind=8), intent(in) :: in_val1, in_val2
  real(kind=8), intent(out) :: in_val1_copy, in_val2_copy, out_val
  logical :: out
  out = .true.
  in_val1_copy = in_val1
  in_val2_copy = in_val2
  out_val = in_val1 + in_val2
  write(*, '("modelD_function(",F10.5,", ",F10.5,") = (",F10.5,")")') in_val1, in_val2, out_val
end function modelD_function
