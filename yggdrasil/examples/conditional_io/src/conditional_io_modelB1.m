function [in_val, out_val] = conditional_io_modelB1(in_val)
  % Only valid if in_val <= 2
  out_val = in_val^2;
  disp(sprintf('modelB_function1(%f) = %f', separateUnits(in_val), separateUnits(out_val)));
end
