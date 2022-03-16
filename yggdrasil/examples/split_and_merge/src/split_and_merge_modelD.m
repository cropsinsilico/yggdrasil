function [in_val1, in_val2, out_val] = split_and_merge_modelD(in_val1, in_val2)
  out_val = in_val1 + in_val2;
  disp(sprintf('modelD_function(%f, %f) = %f', in_val1, in_val2, out_val));
end
