function y = model_function_modelA(x)
  if isa(x, 'sym')
    y = x + 1.0 * str2symunit('g');
    fprintf('Model A: %f -> %f\n', separateUnits(simplify(x)), separateUnits(simplify(y)));
  else;
    y = x + 1.0;
    fprintf('Model A: %f -> %f\n', x, y);
  end;
end
