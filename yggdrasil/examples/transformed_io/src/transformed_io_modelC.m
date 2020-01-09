function [in_val, out_val] = transformed_io_modelC(in_val)
  out_val = 2 * in_val;
  disp(sprintf('modelC_function(%f) = %f', in_val, out_val));
end
