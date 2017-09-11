
function pyobj = PsiInterface(type, varargin)
  PsiInterface = py.importlib.import_module('cis_interface.interface.PsiInterface');
  pyobj = PsiInterface.PsiMatlab(type, py.list(varargin));
end
