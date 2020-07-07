function model_function(inputA, outputA) result(out)
  character(len=*), intent(in) :: inputA
  character(len=:), pointer :: outputA
  logical :: out
  out = .true.
  allocate(character(len=len(inputA)) :: outputA)
  outputA = inputA
  write(*, '("Model A: ",A," (length = ",I3,")")') outputA, len(outputA)
end function model_function
