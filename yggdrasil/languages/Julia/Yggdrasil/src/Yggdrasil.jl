# https://juliahub.com/docs/PyCall/GkzkC/1.91.4/autodocs/#PyCall.pytype_mapping-Tuple{PyObject,Type}
module Yggdrasil

import PyCall
import Unitful
import Base: convert

mutable struct Bytes
  val::String
end
Base.:(==)(x::Bytes, y::Bytes) = x.val == y.val

function Base.convert(::Type{Unitful.Quantity}, o::PyCall.PyObject)
  units = PyCall.pyimport("yggdrasil.units")
  y = String(units.convert_julia_unit_string(units.get_units(o)))
  return Unitful.Quantity(units.get_data(o), Unitful.uparse(y))
end

function Base.convert(::Type{Array{Unitful.Quantity}}, o::PyCall.PyObject)
  units = PyCall.pyimport("yggdrasil.units")
  y = String(units.convert_julia_unit_string(units.get_units(o)))
  x = units.get_data(o)
  return x * Unitful.uparse(y)
end

function Base.convert(::Type{Bytes}, o::PyCall.PyObject)
  return Bytes(o.decode("utf8"))
end

function Base.parse(::Type{T}, o::Bytes) where T
  return parse(T, o.val)
end

function Base.length(x::Bytes)
  return length(x.val)
end

function Base.countlines(x::Bytes)
  return countlines(x.val)
end

function Base.IOBuffer(x::Bytes)
  return IOBuffer(x.val)
end

function PyCall.PyObject(o::Unitful.Quantity)
  units = PyCall.pyimport("yggdrasil.units")
  y = Unitful.ustrip(o)
  z = repr(Unitful.unit(o), context = Pair(:fancy_exponent,false))
  out = PyCall.pycall(units.Quantity, PyCall.PyObject, y, z)
  return out
end

function PyCall.PyObject(o::Array{T}) where {T<:Unitful.Quantity}
  units = PyCall.pyimport("yggdrasil.units")
  y = Unitful.ustrip(o)
  z = repr(Unitful.unit(o[1]), context = Pair(:fancy_exponent,false))
  return PyCall.pycall(units.QuantityArray, PyCall.PyObject, y, z)
end

function PyCall.PyObject(o::Bytes)
  return PyCall.pycall(PyCall.PyObject(o.val).encode, PyCall.PyObject, "utf8")
end

function finalize_comm(pyobj)
  pyobj.atexit()
end

function YggInterface(type::String, args...; kwargs...)
    np = PyCall.pyimport("numpy")
    ygg = PyCall.pyimport("yggdrasil.languages.Python.YggInterface")
    units = PyCall.pyimport("yggdrasil.units")
    PyCall.pytype_mapping(np.int32, Int32)
    PyCall.pytype_mapping(np.int64, Int64)
    PyCall.pytype_mapping(PyCall.pybuiltin("bytes"), Bytes)
    PyCall.pytype_mapping(PyCall.pybuiltin("str"), String)
    PyCall.pytype_mapping(units.Quantity, Unitful.Quantity)
    PyCall.pytype_mapping(units.QuantityArray, Array{Unitful.Quantity})
    out = ygg.YggInit(type, args=args, kwargs=kwargs)
    # finalizer(finalize_comm, out)
    return out
end # function

end # module
