% =============================================================================
%> @brief An alias for the interface with the new name
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
function out = CisInterface(type, varargin)
  out = YggInterface(type, varargin{:});
end
