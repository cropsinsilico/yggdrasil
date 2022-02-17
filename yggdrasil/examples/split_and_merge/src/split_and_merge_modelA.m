function [out_val1, out_val2] = split_and_merge_modelA(in_val)
  out_val1 = 2 * in_val;
  out_val2 = 3 * in_val;
  disp(sprintf('modelA_function(%f) = (%f, %f)', in_val, out_val1, out_val2));
end
