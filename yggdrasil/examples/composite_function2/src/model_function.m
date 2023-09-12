function d, e, f = model_function(a, b, c)
  d = (!a);
  e = c('c1');
  f = zeros(1, 3);
  for i = 1:3
    if a
      f{i} = b * (i ^ c('c1'));
    else
    end;
  end;
end
