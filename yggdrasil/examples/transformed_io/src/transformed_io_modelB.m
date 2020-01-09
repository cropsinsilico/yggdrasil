function [in_val, out_val] = transformed_io_modelB(in_val)
  out_val = 3 * in_val;
  disp(sprintf('modelB_function(%f) = %f', in_val, out_val));
end
