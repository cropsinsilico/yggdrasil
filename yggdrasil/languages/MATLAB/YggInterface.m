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
  pyobj = YggInterface.YggInit(type, py.list(varargin));
  if (nargin > 1);
    out = YggInterfaceClass(pyobj);
  else;
    out = python2matlab(pyobj);
  end;
end
