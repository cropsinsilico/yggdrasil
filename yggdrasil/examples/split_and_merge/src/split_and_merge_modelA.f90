function modelA_function(in_val, out_val1, out_val2) result(out)
  real(kind=8), intent(in) :: in_val
  real(kind=8), intent(out) :: out_val1, out_val2
  logical :: out
  out = .true.
  out_val1 = 2 * in_val
  out_val2 = 3 * in_val
  write(*, '("modelA_function(",F10.5,") = (",F10.5,", ",F10.5,")")') in_val, out_val1, out_val2
end function modelA_function
