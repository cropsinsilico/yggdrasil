% =============================================================================
%> @brief A simple wrapper for importing Python classes & functions.
%>
%> This function imports the correct class/function from the Python
%> PsiInterface module, calls it with the provided input arguments, and returns
%> the result.
%>
%> @param type String specifying which class/function to call from
%> PsiInterface.py.
%> @param varargin Variable number of input arguments passed to specified
%> python class/function.
%>
%> @return pyobj python object returned by the called class/function.
% =============================================================================
function out = PsiInterface(type, varargin)
  PsiInterface = py.importlib.import_module('cis_interface.interface.PsiInterface');
  pyobj = PsiInterface.PsiMatlab(type, py.list(varargin));
  if (nargin > 1)
    out = PsiInterfaceClass(pyobj);
  else
    out = python2matlab(pyobj);
  end;
end
