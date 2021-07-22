function y = model_function_modelB(x)
  if isa(x, 'sym')
    y = x + 2.0 * str2symunit('g');
    fprintf('Model B: %f -> %f\n', separateUnits(simplify(x)), separateUnits(simplify(y)));
  else;
    y = x + 2.0;
    fprintf('Model B: %f -> %f\n', x, y);
  end;
end
