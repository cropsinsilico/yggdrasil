function out = model_function(a, b, c)
  out = zeros(1, 3);
  for i = 1:3
    if a
      out{i} = b * (i ^ c('c1'));
    else
    end;
  end;
end
