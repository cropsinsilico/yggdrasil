// -*- coding: utf-8 -*-
// :Project:   python-rapidjson -- Python extension module
// :Author:    Meagan Lang <langmm.astro@gmail.com>
// :License:   BSD License
//

#ifndef _USE_MATH_DEFINES
#define _USE_MATH_DEFINES
#endif

#include <Python.h>

#include "rapidjson/units.h"
#include "rapidjson/precision.h"
#include "rapidjson/rapidjson.h"
#include <numpy/arrayobject.h>
#include <numpy/ufuncobject.h>

using namespace rapidjson;
using namespace rapidjson::units;


static PyObject* units_error = NULL;

#define QUANTITY_ARRAY_OFFSET_BUFFER 256

//////////////////////////
// Forward declarations //
//////////////////////////

// Units
static void units_dealloc(PyObject* self);
static PyObject* units_new(PyTypeObject* type, PyObject* args, PyObject* kwargs);
static PyObject* units_str(PyObject* self);
static PyObject* units_is_compatible(PyObject* self, PyObject* args, PyObject* kwargs);
static PyObject* units_is_dimensionless(PyObject* self, PyObject* args);
static PyObject* units_richcompare(PyObject *self, PyObject *other, int op);
static PyObject* units_multiply(PyObject *a, PyObject *b);
static PyObject* units_divide(PyObject *a, PyObject *b);
static PyObject* units_power(PyObject *base, PyObject *exp, PyObject *mod);
static PyObject* units_multiply_inplace(PyObject *a, PyObject *b);
static PyObject* units_divide_inplace(PyObject *a, PyObject *b);
static PyObject* units_power_inplace(PyObject *base, PyObject *exp, PyObject *mod);
static PyObject* units__getstate__(PyObject* self, PyObject* args, PyObject* kwargs);
static PyObject* units__setstate__(PyObject* self, PyObject* state);

// Quantity
static PyObject* quantity_new(PyTypeObject* type, PyObject* args, PyObject* kwargs);

// QuantityArray
static void quantity_array_dealloc(PyObject* self);
static PyObject* quantity_array_new(PyTypeObject* type, PyObject* args, PyObject* kwargs);
static PyObject* quantity_array_str(PyObject* self);
static PyObject* quantity_array_repr(PyObject* self);
static PyObject* quantity_array_get_converted_value(PyObject* self, PyObject* units);
static PyObject* quantity_array_units_get(PyObject* self, void* closure);
static int quantity_array_units_set(PyObject* self, PyObject* value, void* closure);
static PyObject* quantity_array_value_get(PyObject* type, void* closure);
static PyObject* quantity_array_value_get_copy(PyObject* type, void* closure);
static int quantity_array_value_set(PyObject* self, PyObject* value, void* closure);
static PyObject* quantity_array_is_compatible(PyObject* self, PyObject* args, PyObject* kwargs);
static PyObject* quantity_array_is_dimensionless(PyObject* self, PyObject* args);
static PyObject* quantity_array_is_equivalent(PyObject* self, PyObject* args);
static PyObject* quantity_array_to(PyObject* self, PyObject* args);
static PyObject* quantity_array__array_ufunc__(PyObject* self, PyObject* args, PyObject* kwargs);
static PyObject* quantity_array__array_finalize__(PyObject* self, PyObject* args);
static PyObject* quantity_array__array_wrap__(PyObject* self, PyObject* args);
static PyObject* quantity_array__array_function__(PyObject* self, PyObject* args, PyObject* kwargs);
static PyObject* quantity_array__format__(PyObject* self, PyObject* args);
static PyObject* quantity_array_subscript(PyObject* self, PyObject* key);
static int quantity_array_ass_subscript(PyObject* self, PyObject* key, PyObject* val);
static PyObject* quantity_array__setstate__(PyObject* self, PyObject* state);
static PyObject* quantity_array__reduce__(PyObject* self, PyObject* args, PyObject* kwargs);


///////////////
// Utilities //
///////////////

enum BinaryOps {
    binaryOpAdd,
    binaryOpSubtract,
    binaryOpMultiply,
    binaryOpDivide,
    binaryOpModulo,
    binaryOpFloorDivide
};


static PyObject* _get_units(PyObject* x,
			    bool dont_allow_empty = false,
			    bool force_copy = false);
static int _has_units(PyObject* x);
static PyObject* _convert_units(PyObject* x, PyObject* units,
				bool stripUnits=false);
static int _compare_units(PyObject* x0, PyObject* x1,
			  bool allowCompat = false,
			  bool dimensionlessCompat = false);
static int _compare_units_tuple(PyObject* x, bool allowCompat = false,
				bool dimensionlessCompat = false,
				PyObject** out_units=NULL);
static PyObject* _get_array(PyObject* item);
static int _copy_array_into(PyObject* dst, PyObject* src, bool copyFlags=false);
PyObject* _copy_array(PyObject* item, PyObject* type, bool copyFlags=false, bool returnScalar=false, PyArray_Descr *dtype = NULL);

#define SET_ERROR(errno, msg, ret)			\
    {							\
	PyObject* error = Py_BuildValue("s", msg);	\
	PyErr_SetObject(errno, error);			\
	Py_XDECREF(error);				\
	return ret;					\
    }

#define SUPER(x, out)							\
    PyTypeObject* super_cls = x->ob_type;				\
    if (super_cls == &Quantity_Type) {					\
	super_cls = &QuantityArray_Type;				\
    }									\
    out = PyObject_CallFunctionObjArgs((PyObject*)&PySuper_Type, super_cls, x, NULL)

#define CALL_BASE_METHOD_NOARGS(method, out)				\
    {									\
	PyObject* base_cls = NULL;					\
	SUPER(self, base_cls);						\
	PyObject* base_fnc = NULL;					\
	if (base_cls != NULL) {						\
	    base_fnc = PyObject_GetAttrString(base_cls, #method);	\
	}								\
	if (base_fnc) {							\
	    PyObject* tmp_args = PyTuple_New(0);			\
	    if (tmp_args != NULL) {					\
		out = PyObject_Call(base_fnc, tmp_args, NULL);		\
		Py_DECREF(tmp_args);					\
	    }								\
	}								\
	Py_XDECREF(base_fnc);						\
	Py_XDECREF(base_cls);						\
    }

#define CALL_BASE_METHOD(method, out, ...)				\
    {									\
	PyObject* base_cls = NULL;					\
	SUPER(self, base_cls);						\
	PyObject* base_fnc = NULL;					\
	if (base_cls != NULL) {						\
	    base_fnc = PyObject_GetAttrString(base_cls, #method);	\
	}								\
	if (base_fnc) {							\
	    out = PyObject_CallFunctionObjArgs(base_fnc, __VA_ARGS__, NULL); \
	}								\
	Py_XDECREF(base_fnc);						\
	Py_XDECREF(base_cls);						\
    }


#define CALL_BASE_METHOD_ARGS_KWARGS(method, out, args, kwargs)		\
    {									\
	PyObject* base_cls = NULL;					\
	SUPER(self, base_cls);						\
        PyObject* base_fnc = NULL;					\
	if (base_cls != NULL) {						\
	    base_fnc = PyObject_GetAttrString(base_cls, #method);	\
	}								\
	if (base_fnc != NULL) {						\
	    out = PyObject_Call(base_fnc, args, kwargs);		\
	}								\
	Py_XDECREF(base_fnc);						\
	Py_XDECREF(base_cls);						\
    }

///////////
// Units //
///////////


typedef struct {
    PyObject_HEAD
    Units *units;
} UnitsObject;


PyDoc_STRVAR(units_doc,
             "Units(expression)\n"
             "\n"
             "Create and return a new Units instance from the given"
             " `expression` string.");


static PyMethodDef units_methods[] = {
    {"is_compatible", (PyCFunction) units_is_compatible, METH_VARARGS,
     "Check if a set of units are compatible with another set."},
    {"is_dimensionless", (PyCFunction) units_is_dimensionless, METH_NOARGS,
     "Check if the units are dimensionless."},
    {"__getstate__", (PyCFunction) units__getstate__,
     METH_NOARGS,
     "Get the instance state."},
    {"__setstate__", (PyCFunction) units__setstate__,
     METH_O,
     "Set the instance state."},
    {NULL}  /* Sentinel */
};


static PyNumberMethods units_number_methods = {
    0,                              /* nb_add */
    0,                              /* nb_subtract */
    units_multiply,                 /* nb_multiply */
    0,                              /* nb_remainder */
    0,                              /* nb_divmod */
    units_power,                    /* nb_power */
    0,                              /* nb_negative */
    0,                              /* nb_positive */
    0,                              /* nb_absolute */
    0,                              /* nb_bool */
    0,                              /* nb_invert */
    0,                              /* nb_lshift */
    0,                              /* nb_rshift */
    0,                              /* nb_and */
    0,                              /* nb_xor */
    0,                              /* nb_or */
    0,                              /* nb_int */
    0,                              /* nb_reserved */
    0,                              /* nb_float */
    //
    0,                              /* nb_inplace_add */
    0,                              /* nb_inplace_subtract */
    units_multiply_inplace,         /* nb_inplace_multiply */
    0,                              /* nb_inplace_remainder */
    units_power_inplace,            /* nb_inplace_power */
    0,                              /* nb_inplace_lshift */
    0,                              /* nb_inplace_rshift */
    0,                              /* nb_inplace_and */
    0,                              /* nb_inplace_xor */
    0,                              /* nb_inplace_or */
    //
    0,                              /* nb_floor_divide */
    units_divide,                   /* nb_true_divide */
    0,                              /* nb_inplace_floor_divide */
    units_divide_inplace,           /* nb_inplace_true_divide */
    //
    0,                              /* nb_index */
    //
    0,                              /* nb_matrix_multiply */
    0,                              /* nb_inplace_matrix_multiply */
};


static PyTypeObject Units_Type = {
    PyVarObject_HEAD_INIT(NULL, 0)
    "yggdrasil.rapidjson.units.Units",        /* tp_name */
    sizeof(UnitsObject),            /* tp_basicsize */
    0,                              /* tp_itemsize */
    (destructor) units_dealloc,     /* tp_dealloc */
    0,                              /* tp_print */
    0,                              /* tp_getattr */
    0,                              /* tp_setattr */
    0,                              /* tp_compare */
    0,                              /* tp_repr */
    &units_number_methods,          /* tp_as_number */
    0,                              /* tp_as_sequence */
    0,                              /* tp_as_mapping */
    0,                              /* tp_hash */
    0,                              /* tp_call */
    units_str,                      /* tp_str */
    0,                              /* tp_getattro */
    0,                              /* tp_setattro */
    0,                              /* tp_as_buffer */
    Py_TPFLAGS_DEFAULT,             /* tp_flags */
    units_doc,                      /* tp_doc */
    0,                              /* tp_traverse */
    0,                              /* tp_clear */
    units_richcompare,              /* tp_richcompare */
    0,                              /* tp_weaklistoffset */
    0,                              /* tp_iter */
    0,                              /* tp_iternext */
    units_methods,                  /* tp_methods */
    0,                              /* tp_members */
    0,                              /* tp_getset */
    0,                              /* tp_base */
    0,                              /* tp_dict */
    0,                              /* tp_descr_get */
    0,                              /* tp_descr_set */
    0,                              /* tp_dictoffset */
    0,                              /* tp_init */
    0,                              /* tp_alloc */
    units_new,                      /* tp_new */
    PyObject_Del,                   /* tp_free */
};


static PyObject*
get_empty_units(PyObject* units = NULL) {
    PyObject* out = NULL;
    PyObject* units_args = NULL;
    if (units == NULL) {
	units = PyUnicode_FromString("");
	if (units == NULL) {
	    return NULL;
	}
	units_args = PyTuple_Pack(1, units);
	Py_DECREF(units);
    } else {
	units_args = PyTuple_Pack(1, units);
    }
    if (units_args == NULL) {
	return NULL;
    }
    out = PyObject_Call((PyObject*)&Units_Type, units_args, NULL);
    Py_DECREF(units_args);
    return out;
}

static UnitsObject* units_coerce(PyObject* x) {
    PyObject* out = NULL;
    if (PyObject_IsInstance(x, (PyObject*)&Units_Type)) {
	Py_INCREF(x);
	return (UnitsObject*)x;
    }
    PyObject* args = PyTuple_Pack(1, x);
    if (args == NULL) return NULL;
    out = PyObject_Call((PyObject*)&Units_Type, args, NULL);
    Py_DECREF(args);
    return (UnitsObject*)out;
}


static void units_dealloc(PyObject* self)
{
    UnitsObject* s = (UnitsObject*) self;
    delete s->units;
    Py_TYPE(self)->tp_free(self);
}


static PyObject* units_new(PyTypeObject* type, PyObject* args, PyObject* kwargs)
{
    PyObject* exprObject;

    if (!PyArg_ParseTuple(args, "O:Units", &exprObject))
	return NULL;

    std::string exprStr_;
    const char* exprStr = 0;
    const UnitsObject* other;

    if (PyBytes_Check(exprObject)) {
        exprStr = PyBytes_AsString(exprObject);
        if (exprStr == NULL)
            return NULL;
    } else if (PyUnicode_Check(exprObject)) {
        exprStr = PyUnicode_AsUTF8(exprObject);
        if (exprStr == NULL)
            return NULL;
    } else if (PyObject_IsInstance(exprObject, (PyObject*)&Units_Type)) {
	other = (UnitsObject*)exprObject;
    } else if (exprObject == Py_None) {
	exprStr = "";
    } else {
        PyErr_SetString(PyExc_TypeError, "Expected string or UTF-8 encoded bytes");
        return NULL;
    }

    UnitsObject* v = (UnitsObject*) type->tp_alloc(type, 0);
    if (v == NULL)
        return NULL;

    if (exprStr) {
	v->units = new Units(exprStr);
    } else {
	exprStr_ = other->units->str();
	exprStr = exprStr_.c_str();
	v->units = new Units(*other->units);
    }
    if (v->units->is_empty()) {
	PyErr_Format(units_error,
		     "Failed to parse units '%s'", exprStr);
	return NULL;
    }

    return (PyObject*) v;
}


static PyObject* units_str(PyObject* self) {
    UnitsObject* v = (UnitsObject*) self;
    std::string s = v->units->str();
    return PyUnicode_FromString(s.c_str());
}

static PyObject* units_is_compatible(PyObject* self, PyObject* args, PyObject* kwargs) {
    PyObject* otherObject;
    const UnitsObject* other;
    
    if (!PyArg_ParseTuple(args, "O", &otherObject))
	return NULL;

    if (PyObject_IsInstance(otherObject, (PyObject*)&Units_Type)) {
	other = (UnitsObject*)otherObject;
	Py_INCREF(otherObject);
    } else {
	other = (UnitsObject*)PyObject_Call((PyObject*)&Units_Type, args, NULL);
    }
    if (other == NULL)
        return NULL;
    
    UnitsObject* v = (UnitsObject*) self;
    bool result = v->units->is_compatible(*other->units);
    Py_DECREF(other);
    if (result) {
	Py_INCREF(Py_True);
	return Py_True;
    }
    Py_INCREF(Py_False);
    return Py_False;
    
}


static PyObject* units_is_dimensionless(PyObject* self, PyObject* args) {
    UnitsObject* v = (UnitsObject*) self;
    bool result = v->units->is_dimensionless();
    if (result) {
	Py_INCREF(Py_True);
	return Py_True;
    }
    Py_INCREF(Py_False);
    return Py_False;
}


static PyObject* units_richcompare(PyObject *self, PyObject *other, int op) {
    if (!PyObject_IsInstance(other, (PyObject*)(&Units_Type))) {
	Py_INCREF(Py_False);
	return Py_False;
    }
    UnitsObject* vself = (UnitsObject*) self;
    UnitsObject* vsolf = (UnitsObject*) other;
    switch (op) {
    case (Py_EQ): {
	if (*(vself->units) == *(vsolf->units)) {
	    Py_INCREF(Py_True);
	    return Py_True;
	}
	Py_INCREF(Py_False);
	return Py_False;
    }
    case (Py_NE): {
	if (*(vself->units) != *(vsolf->units)) {
	    Py_INCREF(Py_True);
	    return Py_True;
	}
	Py_INCREF(Py_False);
	return Py_False;
    }
    default:
	Py_INCREF(Py_NotImplemented);
	return Py_NotImplemented;
    }
}

static PyObject* do_units_op(PyObject* a, PyObject *b, BinaryOps op,
			     bool inplace=false) {
    if (!(PyObject_IsInstance(a, (PyObject*)&Units_Type) &&
	  PyObject_IsInstance(b, (PyObject*)&Units_Type))) {
	PyErr_SetString(PyExc_TypeError, "This operation is only valid for two rapidjson.units.Units instances.");
	return NULL;
    }
    PyObject* out;
    if (inplace) {
	out = a;
    } else {
	out = (PyObject*) Units_Type.tp_alloc(&Units_Type, 0);
	((UnitsObject*)out)->units = new Units();
    }
    switch (op) {
    case (binaryOpMultiply): {
	if (inplace)
	    *(((UnitsObject*)out)->units) *= *(((UnitsObject*)b)->units);
	else
	    *(((UnitsObject*)out)->units) = (*(((UnitsObject*)a)->units) *
					     *(((UnitsObject*)b)->units));
	break;
    }
    case (binaryOpDivide): {
	if (inplace)
	    *(((UnitsObject*)out)->units) /= *(((UnitsObject*)b)->units);
	else
	    *(((UnitsObject*)out)->units) = (*(((UnitsObject*)a)->units) /
					     *(((UnitsObject*)b)->units));
	break;
    }
    default: {
	if (!inplace) {
	    Py_DECREF(out);
	}
	PyErr_SetString(PyExc_NotImplementedError, "yggdrasil.rapidjson.units.Units do not support this operation.");
	return NULL;
    }
    }
    return out;
}

static PyObject* do_units_pow(PyObject* a, PyObject *b, PyObject* mod,
			      bool inplace=false) {
    if (PyObject_IsInstance(b, (PyObject*)&Units_Type)) {
	PyErr_SetString(PyExc_TypeError, "Cannot raise to a rapidjson.units.Units power");
	return NULL;
    }
    if (!PyObject_IsInstance(a, (PyObject*)&Units_Type)) {
	PyErr_SetString(PyExc_TypeError, "Base doesn't have units, why is this being called?");
	return NULL;
    }
    if (mod != Py_None) {
	PyErr_SetString(PyExc_NotImplementedError, "'mod' power argument not supported for rapidjson.units.Units instances.");
	return NULL;
    }
    PyObject* exp = PyNumber_Float(b);
    if (exp == NULL) return NULL;
    double expV = PyFloat_AsDouble(exp);
    Py_DECREF(exp);
    PyObject* out;
    if (inplace) {
	out = a;
	((UnitsObject*)out)->units->pow_inplace(expV);
    } else {
	out = (PyObject*) Units_Type.tp_alloc(&Units_Type, 0);
	((UnitsObject*)out)->units = new Units();
	*(((UnitsObject*)out)->units) = ((UnitsObject*)a)->units->pow(expV);
    }
    return out;
}

static PyObject* units_multiply(PyObject *a, PyObject *b)
{ return do_units_op(a, b, binaryOpMultiply); }
static PyObject* units_divide(PyObject *a, PyObject *b)
{ return do_units_op(a, b, binaryOpDivide); }
static PyObject* units_power(PyObject *base, PyObject *exp, PyObject *mod)
{ return do_units_pow(base, exp, mod); }
static PyObject* units_multiply_inplace(PyObject *a, PyObject *b)
{ return do_units_op(a, b, binaryOpMultiply, true); }
static PyObject* units_divide_inplace(PyObject *a, PyObject *b)
{ return do_units_op(a, b, binaryOpDivide, true); }
static PyObject* units_power_inplace(PyObject *base, PyObject *exp, PyObject *mod)
{ return do_units_pow(base, exp, mod, true); }
static PyObject* units__getstate__(PyObject* self, PyObject*, PyObject*) {
    PyObject* units = units_str(self);
    if (units == NULL)
	return NULL;
    return units;
}
static PyObject* units__setstate__(PyObject* self, PyObject* state) {
    if (!PyUnicode_Check(state)) {
	PyErr_SetString(PyExc_TypeError, "State must be a string");
	return NULL;
    }
    const char* exprStr = PyUnicode_AsUTF8(state);
    if (exprStr == NULL)
	return NULL;
    UnitsObject* v = (UnitsObject*)self;
    delete v->units;
    v->units = new Units(exprStr);
    if (v->units->is_empty()) {
	PyErr_SetString(units_error, "Failed to parse units.");
	return NULL;
    }
    Py_INCREF(Py_None);
    return Py_None;
}


///////////////////
// QuantityArray //
///////////////////

typedef struct {
    PyArrayObject_fields base;
    char buffer[QUANTITY_ARRAY_OFFSET_BUFFER];
    UnitsObject* units;
} QuantityArrayObject;


PyDoc_STRVAR(quantity_array_doc,
             "QuantityArray(value, units, dtype=None)\n"
             "\n"
             "Create and return a new QuantityArray instance from the given"
             " `value` and `units` string or Units instance.");


static PyMethodDef quantity_array_methods[] = {
    {"is_compatible", (PyCFunction) quantity_array_is_compatible, METH_VARARGS,
     "Check if a set of units or quantity is compatible with another set."},
    {"is_dimensionless", (PyCFunction) quantity_array_is_dimensionless, METH_NOARGS,
     "Check if the quantity has dimensionless units."},
    {"to", (PyCFunction) quantity_array_to, METH_VARARGS,
     "Convert the quantity to another set of units."},
    {"is_equivalent", (PyCFunction) quantity_array_is_equivalent, METH_VARARGS,
     "Check if another QuantityArray is equivalent when convert to the same units/"},
    {"__array_ufunc__", (PyCFunction) quantity_array__array_ufunc__, METH_VARARGS | METH_KEYWORDS,
     "UFuncs"},
    {"__array_wrap__", (PyCFunction) quantity_array__array_wrap__, METH_VARARGS,
     "array wrapper for numpy views"},
    {"__array_finalize__", (PyCFunction) quantity_array__array_finalize__, METH_VARARGS,
     "finalize array "},
    {"__array_function__", (PyCFunction) quantity_array__array_function__,
     METH_VARARGS | METH_KEYWORDS,
     "numpy array function handling"},
    {"__format__", (PyCFunction) quantity_array__format__, METH_VARARGS,
     "Format the array according to format spec."},
    {"__reduce__", (PyCFunction) quantity_array__reduce__,
     METH_NOARGS,
     "Get the instance state."},
    {"__setstate__", (PyCFunction) quantity_array__setstate__,
     METH_O,
     "Set the instance state."},
    {NULL}  /* Sentinel */
};


static PyGetSetDef quantity_array_properties[] = {
    {"units", quantity_array_units_get, quantity_array_units_set,
     "The rapidjson.units.Units units for the quantity.", NULL},
    {"value", quantity_array_value_get, quantity_array_value_set,
     "The quantity's value (in the current unit system)."},
    {NULL}
};


static PyMappingMethods quantity_array_map = {
    0,                           // mp_length
    quantity_array_subscript,    // mp_subscript
    quantity_array_ass_subscript // mp_ass_subscript
};


static PyTypeObject QuantityArray_Type = {
    PyVarObject_HEAD_INIT(NULL, 0)
    "yggdrasil.rapidjson.units.QuantityArray",      /* tp_name */
    sizeof(QuantityArrayObject),          /* tp_basicsize */
    0,                                    /* tp_itemsize */
    (destructor) quantity_array_dealloc,  /* tp_dealloc */
    0,                                    /* tp_print */
    0,                                    /* tp_getattr */
    0,                                    /* tp_setattr */
    0,                                    /* tp_compare */
    quantity_array_repr,                  /* tp_repr */
    0,                                    /* tp_as_number */
    0,                                    /* tp_as_sequence */
    &quantity_array_map,                  /* tp_as_mapping */
    0,                                    /* tp_hash */
    0,                                    /* tp_call */
    quantity_array_str,                   /* tp_str */
    0,                                    /* tp_getattro */
    0,                                    /* tp_setattro */
    0,                                    /* tp_as_buffer */
    Py_TPFLAGS_DEFAULT | Py_TPFLAGS_BASETYPE, /* tp_flags */
    quantity_array_doc,                   /* tp_doc */
    0,                                    /* tp_traverse */
    0,                                    /* tp_clear */
    0,                                    /* tp_richcompare */
    0,                                    /* tp_weaklistoffset */
    0,                                    /* tp_iter */
    0,                                    /* tp_iternext */
    quantity_array_methods,               /* tp_methods */
    0,                                    /* tp_members */
    quantity_array_properties,            /* tp_getset */
    0,                                    /* tp_base */
    0,                                    /* tp_dict */
    0,                                    /* tp_descr_get */
    0,                                    /* tp_descr_set */
    0,                                    /* tp_dictoffset */
    0,                                    /* tp_init */
    0,                                    /* tp_alloc */
    quantity_array_new,                   /* tp_new */
    PyObject_Del,                         /* tp_free */
};


//////////////
// Quantity //
//////////////

typedef struct {
    QuantityArrayObject arr;
} QuantityObject;


PyDoc_STRVAR(quantity_doc,
             "Quantity(value, units, dtype=None)\n"
             "\n"
             "Create and return a new Quantity instance from the given"
             " `value` and `units` string or Units instance.");


static PyTypeObject Quantity_Type = {
    PyVarObject_HEAD_INIT(NULL, 0)
    "yggdrasil.rapidjson.units.Quantity",     /* tp_name */
    sizeof(QuantityObject),         /* tp_basicsize */
    0,                              /* tp_itemsize */
    0,                              /* tp_dealloc */
    0,                              /* tp_print */
    0,                              /* tp_getattr */
    0,                              /* tp_setattr */
    0,                              /* tp_compare */
    0,                              /* tp_repr */
    0,                              /* tp_as_number */
    0,                              /* tp_as_sequence */
    0,                              /* tp_as_mapping */
    0,                              /* tp_hash */
    0,                              /* tp_call */
    0,                              /* tp_str */
    0,                              /* tp_getattro */
    0,                              /* tp_setattro */
    0,                              /* tp_as_buffer */
    Py_TPFLAGS_DEFAULT | Py_TPFLAGS_BASETYPE, /* tp_flags */
    quantity_doc,                   /* tp_doc */
    0,                              /* tp_traverse */
    0,                              /* tp_clear */
    0,                              /* tp_richcompare */
    0,                              /* tp_weaklistoffset */
    0,                              /* tp_iter */
    0,                              /* tp_iternext */
    0,                              /* tp_methods */
    0,                              /* tp_members */
    0,                              /* tp_getset */
    0,                              /* tp_base */
    0,                              /* tp_dict */
    0,                              /* tp_descr_get */
    0,                              /* tp_descr_set */
    0,                              /* tp_dictoffset */
    0,                              /* tp_init */
    0,                              /* tp_alloc */
    quantity_new,                   /* tp_new */
    PyObject_Del,                   /* tp_free */
};

/////////////////////////////
// QuantityArray Utilities //
/////////////////////////////

static PyObject* quantity_array_pull_factor(PyObject* x) {
    double factor = ((QuantityArrayObject*)x)->units->units->pull_factor();
    if (!internal::values_eq(factor, 1)) {
	PyObject* py_factor;
	if (internal::values_eq(floor(factor), factor))
	    py_factor = PyLong_FromDouble(factor);
	else
	    py_factor = PyFloat_FromDouble(factor);
	if (py_factor == NULL) {
	    Py_DECREF(x);
	    return NULL;
	}
	PyObject* out = PyNumber_InPlaceMultiply(x, py_factor);
	Py_DECREF(py_factor);
	// Py_DECREF(x);
	return out;
    }
    return x;
}

static QuantityArrayObject* quantity_array_coerce(PyObject* x) {
    PyObject* out = NULL;
    if (PyObject_IsInstance(x, (PyObject*)&QuantityArray_Type)) {
	Py_INCREF(x);
	return (QuantityArrayObject*)x;
    }
    PyObject* args = NULL;
    if (PyObject_HasAttrString(x, "units")) {
	PyObject* units = PyObject_GetAttrString(x, "units");
	if (units == NULL) return NULL;
	args = PyTuple_Pack(2, x, units);
	Py_DECREF(units);
    } else {
	args = PyTuple_Pack(1, x);
    }
    if (args == NULL) return NULL;
    out = PyObject_Call((PyObject*)&QuantityArray_Type, args, NULL);
    Py_DECREF(args);
    return (QuantityArrayObject*)out;
}


static PyObject* quantity_array_numpy_tuple(PyObject* args,
					    bool as_view = false,
					    PyObject* convert_to = NULL) {
    if (!PySequence_Check(args))
	return NULL;
    Py_ssize_t Nargs = PySequence_Size(args);
    Py_ssize_t i = 0;
    PyObject *item, *new_item, *item_array, *out = NULL;
    bool error = false;
    out = PyTuple_New(Nargs);
    if (out == NULL) {
	return NULL;
    }
    for (i = 0; i < Nargs; i++) {
	new_item = NULL;
	item = PySequence_GetItem(args, i);
	if (item == NULL) {
	    error = true;
	    goto cleanup;
	}
	if (convert_to != NULL) {
	    item_array = (PyObject*)quantity_array_coerce(item);
	    if (item_array == NULL) {
		Py_DECREF(item);
		error = true;
		goto cleanup;
	    }
	    new_item = quantity_array_get_converted_value(item_array,
							  convert_to);
	    Py_DECREF(item_array);
	} else if (as_view) {
	    if (!PyArray_Check(item)) {
		Py_DECREF(item);
		PyErr_SetString(units_error, "Internal error in trying to created a view from a non-array input");
		error = true;
		goto cleanup;
	    }
	    new_item = PyArray_View((PyArrayObject*)item, NULL, &PyArray_Type);
	} else if (PyArray_Check(item)) {
	    new_item = _copy_array(item, (PyObject*)&PyArray_Type, true, true);
	} else {
	    if (!PyArray_Converter(item, &new_item)) {
		Py_DECREF(item);
		error = true;
		goto cleanup;
	    }
	    if (PyArray_Check(new_item)) {
		new_item = PyArray_Return((PyArrayObject*)new_item);
	    }
	}
	Py_DECREF(item);
	if (new_item == NULL) {
	    error = true;
	    goto cleanup;
	}
	if (PyTuple_SetItem(out, i, new_item) < 0) {
	    error = true;
	    goto cleanup;
	}
    }
cleanup:
    if (error) {
	Py_DECREF(out);
	out = NULL;
    }
    return out;
}


///////////////////////////
// QuantityArray Methods //
///////////////////////////


static void quantity_array_dealloc(PyObject* self)
{
    QuantityArrayObject* s = (QuantityArrayObject*) self;
    Py_XDECREF(s->units);
    PyArray_Type.tp_dealloc(self);
}


static PyObject* quantity_array_new(PyTypeObject* type, PyObject* args, PyObject* kwargs)
{
    PyObject *valueObject = NULL, *unitsObject = NULL, *dtypeObject = NULL,
	*units = NULL, *out = NULL;
    static char const* kwlist[] = {
	"value",
	"units",
	"dtype",
	NULL
    };
    bool nullUnits = false, dont_pull = false;
    PyArray_Descr* dtype = NULL;

    if (!PyArg_ParseTupleAndKeywords(args, kwargs, "O|OO:QuantityArray",
				     (char**) kwlist,
				     &valueObject, &unitsObject,
				     &dtypeObject))
	return NULL;

    nullUnits = (unitsObject == NULL);
    units = get_empty_units(unitsObject);
    if (units == NULL) {
	return NULL;
    }

    if ((!nullUnits) &&
	PyObject_IsInstance(valueObject, (PyObject*)&QuantityArray_Type)) {
	// This version does not do conversion if valueObject is dimensionless
	// if (((QuantityArrayObject*)valueObject)->units->units->is_dimensionless() &&
	//     !((QuantityArrayObject*)valueObject)->units->units->has_factor()) {
	//     valueObject = quantity_array_value_get_copy(valueObject, NULL);
	// } else {
	valueObject = quantity_array_get_converted_value(valueObject, units);
	dont_pull = true;
	// }
	if (valueObject == NULL) {
	    goto fail;
	}
    } else {
	Py_INCREF(valueObject);
    }
    if (dtypeObject != NULL) {
	if (PyObject_IsInstance(dtypeObject, (PyObject*)&PyArrayDescr_Type)) {
	    Py_INCREF(dtypeObject);
	    dtype = (PyArray_Descr*)dtypeObject;
	} else {
	    dtype = (PyArray_Descr*)PyObject_CallFunctionObjArgs((PyObject*)&PyArrayDescr_Type, dtypeObject, NULL);
	}
	if (dtype == NULL) {
	    goto fail;
	}
    }

    out = _copy_array(valueObject, (PyObject*)type, false, false, dtype);
    Py_DECREF(valueObject);
    if (out == NULL) {
	goto fail;
    }

    ((QuantityArrayObject*)out)->units = (UnitsObject*)units;
    if (!dont_pull) {
	out = quantity_array_pull_factor(out);
    }

    return out;
fail:
    Py_XDECREF(units);
    Py_XDECREF(out);
    return NULL;
}


static PyObject* quantity_array_str(PyObject* self) {
    QuantityArrayObject* v = (QuantityArrayObject*) self;
    PyObject* view = quantity_array_value_get(self, NULL);
    if (view == NULL) return NULL;
    PyObject* base_out = PyObject_Str(view);
    Py_DECREF(view);
    if (base_out == NULL) return NULL;
    std::string units = v->units->units->str();
    PyObject* out = PyUnicode_FromFormat("%U %s", base_out, units.c_str());
    Py_DECREF(base_out);
    return out;
}


static PyObject* quantity_array_repr_from_base(PyObject* self,
					       PyObject* base_out) {
    QuantityArrayObject* v = (QuantityArrayObject*) self;
    Py_ssize_t len = PyUnicode_GetLength(base_out);
    Py_ssize_t idx_paren = PyUnicode_FindChar(base_out, '(', 0, len, 1);
    std::string units = v->units->units->str();
    PyObject* out = NULL;
    if (idx_paren < 0) {
	out = PyUnicode_FromFormat("%U %s", base_out, units.c_str());
    } else {
	PyObject* base_sub = PyUnicode_Substring(base_out, idx_paren, len - 1);
	if (base_sub == NULL) {
	    return NULL;
	}
	PyObject* cls_name = PyObject_GetAttrString((PyObject*)(self->ob_type),
						    "__name__");
	if (cls_name == NULL) {
	    Py_DECREF(base_sub);
	    return NULL;
	}
	PyObject* eq = PyUnicode_FromString("=");
	if (eq == NULL) {
	    return NULL;
	}
	int ret = PySequence_Contains(base_sub, eq);
	Py_DECREF(eq);
	if (ret < 0) {
	    return NULL;
	}
	if (ret)
	    out = PyUnicode_FromFormat("%U%U, units='%s')", cls_name, base_sub, units.c_str());
	else
	    out = PyUnicode_FromFormat("%U%U, '%s')", cls_name, base_sub, units.c_str());
	Py_DECREF(cls_name);
    }
    return out;
}

static PyObject* quantity_array_repr(PyObject* self) {
    PyObject* view = PyArray_View((PyArrayObject*)self, NULL, &PyArray_Type);
    if (view == NULL) {
	return NULL;
    }
    PyObject* base_out = PyObject_Repr(view);
    Py_DECREF(view);
    if (base_out == NULL) {
	return NULL;
    }
    PyObject* out = quantity_array_repr_from_base(self, base_out);
    Py_DECREF(base_out);
    return out;
}


static PyObject* quantity_array_units_get(PyObject* self, void*) {
    QuantityArrayObject* v = (QuantityArrayObject*) self;
    UnitsObject* vu = (UnitsObject*) Units_Type.tp_alloc(&Units_Type, 0);
    if (vu == NULL)
        return NULL;
    vu->units = new Units(*(v->units->units));
    bool vEmpty = v->units->units->is_empty();
    if (!vEmpty && vu->units->is_empty()) {
	PyObject* error = Py_BuildValue("s", "Failed to parse units.");
	PyErr_SetObject(units_error, error);
	Py_XDECREF(error);
	return NULL;
    }
    
    return (PyObject*) vu;
}

static PyObject* quantity_array_get_converted_value(PyObject* self,
						    PyObject* units) {
    PyObject* unitsObject = NULL;
    if (PyObject_IsInstance(units, (PyObject*)&Units_Type)) {
	unitsObject = units;
	Py_INCREF(unitsObject);
    } else {
	PyObject* units_args = PyTuple_Pack(1, units);
	if (units_args == NULL) return NULL;
	unitsObject = PyObject_Call((PyObject*)&Units_Type, units_args, NULL);
	Py_DECREF(units_args);
    }
    if (unitsObject == NULL)
	return NULL;
    QuantityArrayObject* v = (QuantityArrayObject*) self;
    
    if (!v->units->units->is_compatible(*(((UnitsObject*)unitsObject)->units))) {
	std::string u0 = v->units->units->str();
	std::string u1 = ((UnitsObject*)unitsObject)->units->str();
	PyErr_Format(units_error, "Incompatible units: '%s' and '%s'",
		     u0.c_str(), u1.c_str());
	Py_DECREF(unitsObject);
	return NULL;
    }
    std::vector<double> factor = v->units->units->conversion_factor(*(((UnitsObject*)unitsObject)->units));
    Py_DECREF(unitsObject);
    PyObject* arr = quantity_array_value_get_copy(self, NULL);
    if (arr == NULL) {
	return NULL;
    }
    PyObject* tmp = NULL;
    if (!internal::values_eq(factor[1], 0)) {
	PyObject* offset;
	if (internal::values_eq(floor(factor[1]), factor[1]))
	    offset = PyLong_FromDouble(factor[1]);
	else
	    offset = PyFloat_FromDouble(factor[1]);
	if (offset == NULL) {
	    Py_DECREF(arr);
	    return NULL;
	}
	tmp = PyNumber_Subtract(arr, offset);
	Py_DECREF(offset);
	Py_DECREF(arr);
	if (tmp == NULL) {
	    return NULL;
	}
	arr = tmp;
    }
    if (!internal::values_eq(factor[0], 1)) {
	PyObject* scale;
	if (internal::values_eq(floor(factor[0]), factor[0]))
	    scale = PyLong_FromDouble(factor[0]);
	else
	    scale = PyFloat_FromDouble(factor[0]);
	if (scale == NULL) {
	    Py_DECREF(arr);
	    return NULL;
	}
	tmp = PyNumber_Multiply(arr, scale);
	Py_DECREF(scale);
	Py_DECREF(arr);
	if (tmp == NULL) {
	    return NULL;
	}
	arr = tmp;
    }
    return arr;
}

static int quantity_array_units_set(PyObject* self, PyObject* value, void*) {
    PyObject* unitsObject = (PyObject*)units_coerce(value);
    if (unitsObject == NULL)
	return -1;

    PyObject* arr = quantity_array_get_converted_value(self, unitsObject);
    if (arr == NULL) {
	Py_DECREF(unitsObject);
	return -1;
    }
    if (quantity_array_value_set(self, arr, NULL) < 0) {
	Py_DECREF(arr);
	Py_DECREF(unitsObject);
	return -1;
    }
    Py_DECREF(arr);
    QuantityArrayObject* v = (QuantityArrayObject*) self;
    v->units->units[0] = *(((UnitsObject*)unitsObject)->units);
    Py_DECREF(unitsObject);
    return 0;
}


static PyObject* quantity_array_value_get(PyObject* self, void*) {
    return PyArray_Return((PyArrayObject*)PyArray_View((PyArrayObject*)self, NULL, &PyArray_Type));
}


static PyObject* quantity_array_value_get_copy(PyObject* self, void*) {
    return _copy_array(self, (PyObject*)&PyArray_Type, true, true);
}


static int quantity_array_value_set(PyObject* self, PyObject* value, void*) {
    return _copy_array_into(self, value);
}


static PyObject* quantity_array_is_compatible(PyObject* self, PyObject* args, PyObject* kwargs) {
    PyObject* otherObject;
    const UnitsObject* other;
    
    if (!PyArg_ParseTuple(args, "O", &otherObject))
	return NULL;

    if (PyObject_IsInstance(otherObject, (PyObject*)&QuantityArray_Type)) {
	other = (UnitsObject*)quantity_array_units_get(otherObject, NULL);
    } else if (PyObject_IsInstance(otherObject, (PyObject*)&Units_Type)) {
	other = (UnitsObject*)otherObject;
	Py_INCREF(otherObject);
    } else {
	other = (UnitsObject*)PyObject_Call((PyObject*)&Units_Type, args, NULL);
    }
    if (other == NULL)
        return NULL;
    
    QuantityArrayObject* v = (QuantityArrayObject*) self;
    bool result = v->units->units->is_compatible(*other->units);
    Py_DECREF(other);
    if (result) {
	Py_INCREF(Py_True);
	return Py_True;
    }
    Py_INCREF(Py_False);
    return Py_False;
    
}


static PyObject* quantity_array_is_dimensionless(PyObject* self, PyObject* args) {
    QuantityArrayObject* v = (QuantityArrayObject*) self;
    bool result = v->units->units->is_dimensionless();
    if (result) {
	Py_INCREF(Py_True);
	return Py_True;
    }
    Py_INCREF(Py_False);
    return Py_False;
}


static PyObject* quantity_array_is_equivalent(PyObject* self, PyObject* args) {
    PyObject* otherObject;

    if (!PyArg_ParseTuple(args, "O", &otherObject))
	return NULL;
    
    if (!PyObject_IsInstance(otherObject, (PyObject*)&QuantityArray_Type)) {
	PyErr_SetString(PyExc_TypeError, "expected a QuantityArray instance");
	return NULL;
    }
    QuantityArrayObject* va = (QuantityArrayObject*) self;
    QuantityArrayObject* vb = (QuantityArrayObject*) otherObject;
    if (!va->units->units->is_compatible(*vb->units->units)) {
	Py_INCREF(Py_False);
	return Py_False;
    }

    PyObject* a = quantity_array_value_get(self, NULL);
    if (a == NULL) {
	return NULL;
    }
    PyObject* b = quantity_array_get_converted_value(otherObject,
						     (PyObject*)(va->units));
    if (b == NULL) {
	Py_DECREF(a);
	return NULL;
    }
    PyObject* out_arr = NULL;
    out_arr = PyObject_CallMethod(a, "__eq__", "(O)", b);
    Py_DECREF(a);
    Py_DECREF(b);
    PyObject* out = NULL;
    if (out_arr != NULL) {
	if (out_arr == Py_False || out_arr == Py_True) {
	    out = out_arr;
	} else {
	    out = PyObject_CallMethod(out_arr, "all", NULL);
	    Py_DECREF(out_arr);
	}
    }
    return out;
}


static PyObject* quantity_array_to(PyObject* self, PyObject* args) {
    PyObject* unitsObject;

    if (!PyArg_ParseTuple(args, "O", &unitsObject))
	return NULL;

    PyObject* arr = quantity_array_get_converted_value(self, unitsObject);
    if (arr == NULL) {
	return NULL;
    }
    PyObject* quantity_array_args = PyTuple_Pack(2, arr, unitsObject);
    Py_DECREF(arr);
    if (quantity_array_args == NULL) {
	return NULL;
    }
    PyObject* base_cls = (PyObject*)(self->ob_type);
    PyObject* out = PyObject_Call(base_cls, quantity_array_args, NULL);
    Py_DECREF(quantity_array_args);
    if (out == NULL)
	return NULL;

    return out;
}

static PyObject* quantity_array__array_ufunc__(PyObject* self, PyObject* args, PyObject* kwargs) {
    PyObject *ufunc, *method_name, *normal_args, *ufunc_method, *tmp, *tmp2,
	*i0, *i1, *i0_units, *i1_units, *out = NULL, *kw_key, *kw_val;
    PyObject *result = NULL, *result_type = NULL,
	*modified_args = NULL, *modified_kwargs = NULL, *modified_out = NULL;
    PyUFuncObject* ufunc_object;
    PyObject *result_units = NULL, *convert_units = NULL;
    std::string ufunc_name;
    int is_call, res;
    Py_ssize_t Nargs, kw_pos;
    bool inplace = false;

    assert(PyTuple_CheckExact(args));
    assert(kwargs == NULL || PyDict_CheckExact(kwargs));

    if (PyTuple_GET_SIZE(args) < 2) {
	PyErr_SetString(PyExc_TypeError,
			"__array_ufunc__ requires at least 2 arguments");
	return NULL;
    }
    normal_args = PyTuple_GetSlice(args, 2, PyTuple_GET_SIZE(args));
    if (normal_args == NULL) {
	return NULL;
    }
    
    ufunc = PyTuple_GET_ITEM(args, 0);
    method_name = PyTuple_GET_ITEM(args, 1);
    if (ufunc == NULL || method_name == NULL) {
	goto cleanup;
    }
    ufunc_object = (PyUFuncObject*)ufunc;
    ufunc_name.insert(0, ufunc_object->name);
    tmp = PyUnicode_FromString("__call__");
    is_call = PyObject_RichCompareBool(method_name, tmp, Py_EQ);
    Py_DECREF(tmp);
    if (is_call < 0) {
	goto cleanup;
    } else if (!is_call) {
	PyErr_SetString(units_error,
			    "Only the __call__ ufunc method is currently supported by rapidjson.units.QuantityArray");
	goto cleanup;
    }
    if (kwargs != NULL) {
	out = PyDict_GetItemString(kwargs, "out");
    }
    if (out != NULL && PyTuple_Check(out)) {
	modified_out = quantity_array_numpy_tuple(out, true);
	if (modified_out == NULL) {
	    goto cleanup;
	}
	if (PyTuple_Size(out) == 1) {
	    i0 = PyTuple_GET_ITEM(out, 0);
	    if (i0 == NULL) {
		goto cleanup;
	    }
	    result_type = PyObject_Type(i0);
	    Py_DECREF(i0);
	    i0 = NULL;
	    if (result_type == NULL) {
		goto cleanup;
	    }
	}
    }
    Nargs = PyTuple_GET_SIZE(normal_args);
    if (Nargs > 0) {
	i0 = PyTuple_GET_ITEM(normal_args, 0);
	if (i0 == NULL) {
	    goto cleanup;
	}
	if (out != NULL) {
	    inplace = true;
	}
	if (inplace && !PyObject_IsInstance(i0, (PyObject*)&QuantityArray_Type)) {
	    PyErr_Format(units_error,
			 "Inplace '%s' operation not supported by rapidjson.units.QuantityArray", ufunc_name.c_str());
	    goto cleanup;
	}
    }
    // std::cerr << "__array_ufunc__: " << ufunc_name << ", " << Nargs << ", inplace = " << inplace << std::endl;
    if (Nargs == 1) { // unary operators
	if (ufunc_name == "isfinite" ||
	    ufunc_name == "isinf" ||
	    ufunc_name == "isnan" ||
	    ufunc_name == "isnat" ||
	    ufunc_name == "sign" ||
	    ufunc_name == "signbit") {
	    // Strip units
	} else if (ufunc_name == "negative" ||
		   ufunc_name == "positive" ||
		   ufunc_name == "absolute" ||
		   ufunc_name == "fabs" ||
		   ufunc_name == "rint" ||
		   ufunc_name == "floor" ||
		   ufunc_name == "ceil" ||
		   ufunc_name == "trunc") {
	    if (_has_units(i0)) {
		result_units = _get_units(i0);
		if (result_units == NULL) {
		    goto cleanup;
		}
	    }
	} else if (ufunc_name == "sqrt" ||
		   ufunc_name == "square" ||
		   ufunc_name == "cbrt" ||
		   ufunc_name == "reciprocal") {
	    double power = 0;
	    if (ufunc_name == "sqrt")
		power = 0.5;
	    else if (ufunc_name == "square")
		power = 2.0;
	    else if (ufunc_name == "cbrt")
		power = 1.0 / 3.0;
	    else if (ufunc_name == "reciprocal")
		power = -1.0;
	    if (_has_units(i0)) {
		i0_units = _get_units(i0);
		if (i0_units == NULL) {
		    goto cleanup;
		}
		tmp = PyFloat_FromDouble(power);
		if (tmp == NULL) {
		    Py_DECREF(i0_units);
		    goto cleanup;
		}
		result_units = PyNumber_Power(i0_units, tmp, Py_None);
		Py_DECREF(i0_units);
		Py_DECREF(tmp);
		if (result_units == NULL) {
		    goto cleanup;
		}
	    }
	} else if (ufunc_name == "sin" ||
		   ufunc_name == "cos" ||
		   ufunc_name == "tan" ||
		   ufunc_name == "sinh" ||
		   ufunc_name == "cosh" ||
		   ufunc_name == "tanh") {
	    if (_has_units(i0)) {
		tmp2 = _get_units(i0);
		if (((UnitsObject*)tmp2)->units->is_null()) {
		    Py_DECREF(tmp2);
		    convert_units = get_empty_units();
		} else {
		    Py_DECREF(tmp2);
		    tmp = PyUnicode_FromString("radians");
		    if (tmp == NULL) {
			goto cleanup;
		    }
		    convert_units = (PyObject*)units_coerce(tmp);
		    Py_DECREF(tmp);
		}
		tmp2 = NULL;
		if (convert_units == NULL) {
		    goto cleanup;
		}
		result_units = get_empty_units();
		if (result_units == NULL) {
		    goto cleanup;
		}
	    }
	} else if (ufunc_name == "arcsin" ||
		   ufunc_name == "arccos" ||
		   ufunc_name == "arctan" ||
		   ufunc_name == "arcsinh" ||
		   ufunc_name == "arccosh" ||
		   ufunc_name == "arctanh") {
	    if (_has_units(i0)) {
		tmp = PyUnicode_FromString("radians");
		if (tmp == NULL) {
		    goto cleanup;
		}
		result_units = (PyObject*)units_coerce(tmp);
		Py_DECREF(tmp);
		if (result_units == NULL) {
		    goto cleanup;
		}
		convert_units = get_empty_units();
		if (convert_units == NULL) {
		    goto cleanup;
		}
	    }
	} else if (ufunc_name == "degrees" ||
		   ufunc_name == "rad2deg") {
	    if (_has_units(i0)) {
		tmp = PyUnicode_FromString("radians");
		if (tmp == NULL) {
		    goto cleanup;
		}
		convert_units = (PyObject*)units_coerce(tmp);
		Py_DECREF(tmp);
		if (convert_units == NULL) {
		    goto cleanup;
		}
		tmp = PyUnicode_FromString("degrees");
		if (tmp == NULL) {
		    goto cleanup;
		}
		result_units = (PyObject*)units_coerce(tmp);
		Py_DECREF(tmp);
		if (result_units == NULL) {
		    goto cleanup;
		}
	    }
	} else if (ufunc_name == "radians" ||
		   ufunc_name == "deg2rad") {
	    if (_has_units(i0)) {
		tmp = PyUnicode_FromString("degrees");
		if (tmp == NULL) {
		    goto cleanup;
		}
		convert_units = (PyObject*)units_coerce(tmp);
		Py_DECREF(tmp);
		if (convert_units == NULL) {
		    goto cleanup;
		}
		tmp = PyUnicode_FromString("radians");
		if (tmp == NULL) {
		    goto cleanup;
		}
		result_units = (PyObject*)units_coerce(tmp);
		Py_DECREF(tmp);
		if (result_units == NULL) {
		    goto cleanup;
		}
	    }
	} else {
	    PyErr_Format(units_error,
			 "Unary operator '%s' not currently supported by rapidjson.units.QuantityArray.", ufunc_name.c_str());
	    goto cleanup;
	}
    } else if (Nargs == 2) { // binary operators
	i1 = PyTuple_GET_ITEM(normal_args, 1);
	if (i1 == NULL) {
	    goto cleanup;
	}
	if (ufunc_name == "copysign") {
	    // Strip units
	} else if (ufunc_name == "equal") {
	    res = _compare_units(i0, i1, true, true);
	    if (res < 0) {
		goto cleanup;
	    } else if (res == 1) {
		if (_compare_units(i0, i1, false, true) == 0) {
		    convert_units = _get_units(i0);
		    if (convert_units == NULL) {
			goto cleanup;
		    }
		}
	    } else {
		if (PyArray_CheckScalar(i0) && PyArray_CheckScalar(i1)) {
		    Py_INCREF(Py_False);
		    result = Py_False;
		} else if (PyObject_IsInstance(i0, (PyObject*)&PyArray_Type) &&
			   PyObject_IsInstance(i1, (PyObject*)&PyArray_Type) &&
			   PyArray_SAMESHAPE((PyArrayObject*)i0,
					     (PyArrayObject*)i1)) {
		    result = PyArray_ZEROS(PyArray_NDIM((PyArrayObject*)i0),
					   PyArray_DIMS((PyArrayObject*)i0),
					   NPY_BOOL, 0);
		    if (result == NULL) {
			goto cleanup;
		    }
		}
	    }
	} else if (ufunc_name == "not_equal") {
	    res = _compare_units(i0, i1, true, true);
	    if (res < 0) {
		goto cleanup;
	    } else if (res == 1) {
		convert_units = _get_units(i0);
		if (convert_units == NULL) {
		    goto cleanup;
		}
	    } else {
		if (PyArray_CheckScalar(i0) && PyArray_CheckScalar(i1)) {
		    Py_INCREF(Py_True);
		    result = Py_True;
		} else if (PyObject_IsInstance(i0, (PyObject*)&PyArray_Type) &&
			   PyObject_IsInstance(i1, (PyObject*)&PyArray_Type) &&
			   PyArray_SAMESHAPE((PyArrayObject*)i0,
					     (PyArrayObject*)i1)) {
		    tmp = PyArray_ZEROS(PyArray_NDIM((PyArrayObject*)i0),
					PyArray_DIMS((PyArrayObject*)i0),
					NPY_BOOL, 0);
		    if (tmp == NULL) {
			goto cleanup;
		    }
		    tmp2 = PyLong_FromLong(1);
		    result = PyNumber_InPlaceAdd(tmp, tmp2);
		    Py_DECREF(tmp);
		    Py_DECREF(tmp2);
		    if (result == NULL) {
			goto cleanup;
		    }
		}
	    }
	} else if (ufunc_name == "greater" ||
		   ufunc_name == "greater_equal" ||
		   ufunc_name == "less" ||
		   ufunc_name == "less_equal" ||
		   ufunc_name == "hypot") {
	    // Require components have the same units
	    convert_units = _get_units(i0);
	    if (convert_units == NULL) {
		goto cleanup;
	    }
	} else if (ufunc_name == "add" ||
		   ufunc_name == "subtract" ||
		   ufunc_name == "maximum" ||
		   ufunc_name == "minimum" ||
		   ufunc_name == "fmax" ||
		   ufunc_name == "fmin") {
	    // Require components and result have the same units
	    result_units = _get_units(i0);
	    if (result_units == NULL) {
		goto cleanup;
	    }
	    convert_units = result_units;
	    Py_INCREF(result_units);
	} else if (ufunc_name == "multiply" ||
		   ufunc_name == "matmul" ||
		   ufunc_name == "divide" ||
		   ufunc_name == "true_divide" ||
		   ufunc_name == "floor_divide") {
	    i0_units = _get_units(i0);
	    if (i0_units == NULL) {
		goto cleanup;
	    }
	    if (!_has_units(i1)) {
		result_units = i0_units;
	    } else {
		i1_units = _get_units(i1);
		if (i1_units == NULL) {
		    Py_DECREF(i0_units);
		    goto cleanup;
		}
		if (ufunc_name.size() >= 6 &&
		    ufunc_name.substr(ufunc_name.size() - 6) == "divide") {
		    result_units = PyNumber_TrueDivide(i0_units, i1_units);
		} else {
		    result_units = PyNumber_Multiply(i0_units, i1_units);
		}
		Py_DECREF(i1_units);
		Py_DECREF(i0_units);
	    }
	    if (result_units == NULL) {
		goto cleanup;
	    }
	} else if (ufunc_name == "power" ||
		   ufunc_name == "float_power") {
	    if (_has_units(i1)) {
		PyErr_Format(units_error,
			     "Raise to a power with units not supported.");
		goto cleanup;
	    }
	    if (_has_units(i0)) {
		i0_units = _get_units(i0);
		if (i0_units == NULL) {
		    goto cleanup;
		}
		if (PyArray_Check(i1)) {
		    // TODO: Change to array of quantities with different units?
		    PyErr_Format(units_error,
				 "Cannot raise QuantityArray to heterogeneous"
				 " array of powers.");
		    Py_DECREF(i0_units);
		    goto cleanup;
		}
		result_units = PyNumber_Power(i0_units, i1, Py_None);
		Py_DECREF(i0_units);
		if (result_units == NULL) {
		    goto cleanup;
		}
	    }
	} else if (ufunc_name == "remainder" ||
		   ufunc_name == "mod" ||
		   ufunc_name == "fmod") {
	    if (_has_units(i0)) {
		result_units = _get_units(i0);
		if (result_units == NULL) {
		    goto cleanup;
		}
		if (_has_units(i1)) {
		    Py_INCREF(result_units);
		    convert_units = result_units;
		}
	    } else {
		convert_units = _get_units(i0);
		if (convert_units == NULL) {
		    goto cleanup;
		}
	    }
	} else if (ufunc_name == "arctan2") {
	    convert_units = _get_units(i0);
	    if (convert_units == NULL) {
		goto cleanup;
	    }
	    tmp = PyUnicode_FromString("radians");
	    if (tmp == NULL) {
		goto cleanup;
	    }
	    result_units = (PyObject*)units_coerce(tmp);
	    Py_DECREF(tmp);
	    if (result_units == NULL) {
		goto cleanup;
	    }
	} else {
	    PyErr_Format(units_error,
			 "Binary operator '%s' not currently supported by rapidjson.units.QuantityArray.", ufunc_name.c_str());
	    goto cleanup;
	}
    } else {
	PyErr_Format(units_error,
		     "Operator '%s' not currently supported by rapidjson.units.QuantityArray.", ufunc_name.c_str());
	goto cleanup;
    }
    if (result == NULL) {
	if (modified_args == NULL) {
	    modified_args = quantity_array_numpy_tuple(normal_args, false, convert_units);
	    if (modified_args == NULL) {
		goto cleanup;
	    }
	}
	if (modified_kwargs == NULL && kwargs != NULL) {
	    if (modified_out == NULL) {
		Py_INCREF(kwargs);
		modified_kwargs = kwargs;
	    } else {
		modified_kwargs = PyDict_New();
		if (modified_kwargs == NULL) {
		    goto cleanup;
		}
		kw_pos = 0;
		tmp = PyUnicode_FromString("out");
		while (PyDict_Next(kwargs, &kw_pos, &kw_key, &kw_val)) {
		    if (PyObject_RichCompareBool(kw_key, tmp, Py_EQ)) {
			if (PyDict_SetItem(modified_kwargs, kw_key, modified_out) < 0) {
			    Py_DECREF(tmp);
			    goto cleanup;
			}
		    } else {
			if (PyDict_SetItem(modified_kwargs, kw_key, kw_val) < 0) {
			    Py_DECREF(tmp);
			    goto cleanup;
			}
		    }
		}
		Py_DECREF(tmp);
	    }
	}
	ufunc_method = PyObject_GetAttr(ufunc, method_name);
	if (ufunc_method == NULL) {
	    goto cleanup;
	}
	result = PyObject_Call(ufunc_method, modified_args, modified_kwargs);
	Py_DECREF(ufunc_method);
    }
    if (result != NULL && result_units != NULL) {
	if (result_type == NULL) {
	    result_type = (PyObject*)(self->ob_type);
	    Py_INCREF(result_type);
	}
	tmp = PyTuple_Pack(2, result, result_units);
	Py_DECREF(result);
	if (tmp == NULL) {
	    result = NULL;
	    goto cleanup;
	}
	result = PyObject_Call(result_type, tmp, NULL);
	Py_DECREF(tmp);
    }
cleanup:
    Py_DECREF(normal_args);
    Py_XDECREF(result_type);
    Py_XDECREF(result_units);
    Py_XDECREF(convert_units);
    Py_XDECREF(modified_out);
    Py_XDECREF(modified_args);
    Py_XDECREF(modified_kwargs);
    return result;
}

static PyObject* quantity_array__array_finalize__(PyObject* self, PyObject* args) {
    PyObject *attr = NULL;
    PyObject *parent = NULL;
    if (!PyArg_ParseTuple(args, "O", &parent)) {
	return NULL;
    }
    if (parent != NULL) {
	if (PyObject_HasAttrString(parent, "units")) {
	    attr = PyObject_GetAttrString(parent, "units");
	    if (attr == NULL) {
		return NULL;
	    }
	} else {
	    // parent has no 'units' so we make a new empty one
	    attr = get_empty_units();
	    if (attr == NULL) {
		return NULL;
	    }
	}
    } else {
	attr = get_empty_units();
    }
    
    ((QuantityArrayObject*)self)->units = (UnitsObject*)attr;
    Py_INCREF(Py_None);
    return Py_None;
}


static PyObject* quantity_array__array_wrap__(PyObject* self, PyObject* args) {
    PyObject *array = NULL, *context = NULL;
    if (!PyArg_ParseTuple(args, "OO", array, context)) {
	return NULL;
    }
    Py_INCREF(array);
    return array;
}

static PyObject* quantity_array__array_function__(PyObject* self, PyObject* c_args, PyObject* c_kwds) {
    PyObject *func, *func_name, *types, *args, *kwargs, *alt_c_args, *tmp;
    PyObject* alt_args = NULL;
    PyObject *i0, *i1;
    int res;
    Py_ssize_t Nargs = 0, i = 0;
    PyObject *result = NULL, *result_units = NULL, *convert_units = NULL,
	*result_type = NULL, *result_units_list = NULL;
    std::string func_nameS;
    static char const* kwlist[] = {"func", "types", "args", "kwargs", NULL};

    if (!PyArg_ParseTupleAndKeywords(
	    c_args, c_kwds, "OOOO:__array_function__", (char**) kwlist,
	    &func, &types, &args, &kwargs)) {
	return NULL;
    }
    
    func_name = PyObject_GetAttrString(func, "__name__");
    if (func_name == NULL) return NULL;
    func_nameS.insert(0, PyUnicode_AsUTF8(func_name));
    Py_DECREF(func_name);
    Nargs = PyTuple_Size(args);
    // std::cerr << "__array_function__: " << func_nameS << std::endl;
    if (func_nameS == "concatenate" ||
	func_nameS == "hstack" ||
	func_nameS == "vstack") {
	i1 = PyTuple_GetItem(args, 0);
	if (i1 == NULL) {
	    goto cleanup;
	}
	i0 = PySequence_GetItem(i1, 0);
	if (i0 == NULL) {
	    goto cleanup;
	}
	result_units = _get_units(i0);
	Py_DECREF(i0);
	if (result_units == NULL) {
	    goto cleanup;
	}
	// Py_INCREF(result_units);
	tmp = quantity_array_numpy_tuple(i1, false, result_units);
	if (tmp == NULL)
	    goto cleanup;
	alt_args = PyTuple_Pack(1, tmp);
	Py_DECREF(tmp);
	if (alt_args == NULL)
	    goto cleanup;
    } else if (func_nameS == "atleast_1d") {
	// Units for each argument
	if (Nargs == 1) {
	    i0 = PyTuple_GetItem(args, 0);
	    if (i0 == NULL) {
		goto cleanup;
	    }
	    result_units = _get_units(i0);
	    if (result_units == NULL) {
		goto cleanup;
	    }
	} else {
	    result_units_list = PyList_New(Nargs);
	    if (result_units_list == NULL)
		goto cleanup;
	    for (i = 0; i < Nargs; i++) {
		i0 = PyTuple_GetItem(args, i);
		if (i0 == NULL) {
		    goto cleanup;
		}
		result_units = _get_units(i0);
		if (result_units == NULL) {
		    goto cleanup;
		}
		if (PyList_SetItem(result_units_list, i, result_units) < 0)
		    goto cleanup;
		result_units = NULL;
	    }
	}
    } else if (func_nameS == "array_equal" ||
	       func_nameS == "array_equiv" ||
	       func_nameS == "allclose") {
	res = _compare_units_tuple(args, true, true, &convert_units);
	if (res < 0) {
	    goto cleanup;
	} else if (res != 1) {
	    Py_INCREF(Py_False);
	    result = Py_False;
	    goto cleanup;
	}
    } else if (func_nameS == "isclose") {
	res = _compare_units_tuple(args, true, true, &convert_units);
	if (res < 0) {
	    goto cleanup;
	} else if (res != 1) {
	    i0 = PyTuple_GetItem(args, 0);
	    i1 = PyTuple_GetItem(args, 1);
	    if (i0 == NULL || i1 == NULL) {
		goto cleanup;
	    }
	    if (PyArray_CheckScalar(i0) && PyArray_CheckScalar(i1)) {
		Py_INCREF(Py_False);
		result = Py_False;
		goto cleanup;
	    } else if (PyObject_IsInstance(i0, (PyObject*)&PyArray_Type) &&
		       PyObject_IsInstance(i1, (PyObject*)&PyArray_Type) &&
		       PyArray_SAMESHAPE((PyArrayObject*)i0,
					 (PyArrayObject*)i1)) {
		result = PyArray_ZEROS(PyArray_NDIM((PyArrayObject*)i0),
				       PyArray_DIMS((PyArrayObject*)i0),
				       NPY_BOOL, 0);
		goto cleanup;
	    }
	    // fallback to numpy for error if shapes mismatch
	}
    } else if (func_nameS == "array_repr") {
	// No units
    } else {
	    PyErr_Format(units_error,
			 "Array function '%s' not supported by rapidjson.units.QuantityArray", func_nameS.c_str());
	    goto cleanup;
    }
    if (result == NULL) {
	if (alt_args == NULL) {
	    alt_args = quantity_array_numpy_tuple(args, false, convert_units);
	    if (alt_args == NULL) {
		goto cleanup;
	    }
	}
	alt_c_args = PyTuple_Pack(4, func, types, alt_args, kwargs);
	if (alt_c_args == NULL) {
	    goto cleanup;
	}
	CALL_BASE_METHOD_ARGS_KWARGS(__array_function__, result,
				     alt_c_args, c_kwds);
	Py_DECREF(alt_c_args);
    }
    if (result != NULL && result_units != NULL) {
	PyObject* result_args = PyTuple_Pack(2, result, result_units);
	Py_DECREF(result);
	if (result_args == NULL) {
	    result = NULL;
	    goto cleanup;
	}
	// TODO: Determine out type to allow subclassing
	result_type = (PyObject*)(self->ob_type);
	Py_INCREF(result_type);
	result = PyObject_Call(result_type, result_args, NULL);
	Py_DECREF(result_args);
    } else if (result != NULL && result_units_list != NULL) {
	if (!PyList_Check(result) || (PyList_Size(result_units_list) != PyList_Size(result))) {
	    Py_DECREF(result);
	    result = NULL;
	    goto cleanup;
	}
	for (i = 0; i < PyList_Size(result_units_list); i++) {
	    PyObject* iresult = PyList_GetItem(result, i);
	    if (iresult == NULL) {
		Py_DECREF(result);
		result = NULL;
		goto cleanup;
	    }
	    i0 = PyTuple_GetItem(args, i);
	    if (i0 == NULL) {
		Py_DECREF(result);
		result = NULL;
		goto cleanup;
	    }
	    result_type = (PyObject*)(i0->ob_type);
	    if (result_type != (PyObject*)(&QuantityArray_Type)) {
		continue;
	    }
	    Py_INCREF(result_type);
	    PyObject* iresult_units = PyList_GetItem(result_units_list, i);
	    if (iresult_units == NULL) {
		Py_DECREF(result);
		result = NULL;
		goto cleanup;
	    }
	    PyObject* result_args = PyTuple_Pack(2, iresult, iresult_units);
	    if (result_args == NULL) {
		Py_DECREF(result);
		result = NULL;
		goto cleanup;
	    }
	    iresult = PyObject_Call(result_type, result_args, NULL);
	    Py_DECREF(result_args);
	    Py_DECREF(result_type);
	    result_type = NULL;
	    if (iresult == NULL) {
		Py_DECREF(result);
		result = NULL;
		goto cleanup;
	    }
	    if (PyList_SetItem(result, i, iresult) < 0) {
		Py_DECREF(result);
		result = NULL;
		goto cleanup;
	    }
	}
    }
    if (result != NULL && func_nameS == "array_repr") {
	i0 = PyTuple_GetItem(args, 0);
	if (i0 == NULL) {
	    goto cleanup;
	}
	tmp = quantity_array_repr_from_base(i0, result);
	Py_DECREF(result);
	result = tmp;
    }
cleanup:
    Py_XDECREF(result_type);
    Py_XDECREF(result_units);
    Py_XDECREF(result_units_list);
    Py_XDECREF(convert_units);
    Py_XDECREF(alt_args);
    return result;
}

static PyObject* quantity_array__format__(PyObject* self, PyObject* args) {
    PyObject* view = quantity_array_value_get(self, NULL);
    if (view == NULL) {
	return NULL;
    }
    PyObject* base_out = PyObject_CallMethod(view, "__format__", "O", args);
    Py_DECREF(view);
    if (base_out == NULL) {
	return NULL;
    }
    std::string units = ((QuantityArrayObject*)self)->units->units->str();
    PyObject* out = PyUnicode_FromFormat("%U %s", base_out, units.c_str());
    Py_DECREF(base_out);
    return out;
}

static PyObject* quantity_array_subscript(PyObject* self, PyObject* key) {
    PyObject* out = NULL;
    CALL_BASE_METHOD(__getitem__, out, key)
    if (out == NULL || !PyObject_HasAttrString(out, "shape")) {
	return out;
    }
    PyObject* shape = PyObject_GetAttrString(out, "shape");
    if (shape == NULL) {
	Py_DECREF(out);
	return NULL;
    }
    Py_ssize_t ndim = PyTuple_Size(shape);
    Py_DECREF(shape);
    if (ndim != 0) {
	return out;
    }
    PyObject* units = quantity_array_units_get(self, NULL);
    if (units == NULL) {
	Py_DECREF(out);
	return NULL;
    }
    if (((UnitsObject*)units)->units->is_dimensionless() &&
	!((UnitsObject*)units)->units->has_factor()) {
	return out;
    }
    PyObject* args = PyTuple_Pack(2, out, units);
    Py_DECREF(out);
    Py_DECREF(units);
    PyObject* qout = PyObject_Call((PyObject*)&Quantity_Type, args, NULL);
    Py_DECREF(args);
    return qout;
}


static int quantity_array_ass_subscript(PyObject* self, PyObject* key, PyObject* val) {
    PyObject* mod_val = _convert_units(val, (PyObject*)(((QuantityArrayObject*)self)->units), true);
    PyObject* out_val = NULL;
    int out = 0;
    CALL_BASE_METHOD(__setitem__, out_val, key, mod_val);
    Py_DECREF(mod_val);
    if (out_val == NULL) {
	out = -1;
    }
    return out;
}
static PyObject* quantity_array__reduce__(PyObject* self, PyObject*, PyObject*) {
    PyObject* np_out = NULL;
    CALL_BASE_METHOD_NOARGS(__reduce__, np_out);
    if (np_out == NULL)
	return NULL;
    PyObject* state = PyTuple_GetItem(np_out, 2);
    if (state == NULL) {
	Py_DECREF(np_out);
	return NULL;
    }
    PyObject* unitsStr = units_str((PyObject*)(((QuantityArrayObject*)(self))->units));
    if (unitsStr == NULL) {
	Py_DECREF(np_out);
	return NULL;
    }
    PyObject* new_state = PyTuple_Pack(2, state, unitsStr);
    Py_DECREF(unitsStr);
    if (new_state == NULL) {
	Py_DECREF(np_out);
	return NULL;
    }
    if (PyTuple_SetItem(np_out, 2, new_state) < 0) {
	Py_DECREF(np_out);
	return NULL;
    }
    return np_out;
}
static PyObject* quantity_array__setstate__(PyObject* self, PyObject* state) {
    if (!PyTuple_Check(state) || PyTuple_Size(state) != 2) {
	PyErr_SetString(PyExc_TypeError, "State must be a size 2 tuple");
	return NULL;
    }
    PyObject* np_state = PyTuple_GetItem(state, 0);
    if (np_state == NULL)
	return NULL;
    PyObject* result = NULL;
    CALL_BASE_METHOD(__setstate__, result, np_state);
    if (result == NULL)
	return NULL;
    PyObject* units = PyTuple_GetItem(state, 1);
    if (units == NULL)
	return NULL;
    PyObject* units_type = PyObject_Type(units);
    if (units_type == NULL)
	return NULL;
    PyObject* units_type_str = PyObject_Str(units_type);
    if (units_type_str == NULL)
	return NULL;
    if (PyUnicode_Check(units)) {
	QuantityArrayObject* v = (QuantityArrayObject*) self;
	v->units->units[0] = Units(PyUnicode_AsUTF8(units));
    } else {
	PyErr_SetString(PyExc_TypeError, "Units in state are invalid");
	return NULL;
    }
    Py_INCREF(Py_None);
    return Py_None;
}


//////////////////////
// Quantity Methods //
//////////////////////

static PyObject* quantity_new(PyTypeObject* type, PyObject* args, PyObject* kwargs)
{
    return quantity_array_new(type, args, kwargs);
}

///////////////
// Utilities //
///////////////

static PyObject* _get_units(PyObject* x,
			    bool dont_allow_empty, bool force_copy) {
    PyObject* out = NULL;
    if (PyObject_IsInstance(x, (PyObject*)&QuantityArray_Type)) {
	if (force_copy) {
	    out = get_empty_units((PyObject*)(((QuantityArrayObject*)x)->units));
	    if (out == NULL) return NULL;
	} else {
	    out = (PyObject*)(((QuantityArrayObject*)x)->units);
	    Py_INCREF(out);
	}
    } else if (PyObject_IsInstance(x, (PyObject*)&Units_Type)) {
	if (force_copy) {
	    out = get_empty_units(x);
	    if (out == NULL) return NULL;
	} else {
	    out = (PyObject*)x;
	    Py_INCREF(out);
	}
    } else if (PyObject_HasAttrString(x, "units")) {
	PyObject* units_raw = PyObject_GetAttrString(x, "units");
	out = get_empty_units(units_raw);
	Py_DECREF(units_raw);
	if (out == NULL) return NULL;
    } else if (!dont_allow_empty) {
	out = get_empty_units();
	if (out == NULL) return NULL;
    }
    return out;
}


static int _has_units(PyObject* x) {
    return (int)(PyObject_IsInstance(x, (PyObject*)&Quantity_Type) ||
		 PyObject_IsInstance(x, (PyObject*)&QuantityArray_Type) ||
		 PyObject_IsInstance(x, (PyObject*)&Units_Type) ||
		 PyObject_HasAttrString(x, "units"));
}


static PyObject* _convert_units(PyObject* x, PyObject* units,
				bool stripUnits) {
    PyObject* out = NULL;
    // if (PyObject_IsInstance(x, (PyObject*)&Quantity_Type)) {
    // 	PyObject* args = PyTuple_Pack(1, units);
    // 	if (args == NULL) {
    // 	    return NULL;
    // 	}
    // 	out = quantity_to(x, args);
    // 	Py_DECREF(args);
    // 	if (out != NULL && stripUnits) {
    // 	    PyObject* tmp = out;
    // 	    out = quantity_value_get(tmp, NULL);
    // 	    Py_DECREF(tmp);
    // 	}
    // } else
    if (PyObject_IsInstance(x, (PyObject*)&QuantityArray_Type)) {
	if (stripUnits) {
	    out = quantity_array_get_converted_value(x, units);
	} else {
	    PyObject* args = PyTuple_Pack(1, units);
	    if (args == NULL) {
		return NULL;
	    }
	    out = quantity_array_to(x, args);
	    Py_DECREF(args);
	}
    } else if (PyObject_HasAttrString(x, "units")) {
	PyErr_SetString(units_error, "Unknown unit type");
	return NULL;
    } else {
	Py_INCREF(x);
	out = x;
    }
    return out;
}


static int _compare_units(PyObject* x0, PyObject* x1, bool allowCompat,
			  bool dimensionlessCompat) {
    UnitsObject *x0_units = NULL, *x1_units = NULL;
    if (x0 != NULL && _has_units(x0)) {
	x0_units = (UnitsObject*)_get_units(x0);
	if (x0_units == NULL) return -1;
    }
    if (x1 != NULL && _has_units(x1)) {
	x1_units = (UnitsObject*)_get_units(x1);
	if (x1_units == NULL) {
	    Py_DECREF(x0_units);
	    return -1;
	}
    }
    int out = 0;
    if (x0_units != NULL && x1_units != NULL) {
	if (allowCompat) {
	    out = (int)(x0_units->units->is_compatible(*(x1_units->units)));
	} else {
	    out = (int)(*(x0_units->units) == *(x1_units->units));
	}
    } else if ((x0_units == NULL && x1_units == NULL) ||
	       dimensionlessCompat) {
	out = 1;
    } else if (x0_units != NULL && x1_units == NULL) {
	
	out = (int)(x0_units->units->is_null() && !x0_units->units->has_factor());
    } else if (x0_units == NULL && x1_units != NULL) {
	out = (int)(x1_units->units->is_null() && !x1_units->units->has_factor());
    }
    Py_XDECREF(x0_units);
    Py_XDECREF(x1_units);
    return out;
}


static int _compare_units_tuple(PyObject* x, bool allowCompat,
				bool dimensionlessCompat,
				PyObject** out_units) {
    UnitsObject* units = NULL;
    PyObject* item = NULL;
    int res;
    if (out_units != NULL) out_units[0] = NULL;
    for (Py_ssize_t i = 0; i < PyTuple_Size(x); i++) {
	item = PyTuple_GetItem(x, i);
	if (item == NULL) return -1;
	if (i == 0 && _has_units(item)) {
	    units = (UnitsObject*)_get_units(item);
	}
	res = _compare_units((PyObject*)units, item, allowCompat,
			     dimensionlessCompat);
	if (res < 0) {
	    Py_XDECREF(units);
	    return -1;
	} else if (res == 0) {
	    Py_XDECREF(units);
	    return 0;
	}
    }
    if (out_units != NULL && units != NULL) {
	out_units[0] = (PyObject*)units;
	Py_INCREF(units);
    }
    Py_XDECREF(units);
    return 1;
}


static PyObject* _get_array(PyObject* item) {
    PyObject *arr = NULL, *scalar = NULL;
    PyArray_Descr *dtype = NULL;
    void* scalar_data = NULL;
    long il = 0;
    long long ill = 0;
    double d = 0;
    int overflow = 0;
    int req = NPY_ARRAY_C_CONTIGUOUS | NPY_ARRAY_ENSUREARRAY | NPY_ARRAY_ALIGNED;
    int isScalar = (int)(PyArray_CheckScalar(item) && !PyObject_IsInstance(item, (PyObject*)&PyArray_Type));
    if (isScalar || PyFloat_Check(item) || PyLong_Check(item)) {
	if (isScalar) {
	    dtype = PyArray_DescrFromScalar(item);
	    if (dtype == NULL) {
		goto fail;
	    }
	    Py_INCREF(item);
	    scalar = item;
	} else {
	    if (PyFloat_Check(item)) {
		d = PyFloat_AsDouble(item);
		dtype = PyArray_DescrFromType(NPY_DOUBLE);
		if (dtype == NULL) {
		    goto fail;
		}
		scalar_data = (void*)&d;
	    } else if (PyLong_Check(item)) {
		il = PyLong_AsLongAndOverflow(item, &overflow);
		if (il == -1) {
		    if (overflow != 0 && !PyErr_Occurred()) {
			ill = PyLong_AsLongLongAndOverflow(item, &overflow);
			if (ill == -1) {
			    goto fail;
			} else if (sizeof(long long) == sizeof(int32_t)) {
			    dtype = PyArray_DescrFromType(NPY_INT32);
			    scalar_data = (void*)&ill;
			} else if (sizeof(long long) == sizeof(int64_t)) {
			    dtype = PyArray_DescrFromType(NPY_INT64);
			    scalar_data = (void*)&ill;
			}
		    } else {
			goto fail;
		    }
		} else if (sizeof(long) == sizeof(int32_t)) {
		    dtype = PyArray_DescrFromType(NPY_INT32);
		    scalar_data = (void*)&il;
		} else if (sizeof(long) == sizeof(int64_t)) {
		    dtype = PyArray_DescrFromType(NPY_INT64);
		    scalar_data = (void*)&il;
		}
	    }
	    if (dtype == NULL || scalar_data == NULL) {
		Py_XDECREF(dtype);
		goto fail;
	    }
	    Py_INCREF(dtype);
	    scalar = PyArray_Scalar(scalar_data, dtype, NULL);
	}
	if (scalar == NULL) {
	    Py_DECREF(dtype);
	    goto fail;
	}
	arr = PyArray_FromScalar(scalar, dtype);
	if (arr == NULL) {
	    goto fail;
	}
    } else {
	arr = PyArray_FromAny(item, NULL, 0, 0, req, NULL);
	if (arr == item)
	    Py_INCREF(item);
	if (arr == NULL) {
	    goto fail;
	}
    }

    if (!PyArray_Check(arr)) {
	goto fail;
    }
    return arr;
fail:
    Py_XDECREF(arr);
    return NULL;
}

static int _copy_array_into(PyObject* dst, PyObject* src, bool copyFlags) {
    PyObject *arr = NULL;
    PyArrayObject* arr_cast = NULL;
    PyArray_Descr *dtype = NULL;
    int ndim = 0, flags = NPY_ARRAY_DEFAULT, old_flags = 0, nbytes = 1;
    npy_intp *dims = NULL, *strides = NULL;
    PyArrayObject_fields* fa = NULL;
    char* data = NULL;
    arr = _get_array(src);
    if (arr == NULL) {
	goto fail;
    }
    // Rebuild array with new parameters based on
    // numpy/core/src/multiarray/ctors.c::PyArray_NewFromDescr_int
    fa = (PyArrayObject_fields *)dst;
    old_flags = fa->flags;
    if (PyArray_CheckScalar(arr)) {
	dtype = PyArray_DescrNew(PyArray_DESCR((PyArrayObject*)arr));
	if (dtype == NULL) {
	    goto fail;
	}
    } else {
	arr_cast = (PyArrayObject*)arr;
	dtype = PyArray_DescrNew(PyArray_DESCR(arr_cast));
	if (dtype == NULL) {
	    goto fail;
	}
	ndim = PyArray_NDIM(arr_cast);
	dims = PyArray_DIMS(arr_cast);
	strides = PyArray_STRIDES(arr_cast);
	if (copyFlags)
	    flags = PyArray_FLAGS(arr_cast);
    }
    nbytes = PyArray_NBYTES((PyArrayObject*)arr);

    // TODO: Preserve base or take action?
    fa->nd = ndim;
    fa->flags = flags;
    if (fa->base) {
	if (old_flags & NPY_ARRAY_WRITEBACKIFCOPY) {
	    PyErr_SetString(units_error, "NPY_ARRAY_WRITEBACKIFCOPY detected and not currently supported");
	    goto fail;
	    // retval = PyArray_ResolveWritebackIfCopy(self);
	    // if (retval < 0)
	    // {
	    // 	PyErr_Print();
	    // 	PyErr_Clear();
	    // }
	}
	Py_XDECREF(fa->base);
    }
    fa->base = NULL; 
    Py_DECREF(fa->descr);
    fa->descr = dtype;
    // Should weakref's be freed?
    // fa->weakreflist = (PyObject *)NULL;
    if (fa->nd > 0) {
	fa->dimensions = PyDimMem_RENEW((void*)(fa->dimensions), 2 * fa->nd);
	if (fa->dimensions == NULL) {
	    PyErr_NoMemory();
	    goto fail;
	}
	fa->strides = fa->dimensions + fa->nd;
	for (int i = 0; i < fa->nd; i++) {
	    fa->dimensions[i] = dims[i];
	    fa->strides[i] = strides[i];
	}
    } else {
	fa->flags |= NPY_ARRAY_C_CONTIGUOUS|NPY_ARRAY_F_CONTIGUOUS;
    }
    if ((old_flags & NPY_ARRAY_OWNDATA) && fa->data) {
	data = (char*)PyDataMem_RENEW(fa->data, nbytes);
    } else {
	data = (char*)PyDataMem_NEW(nbytes);
    }
    if (data == NULL) {
	PyErr_NoMemory();
	goto fail;
    }
    fa->flags |= NPY_ARRAY_OWNDATA;
    fa->data = data;
    if (PyArray_CopyInto((PyArrayObject*)dst, (PyArrayObject*)arr) < 0) {
	goto fail;
    }
    Py_XDECREF(arr);
    return 0;
fail:
    Py_XDECREF(arr);
    return -1;
}

PyObject* _copy_array(PyObject* item, PyObject* type, bool copyFlags, bool returnScalar,
		      PyArray_Descr *dtype) {
    PyObject *arr = NULL, *out = NULL;
    PyArrayObject* arr_cast = NULL;
    int ndim = 0, flags = 0;
    npy_intp *dims = NULL, *strides = NULL;
    arr = _get_array(item);
    if (arr == NULL) {
	goto fail;
    }
    if (PyArray_CheckScalar(arr)) {
	if (dtype == NULL)
	    dtype = PyArray_DescrNew(PyArray_DESCR((PyArrayObject*)arr));
	if (dtype == NULL) {
	    goto fail;
	}
    } else {
	arr_cast = (PyArrayObject*)arr;
	if (dtype == NULL)
	    dtype = PyArray_DescrNew(PyArray_DESCR(arr_cast));
	if (dtype == NULL) {
	    goto fail;
	}
	ndim = PyArray_NDIM(arr_cast);
	dims = PyArray_DIMS(arr_cast);
	strides = PyArray_STRIDES(arr_cast);
	if (copyFlags)
	    flags = PyArray_FLAGS(arr_cast);
    }

    out = PyArray_NewFromDescr(
	(PyTypeObject*)type, // &QuantityArray_Type,
	dtype,
	ndim,
	dims,
	strides,
	NULL,
	flags, 
	NULL);
    if (out == NULL) {
	Py_DECREF(dtype);
	goto fail;
    }
    if (PyArray_CopyInto((PyArrayObject*)out, (PyArrayObject*)arr) < 0) {
	goto fail;
    }
    Py_XDECREF(arr);
    if (returnScalar) {
	out = PyArray_Return((PyArrayObject*)out);
    }
    return out;
fail:
    Py_XDECREF(arr);
    Py_XDECREF(out);
    return NULL;
}


////////////
// Module //
////////////


static PyMethodDef units_functions[] = {
    {NULL, NULL, 0, NULL} /* sentinel */
};


static int
units_module_exec(PyObject* m)
{
    if (sizeof(PyArrayObject) > (size_t)QuantityArray_Type.tp_basicsize) {
	PyErr_SetString(PyExc_ImportError,
			"Binary incompatibility with NumPy, must recompile/update rapidjson.");
	return -1;
    }
    if (PyType_Ready(&Units_Type) < 0)
        return -1;

    Py_INCREF(&PyArray_Type);
    QuantityArray_Type.tp_base = &PyArray_Type;
    if (PyType_Ready(&QuantityArray_Type) < 0)
        return -1;

    Py_INCREF(&QuantityArray_Type);
    Quantity_Type.tp_base = &QuantityArray_Type;
    if (PyType_Ready(&Quantity_Type) < 0)
        return -1;

#define STRINGIFY(x) XSTRINGIFY(x)
#define XSTRINGIFY(x) #x

    if (PyModule_AddStringConstant(m, "__version__",
				   STRINGIFY(PYTHON_RAPIDJSON_VERSION))
        || PyModule_AddStringConstant(m, "__author__",
				      "Meagan Lang <langmm.astro@gmail.com>")
        || PyModule_AddStringConstant(m, "__rapidjson_version__",
                                      RAPIDJSON_VERSION_STRING)
#ifdef RAPIDJSON_EXACT_VERSION
        || PyModule_AddStringConstant(m, "__rapidjson_exact_version__",
                                      STRINGIFY(RAPIDJSON_EXACT_VERSION))
#endif
        )
        return -1;

    Py_INCREF(&Units_Type);
    if (PyModule_AddObject(m, "Units", (PyObject*) &Units_Type) < 0) {
        Py_DECREF(&Units_Type);
        return -1;
    }

    Py_INCREF(&Quantity_Type);
    if (PyModule_AddObject(m, "Quantity", (PyObject*) &Quantity_Type) < 0) {
        Py_DECREF(&Quantity_Type);
        return -1;
    }

    Py_INCREF(&QuantityArray_Type);
    if (PyModule_AddObject(m, "QuantityArray", (PyObject*) &QuantityArray_Type) < 0) {
        Py_DECREF(&QuantityArray_Type);
        return -1;
    }

    units_error = PyErr_NewException("yggdrasil.rapidjson.UnitsError",
				     PyExc_ValueError, NULL);
    if (units_error == NULL)
        return -1;
    Py_INCREF(units_error);
    if (PyModule_AddObject(m, "UnitsError", units_error) < 0) {
        Py_DECREF(units_error);
        return -1;
    }

    return 0;
}


static struct PyModuleDef_Slot units_slots[] = {
    {Py_mod_exec, (void*) units_module_exec},
    {0, NULL}
};


static PyModuleDef units_module = {
    PyModuleDef_HEAD_INIT,      /* m_base */
    "yggdrasil.rapidjson.units",          /* m_name */
    PyDoc_STR("Fast, simple units library developed for yggdrasil."),
    0,                          /* m_size */
    units_functions,            /* m_methods */
    units_slots,                /* m_slots */
    NULL,                       /* m_traverse */
    NULL,                       /* m_clear */
    NULL                        /* m_free */
};


PyMODINIT_FUNC
PyInit_units()
{
    return PyModuleDef_Init(&units_module);
}
