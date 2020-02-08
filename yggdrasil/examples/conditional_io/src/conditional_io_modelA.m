function out_val = conditional_io_modelA(in_val)
  out_val = in_val;
  disp(sprintf('modelA_function(%f) = %f', separateUnits(in_val), separateUnits(out_val)));
end
