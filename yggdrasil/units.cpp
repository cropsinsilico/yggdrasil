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


using namespace rapidjson;
using namespace rapidjson::units;


static PyObject* units_error = NULL;


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

// Quantity
static void quantity_dealloc(PyObject* self);
static PyObject* quantity_new(PyTypeObject* type, PyObject* args, PyObject* kwargs);
static PyObject* quantity_str(PyObject* self);
static PyObject* quantity_repr(PyObject* self);
static PyObject* quantity_units_get(PyObject* self, void* closure);
static int quantity_units_set(PyObject* self, PyObject* value, void* closure);
static PyObject* quantity_value_get(PyObject* type, void* closure);
static int quantity_value_set(PyObject* self, PyObject* value, void* closure);
static PyObject* quantity_is_compatible(PyObject* self, PyObject* args, PyObject* kwargs);
static PyObject* quantity_is_dimensionless(PyObject* self, PyObject* args);
static PyObject* quantity_is_equivalent(PyObject* self, PyObject* args);
static PyObject* quantity_to(PyObject* self, PyObject* args);
static PyObject* quantity_richcompare(PyObject *self, PyObject *other, int op);
static PyObject* quantity_add(PyObject *a, PyObject *b);
static PyObject* quantity_subtract(PyObject *a, PyObject *b);
static PyObject* quantity_multiply(PyObject *a, PyObject *b);
static PyObject* quantity_divide(PyObject *a, PyObject *b);
static PyObject* quantity_modulo(PyObject *a, PyObject *b);
static PyObject* quantity_power(PyObject *base, PyObject *exp, PyObject *mod);
static PyObject* quantity_floor_divide(PyObject *a, PyObject *b);
static PyObject* quantity_add_inplace(PyObject *a, PyObject *b);
static PyObject* quantity_subtract_inplace(PyObject *a, PyObject *b);
static PyObject* quantity_multiply_inplace(PyObject *a, PyObject *b);
static PyObject* quantity_divide_inplace(PyObject *a, PyObject *b);
static PyObject* quantity_modulo_inplace(PyObject *a, PyObject *b);
static PyObject* quantity_floor_divide_inplace(PyObject *a, PyObject *b);
static PyObject* quantity_power_inplace(PyObject *base, PyObject *exp, PyObject *mod);

// QuantityArray
static void quantity_array_dealloc(PyObject* self);
static PyObject* quantity_array_new(PyTypeObject* type, PyObject* args, PyObject* kwargs);
static PyObject* quantity_array_str(PyObject* self);
static PyObject* quantity_array_repr(PyObject* self);
static PyObject* quantity_array_units_get(PyObject* self, void* closure);
static int quantity_array_units_set(PyObject* self, PyObject* value, void* closure);
static PyObject* quantity_array_value_get(PyObject* type, void* closure);
static int quantity_array_value_set(PyObject* self, PyObject* value, void* closure);
static PyObject* quantity_array_is_compatible(PyObject* self, PyObject* args, PyObject* kwargs);
static PyObject* quantity_array_is_dimensionless(PyObject* self, PyObject* args);
static PyObject* quantity_array_is_equivalent(PyObject* self, PyObject* args);
static PyObject* quantity_array_to(PyObject* self, PyObject* args);
static PyObject* quantity_array_richcompare(PyObject *self, PyObject *other, int op);
static PyObject* quantity_array_add(PyObject *a, PyObject *b);
static PyObject* quantity_array_subtract(PyObject *a, PyObject *b);
static PyObject* quantity_array_multiply(PyObject *a, PyObject *b);
static PyObject* quantity_array_divide(PyObject *a, PyObject *b);
static PyObject* quantity_array_modulo(PyObject *a, PyObject *b);
static PyObject* quantity_array_power(PyObject *base, PyObject *exp, PyObject *mod);
static PyObject* quantity_array_floor_divide(PyObject *a, PyObject *b);
static PyObject* quantity_array_add_inplace(PyObject *a, PyObject *b);
static PyObject* quantity_array_subtract_inplace(PyObject *a, PyObject *b);
static PyObject* quantity_array_multiply_inplace(PyObject *a, PyObject *b);
static PyObject* quantity_array_divide_inplace(PyObject *a, PyObject *b);
static PyObject* quantity_array_modulo_inplace(PyObject *a, PyObject *b);
static PyObject* quantity_array_floor_divide_inplace(PyObject *a, PyObject *b);
static PyObject* quantity_array_power_inplace(PyObject *base, PyObject *exp, PyObject *mod);


///////////////
// Utilities //
///////////////


#define SET_ERROR(errno, msg, ret)			\
    {							\
	PyObject* error = Py_BuildValue("s", msg);	\
	PyErr_SetObject(errno, error);			\
	Py_XDECREF(error);				\
	return ret;					\
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
    {NULL}  /* Sentinel */
};


static PyTypeObject Units_Type = {
    PyVarObject_HEAD_INIT(NULL, 0)
    "rapidjson.Units",              /* tp_name */
    sizeof(UnitsObject),            /* tp_basicsize */
    0,                              /* tp_itemsize */
    (destructor) units_dealloc,     /* tp_dealloc */
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
    } else {
        PyErr_SetString(PyExc_TypeError, "Expected string or UTF-8 encoded bytes");
        return NULL;
    }

    UnitsObject* v = (UnitsObject*) type->tp_alloc(type, 0);
    if (v == NULL)
        return NULL;

    if (exprStr)
	v->units = new Units(exprStr);
    else
	v->units = new Units(*other->units);
    if (v->units->is_empty()) {
	PyObject* error = Py_BuildValue("s", "Failed to parse units.");
	PyErr_SetObject(units_error, error);
	Py_XDECREF(error);
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
    bool created = false;
    
    if (!PyArg_ParseTuple(args, "O", &otherObject))
	return NULL;

    if (PyObject_IsInstance(otherObject, (PyObject*)&Units_Type)) {
	other = (UnitsObject*)otherObject;
    } else {
	other = (UnitsObject*)PyObject_Call((PyObject*)&Units_Type, args, NULL);
	created = true;
    }
    if (other == NULL)
        return NULL;
    
    UnitsObject* v = (UnitsObject*) self;
    bool result = v->units->is_compatible(*other->units);
    if (created)
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


//////////////
// Quantity //
//////////////

enum QuantitySubType {
    kFloatQuantitySubType,
    kDoubleQuantitySubType,
    kUint8QuantitySubType,
    kUint16QuantitySubType,
    kUint32QuantitySubType,
    kUint64QuantitySubType,
    kInt8QuantitySubType,
    kInt16QuantitySubType,
    kInt32QuantitySubType,
    kInt64QuantitySubType,
    kComplexFloatQuantitySubType,
    kComplexDoubleQuantitySubType
};


template<typename T>
PyObject* PyObject_FromScalarYgg(T& v) {
    return NULL;
}
#define NUMPY_FROMSCALARYGG(npT, T)				\
    template<>							\
    PyObject* PyObject_FromScalarYgg(T& v) {			\
	PyArray_Descr* desc = PyArray_DescrNewFromType(npT);	\
	if (desc == NULL)					\
	    return NULL;					\
	return PyArray_Scalar((void*)(&v), desc, NULL);		\
    }
// template<>
// PyObject* PyObject_FromScalarYgg(float& v) {
//     return PyFloat_FromDouble((double)v);
// }
// template<>
// PyObject* PyObject_FromScalarYgg(double& v) {
//     return PyFloat_FromDouble(v);
// }
NUMPY_FROMSCALARYGG(NPY_INT8, int8_t)
NUMPY_FROMSCALARYGG(NPY_INT16, int16_t)
NUMPY_FROMSCALARYGG(NPY_INT32, int32_t)
NUMPY_FROMSCALARYGG(NPY_INT64, int64_t)
NUMPY_FROMSCALARYGG(NPY_UINT8, uint8_t)
NUMPY_FROMSCALARYGG(NPY_UINT16, uint16_t)
NUMPY_FROMSCALARYGG(NPY_UINT32, uint32_t)
NUMPY_FROMSCALARYGG(NPY_UINT64, uint64_t)
NUMPY_FROMSCALARYGG(NPY_FLOAT32, float)
NUMPY_FROMSCALARYGG(NPY_FLOAT64, double)
NUMPY_FROMSCALARYGG(NPY_COMPLEX64, std::complex<float>)
NUMPY_FROMSCALARYGG(NPY_COMPLEX128, std::complex<double>)

#undef NUMPY_FROMSCALARYGG

#define NUMPY_GETSCALARYGG_BODY(pyObj, cObj, npT, T, args)	\
    if (PyArray_CheckScalar(pyObj)) {				\
	PyArray_Descr* desc = PyArray_DescrFromScalar(pyObj);	\
	if (desc->type_num == npT) {				\
	    cObj = new T args;					\
	    PyArray_ScalarAsCtype(pyObj, cObj);			\
	}							\
    }
#define NUMPY_GETSCALARYGG(npT, T, subT, args)				\
    template<>								\
    T* PyObject_GetScalarYgg<T>(PyObject* v, QuantitySubType& subtype) { \
	subtype = subT;							\
	T* out = NULL;							\
	NUMPY_GETSCALARYGG_BODY(v, out, npT, T, args)			\
	return out;							\
    }

template<typename T>
T* PyObject_GetScalarYgg(PyObject*, QuantitySubType&) {
    return NULL;
}
NUMPY_GETSCALARYGG(NPY_FLOAT32, float, kFloatQuantitySubType, (0.0))
template<>
double* PyObject_GetScalarYgg<double>(PyObject* v, QuantitySubType& subtype) {
    subtype = kDoubleQuantitySubType;
    if (PyFloat_AsDouble(v)) {
	double d = PyFloat_AsDouble(v);
	if (d == -1.0 && PyErr_Occurred())
	    return NULL;
	return new double(d);
    }
    double *out = NULL;
    NUMPY_GETSCALARYGG_BODY(v, out, NPY_FLOAT64, double, (0.0))
    return out;
}
NUMPY_GETSCALARYGG(NPY_INT8, int8_t, kInt8QuantitySubType, (0))
NUMPY_GETSCALARYGG(NPY_INT16, int16_t, kInt16QuantitySubType, (0))
#define _PyLong_GetScalarYgg(T)						\
    if ((sizeof(T) == sizeof(long long)) && PyLong_Check(v)) {		\
        int overflow;							\
	long long i = PyLong_AsLongLongAndOverflow(v, &overflow);	\
	if (i == -1 && PyErr_Occurred())				\
	    return NULL;						\
	if (overflow == 0) {						\
	    return new T(i);						\
	} else {							\
	    unsigned long long ui = PyLong_AsUnsignedLongLong(v);	\
	    if (PyErr_Occurred())					\
		return NULL;						\
	    return new T(ui);						\
	}								\
    }
template<>
int32_t* PyObject_GetScalarYgg<int32_t>(PyObject* v, QuantitySubType& subtype) {
    subtype = kInt32QuantitySubType;
    _PyLong_GetScalarYgg(int32_t);
    int32_t *out = NULL;
    NUMPY_GETSCALARYGG_BODY(v, out, NPY_INT32, int32_t, (0))
    return out;
}
template<>
int64_t* PyObject_GetScalarYgg<int64_t>(PyObject* v, QuantitySubType& subtype) {
    subtype = kInt64QuantitySubType;
    _PyLong_GetScalarYgg(int64_t);
    int64_t *out = NULL;
    NUMPY_GETSCALARYGG_BODY(v, out, NPY_INT64, int64_t, (0))
    return out;
}
NUMPY_GETSCALARYGG(NPY_UINT8, uint8_t, kUint8QuantitySubType, (0))
NUMPY_GETSCALARYGG(NPY_UINT16, uint16_t, kUint16QuantitySubType, (0))
NUMPY_GETSCALARYGG(NPY_UINT32, uint32_t, kUint32QuantitySubType, (0))
NUMPY_GETSCALARYGG(NPY_UINT64, uint64_t, kUint64QuantitySubType, (0))
NUMPY_GETSCALARYGG(NPY_COMPLEX64, std::complex<float>, kComplexFloatQuantitySubType, (0, 0))
NUMPY_GETSCALARYGG(NPY_COMPLEX128, std::complex<double>, kComplexDoubleQuantitySubType, (0, 0))

#undef NUMPY_GETSCALARYGG
#undef NUMPY_GETSCALARYGG_BODY


#define CASE_QX_SUBTYPE(cls, var, lhs, rhs, value, type)		\
    case (value): { lhs ((cls<type>*) var->quantity) rhs; break; }

#define SWITCH_QX_SUBTYPE(cls, var, lhs, rhs)				\
    switch(var->subtype) {						\
    CASE_QX_SUBTYPE(cls, var, lhs, rhs, kFloatQuantitySubType, float)	\
    CASE_QX_SUBTYPE(cls, var, lhs, rhs, kDoubleQuantitySubType, double)  \
    CASE_QX_SUBTYPE(cls, var, lhs, rhs, kUint8QuantitySubType, uint8_t)  \
    CASE_QX_SUBTYPE(cls, var, lhs, rhs, kUint16QuantitySubType, uint16_t) \
    CASE_QX_SUBTYPE(cls, var, lhs, rhs, kUint32QuantitySubType, uint32_t) \
    CASE_QX_SUBTYPE(cls, var, lhs, rhs, kUint64QuantitySubType, uint64_t) \
    CASE_QX_SUBTYPE(cls, var, lhs, rhs, kInt8QuantitySubType, int8_t)  \
    CASE_QX_SUBTYPE(cls, var, lhs, rhs, kInt16QuantitySubType, int16_t) \
    CASE_QX_SUBTYPE(cls, var, lhs, rhs, kInt32QuantitySubType, int32_t) \
    CASE_QX_SUBTYPE(cls, var, lhs, rhs, kInt64QuantitySubType, int64_t) \
    CASE_QX_SUBTYPE(cls, var, lhs, rhs, kComplexFloatQuantitySubType, std::complex<float>) \
    CASE_QX_SUBTYPE(cls, var, lhs, rhs, kComplexDoubleQuantitySubType, std::complex<double>) \
    }

#define CASE_QX_SUBTYPE_CALL(cls, var, lhs, value, type, ...)	\
    case (value): { lhs (((cls<type>*) var->quantity), __VA_ARGS__); break; }

#define SWITCH_QX_SUBTYPE_CALL(cls, var, lhs, ...)		\
    switch(var->subtype) {						\
    CASE_QX_SUBTYPE_CALL(cls, var, lhs, kFloatQuantitySubType, float, __VA_ARGS__)	\
    CASE_QX_SUBTYPE_CALL(cls, var, lhs, kDoubleQuantitySubType, double, __VA_ARGS__)  \
    CASE_QX_SUBTYPE_CALL(cls, var, lhs, kUint8QuantitySubType, uint8_t, __VA_ARGS__)  \
    CASE_QX_SUBTYPE_CALL(cls, var, lhs, kUint16QuantitySubType, uint16_t, __VA_ARGS__) \
    CASE_QX_SUBTYPE_CALL(cls, var, lhs, kUint32QuantitySubType, uint32_t, __VA_ARGS__) \
    CASE_QX_SUBTYPE_CALL(cls, var, lhs, kUint64QuantitySubType, uint64_t, __VA_ARGS__) \
    CASE_QX_SUBTYPE_CALL(cls, var, lhs, kInt8QuantitySubType, int8_t, __VA_ARGS__)  \
    CASE_QX_SUBTYPE_CALL(cls, var, lhs, kInt16QuantitySubType, int16_t, __VA_ARGS__) \
    CASE_QX_SUBTYPE_CALL(cls, var, lhs, kInt32QuantitySubType, int32_t, __VA_ARGS__) \
    CASE_QX_SUBTYPE_CALL(cls, var, lhs, kInt64QuantitySubType, int64_t, __VA_ARGS__) \
    CASE_QX_SUBTYPE_CALL(cls, var, lhs, kComplexFloatQuantitySubType, std::complex<float>, __VA_ARGS__) \
    CASE_QX_SUBTYPE_CALL(cls, var, lhs, kComplexDoubleQuantitySubType, std::complex<double>, __VA_ARGS__) \
    }

#define SWITCH_QUANTITY_SUBTYPE(var, lhs, rhs)	\
    SWITCH_QX_SUBTYPE(Quantity, var, lhs, rhs)
#define SWITCH_QUANTITY_SUBTYPE_CALL(var, lhs, ...)	\
    SWITCH_QX_SUBTYPE_CALL(Quantity, var, lhs, __VA_ARGS__)

#define EXTRACT_PYTHON_QX_TYPE(tmp, tempMethod, tempArgs, method, args, T) \
    if (T* tmp = tempMethod<T>tempArgs) {				\
	method<T> args;							\
    }

#define EXTRACT_PYTHON_QX(tmp, tempMethod, tempArgs, method, args, error) \
    EXTRACT_PYTHON_QX_TYPE(tmp, tempMethod, tempArgs, method, args, float)	\
    else EXTRACT_PYTHON_QX_TYPE(tmp, tempMethod, tempArgs, method, args, double) \
    else EXTRACT_PYTHON_QX_TYPE(tmp, tempMethod, tempArgs, method, args, int8_t) \
    else EXTRACT_PYTHON_QX_TYPE(tmp, tempMethod, tempArgs, method, args, int16_t) \
    else EXTRACT_PYTHON_QX_TYPE(tmp, tempMethod, tempArgs, method, args, int32_t) \
    else EXTRACT_PYTHON_QX_TYPE(tmp, tempMethod, tempArgs, method, args, int64_t) \
    else EXTRACT_PYTHON_QX_TYPE(tmp, tempMethod, tempArgs, method, args, uint8_t) \
    else EXTRACT_PYTHON_QX_TYPE(tmp, tempMethod, tempArgs, method, args, uint16_t) \
    else EXTRACT_PYTHON_QX_TYPE(tmp, tempMethod, tempArgs, method, args, uint32_t) \
    else EXTRACT_PYTHON_QX_TYPE(tmp, tempMethod, tempArgs, method, args, uint64_t) \
    else EXTRACT_PYTHON_QX_TYPE(tmp, tempMethod, tempArgs, method, args, std::complex<float>)	\
    else EXTRACT_PYTHON_QX_TYPE(tmp, tempMethod, tempArgs, method, args, std::complex<double>) \
    else { error; }
    
#define EXTRACT_PYTHON_VALUE(var, pyObj, tmp, method, args, error)	\
    EXTRACT_PYTHON_QX(tmp, PyObject_GetScalarYgg, (pyObj, var), method, args, error)



typedef struct {
    PyObject_HEAD
    QuantitySubType subtype;
    void *quantity;
} QuantityObject;


PyDoc_STRVAR(quantity_doc,
             "Quantity(value, units)\n"
             "\n"
             "Create and return a new Quantity instance from the given"
             " `value` and `units` string or Units instance.");


static PyMethodDef quantity_methods[] = {
    {"is_compatible", (PyCFunction) quantity_is_compatible, METH_VARARGS,
     "Check if a set of units or quantity is compatible with another set."},
    {"is_dimensionless", (PyCFunction) quantity_is_dimensionless, METH_NOARGS,
     "Check if the quantity has dimensionless units."},
    {"to", (PyCFunction) quantity_to, METH_VARARGS,
     "Convert the quantity to another set of units."},
    {"is_equivalent", (PyCFunction) quantity_is_equivalent, METH_VARARGS,
     "Check if another Quantity is equivalent when convert to the same units/"},
    {NULL}  /* Sentinel */
};


static PyGetSetDef quantity_properties[] = {
    {"units", quantity_units_get, quantity_units_set,
     "The rapidjson.Units units for the quantity.", NULL},
    {"value", quantity_value_get, quantity_value_set,
     "The quantity's value (in the current unit system).", NULL},
    {NULL}
};


static PyNumberMethods quantity_number_methods = {
    quantity_add,                   /* nb_add */
    quantity_subtract,              /* nb_subtract */
    quantity_multiply,              /* nb_multiply */
    quantity_modulo,                /* nb_remainder */
    0,                              /* nb_divmod */
    quantity_power,                 /* nb_power */
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
    quantity_add_inplace,           /* nb_inplace_add */
    quantity_subtract_inplace,      /* nb_inplace_subtract */
    quantity_multiply_inplace,      /* nb_inplace_multiply */
    quantity_modulo_inplace,        /* nb_inplace_remainder */
    quantity_power_inplace,         /* nb_inplace_power */
    0,                              /* nb_inplace_lshift */
    0,                              /* nb_inplace_rshift */
    0,                              /* nb_inplace_and */
    0,                              /* nb_inplace_xor */
    0,                              /* nb_inplace_or */
    //
    quantity_floor_divide,          /* nb_floor_divide */
    quantity_divide,                /* nb_true_divide */
    quantity_floor_divide_inplace,  /* nb_inplace_floor_divide */
    quantity_divide_inplace,        /* nb_inplace_true_divide */
    //
    0,                              /* nb_index */
    //
    0,                              /* nb_matrix_multiply */
    0,                              /* nb_inplace_matrix_multiply */
};


static PyTypeObject Quantity_Type = {
    PyVarObject_HEAD_INIT(NULL, 0)
    "rapidjson.Quantity",           /* tp_name */
    sizeof(QuantityObject),         /* tp_basicsize */
    0,                              /* tp_itemsize */
    (destructor) quantity_dealloc,  /* tp_dealloc */
    0,                              /* tp_print */
    0,                              /* tp_getattr */
    0,                              /* tp_setattr */
    0,                              /* tp_compare */
    quantity_repr,                  /* tp_repr */
    &quantity_number_methods,       /* tp_as_number */
    0,                              /* tp_as_sequence */
    0,                              /* tp_as_mapping */
    0,                              /* tp_hash */
    0,                              /* tp_call */
    quantity_str,                   /* tp_str */
    0,                              /* tp_getattro */
    0,                              /* tp_setattro */
    0,                              /* tp_as_buffer */
    Py_TPFLAGS_DEFAULT,             /* tp_flags */
    quantity_doc,                   /* tp_doc */
    0,                              /* tp_traverse */
    0,                              /* tp_clear */
    quantity_richcompare,           /* tp_richcompare */
    0,                              /* tp_weaklistoffset */
    0,                              /* tp_iter */
    0,                              /* tp_iternext */
    quantity_methods,               /* tp_methods */
    0,                              /* tp_members */
    quantity_properties,            /* tp_getset */
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


static void quantity_dealloc(PyObject* self)
{
    QuantityObject* s = (QuantityObject*) self;
    SWITCH_QUANTITY_SUBTYPE(s, delete, );
    Py_TYPE(self)->tp_free(self);
}


template<typename T>
void assign_scalar_(QuantityObject* v, T* val, Units* units=nullptr) {
    if (units)
	v->quantity = (void*)(new Quantity<T>(*val, *units));
    else
	v->quantity = (void*)(new Quantity<T>(*val));
    delete val;
}


static PyObject* quantity_new(PyTypeObject* type, PyObject* args, PyObject* kwargs)
{
    PyObject* valueObject;
    PyObject* unitsObject = NULL;
    static char const* kwlist[] = {
	"value",
	"units",
	NULL
    };

    if (!PyArg_ParseTupleAndKeywords(args, kwargs, "O|O:Quantity",
				     (char**) kwlist,
				     &valueObject, &unitsObject))
	return NULL;

    QuantityObject* v = (QuantityObject*) type->tp_alloc(type, 0);
    if (v == NULL)
        return NULL;

    if (valueObject == NULL) {
	PyErr_SetString(PyExc_TypeError, "Invalid value");
	return NULL;
    }

    if (PyObject_IsInstance(valueObject, (PyObject*)&Quantity_Type)) {
	QuantityObject* vother = (QuantityObject*)valueObject;
	v->subtype = vother->subtype;
	SWITCH_QUANTITY_SUBTYPE(vother, v->quantity = , ->copy_void());
    } else if (unitsObject != NULL) {
	PyObject* units_args = PyTuple_Pack(1, unitsObject);
	unitsObject = PyObject_Call((PyObject*)&Units_Type, units_args, NULL);
	Py_DECREF(units_args);
	if (unitsObject == NULL)
	    return NULL;
	EXTRACT_PYTHON_VALUE(v->subtype, valueObject, val, assign_scalar_,
			     (v, val, ((UnitsObject*)unitsObject)->units),
			     { PyErr_SetString(PyExc_TypeError, "Expected scalar integer, floating point, or complex value"); return NULL; })
    } else {
	EXTRACT_PYTHON_VALUE(v->subtype, valueObject, val, assign_scalar_,
			     (v, val),
			     { PyErr_SetString(PyExc_TypeError, "Expected scalar integer, floating point, or complex value"); return NULL; })
    }
	
    return (PyObject*) v;
}


static PyObject* quantity_str(PyObject* self) {
    QuantityObject* v = (QuantityObject*) self;
    std::string s;
    SWITCH_QUANTITY_SUBTYPE(v, s = , ->str());
    return PyUnicode_FromString(s.c_str());
}


static PyObject* quantity_repr(PyObject* self) {
    QuantityObject* v = (QuantityObject*) self;
    std::basic_stringstream<char> ss;
    SWITCH_QUANTITY_SUBTYPE(v, , ->display(ss));
    return PyUnicode_FromString(ss.str().c_str());
}


static PyObject* quantity_units_get(PyObject* self, void*) {
    QuantityObject* v = (QuantityObject*) self;
    UnitsObject* vu = (UnitsObject*) Units_Type.tp_alloc(&Units_Type, 0);
    if (vu == NULL)
        return NULL;
    vu->units = new Units();
    bool vEmpty = false;
    SWITCH_QUANTITY_SUBTYPE(v, vEmpty = , ->units().is_empty());
    SWITCH_QUANTITY_SUBTYPE(v, *(vu->units) = , ->units());
    if (!vEmpty && vu->units->is_empty()) {
	PyObject* error = Py_BuildValue("s", "Failed to parse units.");
	PyErr_SetObject(units_error, error);
	Py_XDECREF(error);
	return NULL;
    }
    
    return (PyObject*) vu;
}

static int quantity_units_set(PyObject* self, PyObject* value, void*) {
    PyObject* units_args = PyTuple_Pack(1, value);
    PyObject* unitsObject = PyObject_Call((PyObject*)&Units_Type, units_args, NULL);
    Py_DECREF(units_args);
    if (unitsObject == NULL)
	return -1;
    
    QuantityObject* v = (QuantityObject*) self;
    SWITCH_QUANTITY_SUBTYPE(v, , ->convert_to(*(((UnitsObject*)unitsObject)->units)));
    return 0;
}

template<typename T>
static PyObject* do_quantity_value_get(Quantity<T>* x, void*) {
    T val = x->value();
    return PyObject_FromScalarYgg(val);
}

static PyObject* quantity_value_get(PyObject* self, void*) {
    QuantityObject* v = (QuantityObject*) self;
    SWITCH_QUANTITY_SUBTYPE_CALL(v, return do_quantity_value_get, NULL);
    return NULL;
}

template<typename T, typename Tval>
static int do_quantity_value_set_lvl2(Quantity<T>* x, Tval& value,
				      RAPIDJSON_ENABLEIF((YGGDRASIL_IS_CASTABLE(Tval, T)))) {
    x->set_value((T)value);
    return 0;
}
template<typename T, typename Tval>
static int do_quantity_value_set_lvl2(Quantity<T>* x, Tval& value,
				      RAPIDJSON_DISABLEIF((YGGDRASIL_IS_CASTABLE(Tval, T)))) {
    return -1;
}

template<typename Tval>
static int do_quantity_value_set_lvl1(QuantityObject* v, Tval& value) {
    SWITCH_QUANTITY_SUBTYPE_CALL(v, return do_quantity_value_set_lvl2, value)
    return -1;
}

static int quantity_value_set(PyObject* self, PyObject* value, void*) {
    QuantityObject* v = (QuantityObject*) self;
    QuantitySubType value_subtype;
    EXTRACT_PYTHON_VALUE(value_subtype, value, val,
			 return do_quantity_value_set_lvl1,
			 (v, *val), return -1)
}

static PyObject* quantity_is_compatible(PyObject* self, PyObject* args, PyObject* kwargs) {
    PyObject* otherObject;
    const UnitsObject* other;
    bool created = false;
    
    if (!PyArg_ParseTuple(args, "O", &otherObject))
	return NULL;

    if (PyObject_IsInstance(otherObject, (PyObject*)&Quantity_Type)) {
	other = (UnitsObject*)quantity_units_get(otherObject, NULL);
    } else if (PyObject_IsInstance(otherObject, (PyObject*)&Units_Type)) {
	other = (UnitsObject*)otherObject;
    } else {
	other = (UnitsObject*)PyObject_Call((PyObject*)&Units_Type, args, NULL);
	created = true;
    }
    if (other == NULL)
        return NULL;
    
    QuantityObject* v = (QuantityObject*) self;
    bool result = false;
    SWITCH_QUANTITY_SUBTYPE(v, result = , ->is_compatible(*other->units));
    if (created)
	Py_DECREF(other);
    if (result) {
	Py_INCREF(Py_True);
	return Py_True;
    }
    Py_INCREF(Py_False);
    return Py_False;
    
}


static PyObject* quantity_is_dimensionless(PyObject* self, PyObject* args) {
    QuantityObject* v = (QuantityObject*) self;
    bool result;
    SWITCH_QUANTITY_SUBTYPE(v, result = , ->is_dimensionless());
    if (result) {
	Py_INCREF(Py_True);
	return Py_True;
    }
    Py_INCREF(Py_False);
    return Py_False;
}


template <typename Ta, typename Tb>
static PyObject* do_is_equivalent(Quantity<Ta>* a, Quantity<Tb>* b,
				  RAPIDJSON_DISABLEIF((YGGDRASIL_IS_CASTABLE(Tb, Ta)))) {
    SET_ERROR(units_error, "Incompatible Quantity value types.", NULL);
    return NULL;
}
template <typename Ta, typename Tb>
static PyObject* do_is_equivalent(Quantity<Ta>* a, Quantity<Tb>* b,
				  RAPIDJSON_ENABLEIF((YGGDRASIL_IS_CASTABLE(Tb, Ta)))) {
    if (a->equivalent_to(*b)) {
	Py_INCREF(Py_True);
	return Py_True;
    }
    Py_INCREF(Py_False);
    return Py_False;
}


template<typename T>
static PyObject* quantity_is_equivalent_nested(Quantity<T>* b,
					       QuantityObject* va) {
    SWITCH_QUANTITY_SUBTYPE_CALL(va, return do_is_equivalent, b)
}


static PyObject* quantity_is_equivalent(PyObject* self, PyObject* args) {
    PyObject* otherObject;

    if (!PyArg_ParseTuple(args, "O", &otherObject))
	return NULL;
    
    if (!PyObject_IsInstance(otherObject, (PyObject*)&Quantity_Type)) {
	PyErr_SetString(PyExc_TypeError, "expected a Quantity instance");
	return NULL;
    }
    
    QuantityObject* va = (QuantityObject*) self;
    QuantityObject* vb = (QuantityObject*) otherObject;

    SWITCH_QUANTITY_SUBTYPE_CALL(vb, return quantity_is_equivalent_nested, va)
}


static PyObject* quantity_to(PyObject* self, PyObject* args) {
    PyObject* unitsObject;

    if (!PyArg_ParseTuple(args, "O", &unitsObject))
	return NULL;

    PyObject* units_args = PyTuple_Pack(1, unitsObject);
    unitsObject = PyObject_Call((PyObject*)&Units_Type, units_args, NULL);
    Py_DECREF(units_args);
    if (unitsObject == NULL)
	return NULL;

    QuantityObject* v = (QuantityObject*) self;
    bool compat = false;
    SWITCH_QUANTITY_SUBTYPE(v, compat = , ->is_compatible(*(((UnitsObject*)unitsObject)->units)));
    if (!compat) {
	PyObject* error = Py_BuildValue("s", "Incompatible units");
	PyErr_SetObject(units_error, error);
	Py_XDECREF(error);
	return NULL;
    }

    PyObject* quantity_args = PyTuple_Pack(1, self);
    PyObject* out = quantity_new(&Quantity_Type, quantity_args, NULL);
    Py_DECREF(quantity_args);
    if (out == NULL)
	return NULL;

    QuantityObject* vout = (QuantityObject*) out;
    SWITCH_QUANTITY_SUBTYPE(vout, , ->convert_to(*(((UnitsObject*)unitsObject)->units)));
    return out;
}


template<typename T>
static PyObject* quantity_richcompare_nest(Quantity<T>* vself,
					   QuantityObject* vsolf0,
					   int op) {
    Quantity<T>* vsolf = (Quantity<T>*)(vsolf0->quantity);
    switch (op) {
    case (Py_LT):
    case (Py_LE):
    case (Py_GT):
    case (Py_GE): {
	if (vsolf->units() != vself->units()) {
	    PyObject* error = Py_BuildValue("s", "Comparison invalid for Quantity instances with different units, convert one first.");
	    PyErr_SetObject(units_error, error);
	    Py_XDECREF(error);
	    return NULL;
	}
	Py_RETURN_RICHCOMPARE(*vself, *vsolf, op);
    }
    case (Py_EQ):
    case (Py_NE):
	Py_RETURN_RICHCOMPARE(*vself, *vsolf, op);
    default:
	Py_INCREF(Py_NotImplemented);
	return Py_NotImplemented;
    }
}


static PyObject* quantity_richcompare(PyObject *self, PyObject *other, int op) {
    QuantityObject* vself = (QuantityObject*) self;
    QuantityObject* vsolf = (QuantityObject*) other;
    if (vself->subtype != vsolf->subtype) {
	Py_INCREF(Py_False);
	return Py_False;
    }
    SWITCH_QUANTITY_SUBTYPE_CALL(vself, return quantity_richcompare_nest,
				 vsolf, op)
}


// Number operations
static QuantityObject* get_quantity(PyObject *a) {
    QuantityObject* va = NULL;
    if (PyObject_IsInstance(a, (PyObject*)&Quantity_Type)) {
	va = (QuantityObject*)a;
    } else {
	PyObject* quantity_args = PyTuple_Pack(1, a);
	va = (QuantityObject*)quantity_new(&Quantity_Type, quantity_args, NULL);
	Py_DECREF(quantity_args);
	if (va == NULL)
	    return NULL;
    }
    return va;
}


enum BinaryOps {
    binaryOpAdd,
    binaryOpSubtract,
    binaryOpMultiply,
    binaryOpDivide,
    binaryOpModulo,
    binaryOpFloorDivide
};


template <typename Ta, typename Tb>
static void* do_quantity_op(Quantity<Ta>* a, Quantity<Tb>* b, BinaryOps op,
			    bool inplace=false,
			    RAPIDJSON_DISABLEIF((YGGDRASIL_IS_CASTABLE(Tb, Ta)))) {
    SET_ERROR(units_error, "Incompatible Quantity value types.", NULL);
}
template <typename Ta, typename Tb>
static void* do_quantity_op(Quantity<Ta>* a, Quantity<Tb>* b, BinaryOps op,
			    bool inplace=false,
			    RAPIDJSON_ENABLEIF((YGGDRASIL_IS_CASTABLE(Tb, Ta)))) {
    Quantity<Ta>* out;
    if (inplace)
	out = a;
    else
	out = new Quantity<Ta>();
    switch (op) {
    case (binaryOpAdd): {
	if (!a->is_compatible(*b))
	    SET_ERROR(units_error, "Cannot add Quantity instances with incompatible units", NULL)
	if (inplace)
	    *out += *b;
	else
	    *out = *a + *b;
	break;
    }
    case (binaryOpSubtract): {
	if (!a->is_compatible(*b))
	    SET_ERROR(units_error, "Cannot subtract Quantity instances with incompatible units", NULL)
	if (inplace)
	    *out -= *b;
	else
	    *out = *a - *b;
	break;
    }
    case (binaryOpMultiply): {
	if (inplace)
	    *out *= *b;
	else
	    *out = *a * *b;
	break;
    }
    case (binaryOpDivide): {
	if (inplace)
	    *out /= *b;
	else
	    *out = *a / *b;
	break;
    }
    case (binaryOpModulo): {
	if (inplace)
	    *out %= *b;
	else
	    *out = *a % *b;
	break;
    }
    case (binaryOpFloorDivide): {
	if (inplace)
	    *out /= *b;
	else
	    *out = *a / *b;
	out->floor_inplace();
	break;
    }
    }
    return (void*)out;
}


template <typename Tb>
static void* do_quantity_op_lvl2(Quantity<Tb>* b, QuantityObject* va, BinaryOps op,
				 bool inplace=false) {
    SWITCH_QUANTITY_SUBTYPE_CALL(va, return do_quantity_op, b, op, inplace)
}


static PyObject* do_quantity_op_lvl1(PyObject *a, PyObject *b, BinaryOps op,
				     bool inplace=false) {
    // if (inplace && !PyObject_IsInstance(a, (PyObject*)&Quantity_Type) && PyObject_IsInstance(b, (PyObject*)&Quantity_Type))
    // 	return do_quantity_op_lvl1(b, a, op, true);
    QuantityObject* va = get_quantity(a);
    QuantityObject* vb = get_quantity(b);
    if ((va == NULL) || (vb == NULL))
	return NULL;
    QuantityObject* out;
    if (inplace && PyObject_IsInstance(a, (PyObject*)&Quantity_Type)) {
	out = va;
	Py_INCREF(a);
    } else {
	out = (QuantityObject*) Quantity_Type.tp_alloc(&Quantity_Type, 0);
	out->subtype = va->subtype;
    }
    SWITCH_QUANTITY_SUBTYPE_CALL(vb, out->quantity = do_quantity_op_lvl2, va, op, inplace)
    if (out->quantity == NULL)
	return NULL;
    return (PyObject*) out;
}
    

static PyObject* quantity_add(PyObject *a, PyObject *b)
{ return do_quantity_op_lvl1(a, b, binaryOpAdd); }
static PyObject* quantity_subtract(PyObject *a, PyObject *b)
{ return do_quantity_op_lvl1(a, b, binaryOpSubtract); }
static PyObject* quantity_multiply(PyObject *a, PyObject *b)
{ return do_quantity_op_lvl1(a, b, binaryOpMultiply); }
static PyObject* quantity_divide(PyObject *a, PyObject *b)
{ return do_quantity_op_lvl1(a, b, binaryOpDivide); }
static PyObject* quantity_floor_divide(PyObject *a, PyObject *b)
{ return do_quantity_op_lvl1(a, b, binaryOpFloorDivide); }
static PyObject* quantity_modulo(PyObject *a, PyObject *b)
{ return do_quantity_op_lvl1(a, b, binaryOpModulo); }
static PyObject* quantity_add_inplace(PyObject *a, PyObject *b)
{ return do_quantity_op_lvl1(a, b, binaryOpAdd, true); }
static PyObject* quantity_subtract_inplace(PyObject *a, PyObject *b)
{ return do_quantity_op_lvl1(a, b, binaryOpSubtract, true); }
static PyObject* quantity_multiply_inplace(PyObject *a, PyObject *b)
{ return do_quantity_op_lvl1(a, b, binaryOpMultiply, true); }
static PyObject* quantity_divide_inplace(PyObject *a, PyObject *b)
{ return do_quantity_op_lvl1(a, b, binaryOpDivide, true); }
static PyObject* quantity_modulo_inplace(PyObject *a, PyObject *b)
{ return do_quantity_op_lvl1(a, b, binaryOpModulo, true); }
static PyObject* quantity_floor_divide_inplace(PyObject *a, PyObject *b)
{ return do_quantity_op_lvl1(a, b, binaryOpFloorDivide, true); }

template<typename Tbase, typename Tmod, typename T>
static void* quantity_power_lvl4(Quantity<Tbase>* base, Quantity<Tmod>* mod, T* val,
				 bool inplace=false) {
    Quantity<Tbase>* out;
    if (inplace) {
	out = base;
	out->inplace_pow(*val);
    } else {
	out = new Quantity<Tbase>();
	*out = base->pow(*val);
    }
    *out %= *mod;
    return (void*)out;
}
template<typename Tbase, typename Tmod, typename T>
static void* quantity_power_lvl4(Quantity<Tbase>* base, Quantity<Tmod>* mod, std::complex<T>* val,
				 bool inplace=false) {
    PyErr_SetString(PyExc_TypeError, "Complex exponent not supported");
    return NULL;
}
template<typename Tmod, typename T>
static void* quantity_power_lvl3(Quantity<Tmod>* mod, T* val, QuantityObject* vbase,
				 bool inplace=false) {
    SWITCH_QUANTITY_SUBTYPE_CALL(vbase, return quantity_power_lvl4, mod, val, inplace);
}
template<typename T>
static void* quantity_power_lvl2(T* val, QuantityObject* vbase, QuantityObject* vmod,
				 bool inplace=false) {
    SWITCH_QUANTITY_SUBTYPE_CALL(vmod, return quantity_power_lvl3, val, vbase, inplace);
}
static PyObject* quantity_power_lvl1(PyObject *base, PyObject *exp, PyObject *mod,
				     bool inplace=false) {
    QuantityObject* vbase = get_quantity(base);
    QuantityObject* vmod = get_quantity(mod);
    if ((vbase == NULL) || (vmod == NULL))
	return NULL;
    if (PyObject_IsInstance(exp, (PyObject*)&Quantity_Type))
	SET_ERROR(units_error, "Raising to a Quantity power not supported", NULL);
    QuantityObject* out;
    if (inplace && PyObject_IsInstance(base, (PyObject*)&Quantity_Type)) {
	out = vbase;
	Py_INCREF(base);
    } else {
	out = (QuantityObject*) Quantity_Type.tp_alloc(&Quantity_Type, 0);
	out->subtype = vbase->subtype;
    }
    QuantitySubType subtype_exp;
    EXTRACT_PYTHON_VALUE(subtype_exp, exp, tmp,
			 out->quantity = quantity_power_lvl2,
			 (tmp, vbase, vmod, inplace),
			 { PyErr_SetString(PyExc_TypeError, "Expected scalar integer, floating point, or complex value"); return NULL; })
    if (out->quantity == NULL)
	return NULL;
    return (PyObject*) out;
}
static PyObject* quantity_power(PyObject *base, PyObject *exp, PyObject *mod)
{ return quantity_power_lvl1(base, exp, mod); }
static PyObject* quantity_power_inplace(PyObject *base, PyObject *exp, PyObject *mod)
{ return quantity_power_lvl1(base, exp, mod, true); }


///////////////////
// QuantityArray //
///////////////////

template<typename T>
PyObject* PyObject_FromArrayYgg(const T* v, int ndim, npy_intp* shape) {
    return NULL;
}
#define NUMPY_FROMARRAYYGG(npT, T)					\
    template<>								\
    PyObject* PyObject_FromArrayYgg(const T* v, int ndim, npy_intp* shape) { \
	PyArray_Descr* desc = PyArray_DescrNewFromType(npT);		\
	if (desc == NULL)						\
	    return NULL;						\
	PyObject* tmp = PyArray_SimpleNewFromData((int)ndim, shape, npT, (void*)v); \
	if (tmp == NULL)						\
	    return NULL;						\
	PyObject* out = PyArray_NewCopy((PyArrayObject*)tmp, NPY_CORDER); \
	Py_DECREF(tmp);							\
	return out;							\
    }
NUMPY_FROMARRAYYGG(NPY_INT8, int8_t)
NUMPY_FROMARRAYYGG(NPY_INT16, int16_t)
NUMPY_FROMARRAYYGG(NPY_INT32, int32_t)
NUMPY_FROMARRAYYGG(NPY_INT64, int64_t)
NUMPY_FROMARRAYYGG(NPY_UINT8, uint8_t)
NUMPY_FROMARRAYYGG(NPY_UINT16, uint16_t)
NUMPY_FROMARRAYYGG(NPY_UINT32, uint32_t)
NUMPY_FROMARRAYYGG(NPY_UINT64, uint64_t)
NUMPY_FROMARRAYYGG(NPY_FLOAT32, float)
NUMPY_FROMARRAYYGG(NPY_FLOAT64, double)
NUMPY_FROMARRAYYGG(NPY_COMPLEX64, std::complex<float>)
NUMPY_FROMARRAYYGG(NPY_COMPLEX128, std::complex<double>)

#undef NUMPY_FROMARRAYYGG

template<typename T>
T* PyObject_GetArrayYgg(PyObject*, QuantitySubType&, PyArrayObject*&) {
			
    return NULL;
}

#define NUMPY_GETARRAYYGG(npT, T, subT)					\
    template<>								\
    T* PyObject_GetArrayYgg<T>(PyObject* v, QuantitySubType& subtype,	\
			       PyArrayObject*& cpy) {			\
	subtype = subT;							\
	T* out = NULL;							\
	if (!PyArray_Check(v))						\
	    return PyObject_GetScalarYgg<T>(v, subtype);		\
	PyArray_Descr* desc = PyArray_DESCR((PyArrayObject*)v);		\
	if (desc->type_num != npT)					\
	    return out;							\
	cpy = PyArray_GETCONTIGUOUS((PyArrayObject*)v);			\
	if (cpy == NULL)						\
	    return out;							\
	out = (T*)PyArray_BYTES(cpy);					\
	return out;							\
    }

NUMPY_GETARRAYYGG(NPY_INT8, int8_t, kInt8QuantitySubType)
NUMPY_GETARRAYYGG(NPY_INT16, int16_t, kInt16QuantitySubType)
NUMPY_GETARRAYYGG(NPY_INT32, int32_t, kInt32QuantitySubType)
NUMPY_GETARRAYYGG(NPY_INT64, int64_t, kInt64QuantitySubType)
NUMPY_GETARRAYYGG(NPY_UINT8, uint8_t, kUint8QuantitySubType)
NUMPY_GETARRAYYGG(NPY_UINT16, uint16_t, kUint16QuantitySubType)
NUMPY_GETARRAYYGG(NPY_UINT32, uint32_t, kUint32QuantitySubType)
NUMPY_GETARRAYYGG(NPY_UINT64, uint64_t, kUint64QuantitySubType)
NUMPY_GETARRAYYGG(NPY_FLOAT32, float, kFloatQuantitySubType)
NUMPY_GETARRAYYGG(NPY_FLOAT64, double, kDoubleQuantitySubType)
NUMPY_GETARRAYYGG(NPY_COMPLEX64, std::complex<float>, kComplexFloatQuantitySubType)
NUMPY_GETARRAYYGG(NPY_COMPLEX128, std::complex<double>, kComplexDoubleQuantitySubType)

#undef NUMPY_GETARRAYYGG

#define SWITCH_QUANTITY_ARRAY_SUBTYPE(var, lhs, rhs)			\
    SWITCH_QX_SUBTYPE(QuantityArray, var, lhs, rhs)
#define SWITCH_QUANTITY_ARRAY_SUBTYPE_CALL(var, lhs, ...)	\
    SWITCH_QX_SUBTYPE_CALL(QuantityArray, var, lhs, __VA_ARGS__)


typedef struct {
    PyObject_HEAD
    QuantitySubType subtype;
    void *quantity;
} QuantityArrayObject;


PyDoc_STRVAR(quantity_array_doc,
             "QuantityArray(value, units)\n"
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
    {NULL}  /* Sentinel */
};


static PyGetSetDef quantity_array_properties[] = {
    {"units", quantity_array_units_get, quantity_array_units_set,
     "The rapidjson.Units units for the quantity.", NULL},
    {"value", quantity_array_value_get, quantity_array_value_set,
     "The quantity's value (in the current unit system)."},
    {NULL}
};


static PyNumberMethods quantity_array_number_methods = {
    quantity_array_add,                   /* nb_add */
    quantity_array_subtract,              /* nb_subtract */
    quantity_array_multiply,              /* nb_multiply */
    quantity_array_modulo,                /* nb_remainder */
    0,                                    /* nb_divmod */
    quantity_array_power,                 /* nb_power */
    0,                                    /* nb_negative */
    0,                                    /* nb_positive */
    0,                                    /* nb_absolute */
    0,                                    /* nb_bool */
    0,                                    /* nb_invert */
    0,                                    /* nb_lshift */
    0,                                    /* nb_rshift */
    0,                                    /* nb_and */
    0,                                    /* nb_xor */
    0,                                    /* nb_or */
    0,                                    /* nb_int */
    0,                                    /* nb_reserved */
    0,                                    /* nb_float */
    //
    quantity_array_add_inplace,           /* nb_inplace_add */
    quantity_array_subtract_inplace,      /* nb_inplace_subtract */
    quantity_array_multiply_inplace,      /* nb_inplace_multiply */
    quantity_array_modulo_inplace,        /* nb_inplace_remainder */
    quantity_array_power_inplace,         /* nb_inplace_power */
    0,                                    /* nb_inplace_lshift */
    0,                                    /* nb_inplace_rshift */
    0,                                    /* nb_inplace_and */
    0,                                    /* nb_inplace_xor */
    0,                                    /* nb_inplace_or */
    //
    quantity_array_floor_divide,          /* nb_floor_divide */
    quantity_array_divide,                /* nb_true_divide */
    quantity_array_floor_divide_inplace,  /* nb_inplace_floor_divide */
    quantity_array_divide_inplace,        /* nb_inplace_true_divide */
    //
    0,                                    /* nb_index */
    //
    0,                                    /* nb_matrix_multiply */
    0,                                    /* nb_inplace_matrix_multiply */
};


static PyTypeObject QuantityArray_Type = {
    PyVarObject_HEAD_INIT(NULL, 0)
    "rapidjson.QuantityArray",            /* tp_name */
    sizeof(QuantityArrayObject),          /* tp_basicsize */
    0,                                    /* tp_itemsize */
    (destructor) quantity_array_dealloc,  /* tp_dealloc */
    0,                                    /* tp_print */
    0,                                    /* tp_getattr */
    0,                                    /* tp_setattr */
    0,                                    /* tp_compare */
    quantity_array_repr,                  /* tp_repr */
    &quantity_array_number_methods,       /* tp_as_number */
    0,                                    /* tp_as_sequence */
    0,                                    /* tp_as_mapping */
    0,                                    /* tp_hash */
    0,                                    /* tp_call */
    quantity_array_str,                   /* tp_str */
    0,                                    /* tp_getattro */
    0,                                    /* tp_setattro */
    0,                                    /* tp_as_buffer */
    Py_TPFLAGS_DEFAULT,                   /* tp_flags */
    quantity_array_doc,                   /* tp_doc */
    0,                                    /* tp_traverse */
    0,                                    /* tp_clear */
    quantity_array_richcompare,           /* tp_richcompare */
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


static void quantity_array_dealloc(PyObject* self)
{
    QuantityArrayObject* s = (QuantityArrayObject*) self;
    SWITCH_QUANTITY_ARRAY_SUBTYPE(s, delete, );
    Py_TYPE(self)->tp_free(self);
}


template<typename T>
void assign_array_(QuantityArrayObject* v, T* val,
		   PyArrayObject*& cpy, Units* units=nullptr) {
    SizeType ndim = 0;
    SizeType* shape = NULL;
    if (cpy == NULL) {
	ndim = 1;
	shape = &ndim;
    } else {
	ndim = (SizeType)PyArray_NDIM(cpy);
	npy_intp* np_shape = PyArray_SHAPE(cpy);
	shape = (SizeType*)malloc(ndim * sizeof(SizeType));
	for (SizeType i = 0; i < ndim; i++)
	    shape[i] = (SizeType)np_shape[i];
    }
    if (units)
	v->quantity = (void*)(new QuantityArray<T>(val, ndim, shape, *units));
    else
	v->quantity = (void*)(new QuantityArray<T>(val, ndim, shape));
    if (cpy == NULL)
	delete val;
    else
	free(shape);
}


static PyObject* quantity_array_new(PyTypeObject* type, PyObject* args, PyObject* kwargs)
{
    PyObject* valueObject;
    PyObject* unitsObject = NULL;
    static char const* kwlist[] = {
	"value",
	"units",
	NULL
    };

    if (!PyArg_ParseTupleAndKeywords(args, kwargs, "O|O:QuantityArray",
				     (char**) kwlist,
				     &valueObject, &unitsObject))
	return NULL;

    QuantityArrayObject* v = (QuantityArrayObject*) type->tp_alloc(type, 0);
    if (v == NULL)
        return NULL;

    if (valueObject == NULL) {
	PyErr_SetString(PyExc_TypeError, "Invalid value");
	return NULL;
    }

    if (PyObject_IsInstance(valueObject, (PyObject*)&QuantityArray_Type)) {
	QuantityArrayObject* vother = (QuantityArrayObject*)valueObject;
	v->subtype = vother->subtype;
	SWITCH_QUANTITY_ARRAY_SUBTYPE(vother, v->quantity = , ->copy_void());
    } else if (unitsObject != NULL) {
	PyObject* units_args = PyTuple_Pack(1, unitsObject);
	unitsObject = PyObject_Call((PyObject*)&Units_Type, units_args, NULL);
	Py_DECREF(units_args);
	if (unitsObject == NULL)
	    return NULL;
	PyArrayObject* cpy = NULL;
	EXTRACT_PYTHON_QX(val, PyObject_GetArrayYgg, (valueObject, v->subtype, cpy),
			  assign_array_, (v, val, cpy, ((UnitsObject*)unitsObject)->units),
			  { PyErr_SetString(PyExc_TypeError, "Expected array of integer, floating point, or complex values"); return NULL; })
	Py_XDECREF(cpy);
    } else {
	PyArrayObject* cpy = NULL;
	EXTRACT_PYTHON_QX(val, PyObject_GetArrayYgg, (valueObject, v->subtype, cpy),
			  assign_array_, (v, val, cpy),
			  { PyErr_SetString(PyExc_TypeError, "Expected array of integer, floating point, or complex values"); return NULL; })
	Py_XDECREF(cpy);
    }
	
    return (PyObject*) v;
}


static PyObject* quantity_array_str(PyObject* self) {
    QuantityArrayObject* v = (QuantityArrayObject*) self;
    std::string s;
    SWITCH_QUANTITY_ARRAY_SUBTYPE(v, s = , ->str());
    return PyUnicode_FromString(s.c_str());
}


static PyObject* quantity_array_repr(PyObject* self) {
    QuantityArrayObject* v = (QuantityArrayObject*) self;
    std::basic_stringstream<char> ss;
    SWITCH_QUANTITY_ARRAY_SUBTYPE(v, , ->display(ss));
    return PyUnicode_FromString(ss.str().c_str());
}


static PyObject* quantity_array_units_get(PyObject* self, void*) {
    QuantityArrayObject* v = (QuantityArrayObject*) self;
    UnitsObject* vu = (UnitsObject*) Units_Type.tp_alloc(&Units_Type, 0);
    if (vu == NULL)
        return NULL;
    vu->units = new Units();
    bool vEmpty = false;
    SWITCH_QUANTITY_SUBTYPE(v, vEmpty = , ->units().is_empty());
    SWITCH_QUANTITY_ARRAY_SUBTYPE(v, *(vu->units) = , ->units());
    if (!vEmpty && vu->units->is_empty()) {
	PyObject* error = Py_BuildValue("s", "Failed to parse units.");
	PyErr_SetObject(units_error, error);
	Py_XDECREF(error);
	return NULL;
    }
    
    return (PyObject*) vu;
}

static int quantity_array_units_set(PyObject* self, PyObject* value, void*) {
    PyObject* units_args = PyTuple_Pack(1, value);
    PyObject* unitsObject = PyObject_Call((PyObject*)&Units_Type, units_args, NULL);
    Py_DECREF(units_args);
    if (unitsObject == NULL)
	return -1;
    
    QuantityArrayObject* v = (QuantityArrayObject*) self;
    SWITCH_QUANTITY_ARRAY_SUBTYPE(v, , ->convert_to(*(((UnitsObject*)unitsObject)->units)));
    return 0;
}

template<typename T>
static PyObject* do_quantity_array_value_get(QuantityArray<T>* x, void*) {
    const T* val = x->value();
    int ndim = (int)(x->ndim());
    npy_intp* shape = (npy_intp*)malloc(ndim * sizeof(npy_intp));
    for (int i = 0; i < ndim; i++)
	shape[i] = (npy_intp)(x->shape()[i]);
    PyObject* out = PyObject_FromArrayYgg(val, ndim, shape);
    free(shape);
    return out;
}

static PyObject* quantity_array_value_get(PyObject* self, void*) {
    QuantityArrayObject* v = (QuantityArrayObject*) self;
    SWITCH_QUANTITY_ARRAY_SUBTYPE_CALL(v, return do_quantity_array_value_get, NULL);
    return NULL;
}

template<typename T, typename Tval>
static int do_quantity_array_value_set_lvl2(QuantityArray<T>* x, Tval* value,
					    PyArrayObject* cpy,
					    RAPIDJSON_ENABLEIF((YGGDRASIL_IS_CASTABLE(Tval, T)))) {
    SizeType ndim = 0;
    SizeType* shape = NULL;
    if (cpy == NULL) {
	ndim = 1;
	shape = &ndim;
    } else {
	ndim = (SizeType)PyArray_NDIM(cpy);
	npy_intp* np_shape = PyArray_SHAPE(cpy);
	shape = (SizeType*)malloc(ndim * sizeof(SizeType));
	if (!shape)
	    return -1;
	for (SizeType i = 0; i < ndim; i++)
	    shape[i] = (SizeType)(np_shape[i]);
    }
    x->set_value(value, ndim, shape);
    if (cpy != NULL)
	free(shape);
    return 0;
}
template<typename T, typename Tval>
static int do_quantity_array_value_set_lvl2(QuantityArray<T>* x, Tval* value,
					    PyArrayObject* cpy,
					    RAPIDJSON_DISABLEIF((YGGDRASIL_IS_CASTABLE(Tval, T)))) {
    return -1;
}

template<typename Tval>
static int do_quantity_array_value_set_lvl1(QuantityArrayObject* v, Tval* value,
					    PyArrayObject* cpy) {
    SWITCH_QUANTITY_ARRAY_SUBTYPE_CALL(v, return do_quantity_array_value_set_lvl2, value, cpy)
    return -1;
}

static int quantity_array_value_set(PyObject* self, PyObject* value, void*) {
    QuantityArrayObject* v = (QuantityArrayObject*) self;
    QuantitySubType value_subtype;
    PyArrayObject* cpy = NULL;
    int out = -1;
    EXTRACT_PYTHON_QX(val, PyObject_GetArrayYgg, (value, value_subtype, cpy),
		      out = do_quantity_array_value_set_lvl1,
		      (v, val, cpy), out = -1)
    Py_XDECREF(cpy);
    return out;
}

static PyObject* quantity_array_is_compatible(PyObject* self, PyObject* args, PyObject* kwargs) {
    PyObject* otherObject;
    const UnitsObject* other;
    bool created = false;
    
    if (!PyArg_ParseTuple(args, "O", &otherObject))
	return NULL;

    if (PyObject_IsInstance(otherObject, (PyObject*)&QuantityArray_Type)) {
	other = (UnitsObject*)quantity_array_units_get(otherObject, NULL);
    } else if (PyObject_IsInstance(otherObject, (PyObject*)&Units_Type)) {
	other = (UnitsObject*)otherObject;
    } else {
	other = (UnitsObject*)PyObject_Call((PyObject*)&Units_Type, args, NULL);
	created = true;
    }
    if (other == NULL)
        return NULL;
    
    QuantityArrayObject* v = (QuantityArrayObject*) self;
    bool result = false;
    SWITCH_QUANTITY_ARRAY_SUBTYPE(v, result = , ->is_compatible(*other->units));
    if (created)
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
    bool result;
    SWITCH_QUANTITY_ARRAY_SUBTYPE(v, result = , ->is_dimensionless());
    if (result) {
	Py_INCREF(Py_True);
	return Py_True;
    }
    Py_INCREF(Py_False);
    return Py_False;
}


template <typename Ta, typename Tb>
static PyObject* do_quantity_array_is_equivalent(QuantityArray<Ta>* a, QuantityArray<Tb>* b,
						 RAPIDJSON_DISABLEIF((YGGDRASIL_IS_CASTABLE(Tb, Ta)))) {
    SET_ERROR(units_error, "Incompatible QuantityArray value types.", NULL);
    return NULL;
}
template <typename Ta, typename Tb>
static PyObject* do_quantity_array_is_equivalent(QuantityArray<Ta>* a, QuantityArray<Tb>* b,
						 RAPIDJSON_ENABLEIF((YGGDRASIL_IS_CASTABLE(Tb, Ta)))) {
    if (a->equivalent_to(*b)) {
	Py_INCREF(Py_True);
	return Py_True;
    }
    Py_INCREF(Py_False);
    return Py_False;
}


template<typename T>
static PyObject* quantity_array_is_equivalent_nested(QuantityArray<T>* b,
						     QuantityArrayObject* va) {
    SWITCH_QUANTITY_ARRAY_SUBTYPE_CALL(va, return do_quantity_array_is_equivalent, b)
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

    SWITCH_QUANTITY_ARRAY_SUBTYPE_CALL(vb, return quantity_array_is_equivalent_nested, va)
}


static PyObject* quantity_array_to(PyObject* self, PyObject* args) {
    PyObject* unitsObject;

    if (!PyArg_ParseTuple(args, "O", &unitsObject))
	return NULL;

    PyObject* units_args = PyTuple_Pack(1, unitsObject);
    unitsObject = PyObject_Call((PyObject*)&Units_Type, units_args, NULL);
    Py_DECREF(units_args);
    if (unitsObject == NULL)
	return NULL;

    QuantityArrayObject* v = (QuantityArrayObject*) self;
    bool compat = false;
    SWITCH_QUANTITY_ARRAY_SUBTYPE(v, compat = , ->is_compatible(*(((UnitsObject*)unitsObject)->units)));
    if (!compat) {
	PyObject* error = Py_BuildValue("s", "Incompatible units");
	PyErr_SetObject(units_error, error);
	Py_XDECREF(error);
	return NULL;
    }

    PyObject* quantity_array_args = PyTuple_Pack(1, self);
    PyObject* out = quantity_array_new(&QuantityArray_Type, quantity_array_args, NULL);
    Py_DECREF(quantity_array_args);
    if (out == NULL)
	return NULL;

    QuantityArrayObject* vout = (QuantityArrayObject*) out;
    SWITCH_QUANTITY_ARRAY_SUBTYPE(vout, , ->convert_to(*(((UnitsObject*)unitsObject)->units)));
    return out;
}


template<typename T>
static PyObject* quantity_array_richcompare_nest(QuantityArray<T>* vself,
						 QuantityArrayObject* vsolf0,
						 int op) {
    QuantityArray<T>* vsolf = (QuantityArray<T>*)(vsolf0->quantity);
    switch (op) {
    case (Py_LT):
    case (Py_LE):
    case (Py_GT):
    case (Py_GE): {
	if (vsolf->units() != vself->units()) {
	    PyObject* error = Py_BuildValue("s", "Comparison invalid for QuantityArray instances with different units, convert one first.");
	    PyErr_SetObject(units_error, error);
	    Py_XDECREF(error);
	    return NULL;
	}
	Py_RETURN_RICHCOMPARE(*vself, *vsolf, op);
    }
    case (Py_EQ):
    case (Py_NE):
	Py_RETURN_RICHCOMPARE(*vself, *vsolf, op);
    default:
	Py_INCREF(Py_NotImplemented);
	return Py_NotImplemented;
    }
}


static PyObject* quantity_array_richcompare(PyObject *self, PyObject *other, int op) {
    QuantityArrayObject* vself = (QuantityArrayObject*) self;
    QuantityArrayObject* vsolf = (QuantityArrayObject*) other;
    if (vself->subtype != vsolf->subtype) {
	Py_INCREF(Py_False);
	return Py_False;
    }
    SWITCH_QUANTITY_ARRAY_SUBTYPE_CALL(vself, return quantity_array_richcompare_nest,
				       vsolf, op)
}


// Number operations
static QuantityArrayObject* get_quantity_array(PyObject *a) {
    QuantityArrayObject* va = NULL;
    if (PyObject_IsInstance(a, (PyObject*)&QuantityArray_Type)) {
	va = (QuantityArrayObject*)a;
    } else {
	PyObject* quantity_array_args = PyTuple_Pack(1, a);
	va = (QuantityArrayObject*)quantity_array_new(&QuantityArray_Type, quantity_array_args, NULL);
	Py_DECREF(quantity_array_args);
	if (va == NULL)
	    return NULL;
    }
    return va;
}


template <typename Ta, typename Tb>
static void* do_quantity_array_op(QuantityArray<Ta>* a, QuantityArray<Tb>* b, BinaryOps op,
				  bool inplace=false,
				  RAPIDJSON_DISABLEIF((YGGDRASIL_IS_CASTABLE(Tb, Ta)))) {
    SET_ERROR(units_error, "Incompatible QuantityArray value types.", NULL);
}
template <typename Ta, typename Tb>
static void* do_quantity_array_op(QuantityArray<Ta>* a, QuantityArray<Tb>* b, BinaryOps op,
				  bool inplace=false,
				  RAPIDJSON_ENABLEIF((YGGDRASIL_IS_CASTABLE(Tb, Ta)))) {
    QuantityArray<Ta>* out;
    if (inplace)
	out = a;
    else
	out = new QuantityArray<Ta>();
    if (!(a->is_same_shape(*b) || (a->nelements() == 1) || (b->nelements() == 1)))
	SET_ERROR(units_error, "Cannot perform operations between QuantityArray instances with different shapes", NULL)
    switch (op) {
    case (binaryOpAdd): {
	if (!a->is_compatible(*b))
	    SET_ERROR(units_error, "Cannot add QuantityArray instances with incompatible units", NULL)
	if (inplace)
	    *out += *b;
	else
	    *out = *a + *b;
	break;
    }
    case (binaryOpSubtract): {
	if (!a->is_compatible(*b))
	    SET_ERROR(units_error, "Cannot subtract QuantityArray instances with incompatible units", NULL)
	if (inplace)
	    *out -= *b;
	else
	    *out = *a - *b;
	break;
    }
    case (binaryOpMultiply): {
	if (inplace)
	    *out *= *b;
	else
	    *out = *a * *b;
	break;
    }
    case (binaryOpDivide): {
	if (inplace)
	    *out /= *b;
	else
	    *out = *a / *b;
	break;
    }
    case (binaryOpModulo): {
	if (inplace)
	    *out %= *b;
	else
	    *out = *a % *b;
	break;
    }
    case (binaryOpFloorDivide): {
	if (inplace)
	    *out /= *b;
	else
	    *out = *a / *b;
	out->floor_inplace();
	break;
    }
    }
    return (void*)out;
}


template <typename Tb>
static void* do_quantity_array_op_lvl2(QuantityArray<Tb>* b, QuantityArrayObject* va, BinaryOps op,
				       bool inplace=false) {
    SWITCH_QUANTITY_ARRAY_SUBTYPE_CALL(va, return do_quantity_array_op, b, op, inplace)
}


static PyObject* do_quantity_array_op_lvl1(PyObject *a, PyObject *b, BinaryOps op,
					   bool inplace=false) {
    // if (inplace && !PyObject_IsInstance(a, (PyObject*)&QuantityArray_Type) && PyObject_IsInstance(b, (PyObject*)&QuantityArray_Type))
    // 	return do_quantity_array_op_lvl1(b, a, op, true);
    QuantityArrayObject* va = get_quantity_array(a);
    QuantityArrayObject* vb = get_quantity_array(b);
    if ((va == NULL) || (vb == NULL))
	return NULL;
    QuantityArrayObject* out;
    if (inplace && PyObject_IsInstance(a, (PyObject*)&QuantityArray_Type)) {
	out = va;
	Py_INCREF(a);
    } else {
	out = (QuantityArrayObject*) QuantityArray_Type.tp_alloc(&QuantityArray_Type, 0);
	out->subtype = va->subtype;
    }
    SWITCH_QUANTITY_ARRAY_SUBTYPE_CALL(vb, out->quantity = do_quantity_array_op_lvl2, va, op, inplace)
    if (out->quantity == NULL)
	return NULL;
    return (PyObject*) out;
}
    

static PyObject* quantity_array_add(PyObject *a, PyObject *b)
{ return do_quantity_array_op_lvl1(a, b, binaryOpAdd); }
static PyObject* quantity_array_subtract(PyObject *a, PyObject *b)
{ return do_quantity_array_op_lvl1(a, b, binaryOpSubtract); }
static PyObject* quantity_array_multiply(PyObject *a, PyObject *b)
{ return do_quantity_array_op_lvl1(a, b, binaryOpMultiply); }
static PyObject* quantity_array_divide(PyObject *a, PyObject *b)
{ return do_quantity_array_op_lvl1(a, b, binaryOpDivide); }
static PyObject* quantity_array_floor_divide(PyObject *a, PyObject *b)
{ return do_quantity_array_op_lvl1(a, b, binaryOpFloorDivide); }
static PyObject* quantity_array_modulo(PyObject *a, PyObject *b)
{ return do_quantity_array_op_lvl1(a, b, binaryOpModulo); }
static PyObject* quantity_array_add_inplace(PyObject *a, PyObject *b)
{ return do_quantity_array_op_lvl1(a, b, binaryOpAdd, true); }
static PyObject* quantity_array_subtract_inplace(PyObject *a, PyObject *b)
{ return do_quantity_array_op_lvl1(a, b, binaryOpSubtract, true); }
static PyObject* quantity_array_multiply_inplace(PyObject *a, PyObject *b)
{ return do_quantity_array_op_lvl1(a, b, binaryOpMultiply, true); }
static PyObject* quantity_array_divide_inplace(PyObject *a, PyObject *b)
{ return do_quantity_array_op_lvl1(a, b, binaryOpDivide, true); }
static PyObject* quantity_array_modulo_inplace(PyObject *a, PyObject *b)
{ return do_quantity_array_op_lvl1(a, b, binaryOpModulo, true); }
static PyObject* quantity_array_floor_divide_inplace(PyObject *a, PyObject *b)
{ return do_quantity_array_op_lvl1(a, b, binaryOpFloorDivide, true); }

template<typename Tbase, typename Tmod, typename T>
static void* quantity_array_power_lvl4(QuantityArray<Tbase>* base, QuantityArray<Tmod>* mod, T* val,
				 bool inplace=false) {
    QuantityArray<Tbase>* out;
    if (inplace) {
	out = base;
	out->inplace_pow(*val);
    } else {
	out = new QuantityArray<Tbase>();
	*out = base->pow(*val);
    }
    *out %= *mod;
    return (void*)out;
}
template<typename Tbase, typename Tmod, typename T>
static void* quantity_array_power_lvl4(QuantityArray<Tbase>* base, QuantityArray<Tmod>* mod, std::complex<T>* val,
				       bool inplace=false) {
    PyErr_SetString(PyExc_TypeError, "Complex exponent not supported");
    return NULL;
}
template<typename Tmod, typename T>
static void* quantity_array_power_lvl3(QuantityArray<Tmod>* mod, T* val, QuantityArrayObject* vbase,
				       bool inplace=false) {
    SWITCH_QUANTITY_ARRAY_SUBTYPE_CALL(vbase, return quantity_array_power_lvl4, mod, val, inplace);
}
template<typename T>
static void* quantity_array_power_lvl2(T* val, QuantityArrayObject* vbase, QuantityArrayObject* vmod,
				       bool inplace=false) {
    SWITCH_QUANTITY_ARRAY_SUBTYPE_CALL(vmod, return quantity_array_power_lvl3, val, vbase, inplace);
}
static PyObject* quantity_array_power_lvl1(PyObject *base, PyObject *exp, PyObject *mod,
					   bool inplace=false) {
    QuantityArrayObject* vbase = get_quantity_array(base);
    QuantityArrayObject* vmod = get_quantity_array(mod);
    if ((vbase == NULL) || (vmod == NULL))
	return NULL;
    if (PyObject_IsInstance(exp, (PyObject*)&QuantityArray_Type))
	SET_ERROR(units_error, "Raising to a QuantityArray power not supported", NULL);
    QuantityArrayObject* out;
    if (inplace && PyObject_IsInstance(base, (PyObject*)&QuantityArray_Type)) {
	out = vbase;
	Py_INCREF(base);
    } else {
	out = (QuantityArrayObject*) QuantityArray_Type.tp_alloc(&QuantityArray_Type, 0);
	out->subtype = vbase->subtype;
    }
    QuantitySubType subtype_exp;
    PyArrayObject* cpy = NULL;
    EXTRACT_PYTHON_QX(tmp, PyObject_GetArrayYgg,
		      (exp, subtype_exp, cpy),
		      out->quantity = quantity_array_power_lvl2,
		      (tmp, vbase, vmod, inplace),
		      { PyErr_SetString(PyExc_TypeError, "Expected array of integer, floating point, or complex values"); return NULL; })
    Py_XDECREF(cpy);
    if (out->quantity == NULL)
	return NULL;
    return (PyObject*) out;
}
static PyObject* quantity_array_power(PyObject *base, PyObject *exp, PyObject *mod)
{ return quantity_array_power_lvl1(base, exp, mod); }
static PyObject* quantity_array_power_inplace(PyObject *base, PyObject *exp, PyObject *mod)
{ return quantity_array_power_lvl1(base, exp, mod, true); }


////////////
// Module //
////////////


static PyMethodDef units_functions[] = {
    {NULL, NULL, 0, NULL} /* sentinel */
};


static int
units_module_exec(PyObject* m)
{
    if (PyType_Ready(&Units_Type) < 0)
        return -1;

    if (PyType_Ready(&Quantity_Type) < 0)
        return -1;

    if (PyType_Ready(&QuantityArray_Type) < 0)
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

    units_error = PyErr_NewException("rapidjson.UnitsError",
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
    "units",                    /* m_name */
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
