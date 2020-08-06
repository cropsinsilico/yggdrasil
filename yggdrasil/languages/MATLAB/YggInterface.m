% =============================================================================
%> @brief A simple wrapper for importing Python classes & functions.
%>
%> This function imports the correct class/function from the Python
%> YggInterface module, calls it with the provided input arguments, and returns
%> the result.
%>
%> @param type String specifying which class/function to call from
%> YggInterface.py.
%> @param varargin Variable number of input arguments passed to specified
%> python class/function.
%>
%> @return out python object returned by the called class/function.
% =============================================================================
function out = YggInterface(type, varargin)
  YggInterface = py.importlib.import_module('yggdrasil.languages.Python.YggInterface');
  keyword_names = {'global_scope', 'format_str', 'infmt', 'outfmt', ...
		   'as_array', 'fmt'};
  args = {};
  kwargs = containers.Map();
  i = 1;
  while (i <= length(varargin));
    if (ischar(varargin{i}));
      if any(strcmp(varargin{i},keyword_names));
        kwargs(varargin{i}) = varargin{i+1};
        i = i + 2;
      else;
        args{length(args)+1} = varargin{i};
        i = i + 1;
      end;
    else;
      i = i + 1;
    end;
  end;
  pyobj = YggInterface.YggInit(type, matlab2python(args), ...
			       matlab2python(kwargs));
  if (nargin > 1);
    out = YggInterfaceClass(pyobj);
  else;
    out = python2matlab(pyobj);
  end;
end
