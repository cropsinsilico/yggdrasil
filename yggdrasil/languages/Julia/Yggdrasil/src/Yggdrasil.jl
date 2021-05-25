# https://juliahub.com/docs/PyCall/GkzkC/1.91.4/autodocs/#PyCall.pytype_mapping-Tuple{PyObject,Type}
module Yggdrasil

import PyCall
# import Base: convert
# np = PyCall.pyimport("numpy")

# function Base.convert(::Type{np.ndarray}, obj::PyObject)
#     return
# end

mutable struct Bytes
    val::String
end

function YggInterface(type::String, args...; kwargs...)
    np = PyCall.pyimport("numpy")
    ygg = PyCall.pyimport("yggdrasil.languages.Python.YggInterface")
    PyCall.pytype_mapping(np.int32, Int32)
    PyCall.pytype_mapping(PyCall.pybuiltin("bytes"), Bytes)
    PyCall.pytype_mapping(PyCall.pybuiltin("str"), String)
    out = ygg.YggInit(type, args=args, kwargs=kwargs)
    return out
end # function

end # module
