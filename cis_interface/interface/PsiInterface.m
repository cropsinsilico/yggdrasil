% =============================================================================
%> @brief An alias for CisInterface wrapper. See the documentation for
%> CisInterface.
% =============================================================================
function out = PsiInterface(type, varargin)
  out = CisInterface(type, varargin{:});
end
