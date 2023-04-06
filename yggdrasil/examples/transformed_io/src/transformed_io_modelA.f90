function modelA_function(in_val) result(out_val)
  real(kind=4), intent(in) :: in_val
  real(kind=4) :: out_val
  out_val = in_val
  write(*, '("modelA_function(",F10.5,") = ",F10.5)') in_val, out_val
end function modelA_function
