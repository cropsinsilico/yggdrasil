% =============================================================================
%> @brief A wrapper for conversion from Python datatypes to Matlab datatypes.
%>
%> This function takes a Python object as input and converts it into an
%> equivalent Matlab object.
%>
%> @param x_py Python object that should be converted.
%>
%> @return x_ml Matlab version of x_py.
% =============================================================================
function x_ml = python2matlab(x_py)
  [version, executable, isloaded] = pyversion;
  if isa(x_py, 'py.None')
    x_ml = NaN;
  elseif isa(x_py, 'py.float')
    x_ml = single(double(x_py));
  elseif isa(x_py, 'py.double')
    x_ml = double(x_py);
  elseif isa(x_py, 'py.int')
    x_ml = int64(x_py);
  elseif isa(x_py, 'py.numpy.int64')
    x_ml = int64(py.int(x_py));
  elseif isa(x_py, 'py.numpy.int32')
    x_ml = int32(int64(py.int(x_py)));
  elseif isa(x_py, 'py.numpy.uint8')
    x_ml = uint8(python2matlab(py.int(x_py)));
  elseif isa(x_py, 'py.numpy.uint32')
    x_ml = uint32(python2matlab(py.int(x_py)));
  elseif isa(x_py, 'py.numpy.uint64')
    x_ml = uint64(python2matlab(py.int(x_py)));
  elseif isa(x_py, 'py.numpy.float64')
    x_ml = python2matlab(py.double(x_py));
  elseif isa(x_py, 'py.numpy.float32')
    x_ml = python2matlab(py.float(x_py));
  elseif isa(x_py, 'py.bytes')
    x_ml = string(char(x_py.decode('utf-8')));
  elseif isa(x_py, 'py.unicode')
    x_ml = char(x_py);
  elseif isa(x_py, 'py.string')
    x_ml = char(x_py);
  elseif isa(x_py, 'py.str')
    if version == '2.7';
      x_ml = string(char(x_py.decode('utf-8')));
    else;
      x_ml = char(x_py);
    end;
  elseif isa(x_py, 'py.bool')
    x_ml = logical(x_py);
  elseif isa(x_py, ...
             ['py.yggdrasil.metaschema.datatypes' ...
              '.PlyMetaschemaType.PlyDict']);
    x_ml = python2matlab(x_py.as_dict());
  elseif isa(x_py, ...
             ['py.yggdrasil.metaschema.datatypes' ...
              '.ObjMetaschemaType.ObjDict']);
    x_ml = python2matlab(x_py.as_dict());
  elseif isa(x_py, 'py.dict')
    % x_ml = struct(x_py);
    dict_keys = python2matlab(py.list(keys(x_py)));
    dict_vals = python2matlab(py.list(values(x_py)));
    [nr, nc] = size(dict_keys);
    for i = 1:nr
      for j = 1:nc
	dict_keys{i, j} = char(dict_keys{i, j});
      end;
    end;
    x_ml = containers.Map(dict_keys, dict_vals);
  elseif (isa(x_py, 'py.list') || isa(x_py, 'py.tuple') || isa(x_py, 'py.set'))
    x_ml = cell(x_py);
    [nr, nc] = size(x_ml);
    for i = 1:nr
      for j = 1:nc
	x_ml{i, j} = python2matlab(x_ml{i, j});
      end;
    end;
  elseif (isa(x_py, 'py.unyt.array.unyt_quantity') || isa(x_py, 'py.unyt.array.unyt_array') || isa(x_py, 'py.pint.quantity.Quantity'))
    sym_env = getenv('YGG_MATLAB_SYMUNIT');
    if ((length(sym_env) > 0) && strcmp(lower(sym_env), 'true'))
      x_ml_data = python2matlab(py.yggdrasil.units.get_data(x_py));
      x_ml_unit = python2matlab(py.yggdrasil.units.get_units(x_py));
      x_ml = x_ml_data * str2symunit(x_ml_unit);
    else
      x_ml = python2matlab(py.yggdrasil.units.get_data(x_py));
    end;
  elseif isa(x_py, 'py.numpy.void')
    x_ml = python2matlab(py.tuple(x_py));
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
    x_ml = python2matlab(py.list(x_py));
    if ndim == 2
      x_ml = transpose(x_ml);
      x_ml = vertcat(x_ml{:});
    elseif ndim > 2
      disp('Conversion of numpy arrays with ndim > 2 uses nested cell arrays.');
    end;
    if (is_struct)
      x_ml = cell2table(x_ml, 'VariableNames', ...
			matlab.lang.makeValidName(string(python2matlab(x_py.dtype.names))));
    elseif ismember(char_code, ['f', 'i'])
      if isa(x_ml, 'cell')
        x_ml = cell2mat(x_ml);
      end;
    elseif ismember(char_code, ['S'])
      if isa(x_ml, 'cell')
        x_ml = string(x_ml);
      end;
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
