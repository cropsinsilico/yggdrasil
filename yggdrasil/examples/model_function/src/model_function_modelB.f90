module example_module
contains
  function model_function(inputB, outputB) result(out)
    character(len=*), intent(in) :: inputB
    character(len=:), pointer :: outputB
    logical :: out
    out = .true.
    allocate(character(len=len(inputB)) :: outputB)
    outputB = inputB
    write(*, '("Model B: ",A," (length = ",I3,")")') outputB, len(outputB)
  end function model_function
end module example_module
