function x_ml = python2matlab(x_py)
  if isa(x_py, 'py.float')
    x_ml = float(x_py);
  elseif isa(x_py, 'py.double')
    x_ml = double(x_py);
  elseif isa(x_py, 'py.int')
    x_ml = int64(x_py);
  elseif isa(x_py, 'py.bytes')
    x_ml = char(x_py.decode('utf-8'));
  elseif isa(x_py, 'py.string')
    x_ml = char(x_py);
  elseif isa(x_py, 'py.str')
    x_ml = char(x_py);
  elseif isa(x_py, 'py.bool')
    x_ml = logical(x_py);
  elseif isa(x_py, 'py.dict')
    % x_ml = struct(x_py);
    dict_keys = python2matlab(py.list(keys(x_py)));
    dict_vals = python2matlab(py.list(values(x_py)));
    x_ml = containers.Map(dict_keys, dict_vals);
  elseif (isa(x_py, 'py.list') || isa(x_py, 'py.tuple') || isa(x_py, 'py.set'))
    x_ml = cell(x_py);
    [nr, nc] = size(x_ml);
    for i = 1:nr
      for j = 1:nc
	x_ml{i, j} = python2matlab(x_ml{i, j});
      end;
    end;
  elseif isa(x_py, 'py.numpy.ndarray')
    ndim = x_py.ndim;
    char_code = char(x_py.dtype.kind);
    is_struct = false;
    if isa(x_py.dtype.names, 'py.tuple')
      is_struct = true;
      [nr, nc] = x_py.dtype.names.size;
      if (nr * nc) > 1
	ndim = ndim + 1;
      end;
    end;
    x_ml = python2matlab(x_py.tolist());
    if ndim == 2
      x_ml = transpose(x_ml);
      x_ml = vertcat(x_ml{:});
    elseif ndim > 2
      disp('Conversion of numpy arrays with ndim > 2 uses nested cell arrays.');
    end;
    % if ~is_struct
    if ismember(char_code, ['f', 'i'])
      x_ml = cell2mat(x_ml);
      % x_ml = py.array.array(char_code, x_py.tolist());
      % if char_code == 'f'
      %   x_ml = double(x_ml);
      % elseif char_code == 'i'
      %   x_ml = int64(x_ml);
      % else
      %   fprintf('Could not find Matlab type for code %s\n', char_code);
      % end;
    end;
  elseif (isa(x_py, 'numeric') || isa(x_py, 'logical'))
    x_ml = x_py;
  else
    disp('Could not convert python type to matlab type.');
    disp(x_py);
    disp(class(x_py));
    x_ml = x_py;
  end;
end
