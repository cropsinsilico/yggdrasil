function [in_val, out_val] = conditional_io_modelB2(in_val)
  % Only valid if in_val > 2
  out_val = 2 * in_val^2;
  disp(sprintf('modelB_function2(%f) = %f', separateUnits(in_val), separateUnits(out_val)));
end
