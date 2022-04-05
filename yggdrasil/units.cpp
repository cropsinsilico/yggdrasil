// -*- coding: utf-8 -*-
// :Project:   python-rapidjson -- Python extension module
// :Author:    Meagan Lang <langmm.astro@gmail.com>
// :License:   BSD License
//

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

    const char* exprStr;
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
    
    if (!PyArg_ParseTuple(args, "O", &otherObject))
	return NULL;

    if (PyObject_IsInstance(otherObject, (PyObject*)&Units_Type)) {
	other = (UnitsObject*)otherObject;
    } else {
        PyErr_SetString(PyExc_TypeError, "Expected a units instance");
        return NULL;
    }
    
    UnitsObject* v = (UnitsObject*) self;
    bool result = v->units->is_compatible(*other->units);
    if (result)
	return Py_True;
    return Py_False;
    
}


static PyObject* units_is_dimensionless(PyObject* self, PyObject* args) {
    UnitsObject* v = (UnitsObject*) self;
    bool result = v->units->is_dimensionless();
    if (result)
	return Py_True;
    return Py_False;
}


static PyObject* units_richcompare(PyObject *self, PyObject *other, int op) {
    UnitsObject* vself = (UnitsObject*) self;
    UnitsObject* vsolf = (UnitsObject*) other;
    switch (op) {
    case (Py_EQ): {
	if (*(vself->units) == *(vsolf->units))
	    return Py_True;
	return Py_False;
    }
    case (Py_NE): {
	if (*(vself->units) != *(vsolf->units))
	    return Py_True;
	return Py_False;
    }
    default:
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
T* PyObject_GetScalarYgg(PyObject*, QuantitySubType&) {
    return NULL;
}
template<>
float* PyObject_GetScalarYgg<float>(PyObject*, QuantitySubType& subtype) {
    subtype = kFloatQuantitySubType;
    return NULL;
}
template<>
double* PyObject_GetScalarYgg<double>(PyObject* v, QuantitySubType& subtype) {
    subtype = kDoubleQuantitySubType;
    if (PyFloat_AsDouble(v)) {
	double d = PyFloat_AsDouble(v);
	if (d == -1.0 && PyErr_Occurred())
	    return NULL;
	return new double(d);
    }
    return NULL;
}
template<>
int8_t* PyObject_GetScalarYgg<int8_t>(PyObject*, QuantitySubType& subtype) {
    subtype = kInt8QuantitySubType;
    return NULL;
}
template<>
int16_t* PyObject_GetScalarYgg<int16_t>(PyObject*, QuantitySubType& subtype) {
    subtype = kInt16QuantitySubType;
    return NULL;
}
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
    // _PyLong_GetScalarYgg(int32_t);
    return NULL;
}
template<>
int64_t* PyObject_GetScalarYgg<int64_t>(PyObject* v, QuantitySubType& subtype) {
    subtype = kInt64QuantitySubType;
    // _PyLong_GetScalarYgg(int64_t);
    return NULL;
}
template<>
uint8_t* PyObject_GetScalarYgg<uint8_t>(PyObject*, QuantitySubType& subtype) {
    subtype = kUint8QuantitySubType;
    return NULL;
}
template<>
uint16_t* PyObject_GetScalarYgg<uint16_t>(PyObject*, QuantitySubType& subtype) {
    subtype = kUint16QuantitySubType;
    return NULL;
}
template<>
uint32_t* PyObject_GetScalarYgg<uint32_t>(PyObject*, QuantitySubType& subtype) {
    subtype = kUint32QuantitySubType;
    return NULL;
}
template<>
uint64_t* PyObject_GetScalarYgg<uint64_t>(PyObject*, QuantitySubType& subtype) {
    subtype = kUint64QuantitySubType;
    return NULL;
}
template<>
std::complex<float>* PyObject_GetScalarYgg<std::complex<float> >(PyObject*, QuantitySubType& subtype) {
    subtype = kComplexFloatQuantitySubType;
    return NULL;
}
template<>
std::complex<double>* PyObject_GetScalarYgg<std::complex<double> >(PyObject*, QuantitySubType& subtype) {
    subtype = kComplexDoubleQuantitySubType;
    return NULL;
}


#define CASE_QUANTITY_SUBTYPE(var, lhs, rhs, value, type)	\
    case (value): { lhs ((Quantity<type>*) var->quantity) rhs; break; }

#define SWITCH_QUANTITY_SUBTYPE(var, lhs, rhs)				\
    switch(var->subtype) {						\
    CASE_QUANTITY_SUBTYPE(var, lhs, rhs, kFloatQuantitySubType, float)	\
    CASE_QUANTITY_SUBTYPE(var, lhs, rhs, kDoubleQuantitySubType, double)  \
    CASE_QUANTITY_SUBTYPE(var, lhs, rhs, kUint8QuantitySubType, uint8_t)  \
    CASE_QUANTITY_SUBTYPE(var, lhs, rhs, kUint16QuantitySubType, uint16_t) \
    CASE_QUANTITY_SUBTYPE(var, lhs, rhs, kUint32QuantitySubType, uint32_t) \
    CASE_QUANTITY_SUBTYPE(var, lhs, rhs, kUint64QuantitySubType, uint64_t) \
    CASE_QUANTITY_SUBTYPE(var, lhs, rhs, kInt8QuantitySubType, int8_t)  \
    CASE_QUANTITY_SUBTYPE(var, lhs, rhs, kInt16QuantitySubType, int16_t) \
    CASE_QUANTITY_SUBTYPE(var, lhs, rhs, kInt32QuantitySubType, int32_t) \
    CASE_QUANTITY_SUBTYPE(var, lhs, rhs, kInt64QuantitySubType, int64_t) \
    CASE_QUANTITY_SUBTYPE(var, lhs, rhs, kComplexFloatQuantitySubType, std::complex<float>) \
    CASE_QUANTITY_SUBTYPE(var, lhs, rhs, kComplexDoubleQuantitySubType, std::complex<double>) \
    }

#define CASE_QUANTITY_SUBTYPE_CALL(var, lhs, value, type, ...)		\
    case (value): { lhs (((Quantity<type>*) var->quantity), __VA_ARGS__); break; }

#define SWITCH_QUANTITY_SUBTYPE_CALL(var, lhs, ...)			\
    switch(var->subtype) {						\
    CASE_QUANTITY_SUBTYPE_CALL(var, lhs, kFloatQuantitySubType, float, __VA_ARGS__)	\
    CASE_QUANTITY_SUBTYPE_CALL(var, lhs, kDoubleQuantitySubType, double, __VA_ARGS__)  \
    CASE_QUANTITY_SUBTYPE_CALL(var, lhs, kUint8QuantitySubType, uint8_t, __VA_ARGS__)  \
    CASE_QUANTITY_SUBTYPE_CALL(var, lhs, kUint16QuantitySubType, uint16_t, __VA_ARGS__) \
    CASE_QUANTITY_SUBTYPE_CALL(var, lhs, kUint32QuantitySubType, uint32_t, __VA_ARGS__) \
    CASE_QUANTITY_SUBTYPE_CALL(var, lhs, kUint64QuantitySubType, uint64_t, __VA_ARGS__) \
    CASE_QUANTITY_SUBTYPE_CALL(var, lhs, kInt8QuantitySubType, int8_t, __VA_ARGS__)  \
    CASE_QUANTITY_SUBTYPE_CALL(var, lhs, kInt16QuantitySubType, int16_t, __VA_ARGS__) \
    CASE_QUANTITY_SUBTYPE_CALL(var, lhs, kInt32QuantitySubType, int32_t, __VA_ARGS__) \
    CASE_QUANTITY_SUBTYPE_CALL(var, lhs, kInt64QuantitySubType, int64_t, __VA_ARGS__) \
    CASE_QUANTITY_SUBTYPE_CALL(var, lhs, kComplexFloatQuantitySubType, std::complex<float>, __VA_ARGS__) \
    CASE_QUANTITY_SUBTYPE_CALL(var, lhs, kComplexDoubleQuantitySubType, std::complex<double>, __VA_ARGS__) \
    }

#define EXTRACT_PYTHON_VALUE_TYPE(var, pyObj, tmp, method, args, T)	\
    if (T* tmp = PyObject_GetScalarYgg<T>(pyObj, var)) {		\
	method<T> args;							\
    }

#define EXTRACT_PYTHON_VALUE(var, pyObj, tmp, method, args, error)	\
    EXTRACT_PYTHON_VALUE_TYPE(var, pyObj, tmp, method, args, float)	\
    else EXTRACT_PYTHON_VALUE_TYPE(var, pyObj, tmp, method, args, double) \
    else EXTRACT_PYTHON_VALUE_TYPE(var, pyObj, tmp, method, args, int8_t) \
    else EXTRACT_PYTHON_VALUE_TYPE(var, pyObj, tmp, method, args, int16_t) \
    else EXTRACT_PYTHON_VALUE_TYPE(var, pyObj, tmp, method, args, int32_t) \
    else EXTRACT_PYTHON_VALUE_TYPE(var, pyObj, tmp, method, args, int64_t) \
    else EXTRACT_PYTHON_VALUE_TYPE(var, pyObj, tmp, method, args, uint8_t) \
    else EXTRACT_PYTHON_VALUE_TYPE(var, pyObj, tmp, method, args, uint16_t) \
    else EXTRACT_PYTHON_VALUE_TYPE(var, pyObj, tmp, method, args, uint32_t) \
    else EXTRACT_PYTHON_VALUE_TYPE(var, pyObj, tmp, method, args, uint64_t) \
    else EXTRACT_PYTHON_VALUE_TYPE(var, pyObj, tmp, method, args, std::complex<float>)	\
    else EXTRACT_PYTHON_VALUE_TYPE(var, pyObj, tmp, method, args, std::complex<double>) \
    else { error; }
    
    


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
     "The quantity's value (in the current unit system)."},
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
    SWITCH_QUANTITY_SUBTYPE(v, *(vu->units) = , ->units());
    if (vu->units->is_empty()) {
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

static PyObject* quantity_value_get(PyObject* self, void*) {
    return NULL;
}

static int quantity_value_set(PyObject* self, PyObject* value, void*) {
    return -1;
}

static PyObject* quantity_is_compatible(PyObject* self, PyObject* args, PyObject* kwargs) {
    PyObject* otherObject;
    const UnitsObject* other;
    
    if (!PyArg_ParseTuple(args, "O", &otherObject))
	return NULL;

    if (PyObject_IsInstance(otherObject, (PyObject*)&Quantity_Type)) {
	other = (UnitsObject*)quantity_units_get(otherObject, NULL);
    } else {
	other = (UnitsObject*)PyObject_Call((PyObject*)&Units_Type, args, NULL);
    }
    if (other == NULL) {
        PyErr_SetString(PyExc_TypeError, "Expected a units instance");
        return NULL;
    }
    
    QuantityObject* v = (QuantityObject*) self;
    bool result = false;
    SWITCH_QUANTITY_SUBTYPE(v, result = , ->is_compatible(*other->units));
    Py_DECREF(other);
    if (result)
	return Py_True;
    return Py_False;
    
}


static PyObject* quantity_is_dimensionless(PyObject* self, PyObject* args) {
    QuantityObject* v = (QuantityObject*) self;
    bool result;
    SWITCH_QUANTITY_SUBTYPE(v, result = , ->is_dimensionless());
    if (result)
	return Py_True;
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
    if (a->equivalent_to(*b))
	return Py_True;
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
	return Py_NotImplemented;
    }
}


static PyObject* quantity_richcompare(PyObject *self, PyObject *other, int op) {
    QuantityObject* vself = (QuantityObject*) self;
    QuantityObject* vsolf = (QuantityObject*) other;
    if (vself->subtype != vsolf->subtype)
	return Py_False;
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

    // if (PyType_Ready(&QuantityArray_Type) < 0)
    //     return -1;

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

    // Py_INCREF(&QuantityArray_Type);
    // if (PyModule_AddObject(m, "QuantityArray", (PyObject*) &QuantityArray_Type) < 0) {
    //     Py_DECREF(&QuantityArray_Type);
    //     return -1;
    // }

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
