% =============================================================================
%> @brief A simple wrapper for importing Python classes & functions.
%>
%> This function imports the correct class/function from the Python
%> CisInterface module, calls it with the provided input arguments, and returns
%> the result.
%>
%> @param type String specifying which class/function to call from
%> CisInterface.py.
%> @param varargin Variable number of input arguments passed to specified
%> python class/function.
%>
%> @return out python object returned by the called class/function.
% =============================================================================
function out = CisInterface(type, varargin)
  CisInterface = py.importlib.import_module('cis_interface.interface.CisInterface');
  pyobj = CisInterface.CisMatlab(type, py.list(varargin));
  if (nargin > 1);
    out = CisInterfaceClass(pyobj);
  else;
    out = python2matlab(pyobj);
  end;
end
