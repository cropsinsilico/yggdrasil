// -*- coding: utf-8 -*-
// :Project:   python-rapidjson -- Python extension module
// :Author:    Meagan Lang <langmm.astro@gmail.com>
// :License:   BSD License
//

#ifndef _USE_MATH_DEFINES
#define _USE_MATH_DEFINES
#endif

#include <Python.h>

#include "rapidjson/ply.h"
#include "rapidjson/obj.h"
#include "rapidjson/precision.h"
#include "rapidjson/rapidjson.h"


using namespace rapidjson;


static PyObject* geom_error = NULL;


// TODO: classes for element sets, elements, subtypes to allow set via dict?


//////////////////////////
// Forward declarations //
//////////////////////////

// Ply
static void ply_dealloc(PyObject* self);
static PyObject* ply_new(PyTypeObject* type, PyObject* args, PyObject* kwargs);
static PyObject* ply_richcompare(PyObject *self, PyObject *other, int op);
static PyObject* ply_get_elements(PyObject* self, PyObject* args, PyObject* kwargs);
static PyObject* ply_add_elements(PyObject* self, PyObject* args, PyObject* kwargs);
static PyObject* ply_as_dict(PyObject* self, PyObject* args, PyObject* kwargs);
static PyObject* ply_from_dict(PyObject* self, PyObject* args, PyObject* kwargs);
static PyObject* ply_count_elements(PyObject* self, PyObject* args, PyObject* kwargs);
static PyObject* ply_append(PyObject* self, PyObject* args, PyObject* kwargs);
static PyObject* ply_bounds_get(PyObject* self, void*);
static PyObject* ply_mesh_get(PyObject* self, void*);
static PyObject* ply_str(PyObject* self);
static Py_ssize_t ply_size(PyObject* self);
static PyObject* ply_subscript(PyObject* self, PyObject* key);
static int ply_contains(PyObject* self, PyObject* value);
static PyObject* ply_items(PyObject* self, PyObject* args, PyObject* kwargs);
static PyObject* ply_add_colors(PyObject* self, PyObject* args, PyObject* kwargs);
static PyObject* ply_get_colors(PyObject* self, PyObject* args, PyObject* kwargs);


// Objwavefront
static void objwavefront_dealloc(PyObject* self);
static PyObject* objwavefront_new(PyTypeObject* type, PyObject* args, PyObject* kwargs);
static PyObject* objwavefront_richcompare(PyObject *self, PyObject *other, int op);
static PyObject* objwavefront_get_elements(PyObject* self, PyObject* args, PyObject* kwargs);
static PyObject* objwavefront_add_elements(PyObject* self, PyObject* args, PyObject* kwargs);
static PyObject* objwavefront_as_dict(PyObject* self, PyObject* args, PyObject* kwargs);
static PyObject* objwavefront_from_dict(PyObject* self, PyObject* args, PyObject* kwargs);
static PyObject* objwavefront_count_elements(PyObject* self, PyObject* args, PyObject* kwargs);
static PyObject* objwavefront_append(PyObject* self, PyObject* args, PyObject* kwargs);
static PyObject* objwavefront_bounds_get(PyObject* self, void*);
static PyObject* objwavefront_mesh_get(PyObject* self, void*);
static PyObject* objwavefront_str(PyObject* self);
static Py_ssize_t objwavefront_size(PyObject* self);
static PyObject* objwavefront_subscript(PyObject* self, PyObject* key);
static int objwavefront_contains(PyObject* self, PyObject* value);
static PyObject* objwavefront_items(PyObject* self, PyObject* args, PyObject* kwargs);
static PyObject* objwavefront_add_colors(PyObject* self, PyObject* args, PyObject* kwargs);
static PyObject* objwavefront_get_colors(PyObject* self, PyObject* args, PyObject* kwargs);


/////////
// Ply //
/////////


typedef struct {
    PyObject_HEAD
    Ply *ply;
} PlyObject;


PyDoc_STRVAR(ply_doc,
             "Ply(vertices, faces=None, edges=None)\n"
             "\n"
             "Create and return a new Ply instance from the given"
             " set of vertices, faces, and edges.");


// Handle missing properties
static PyMethodDef ply_methods[] = {
    {"get_elements", (PyCFunction) ply_get_elements,
     METH_VARARGS | METH_KEYWORDS,
     "Get all elements of a given type."},
    {"add_elements", (PyCFunction) ply_add_elements,
     METH_VARARGS, "Add elements of a given type."},
    {"as_dict", (PyCFunction) ply_as_dict,
     METH_VARARGS | METH_KEYWORDS,
     "Get the structure as a dictionary."},
    {"from_dict", (PyCFunction) ply_from_dict,
     METH_VARARGS | METH_CLASS,
     "Create a Ply instance from a dictionary of elements."},
    {"count_elements", (PyCFunction) ply_count_elements,
     METH_VARARGS,
     "Get the number of elements of a given type in the structure."},
    {"append", (PyCFunction) ply_append,
     METH_VARARGS,
     "Append another 3D structure."},
    {"items", (PyCFunction) ply_items,
     METH_NOARGS,
     "Get the dict-like list of items in the structure."},
    {"get_colors", (PyCFunction) ply_get_colors,
     METH_VARARGS | METH_KEYWORDS,
     "Get colors associated with elements of a given type."},
    {"add_colors", (PyCFunction) ply_add_colors,
     METH_VARARGS,
     "Set colors associated with elements of a given type."},
    {NULL}  /* Sentinel */
};


static PyGetSetDef ply_properties[] = {
    {"bounds", ply_bounds_get, NULL,
     "The minimum & maximum bounds for the structure in x, y, & z.", NULL},
    {"mesh", ply_mesh_get, NULL,
     "The 3D mesh representing the faces in the structure.", NULL},
    {NULL}
};


static PyMappingMethods ply_mapping = {
    ply_size, ply_subscript, NULL
};


static PySequenceMethods ply_seq = {
    ply_size, NULL, NULL, NULL, NULL, NULL, NULL,
    ply_contains,
    NULL, NULL
};


static PyTypeObject Ply_Type = {
    PyVarObject_HEAD_INIT(NULL, 0)
    "rapidjson.Ply",                /* tp_name */
    sizeof(PlyObject),              /* tp_basicsize */
    0,                              /* tp_itemsize */
    (destructor) ply_dealloc,       /* tp_dealloc */
    0,                              /* tp_print */
    0,                              /* tp_getattr */
    0,                              /* tp_setattr */
    0,                              /* tp_compare */
    0,                              /* tp_repr */
    0,                              /* tp_as_number */
    &ply_seq,                       /* tp_as_sequence */
    &ply_mapping,                   /* tp_as_mapping */
    0,                              /* tp_hash */
    0,                              /* tp_call */
    ply_str,                        /* tp_str */
    0,                              /* tp_getattro */
    0,                              /* tp_setattro */
    0,                              /* tp_as_buffer */
    Py_TPFLAGS_DEFAULT | Py_TPFLAGS_BASETYPE, /* tp_flags */
    ply_doc,                        /* tp_doc */
    0,                              /* tp_traverse */
    0,                              /* tp_clear */
    ply_richcompare,                /* tp_richcompare */
    0,                              /* tp_weaklistoffset */
    0,                              /* tp_iter */
    0,                              /* tp_iternext */
    ply_methods,                    /* tp_methods */
    0,                              /* tp_members */
    ply_properties,                 /* tp_getset */
    0,                              /* tp_base */
    0,                              /* tp_dict */
    0,                              /* tp_descr_get */
    0,                              /* tp_descr_set */
    0,                              /* tp_dictoffset */
    0,                              /* tp_init */
    0,                              /* tp_alloc */
    ply_new,                        /* tp_new */
    PyObject_Del,                   /* tp_free */
};


static void ply_dealloc(PyObject* self)
{
    PlyObject* s = (PlyObject*) self;
    delete s->ply;
    Py_TYPE(self)->tp_free(self);
}


static PyObject* ply_new(PyTypeObject* type, PyObject* args, PyObject* kwargs)
{
    PyObject* vertObject = NULL;
    PyObject* faceObject = NULL;
    PyObject* edgeObject = NULL;

    if (!PyArg_UnpackTuple(args, "Ply", 0, 3,
			   &vertObject, &faceObject, &edgeObject))
	return NULL;
    if (kwargs && !PyArg_ValidateKeywordArguments(kwargs))
	return NULL;

    const char* readFrom = 0;
    if (vertObject && !faceObject && !edgeObject && !kwargs) {
	if (PyDict_Check(vertObject)) {
	    kwargs = vertObject;
	    vertObject = NULL;
	} else if (PyUnicode_Check(vertObject)) {
	    readFrom = PyUnicode_AsUTF8(vertObject);
	    vertObject = NULL;
	} else if (PyBytes_Check(vertObject)) {
	    readFrom = PyBytes_AsString(vertObject);
	    vertObject = NULL;
	}
    }
    
    PlyObject* v = (PlyObject*) type->tp_alloc(type, 0);
    if (v == NULL)
        return NULL;
    v->ply = new Ply();

    if (readFrom) {
	std::stringstream ss;
	ss.str(std::string(readFrom));
	if (!v->ply->read(ss)) {
	    PyErr_SetString(geom_error, "Error reading from string");
	    return NULL;
	}
    }
    
#define ADD_ARRAY(x, name)						\
    if (x != NULL) {							\
	PyObject* x_name = PyUnicode_FromString(#name);			\
	if (x_name == NULL) return NULL;				\
	PyObject* iargs = Py_BuildValue("(OO)", x_name, x);		\
	Py_DECREF(x_name);						\
	if (iargs == NULL) return NULL;					\
	if (ply_add_elements((PyObject*)v, iargs, NULL) == NULL) {	\
	    Py_DECREF(iargs);						\
	    return NULL;						\
	}								\
	Py_DECREF(iargs);						\
    }

    ADD_ARRAY(vertObject, vertex)
    ADD_ARRAY(faceObject, face)
    ADD_ARRAY(edgeObject, edge)

#undef ADD_ARRAY

    if (kwargs) {
	PyObject *key, *value;
	Py_ssize_t pos = 0;
	std::vector<std::string> delayed;
	while (PyDict_Next(kwargs, &pos, &key, &value)) {
	    std::string keyS(PyUnicode_AsUTF8(key));
	    if (keyS.size() > 7 &&
		keyS.substr(keyS.size() - 7) == "_colors") {
		delayed.push_back(keyS);
		continue;
	    }
	    PyObject* iargs = Py_BuildValue("(OO)", key, value);
	    if (ply_add_elements((PyObject*)v, iargs, NULL) == NULL) {
		Py_DECREF(iargs);
		return NULL;
	    }
	    Py_DECREF(iargs);
	}
	for (std::vector<std::string>::iterator it = delayed.begin();
	     it != delayed.end(); it++) {
	    value = PyDict_GetItemString(kwargs, it->c_str());
	    PyObject* iargs = Py_BuildValue("(sO)", it->c_str(), value);
	    if (ply_add_elements((PyObject*)v, iargs, NULL) == NULL) {
		Py_DECREF(iargs);
		return NULL;
	    }
	    Py_DECREF(iargs);
	}
    }

    // if (!v->ply->get_element_set("vertex"))
    // 	v->ply->add_element_set("vertex");
    // if (!v->ply->get_element_set("face"))
    // 	v->ply->add_element_set("face");
    

    if (!v->ply->is_valid()) {
	PyErr_SetString(geom_error, "Structure is invalid. Check that indexes do not exceed the number of vertices");
	return NULL;
    }

    return (PyObject*) v;
}


static PyObject* ply_richcompare(PyObject *self, PyObject *other, int op) {
    PyObject* value = NULL;
    if (!PyObject_IsInstance(other, (PyObject*)&Ply_Type)) {
	switch (op) {
	case (Py_EQ):
	    value = Py_False;
	    break;
	case (Py_NE):
	    value = Py_True;
	    break;
	default:
	    value = Py_NotImplemented;
	}
    } else {
	PlyObject* vself = (PlyObject*) self;
	PlyObject* vsolf = (PlyObject*) other;
	switch (op) {
	case (Py_EQ):
	    value = (*(vself->ply) == *(vsolf->ply)) ? Py_True : Py_False;
	    break;
	case (Py_NE):
	    value = (*(vself->ply) != *(vsolf->ply)) ? Py_True : Py_False;
	    break;
	default:
	    value = Py_NotImplemented;
	}
    }
    Py_INCREF(value);
    return value;
}

static PyObject* ply_get_elements(PyObject* self, PyObject* args, PyObject* kwargs) {
    const char* elementType0 = 0;
    int asArray = 0;
    
    static char const* kwlist[] = {
	"name",
	"as_array",
        NULL
    };
    
    
    if (!PyArg_ParseTupleAndKeywords(args, kwargs, "s|p:", (char**) kwlist,
				     &elementType0, &asArray))
	return NULL;

    std::string elementType(elementType0);

    PlyObject* v = (PlyObject*) self;
    
    const PlyElementSet* elementSet = v->ply->get_element_set(elementType);
    if (elementSet == NULL) {
	PyErr_SetString(PyExc_KeyError, elementType0);
	return NULL;
    }

    PyObject* out = NULL;
    
    if (asArray) {
	
#define GET_ARRAY(T, npT)						\
	size_t N = 0, M = 0;						\
	std::vector<T> vect = v->ply->get_ ## T ## _array(elementType, N, M, true); \
	PyArray_Descr* desc = PyArray_DescrNewFromType(npT);		\
	if (desc == NULL) return NULL;					\
	npy_intp np_shape[2] = { (npy_intp)N, (npy_intp)M };		\
	PyObject* tmp = PyArray_NewFromDescr(&PyArray_Type, desc,	\
					     2, np_shape, NULL,		\
					     (void*)vect.data(), 0, NULL); \
	if (tmp == NULL) return NULL;					\
	out = (PyObject*)PyArray_NewCopy((PyArrayObject*)tmp, NPY_CORDER); \
	Py_DECREF(tmp)
	
	if (elementSet->requires_double()) {
	    GET_ARRAY(double, NPY_DOUBLE);
	} else {
	    GET_ARRAY(int, NPY_INT);
	}
#undef GET_ARRAY
    } else {
	out = PyDict_New();
	if (out == NULL)
	    return NULL;
	{
	    PyObject* val = PyList_New(elementSet->elements.size());
	    if (val == NULL) {
		Py_DECREF(out);
		return NULL;
	    }
	    Py_ssize_t i = 0;
	    for (std::vector<PlyElement>::const_iterator elit = elementSet->elements.begin(); elit != elementSet->elements.end(); elit++, i++) {
		PyObject* item = PyDict_New();
		if (item == NULL) {
		    Py_DECREF(val);
		    Py_DECREF(out);
		    return NULL;
		}
		for (std::vector<std::string>::const_iterator p = elit->property_order.begin(); p != elit->property_order.end(); p++) {
		    PyObject* ival = NULL;
		    if (elit->is_vector(*p)) {
			ival = PyList_New(elit->size());
			if (ival != NULL) {
			    for (size_t iProp = 0; iProp < elit->size(); iProp++) {
				PyObject* iival = NULL;
				if (elit->requires_double(*p))
				    iival = PyFloat_FromDouble(elit->get_value_as<double>(*p, iProp));
				else
				    iival = PyLong_FromLong(elit->get_value_as<long>(*p, iProp));
				if (iival == NULL) {
				    Py_DECREF(ival);
				    Py_DECREF(item);
				    Py_DECREF(val);
				    Py_DECREF(out);
				    return NULL;
				}
				if (PyList_SetItem(ival, iProp, iival) < 0) {
				    Py_DECREF(iival);
				    Py_DECREF(ival);
				    Py_DECREF(item);
				    Py_DECREF(val);
				    Py_DECREF(out);
				    return NULL;
				}
			    }
			}
		    } else if (elit->requires_double(*p)) {
			ival = PyFloat_FromDouble(elit->get_value_as<double>(*p));
		    } else {
			ival = PyLong_FromLong(elit->get_value_as<long>(*p));
		    }
		    if (ival == NULL) {
			Py_DECREF(item);
			Py_DECREF(val);
			Py_DECREF(out);
			return NULL;
		    }
		    if (PyDict_SetItemString(item, p->c_str(), ival) < 0) {
			Py_DECREF(ival);
			Py_DECREF(item);
			Py_DECREF(val);
			Py_DECREF(out);
			return NULL;
		    }
		    Py_DECREF(ival);
		}
		if (PyList_SetItem(val, i, item) < 0) {
		    Py_DECREF(item);
		    Py_DECREF(val);
		    Py_DECREF(out);
		    return NULL;
		}
	    }
	    out = val;
	}
    }
    
    return out;
    
}

static PyObject* ply_add_elements(PyObject* self, PyObject* args, PyObject* kwargs) {
    const char* name0 = 0;
    PyObject* x = NULL;
    
    if (!PyArg_ParseTuple(args, "sO:", &name0, &x))
	return NULL;

    std::string name(name0);

    PlyObject* v = (PlyObject*) self;

    bool isColor = (name.size() > 7 &&
		    name.substr(name.size() - 7) == "_colors");
    if (isColor) {
	name.erase(name.end() - 7, name.end());
	PyObject* iargs = Py_BuildValue("(sO)", name.c_str(), x);
	PyObject* out = ply_add_colors(self, iargs, NULL);
	Py_DECREF(iargs);
	return out;
    }
    
    if (PyList_Check(x)) {
	for (Py_ssize_t i = 0; i < PyList_Size(x); i++) {
	    PyObject* item = PyList_GetItem(x, i);
	    if (item == NULL) return NULL;
	    if (PyDict_Check(item)) {
		PyObject *key, *value;
		Py_ssize_t pos = 0;
		bool isDouble = false;
		std::vector<double> values;
		std::vector<std::string> names;
		std::vector<std::string> colors;
		while (PyDict_Next(item, &pos, &key, &value)) {
		    if (!PyUnicode_Check(key)) {
			PyErr_SetString(PyExc_TypeError, "Ply element keys must be strings");
			return NULL;
		    }
		    std::string iname = std::string(PyUnicode_AsUTF8(key));
		    names.push_back(iname);
		    if (iname == "red" || iname == "blue" || iname == "green")
			colors.push_back(iname);
		    if (PyLong_Check(value)) {
			values.push_back(PyLong_AsDouble(value));
		    } else if (PyFloat_Check(value)) {
			values.push_back(PyFloat_AsDouble(value));
			isDouble = true;
		    } else if (PyList_Check(value)) {
			for (Py_ssize_t j = 0; j < PyList_Size(value); j++) {
			    PyObject* vv = PyList_GetItem(value, j);
			    if (vv == NULL) return NULL;
			    if (PyLong_Check(vv)) {
				values.push_back(PyLong_AsDouble(vv));
			    } else if (PyFloat_Check(vv)) {
				values.push_back(PyFloat_AsDouble(vv));
				isDouble = true;
			    } else if (PyArray_CheckScalar(vv)) {
				PyArray_Descr* desc0 = PyArray_DescrFromScalar(vv);
				if (PyDataType_ISFLOAT(desc0))
				    isDouble = true;
				PyArray_Descr* desc = PyArray_DescrNewFromType(NPY_FLOAT64);
				double d = 0;
				PyArray_CastScalarToCtype(vv, &d, desc);
				values.push_back(d);
				Py_DECREF(desc);
			    } else {
				PyErr_SetString(PyExc_TypeError, "Ply element list values must be integers or floats");
				return NULL;
			    }
			}
		    } else if (PyArray_CheckScalar(value)) {
			PyArray_Descr* desc0 = PyArray_DescrFromScalar(value);
			if (PyDataType_ISFLOAT(desc0))
			    isDouble = true;
			PyArray_Descr* desc = PyArray_DescrNewFromType(NPY_FLOAT64);
			double d = 0;
			PyArray_CastScalarToCtype(value, &d, desc);
			values.push_back(d);
			Py_DECREF(desc);
		    } else {
			PyErr_SetString(PyExc_TypeError, "Ply element values must be integers or floats");
			return NULL;
		    }
		}
		if (isDouble) {
		    v->ply->add_element(name, values, names, colors);
		} else {
		    std::vector<int> values_int;
		    for (std::vector<double>::iterator it = values.begin(); it != values.end(); it++)
			values_int.push_back((int)(*it));
		    v->ply->add_element(name, values_int, names, colors);
		}
	    } else if (PyList_Check(item)) {
		bool isDouble = false;
		std::vector<double> values;
		for (Py_ssize_t j = 0; j < PyList_Size(item); j++) {
		    PyObject* value = PyList_GetItem(item, j);
		    if (value == NULL) return NULL;
		    if (PyLong_Check(value)) {
			values.push_back(PyLong_AsDouble(value));
		    } else if (PyFloat_Check(value)) {
			values.push_back(PyFloat_AsDouble(value));
			isDouble = true;
		    } else {
			PyErr_SetString(PyExc_TypeError, "Ply element list values must be integers or floats");
			return NULL;
		    }
		}
		if (isDouble) {
		    double ignore = NAN;
		    v->ply->add_element(name, values, &ignore);
		} else {
		    std::vector<int> values_int;
		    for (std::vector<double>::iterator it = values.begin(); it != values.end(); it++)
			values_int.push_back((int)(*it));
		    int ignore = -1;
		    v->ply->add_element(name, values_int, &ignore);
		}
	    } else {
		PyErr_SetString(PyExc_TypeError, "Ply elements must be lists, integers, or floats");
		return NULL;
	    }
	}
    } else if (PyArray_Check(x)) {
	SizeType xn = 0, xm = 0;
	int ndim = PyArray_NDIM((PyArrayObject*)x);
	if (ndim != 2) return NULL;
	npy_intp* np_shape = PyArray_SHAPE((PyArrayObject*)x);
	if (np_shape == NULL) return NULL;
	xn = (SizeType)(np_shape[0]);
	xm = (SizeType)(np_shape[1]);
	bool isDouble = PyTypeNum_ISFLOAT(PyArray_TYPE((PyArrayObject*)x));
	PyObject* x2 = NULL;
	if (isDouble)
	    x2 = PyArray_Cast((PyArrayObject*)x, NPY_FLOAT64);
	else
	    x2 = PyArray_Cast((PyArrayObject*)x, NPY_INT);
	if (x2 == NULL) return NULL;
	if (!PyArray_IS_C_CONTIGUOUS((PyArrayObject*)x2)) {
	    PyArrayObject* cpy = PyArray_GETCONTIGUOUS((PyArrayObject*)x2);
	    if (cpy == NULL) return NULL;
	    Py_DECREF(x2);
	    x2 = (PyObject*)cpy;
	}
	if (isDouble) {
	    double* xa = (double*)PyArray_BYTES((PyArrayObject*)x2);
	    double ignore = NAN;
	    v->ply->add_element_set(name, xa, xn, xm, &ignore);
	} else {
	    int* xa = (int*)PyArray_BYTES((PyArrayObject*)x2);
	    int ignore = -1;
	    v->ply->add_element_set(name, xa, xn, xm, &ignore);
	}
	Py_DECREF(x2);
    } else {
	PyErr_SetString(PyExc_TypeError, "Ply element sets must be lists of element dictionaries or arrays.");
	return NULL;
    }
    
    Py_RETURN_NONE;
    
}


static PyObject* ply_as_dict(PyObject* self, PyObject* args, PyObject* kwargs) {
    int asArray = 0;
    
    static char const* kwlist[] = {
	"as_array",
        NULL
    };
    
    
    if (!PyArg_ParseTupleAndKeywords(args, kwargs, "|p:", (char**) kwlist,
				     &asArray))
	return NULL;

    PlyObject* v = (PlyObject*) self;

    PyObject* out = PyDict_New();
    if (out == NULL)
	return NULL;
    for (std::vector<std::string>::const_iterator it = v->ply->element_order.begin(); it != v->ply->element_order.end(); it++) {
	std::map<std::string,PlyElementSet>::const_iterator eit = v->ply->elements.find(*it);
	if (eit == v->ply->elements.end()) continue;
	PyObject* iargs = Py_BuildValue("(s)", it->c_str());
	PyObject* val = ply_get_elements(self, iargs, kwargs);
	Py_DECREF(iargs);
	if (val == NULL) {
	    Py_DECREF(out);
	    return NULL;
	}
	if (PyDict_SetItemString(out, it->c_str(), val) < 0) {
	    Py_DECREF(val);
	    Py_DECREF(out);
	    return NULL;
	}
	Py_DECREF(val);
	// Colors
	if (asArray && eit->second.colors.size() > 0) {
	    iargs = Py_BuildValue("(s)", it->c_str());
	    val = ply_get_colors(self, iargs, kwargs);
	    Py_DECREF(iargs);
	    if (val == NULL) {
		Py_DECREF(out);
		return NULL;
	    }
	    char key[100];
	    sprintf(key, "%s_colors", it->c_str());
	    if (PyDict_SetItemString(out, key, val) < 0) {
		Py_DECREF(val);
		Py_DECREF(out);
		return NULL;
	    }
	    Py_DECREF(val);
	}
    }
    
    return out;
    
}


static PyObject* ply_from_dict(PyObject* self, PyObject* args, PyObject* kwargs) {
    PyObject* inDict = NULL;
    
    if (!PyArg_ParseTuple(args, "O:", &inDict))
	return NULL;

    if (!PyDict_Check(inDict)) {
	PyErr_SetString(PyExc_TypeError, "Argument must be a dictionary.");
	return NULL;
    }

    PyObject* emptyArgs = PyTuple_New(0);

    PyObject* out = ply_new(&Ply_Type, emptyArgs, inDict);
    
    Py_DECREF(emptyArgs);
    
    return out;
    
}

#define VECTOR2LIST_(T, meth, args)					\
    template<>								\
    PyObject* vector2list(const std::vector<T>& x) {			\
        PyObject* out = PyList_New(x.size());				\
	if (out == NULL) return NULL;					\
	Py_ssize_t i = 0;						\
	for (std::vector<T>::const_iterator it = x.begin(); it != x.end(); it++, i++) { \
	    PyObject* item = meth args;					\
	    if (item == NULL) {						\
		Py_DECREF(out);						\
		return NULL;						\
	    }								\
	    if (PyList_SetItem(out, i, item) < 0) {			\
		Py_DECREF(item);					\
		Py_DECREF(out);						\
		return NULL;						\
	    }								\
	}								\
	return out;							\
    }
template<typename T>
PyObject* vector2list(const std::vector<T>&) {
    PyErr_SetString(PyExc_TypeError, "Unsupported type in vector2list");
    return NULL;
}
VECTOR2LIST_(double, PyFloat_FromDouble, (*it))
VECTOR2LIST_(int, PyLong_FromLong, (*it))


static PyObject* ply_count_elements(PyObject* self, PyObject* args, PyObject* kwargs) {
    const char* elementType0 = 0;
    
    if (!PyArg_ParseTuple(args, "s:", &elementType0))
	return NULL;

    std::string elementType(elementType0);

    PlyObject* v = (PlyObject*) self;

    size_t nElements = 0;
    const PlyElementSet* elementSet = v->ply->get_element_set(elementType);
    if (elementSet != NULL) {
	nElements = elementSet->elements.size();
    }

    PyObject* out = PyLong_FromSize_t(nElements);
    return out;
    
}


static PyObject* ply_append(PyObject* self, PyObject* args, PyObject* kwargs) {
    PyObject* solf = NULL;
    if (!PyArg_ParseTuple(args, "O:", &solf))
	return NULL;
    if (!PyObject_IsInstance(solf, (PyObject*)&Ply_Type)) {
	PyErr_Format(PyExc_TypeError, "Can only append other Ply instances.");
	return NULL;
    }

    PlyObject* v = (PlyObject*) self;
    if (v->ply == ((PlyObject*)solf)->ply) {
	Ply cpy(*v->ply);
	v->ply->append(cpy);
    } else {
	v->ply->append(*((PlyObject*)solf)->ply);
    }
    if (!v->ply->is_valid()) {
	PyErr_SetString(geom_error, "Structure is invalid. Check that indexes do not exceed the number of vertices");
	return NULL;
    }
    Py_RETURN_NONE;
}

static PyObject* ply_items(PyObject* self, PyObject*, PyObject*) {
    PlyObject* v = (PlyObject*) self;

    PyObject* out = PyList_New(v->ply->elements.size());
    if (out == NULL)
	return NULL;
    Py_ssize_t i = 0;
    for (std::vector<std::string>::const_iterator it = v->ply->element_order.begin(); it != v->ply->element_order.end(); it++) {
	std::map<std::string,PlyElementSet>::const_iterator eit = v->ply->elements.find(*it);
	if (eit == v->ply->elements.end()) continue;
	PyObject* iargs = Py_BuildValue("(s)", it->c_str());
	PyObject* val = ply_get_elements(self, iargs, NULL);
	Py_DECREF(iargs);
	if (val == NULL) {
	    Py_DECREF(out);
	    return NULL;
	}
	PyObject* key = PyUnicode_FromString(it->c_str());
	if (key == NULL) {
	    Py_DECREF(val);
	    Py_DECREF(out);
	    return NULL;
	}
	PyObject* item = PyTuple_Pack(2, key, val);
	Py_DECREF(key);
	Py_DECREF(val);
	if (item == NULL) {
	    Py_DECREF(out);
	    return NULL;
	}
	if (PyList_SetItem(out, i, item)) {
	    Py_DECREF(item);
	    Py_DECREF(out);
	    return NULL;
	}
	i++;
    }
    
    return out;
}


static PyObject* ply_bounds_get(PyObject* self, void*) {
    PlyObject* v = (PlyObject*) self;
    std::vector<double> mins = v->ply->minimums();
    std::vector<double> maxs = v->ply->maximums();
    npy_intp np_shape[1] = { (npy_intp) 3 };
    PyObject* pyMins = PyArray_EMPTY(1, np_shape, NPY_FLOAT64, 0);
    if (pyMins == NULL) return NULL;
    PyObject* pyMaxs = PyArray_EMPTY(1, np_shape, NPY_FLOAT64, 0);
    if (pyMaxs == NULL) {
	Py_DECREF(pyMins);
	return NULL;
    }
    std::memcpy(PyArray_DATA((PyArrayObject*)pyMins), mins.data(), 3 * sizeof(double));
    std::memcpy(PyArray_DATA((PyArrayObject*)pyMaxs), maxs.data(), 3 * sizeof(double));
    PyObject* out = Py_BuildValue("(OO)", pyMins, pyMaxs);
    Py_DECREF(pyMins);
    Py_DECREF(pyMaxs);
    return out;
}


static PyObject* ply_mesh_get(PyObject* self, void*) {
    PlyObject* v = (PlyObject*) self;
    std::vector<std::vector<double>> mesh = v->ply->mesh();
    PyObject* out = PyList_New(mesh.size());
    if (out == NULL) return NULL;
    Py_ssize_t i = 0;
    for (std::vector<std::vector<double>>::const_iterator it = mesh.begin();
	 it != mesh.end(); it++, i++) {
	PyObject* item = vector2list(*it);
	if (item == NULL) {
	    Py_DECREF(out);
	    return NULL;
	}
	if (PyList_SetItem(out, i, item) < 0) {
	    Py_DECREF(item);
	    Py_DECREF(out);
	    return NULL;
	}
    }
    return out;
}


static PyObject* ply_str(PyObject* self) {
    PlyObject* v = (PlyObject*) self;
    std::basic_stringstream<char> ss;
    ss << *v->ply;
    return PyUnicode_FromString(ss.str().c_str());
}


static Py_ssize_t ply_size(PyObject* self) {
    PlyObject* v = (PlyObject*) self;
    Py_ssize_t out = (Py_ssize_t)v->ply->elements.size();
    return out;
}


static PyObject* ply_subscript(PyObject* self, PyObject* key) {
    PyObject* iargs = Py_BuildValue("(O)", key);
    PyObject* out = ply_get_elements(self, iargs, NULL);
    Py_DECREF(iargs);
    return out;
}


static int ply_contains(PyObject* self, PyObject* value) {
    const char* elementType0;

    if (PyUnicode_Check(value)) {
	elementType0 = PyUnicode_AsUTF8(value);
	if (elementType0 == NULL) {
	    return -1;
	}
    } else {
	return 0;
    }

    std::string elementType(elementType0);

    PlyObject* v = (PlyObject*) self;

    if (v->ply->count_elements(elementType) == 0) {
	return 0;
    }

    return 1;
}


static PyObject* ply_add_colors(PyObject* self, PyObject* args, PyObject* kwargs) {
    const char* name0 = 0;
    PyObject* x = NULL;
    
    if (!PyArg_ParseTuple(args, "sO:", &name0, &x))
	return NULL;

    std::string name(name0);

    PlyObject* v = (PlyObject*) self;

    PlyElementSet* elementSet = v->ply->get_element_set(name);
    if (elementSet == NULL) {
	PyErr_SetString(geom_error, "There are not any elements of the indicated type.");
	return NULL;
    }
    
    if (PyList_Check(x)) {
	if (PyList_Size(x) != (Py_ssize_t)elementSet->elements.size()) {
	    PyErr_SetString(geom_error, "Number of colors dosn't match the number of elements in the set.");
	    return NULL;
	}
	for (Py_ssize_t i = 0; i < PyList_Size(x); i++) {
	    PyObject* item = PyList_GetItem(x, i);
	    if (item == NULL) return NULL;
	    std::vector<uint8_t> values;
	    std::vector<std::string> names;
	    if (PyDict_Check(item)) {
		if (PyDict_Size(item) != 3) {
		    PyErr_SetString(geom_error, "Colors must each have 3 elements");
		    return NULL;
		}
		PyObject *key, *value;
		Py_ssize_t pos = 0;
		while (PyDict_Next(item, &pos, &key, &value)) {
		    if (!PyUnicode_Check(key)) {
			PyErr_SetString(PyExc_TypeError, "Ply element keys must be strings");
			return NULL;
		    }
		    names.push_back(std::string(PyUnicode_AsUTF8(key)));
		    if (PyLong_Check(value)) {
			long vc = PyLong_AsLong(value);
			if (vc < 0 || vc > 255) {
			    PyErr_SetString(geom_error, "Color out of range (0, 255).");
			    return NULL;
			}
			values.push_back((uint8_t)vc);
		    } else if (PyArray_CheckScalar(value)) {
			PyArray_Descr* desc = PyArray_DescrNewFromType(NPY_UINT8);
			uint8_t vc = 0;
			PyArray_CastScalarToCtype(value, &vc, desc);
			values.push_back(vc);
			Py_DECREF(desc);
		    } else {
			PyErr_SetString(PyExc_TypeError, "Ply element colors must be integers.");
			return NULL;
		    }
		}
	    } else if (PyList_Check(item)) {
		if (PyList_Size(item) != 3) {
		    PyErr_SetString(geom_error, "Colors must each have 3 elements");
		    return NULL;
		}
		for (Py_ssize_t j = 0; j < PyList_Size(item); j++) {
		    PyObject* value = PyList_GetItem(item, j);
		    if (value == NULL) return NULL;
		    if (PyLong_Check(value)) {
			long vc = PyLong_AsLong(value);
			if (vc < 0 || vc > 255) {
			    PyErr_SetString(geom_error, "Color out of range (0, 255).");
			    return NULL;
			}
			values.push_back((uint8_t)vc);
		    } else {
			PyErr_SetString(PyExc_TypeError, "Ply element color values must be integers.");
			return NULL;
		    }
		}
	    } else {
		PyErr_SetString(PyExc_TypeError, "Ply element colors must be lists or dictionaries.");
		return NULL;
	    }
	    bool ret = false;
	    if (names.empty())
		ret = elementSet->add_element_colors(i, values);
	    else
		ret = elementSet->add_element_colors(i, values, names);
	    if (!ret) {
		PyErr_SetString(geom_error, "Error adding colors to element.");
		return NULL;
	    }
	}
    } else if (PyArray_Check(x)) {
	SizeType xn = 0, xm = 0;
	int ndim = PyArray_NDIM((PyArrayObject*)x);
	if (ndim != 2) return NULL;
	npy_intp* np_shape = PyArray_SHAPE((PyArrayObject*)x);
	if (np_shape == NULL) return NULL;
	xn = (SizeType)(np_shape[0]);
	xm = (SizeType)(np_shape[1]);
	if (xn != elementSet->elements.size() || xm != 3) {
	    PyErr_SetString(geom_error, "Colors array is not the correct shape.");
	    return NULL;
	}
	PyObject* x2 = PyArray_Cast((PyArrayObject*)x, NPY_UINT8);
	if (x2 == NULL) return NULL;
	if (!PyArray_IS_C_CONTIGUOUS((PyArrayObject*)x2)) {
	    PyArrayObject* cpy = PyArray_GETCONTIGUOUS((PyArrayObject*)x2);
	    if (cpy == NULL) return NULL;
	    Py_DECREF(x2);
	    x2 = (PyObject*)cpy;
	}
	uint8_t* xa = (uint8_t*)PyArray_BYTES((PyArrayObject*)x2);
	bool ret = v->ply->add_element_set_colors(name, xa, xn, xm);
	Py_DECREF(x2);
	if (!ret) {
	    PyErr_SetString(geom_error, "Error adding colors array.");
	    return NULL;
	}
    } else {
	PyErr_SetString(PyExc_TypeError, "Ply element colors must be lists of element dictionaries or an array.");
	return NULL;
    }
    Py_RETURN_NONE;
}


static PyObject* ply_get_colors(PyObject* self, PyObject* args, PyObject* kwargs) {
    const char* elementType0 = 0;
    int asArray = 0;
    
    static char const* kwlist[] = {
	"name",
	"as_array",
        NULL
    };
    
    
    if (!PyArg_ParseTupleAndKeywords(args, kwargs, "s|p:", (char**) kwlist,
				     &elementType0, &asArray))
	return NULL;

    std::string elementType(elementType0);

    PlyObject* v = (PlyObject*) self;
    
    const PlyElementSet* elementSet = v->ply->get_element_set(elementType);
    if (elementSet == NULL) {
	PyErr_SetString(PyExc_KeyError, elementType0);
	return NULL;
    }

    PyObject* out = NULL;
    
    if (asArray) {
	
	size_t N = 0, M = 0;
	std::vector<uint8_t> vect = v->ply->get_colors_array(elementType, N, M);
	PyArray_Descr* desc = PyArray_DescrNewFromType(NPY_UINT8);
	if (desc == NULL) return NULL;
	npy_intp np_shape[2] = { (npy_intp)N, (npy_intp)M };
	PyObject* tmp = PyArray_NewFromDescr(&PyArray_Type, desc,
					     2, np_shape, NULL,
					     (void*)vect.data(), 0, NULL);
	if (tmp == NULL) return NULL;
	out = (PyObject*)PyArray_NewCopy((PyArrayObject*)tmp, NPY_CORDER);
	Py_DECREF(tmp);

    } else {
	PyObject* out = PyList_New(elementSet->elements.size());
	if (out == NULL) {
	    return NULL;
	}
	Py_ssize_t i = 0;
	for (std::vector<PlyElement>::const_iterator elit = elementSet->elements.begin(); elit != elementSet->elements.end(); elit++, i++) {
	    PyObject* item = PyDict_New();
	    if (item == NULL) {
		Py_DECREF(out);
		return NULL;
	    }
	    for (std::vector<std::string>::const_iterator p = elit->colors.begin(); p != elit->colors.end(); p++) {
		PyObject* ival = NULL;
		if (elit->is_vector(*p)) {
		    ival = PyList_New(elit->size());
		    if (ival != NULL) {
			for (size_t iProp = 0; iProp < elit->size(); iProp++) {
			    PyObject* iival = PyLong_FromLong(elit->get_value_as<long>(*p, iProp));
			    if (iival == NULL) {
				Py_DECREF(ival);
				Py_DECREF(item);
				Py_DECREF(out);
				return NULL;
			    }
			    if (PyList_SetItem(ival, iProp, iival) < 0) {
				Py_DECREF(iival);
				Py_DECREF(ival);
				Py_DECREF(item);
				Py_DECREF(out);
				return NULL;
			    }
			}
		    }
		} else {
		    ival = PyLong_FromLong(elit->get_value_as<long>(*p));
		}
		if (ival == NULL) {
		    Py_DECREF(item);
		    Py_DECREF(out);
		    return NULL;
		}
		if (PyDict_SetItemString(item, p->c_str(), ival) < 0) {
		    Py_DECREF(ival);
		    Py_DECREF(item);
		    Py_DECREF(out);
		    return NULL;
		}
		Py_DECREF(ival);
	    }
	    if (PyList_SetItem(out, i, item) < 0) {
		Py_DECREF(item);
		Py_DECREF(out);
		return NULL;
	    }
	}
    }
    
    return out;

    
}


//////////////////
// ObjWavefront //
//////////////////


typedef struct {
    PyObject_HEAD
    ObjWavefront *obj;
} ObjWavefrontObject;


PyDoc_STRVAR(objwavefront_doc,
             "ObjWavefront(vertices, faces=None, edges=None)\n"
             "\n"
             "Create and return a new ObjWavefront instance from the given"
             " set of vertices, faces, and edges.");


// Handle missing properties
static PyMethodDef objwavefront_methods[] = {
    {"get_elements", (PyCFunction) objwavefront_get_elements,
     METH_VARARGS | METH_KEYWORDS,
     "Get all elements of a given type."},
    {"add_elements", (PyCFunction) objwavefront_add_elements,
     METH_VARARGS, "Add elements of a given type."},
    {"as_dict", (PyCFunction) objwavefront_as_dict,
     METH_VARARGS | METH_KEYWORDS,
     "Get the structure as a dictionary."},
    {"from_dict", (PyCFunction) objwavefront_from_dict,
     METH_VARARGS | METH_CLASS,
     "Create a ObjWavefront instance from a dictionary of elements."},
    {"count_elements", (PyCFunction) objwavefront_count_elements,
     METH_VARARGS,
     "Get the number of elements of a given type in the structure."},
    {"append", (PyCFunction) objwavefront_append,
     METH_VARARGS,
     "Append another 3D structure."},
    {"items", (PyCFunction) objwavefront_items,
     METH_NOARGS,
     "Get the dict-like list of items in the structure."},
    {"get_colors", (PyCFunction) objwavefront_get_colors,
     METH_VARARGS | METH_KEYWORDS,
     "Get colors associated with elements of a given type."},
    {"add_colors", (PyCFunction) objwavefront_add_colors,
     METH_VARARGS,
     "Set colors associated with elements of a given type."},
    {NULL}  /* Sentinel */
};


static PyGetSetDef objwavefront_properties[] = {
    {"bounds", objwavefront_bounds_get, NULL,
     "The minimum & maximum bounds for the structure in x, y, & z.", NULL},
    {"mesh", objwavefront_mesh_get, NULL,
     "The 3D mesh representing the faces in the structure.", NULL},
    {NULL}
};


static PyMappingMethods objwavefront_mapping = {
    objwavefront_size, objwavefront_subscript, NULL
};

static PySequenceMethods objwavefront_seq = {
    objwavefront_size, NULL, NULL, NULL, NULL, NULL, NULL,
    objwavefront_contains,
    NULL, NULL
};


static PyTypeObject ObjWavefront_Type = {
    PyVarObject_HEAD_INIT(NULL, 0)
    "rapidjson.ObjWavefront",           /* tp_name */
    sizeof(ObjWavefrontObject),         /* tp_basicsize */
    0,                                  /* tp_itemsize */
    (destructor) objwavefront_dealloc,  /* tp_dealloc */
    0,                                  /* tp_print */
    0,                                  /* tp_getattr */
    0,                                  /* tp_setattr */
    0,                                  /* tp_compare */
    0,                                  /* tp_repr */
    0,                                  /* tp_as_number */
    &objwavefront_seq,                  /* tp_as_sequence */
    &objwavefront_mapping,              /* tp_as_mapping */
    0,                                  /* tp_hash */
    0,                                  /* tp_call */
    objwavefront_str,                   /* tp_str */
    0,                                  /* tp_getattro */
    0,                                  /* tp_setattro */
    0,                                  /* tp_as_buffer */
    Py_TPFLAGS_DEFAULT | Py_TPFLAGS_BASETYPE, /* tp_flags */
    objwavefront_doc,                   /* tp_doc */
    0,                                  /* tp_traverse */
    0,                                  /* tp_clear */
    objwavefront_richcompare,           /* tp_richcompare */
    0,                                  /* tp_weaklistoffset */
    0,                                  /* tp_iter */
    0,                                  /* tp_iternext */
    objwavefront_methods,               /* tp_methods */
    0,                                  /* tp_members */
    objwavefront_properties,            /* tp_getset */
    0,                                  /* tp_base */
    0,                                  /* tp_dict */
    0,                                  /* tp_descr_get */
    0,                                  /* tp_descr_set */
    0,                                  /* tp_dictoffset */
    0,                                  /* tp_init */
    0,                                  /* tp_alloc */
    objwavefront_new,                   /* tp_new */
    PyObject_Del,                       /* tp_free */
};


static void objwavefront_dealloc(PyObject* self)
{
    ObjWavefrontObject* s = (ObjWavefrontObject*) self;
    delete s->obj;
    Py_TYPE(self)->tp_free(self);
}


static PyObject* objwavefront_new(PyTypeObject* type, PyObject* args, PyObject* kwargs)
{
    PyObject* vertObject = NULL;
    PyObject* faceObject = NULL;
    PyObject* edgeObject = NULL;

    if (!PyArg_UnpackTuple(args, "ObjWavefront", 0, 3,
			   &vertObject, &faceObject, &edgeObject))
	return NULL;
    if (kwargs && !PyArg_ValidateKeywordArguments(kwargs))
	return NULL;

    const char* readFrom = 0;
    const ObjWavefrontObject* copyFrom = 0;
    if (vertObject && !faceObject && !edgeObject && !kwargs) {
	if (PyDict_Check(vertObject)) {
	    kwargs = vertObject;
	    vertObject = NULL;
	} else if (PyUnicode_Check(vertObject)) {
	    readFrom = PyUnicode_AsUTF8(vertObject);
	    vertObject = NULL;
	} else if (PyBytes_Check(vertObject)) {
	    readFrom = PyBytes_AsString(vertObject);
	    vertObject = NULL;
	} else if (PyObject_IsInstance(vertObject, (PyObject*)&ObjWavefront_Type)) {
	    copyFrom = (ObjWavefrontObject*)vertObject;
	    vertObject = NULL;
	}
    }
    
    ObjWavefrontObject* v = (ObjWavefrontObject*) type->tp_alloc(type, 0);
    if (v == NULL)
        return NULL;
    if (copyFrom) {
	v->obj = (ObjWavefront*)(copyFrom->obj->copy());
    } else {
	v->obj = new ObjWavefront();
    }
    
    if (readFrom) {
	std::stringstream ss;
	ss.str(std::string(readFrom));
	if (!v->obj->read(ss)) {
	    PyErr_SetString(geom_error, "Error reading from string");
	    return NULL;
	}
    }
    
#define ADD_ARRAY(x, name)						\
    if (x != NULL) {							\
	PyObject* x_name = PyUnicode_FromString(#name);			\
	if (x_name == NULL) return NULL;				\
	PyObject* iargs = Py_BuildValue("(OO)", x_name, x);		\
	Py_DECREF(x_name);						\
	if (iargs == NULL) return NULL;					\
	if (objwavefront_add_elements((PyObject*)v, iargs, NULL) == NULL) {	\
	    Py_DECREF(iargs);						\
	    return NULL;						\
	}								\
	Py_DECREF(iargs);						\
    }

    ADD_ARRAY(vertObject, vertex)
    ADD_ARRAY(faceObject, face)
    ADD_ARRAY(edgeObject, edge)

#undef ADD_ARRAY

    if (kwargs) {
	PyObject *key, *value;
	Py_ssize_t pos = 0;
	std::vector<std::string> delayed;

	// Do vertices first
	std::string vert_key;
	std::vector<std::string> vert_names = {"vertex", "vertices", "vertexes"};
	for (std::vector<std::string>::iterator it = vert_names.begin();
	     it != vert_names.end(); it++) {
	    value = PyDict_GetItemString(kwargs, it->c_str());
	    if (value == NULL) continue;
	    PyObject* iargs = Py_BuildValue("(sO)", it->c_str(), value);
	    if (objwavefront_add_elements((PyObject*)v, iargs, NULL) == NULL) {
		Py_DECREF(iargs);
		return NULL;
	    }
	    Py_DECREF(iargs);
	    vert_key = *it;
	    break;
	}
	while (PyDict_Next(kwargs, &pos, &key, &value)) {
	    std::string keyS(PyUnicode_AsUTF8(key));
	    if (keyS == vert_key) continue;
	    if (keyS.size() > 7 &&
		keyS.substr(keyS.size() - 7) == "_colors") {
		delayed.push_back(keyS);
		continue;
	    }
	    PyObject* iargs = Py_BuildValue("(OO)", key, value);
	    if (objwavefront_add_elements((PyObject*)v, iargs, NULL) == NULL) {
		Py_DECREF(iargs);
		return NULL;
	    }
	    Py_DECREF(iargs);
	}
	for (std::vector<std::string>::iterator it = delayed.begin();
	     it != delayed.end(); it++) {
	    value = PyDict_GetItemString(kwargs, it->c_str());
	    PyObject* iargs = Py_BuildValue("(sO)", it->c_str(), value);
	    if (objwavefront_add_elements((PyObject*)v, iargs, NULL) == NULL) {
		Py_DECREF(iargs);
		return NULL;
	    }
	    Py_DECREF(iargs);
	}
    }

    // if (!v->obj->get_element_set("vertex"))
    // 	v->obj->add_element_set("vertex");
    // if (!v->obj->get_element_set("face"))
    // 	v->obj->add_element_set("face");
    

    if (!v->obj->is_valid()) {
	PyErr_SetString(geom_error, "Structure is invalid. Check that indexes do not exceed the number of vertices");
	return NULL;
    }

    return (PyObject*) v;
}


static PyObject* objwavefront_richcompare(PyObject *self, PyObject *other, int op) {
    PyObject* value = NULL;
    if (!PyObject_IsInstance(other, (PyObject*)&ObjWavefront_Type)) {
	switch (op) {
	case (Py_EQ):
	    value = Py_False;
	    break;
	case (Py_NE):
	    value = Py_True;
	    break;
	default:
	    value = Py_NotImplemented;
	}
    } else {
	ObjWavefrontObject* vself = (ObjWavefrontObject*) self;
	ObjWavefrontObject* vsolf = (ObjWavefrontObject*) other;
	switch (op) {
	case (Py_EQ):
	    value = (*(vself->obj) == *(vsolf->obj)) ? Py_True : Py_False;
	    break;
	case (Py_NE):
	    value = (*(vself->obj) != *(vsolf->obj)) ? Py_True : Py_False;
	    break;
	default:
	    value = Py_NotImplemented;
	}
    }
    Py_INCREF(value);
    return value;
}

static PyObject* objwavefront_get_elements(PyObject* self, PyObject* args, PyObject* kwargs) {
    const char* elementType0 = 0;
    int asArray = 0;
    
    static char const* kwlist[] = {
	"name",
	"as_array",
        NULL
    };
    
    
    if (!PyArg_ParseTupleAndKeywords(args, kwargs, "s|p:", (char**) kwlist,
				     &elementType0, &asArray))
	return NULL;

    std::string elementType = obj_alias2base(std::string(elementType0));

    ObjWavefrontObject* v = (ObjWavefrontObject*) self;

    if (v->obj->count_elements(elementType) == 0) {
	PyErr_SetString(PyExc_KeyError, elementType0);
	return NULL;
    }
    
    PyObject* out = NULL;
    
    if (asArray) {
	
#define GET_ARRAY(T, npT)						\
	size_t N = 0, M = 0;						\
	std::vector<T> vect = v->obj->get_ ## T ## _array(elementType, N, M, true); \
	PyArray_Descr* desc = PyArray_DescrNewFromType(npT);		\
	if (desc == NULL) return NULL;					\
	npy_intp np_shape[2] = { (npy_intp)N, (npy_intp)M };		\
	PyObject* tmp = PyArray_NewFromDescr(&PyArray_Type, desc,	\
					     2, np_shape, NULL,		\
					     (void*)vect.data(), 0, NULL); \
	if (tmp == NULL) return NULL;					\
	out = (PyObject*)PyArray_NewCopy((PyArrayObject*)tmp, NPY_CORDER); \
	Py_DECREF(tmp)
	
	if (v->obj->requires_double(elementType)) {
	    GET_ARRAY(double, NPY_DOUBLE);
	} else {
	    GET_ARRAY(int, NPY_INT);
	}
#undef GET_ARRAY
    } else {
	out = PyDict_New();
	if (out == NULL)
	    return NULL;
	{
	    PyObject* val = PyList_New(v->obj->count_elements(elementType));
	    if (val == NULL) {
		Py_DECREF(out);
		return NULL;
	    }
	    Py_ssize_t i = 0;
	    for (std::vector<ObjElement*>::const_iterator elit = v->obj->elements.begin(); elit != v->obj->elements.end(); elit++) {
		if ((*elit)->code != elementType) continue;
		PyObject* item = PyDict_New();
		if (item == NULL) {
		    Py_DECREF(val);
		    Py_DECREF(out);
		    return NULL;
		}
		for (ObjPropertiesMap::const_iterator p = (*elit)->properties.begin();
		     p != (*elit)->properties.end(); p++) {
		    PyObject* ival = NULL;
		    if (!(*elit)->has_property(p->first, true)) continue;
		    if (p->is_vector()) {
			ival = PyList_New((*elit)->size());
			if (ival == NULL) {
			    Py_DECREF(item);
			    Py_DECREF(val);
			    Py_DECREF(out);
			    return NULL;
			}
#define GET_ARRAY_(type, method)					\
			std::vector<type> values;			\
			if (!p->get(values)) {				\
			    Py_DECREF(ival);				\
			    Py_DECREF(item);				\
			    Py_DECREF(val);				\
			    Py_DECREF(out);				\
			    return NULL;				\
			}						\
			for (size_t iProp = 0; iProp < values.size(); iProp++) { \
			    PyObject* iival = method;			\
			    if (iival == NULL) {			\
				Py_DECREF(ival);			\
				Py_DECREF(item);			\
				Py_DECREF(val);				\
				Py_DECREF(out);				\
				return NULL;				\
			    }						\
			    if (PyList_SetItem(ival, iProp, iival) < 0) { \
				Py_DECREF(iival);			\
				Py_DECREF(ival);			\
				Py_DECREF(item);			\
				Py_DECREF(val);				\
				Py_DECREF(out);				\
				return NULL;				\
			    }						\
	                }

			if (_type_compatible_double(p->second)) {
			    GET_ARRAY_(double, PyFloat_FromDouble(values[iProp]));
			} else if (_type_compatible_int(p->second)) {
			    GET_ARRAY_(int, PyLong_FromLong(values[iProp]));
			} else if (_type_compatible_string(p->second)) {
			    GET_ARRAY_(std::string, PyUnicode_FromString(values[iProp].c_str()));
			} else {
			    Py_DECREF(item);
			    Py_DECREF(val);
			    Py_DECREF(out);
			    PyErr_SetString(PyExc_TypeError, "Could not find a Python type to match the C++ type");
			    return NULL;
			}

#undef GET_ARRAY_
#define GET_SCALAR_(type, method)				\
			type value;					\
			if (!p->get(value)) {				\
			    Py_DECREF(item);				\
			    Py_DECREF(val);				\
			    Py_DECREF(out);				\
			    return NULL;				\
			}						\
			ival = method
		    } else if (_type_compatible_double(p->second)) {
			GET_SCALAR_(double, PyFloat_FromDouble(value));
		    } else if (_type_compatible_int(p->second)) {
			GET_SCALAR_(int, PyLong_FromLong(value));
		    } else if (_type_compatible_string(p->second)) {
			GET_SCALAR_(std::string, PyUnicode_FromString(value.c_str()));
		    } else {
			Py_DECREF(item);
			Py_DECREF(val);
			Py_DECREF(out);
			PyErr_SetString(PyExc_TypeError, "Could not find a Python type to match the C++ type");
			return NULL;
		    }
#undef GET_SCALAR_
		    if (ival == NULL) {
			Py_DECREF(item);
			Py_DECREF(val);
			Py_DECREF(out);
			return NULL;
		    }
		    if (PyDict_SetItemString(item, p->first.c_str(), ival) < 0) {
			Py_DECREF(ival);
			Py_DECREF(item);
			Py_DECREF(val);
			Py_DECREF(out);
			return NULL;
		    }
		    Py_DECREF(ival);
		}
		if (PyList_SetItem(val, i, item) < 0) {
		    Py_DECREF(item);
		    Py_DECREF(val);
		    Py_DECREF(out);
		    return NULL;
		}
		i++;
	    }
	    out = val;
	}
    }
    
    return out;
    
}

static PyObject* objwavefront_add_elements(PyObject* self, PyObject* args, PyObject* kwargs) {
    const char* name0 = 0;
    PyObject* x = NULL;
    
    if (!PyArg_ParseTuple(args, "sO:", &name0, &x))
	return NULL;

    std::string name(name0);

    ObjWavefrontObject* v = (ObjWavefrontObject*) self;

    bool isColor = (name.size() > 7 &&
		    name.substr(name.size() - 7) == "_colors");
    if (isColor) {
	name.erase(name.end() - 7, name.end());
	PyObject* iargs = Py_BuildValue("(sO)", name.c_str(), x);
	PyObject* out = objwavefront_add_colors(self, iargs, NULL);
	Py_DECREF(iargs);
	return out;
    }
    
    if (PyList_Check(x)) {
	for (Py_ssize_t i = 0; i < PyList_Size(x); i++) {
	    PyObject* item = PyList_GetItem(x, i);
	    if (item == NULL) return NULL;
	    if (PyDict_Check(item)) { // Dictionary of element properties
		PyObject *key, *value;
		Py_ssize_t pos = 0;
		ObjElement* new_element = v->obj->add_element(name);
		if (!new_element) {
		    PyErr_SetString(geom_error, "Error adding element to ObjWavefront instance");
		    return NULL;
		}
		if (!new_element->set_meta_properties(PyDict_Size(item))) {
		    PyErr_SetString(geom_error, "Error setting metadata for ObjWavefront element.");
		    return NULL;
		}
		while (PyDict_Next(item, &pos, &key, &value)) {
		    if (!PyUnicode_Check(key)) {
			PyErr_SetString(PyExc_TypeError, "ObjWavefront element keys must be strings");
			return NULL;
		    }
		    std::string iname = std::string(PyUnicode_AsUTF8(key));
#define HANDLE_SCALAR_(type, method)					\
		    type ivalue = method;				\
		    if (!new_element->set_property(iname, ivalue)) {	\
			PyErr_SetString(geom_error, "Error adding " #type " value to ObjWavefront element"); \
			return NULL;					\
		    }
#define HANDLE_SCALAR_NPY_(type, npy_type)				\
		    type ivalue;					\
		    PyArray_Descr* desc = PyArray_DescrNewFromType(npy_type); \
		    PyArray_CastScalarToCtype(value, &ivalue, desc);	\
		    Py_DECREF(desc);					\
		    if (!new_element->set_property(iname, ivalue)) {	\
			PyErr_SetString(geom_error, "Error adding " #type " numpy scalar value to ObjWavefront element"); \
			return NULL;					\
		    }
#define HANDLE_ARRAY_(type, check, method)				\
		    std::vector<type> values;				\
		    for (Py_ssize_t j = 0; j < PyList_Size(value); j++) { \
			PyObject* vv = PyList_GetItem(value, j);	\
			if (vv == NULL) return NULL;			\
			if (!check(vv)) {				\
			    PyErr_SetString(geom_error, "Error adding " #type " values array to ObjWavefront element. Not all elements are the same type."); \
			    return NULL;				\
			}						\
			values.push_back(method);			\
		    }							\
		    if (!new_element->set_property(iname, values)) {	\
			PyErr_SetString(geom_error, "Error adding " #type " values to ObjWavefront element"); \
			return NULL;					\
		    }
#define HANDLE_ARRAY_NPY_(type, check, npy_type)			\
		    std::vector<type> values;				\
		    for (Py_ssize_t j = 0; j < PyList_Size(value); j++) { \
			PyObject* vv = PyList_GetItem(value, j);	\
			if (vv == NULL) return NULL;			\
			if (!PyArray_CheckScalar(vv)) {			\
			    PyErr_SetString(geom_error, "Error adding " #type " values array to ObjWavefront element. Not all elements are numpy scalars."); \
			    return NULL;				\
			}						\
			PyArray_Descr* desc0 = PyArray_DescrFromScalar(vv); \
			if (!check(desc0)) {				\
			    PyErr_SetString(geom_error, "Error adding " #type " values array to ObjWavefront element from numpy scalars. Not all elements are the same type."); \
			    return NULL;				\
			}						\
			type ivalue;					\
			PyArray_Descr* desc = PyArray_DescrNewFromType(npy_type); \
			PyArray_CastScalarToCtype(vv, &ivalue, desc);	\
			values.push_back(ivalue);			\
			Py_DECREF(desc);				\
		    }							\
		    if (!new_element->set_property(iname, values)) {	\
			PyErr_SetString(geom_error, "Error adding " #type " values to ObjWavefront element"); \
			return NULL;					\
		    }
		    
		    if (PyLong_Check(value)) {
			HANDLE_SCALAR_(int, static_cast<int>(PyLong_AsLong(value)));
		    } else if (PyFloat_Check(value)) {
			HANDLE_SCALAR_(double, PyFloat_AsDouble(value));
		    } else if (PyUnicode_Check(value)) {
			HANDLE_SCALAR_(std::string, std::string(PyUnicode_AsUTF8(value)));
		    } else if (PyArray_CheckScalar(value)) {
			PyArray_Descr* desc0 = PyArray_DescrFromScalar(value);
			if (PyDataType_ISINTEGER(desc0)) {
			    HANDLE_SCALAR_NPY_(int, NPY_INT32);
			} else if (PyDataType_ISFLOAT(desc0)) {
			    HANDLE_SCALAR_NPY_(double, NPY_FLOAT64);
			} else if (PyDataType_ISSTRING(desc0)) {
			    HANDLE_SCALAR_NPY_(std::string, NPY_UNICODE);
			} else {
			    PyErr_SetString(PyExc_TypeError, "ObjWavefront element property value must be integer, float, or string");
			    return NULL;
			}
		    } else if (PyList_Check(value)) {
			PyObject* first_item = PyList_GetItem(value, 0);
			if (first_item == NULL) return NULL;
			if (PyLong_Check(first_item)) {
			    HANDLE_ARRAY_(int, PyLong_Check, static_cast<int>(PyLong_AsLong(vv)));
			} else if (PyFloat_Check(first_item)) {
			    HANDLE_ARRAY_(double, PyFloat_Check, PyFloat_AsDouble(vv));
			} else if (PyUnicode_Check(first_item)) {
			    HANDLE_ARRAY_(std::string, PyUnicode_Check, std::string(PyUnicode_AsUTF8(vv)));
			} else if (PyArray_CheckScalar(first_item)) {
			    PyArray_Descr* first_desc = PyArray_DescrFromScalar(first_item);
			    if (PyDataType_ISINTEGER(first_desc)) {
				HANDLE_ARRAY_NPY_(int, PyDataType_ISINTEGER, NPY_INT32);
			    } else if (PyDataType_ISFLOAT(first_desc)) {
				HANDLE_ARRAY_NPY_(double, PyDataType_ISFLOAT, NPY_FLOAT64);
			    } else if (PyDataType_ISSTRING(first_desc)) {
				HANDLE_ARRAY_NPY_(std::string, PyDataType_ISSTRING, NPY_UNICODE);
			    } else {
				PyErr_SetString(PyExc_TypeError, "ObjWavefront element list values must be integers, floats, or strings");
				return NULL;
			    }
			} else {
			    PyErr_SetString(PyExc_TypeError, "ObjWavefront element list values must be integers, floats, or strings");
			    return NULL;
			}
#undef HANDLE_SCALAR_
#undef HANDLE_SCALAR_NPY_
#undef HANDLE_ARRAY_
#undef HANDLE_ARRAY_NPY_
		    } else {
			PyErr_SetString(PyExc_TypeError, "ObjWavefront element property values must be integers, floats, strings, or lists of those types.");
			return NULL;
		    }
		}
	    } else if (PyList_Check(item)) { // List of element properties
		ObjElement* new_element = v->obj->add_element(name);
		if (!new_element) {
		    PyErr_SetString(geom_error, "Error adding element to ObjWavefront instance");
		    return NULL;
		}
		Py_ssize_t item_size = PyList_Size(item);
		if (!new_element->set_meta_properties(item_size)) {
		    PyErr_SetString(geom_error, "Error setting metadata for ObjWavefront element.");
		    return NULL;
		}
		int min_size = new_element->min_values();
		int max_size = new_element->max_values();
		if ((min_size >= 0 && item_size < (Py_ssize_t)min_size) ||
		    (max_size >= 0 && item_size > (Py_ssize_t)max_size)) {
		    PyErr_SetString(geom_error, "Error adding element to ObjWavefront instance. Incorrect number of property values.");
		    return NULL;
		}
		for (Py_ssize_t j = 0; j < PyList_Size(item); j++) {
		    PyObject* value = PyList_GetItem(item, j);
		    if (value == NULL) return NULL;
#define HANDLE_SCALAR_(method)						\
		    if (!new_element->set_property(static_cast<size_t>(j), \
						   method)) {		\
			PyErr_SetString(geom_error, "Error setting ObjWavefront element property."); \
			return NULL;					\
		    }
		    if (PyLong_Check(value)) {
			HANDLE_SCALAR_(static_cast<int>(PyLong_AsLong(value)));
		    } else if (PyFloat_Check(value)) {
			HANDLE_SCALAR_(PyFloat_AsDouble(value));
		    } else if (PyUnicode_Check(value)) {
			HANDLE_SCALAR_(std::string(PyUnicode_AsUTF8(value)));
#undef HANDLE_SCALAR_
		    } else if (PyDict_Check(value)) {
#define HANDLE_SCALAR_(type, method)					\
			type ivalue = method;				\
			if (!last_sub->set_property(keyS, ivalue)) {	\
			    PyErr_SetString(geom_error, "Error setting subelement property for ObjWavefront element.");	\
			    return NULL;				\
			}
			if (!new_element->add_subelement()) {
			    PyErr_SetString(geom_error, "Error adding subelement to ObjWavefront element.");
			    return NULL;
			}
			bool temp = false;
			ObjPropertyElement* last_sub = new_element->last_subelement(&temp);
			if (!last_sub) {
			    PyErr_SetString(geom_error, "Error retrieving last subelement from ObjWavefront element.");
			    return NULL;
			}
			PyObject *key, *key_value;
			Py_ssize_t pos = 0;
			while (PyDict_Next(value, &pos, &key, &key_value)) {
			    std::string keyS = PyUnicode_AsUTF8(key);
			    if (PyLong_Check(key_value)) {
				HANDLE_SCALAR_(int, static_cast<int>(PyLong_AsLong(key_value)));
			    } else if (PyFloat_Check(key_value)) {
				HANDLE_SCALAR_(double, PyFloat_AsDouble(key_value));
			    } else if (PyUnicode_Check(key_value)) {
				HANDLE_SCALAR_(std::string, std::string(PyUnicode_AsUTF8(key_value)));
			    // } else if (PyList_Check(key_value)) {
			    // 	PyObject* first_item = PyList_GetItem(value, 0);
			    // 	if (first_item == NULL) return NULL;
				
			    // 	for (Py_ssize_t k = 0; k < PyList_Size(key_value); k++) {
			    // 	    PyObject* kvv = PyList_GetItem(key_value, k);
			    // 	    if (kvv == NULL) return NULL;
			    // 	    if (PyLong_Check(kvv)) {
			    // 		it->second.push_back(PyLong_AsDouble(kvv));
			    // 	    } else if (PyFloat_Check(kvv)) {
			    // 		it->second.push_back(PyFloat_AsDouble(kvv));
			    // 	    } else {
			    // 		PyErr_SetString(PyExc_TypeError, "ObjWavefront element parameter list values must be integers or floats");
			    // 		return NULL;
			    // 	    }
			    // 	}
			    } else {
				PyErr_SetString(PyExc_TypeError, "ObjWavefront element subelements must be integers, floats, or strings");
				return NULL;
			    }
			}
			if (temp) {
			    delete last_sub;
			}
#undef HANDLE_SCALAR_
		    } else {
			PyErr_SetString(PyExc_TypeError, "ObjWavefront element list values must be integers or floats");
			return NULL;
		    }
		}
		std::map<std::string,size_t> counts = v->obj->element_counts();
		if (!new_element->is_valid_idx(counts)) {
		    PyErr_SetString(geom_error, "New ObjWavefront element is invalid");
		    return NULL;
		}
	    } else {
		PyErr_SetString(PyExc_TypeError, "ObjWavefront elements must be lists, integers, or floats");
		return NULL;
	    }
	}
    } else if (PyArray_Check(x)) {
	SizeType xn = 0, xm = 0;
	int ndim = PyArray_NDIM((PyArrayObject*)x);
	if (ndim != 2) return NULL;
	npy_intp* np_shape = PyArray_SHAPE((PyArrayObject*)x);
	if (np_shape == NULL) return NULL;
	xn = (SizeType)(np_shape[0]);
	xm = (SizeType)(np_shape[1]);
	bool isDouble = PyTypeNum_ISFLOAT(PyArray_TYPE((PyArrayObject*)x));
	PyObject* x2 = NULL;
	if (isDouble)
	    x2 = PyArray_Cast((PyArrayObject*)x, NPY_FLOAT64);
	else
	    x2 = PyArray_Cast((PyArrayObject*)x, NPY_INT);
	if (x2 == NULL) return NULL;
	if (!PyArray_IS_C_CONTIGUOUS((PyArrayObject*)x2)) {
	    PyArrayObject* cpy = PyArray_GETCONTIGUOUS((PyArrayObject*)x2);
	    if (cpy == NULL) return NULL;
	    Py_DECREF(x2);
	    x2 = (PyObject*)cpy;
	}
	if (isDouble) {
	    double* xa = (double*)PyArray_BYTES((PyArrayObject*)x2);
	    double ignore = NAN;
	    v->obj->add_element_set(name, xa, xn, xm, &ignore);
	} else {
	    int* xa = (int*)PyArray_BYTES((PyArrayObject*)x2);
	    int ignore = 0;
	    v->obj->add_element_set(name, xa, xn, xm, &ignore);
	}
	Py_DECREF(x2);
    } else {
	PyErr_SetString(PyExc_TypeError, "ObjWavefront element sets must be lists of element dictionaries or arrays.");
	return NULL;
    }
    
    Py_RETURN_NONE;
    
}


static PyObject* objwavefront_as_dict(PyObject* self, PyObject* args, PyObject* kwargs) {
    int asArray = 0;
    
    static char const* kwlist[] = {
	"as_array",
        NULL
    };
    
    
    if (!PyArg_ParseTupleAndKeywords(args, kwargs, "|p:", (char**) kwlist,
				     &asArray))
	return NULL;

    ObjWavefrontObject* v = (ObjWavefrontObject*) self;

    PyObject* out = PyDict_New();
    if (out == NULL)
	return NULL;
    std::vector<std::string> unique = v->obj->element_types();
    for (std::vector<std::string>::const_iterator it = unique.begin(); it != unique.end(); it++) {
	std::string longName = obj_code2long(*it);
	PyObject* iargs = Py_BuildValue("(s)", it->c_str());
	PyObject* val = objwavefront_get_elements(self, iargs, kwargs);
	Py_DECREF(iargs);
	if (val == NULL) {
	    Py_DECREF(out);
	    return NULL;
	}
	if (PyDict_SetItemString(out, longName.c_str(), val) < 0) {
	    Py_DECREF(val);
	    Py_DECREF(out);
	    return NULL;
	}
	Py_DECREF(val);
	// Colors
	if (asArray && v->obj->has_colors(*it)) {
	    iargs = Py_BuildValue("(s)", it->c_str());
	    val = objwavefront_get_colors(self, iargs, kwargs);
	    Py_DECREF(iargs);
	    if (val == NULL) {
		Py_DECREF(out);
		return NULL;
	    }
	    char key[100];
	    sprintf(key, "%s_colors", longName.c_str());
	    if (PyDict_SetItemString(out, key, val) < 0) {
		Py_DECREF(val);
		Py_DECREF(out);
		return NULL;
	    }
	    Py_DECREF(val);
	}
    }
    
    return out;
    
}


static PyObject* objwavefront_from_dict(PyObject* self, PyObject* args, PyObject* kwargs) {
    PyObject* inDict = NULL;
    
    if (!PyArg_ParseTuple(args, "O:", &inDict))
	return NULL;

    if (!PyDict_Check(inDict)) {
	PyErr_SetString(PyExc_TypeError, "Argument must be a dictionary.");
	return NULL;
    }

    PyObject* emptyArgs = PyTuple_New(0);

    PyObject* out = objwavefront_new(&ObjWavefront_Type, emptyArgs, inDict);
    
    Py_DECREF(emptyArgs);
    
    return out;
    
}

static PyObject* objwavefront_count_elements(PyObject* self, PyObject* args, PyObject* kwargs) {
    const char* elementType0 = 0;
    
    if (!PyArg_ParseTuple(args, "s:", &elementType0))
	return NULL;

    std::string elementType(elementType0);

    ObjWavefrontObject* v = (ObjWavefrontObject*) self;

    size_t nElements = v->obj->count_elements(elementType);
    PyObject* out = PyLong_FromSize_t(nElements);
    
    return out;
    
}


static PyObject* objwavefront_append(PyObject* self, PyObject* args, PyObject* kwargs) {
    PyObject* solf = NULL;
    if (!PyArg_ParseTuple(args, "O:", &solf))
	return NULL;
    if (!PyObject_IsInstance(solf, (PyObject*)&ObjWavefront_Type)) {
	PyErr_Format(PyExc_TypeError, "Can only append other ObjWavefront instances.");
	return NULL;
    }

    ObjWavefrontObject* v = (ObjWavefrontObject*) self;
    if (v->obj == ((ObjWavefrontObject*)solf)->obj) {
	ObjWavefront cpy(*v->obj);
	v->obj->append(&cpy);
    } else {
	v->obj->append(((ObjWavefrontObject*)solf)->obj);
    }
    if (!v->obj->is_valid()) {
	PyErr_SetString(geom_error, "Structure is invalid. Check that indexes do not exceed the number of vertices");
	return NULL;
    }
    Py_RETURN_NONE;
}


static PyObject* objwavefront_items(PyObject* self, PyObject*, PyObject*) {

    ObjWavefrontObject* v = (ObjWavefrontObject*) self;

    std::vector<std::string> unique = v->obj->element_types();
    PyObject* out = PyList_New(unique.size());
    if (out == NULL)
	return NULL;
    Py_ssize_t i = 0;
    for (std::vector<std::string>::const_iterator it = unique.begin(); it != unique.end(); it++, i++) {
	std::string longName = obj_code2long(*it);
	PyObject* iargs = Py_BuildValue("(s)", it->c_str());
	PyObject* val = objwavefront_get_elements(self, iargs, NULL);
	Py_DECREF(iargs);
	if (val == NULL) {
	    Py_DECREF(out);
	    return NULL;
	}
	PyObject* key = PyUnicode_FromString(longName.c_str());
	if (key == NULL) {
	    Py_DECREF(val);
	    Py_DECREF(out);
	    return NULL;
	}
	PyObject* item = PyTuple_Pack(2, key, val);
	Py_DECREF(key);
	Py_DECREF(val);
	if (item == NULL) {
	    Py_DECREF(out);
	    return NULL;
	}
	if (PyList_SetItem(out, i, item)) {
	    Py_DECREF(item);
	    Py_DECREF(out);
	    return NULL;
	}
    }
    
    return out;
}


static PyObject* objwavefront_bounds_get(PyObject* self, void*) {
    ObjWavefrontObject* v = (ObjWavefrontObject*) self;
    std::vector<double> mins = v->obj->minimums();
    std::vector<double> maxs = v->obj->maximums();
    npy_intp np_shape[1] = { (npy_intp) 3 };
    PyObject* pyMins = PyArray_EMPTY(1, np_shape, NPY_FLOAT64, 0);
    if (pyMins == NULL) return NULL;
    PyObject* pyMaxs = PyArray_EMPTY(1, np_shape, NPY_FLOAT64, 0);
    if (pyMaxs == NULL) {
	Py_DECREF(pyMins);
	return NULL;
    }
    std::memcpy(PyArray_DATA((PyArrayObject*)pyMins), mins.data(), 3 * sizeof(double));
    std::memcpy(PyArray_DATA((PyArrayObject*)pyMaxs), maxs.data(), 3 * sizeof(double));
    PyObject* out = Py_BuildValue("(OO)", pyMins, pyMaxs);
    Py_DECREF(pyMins);
    Py_DECREF(pyMaxs);
    return out;
}


static PyObject* objwavefront_mesh_get(PyObject* self, void*) {
    ObjWavefrontObject* v = (ObjWavefrontObject*) self;
    std::vector<std::vector<double>> mesh = v->obj->mesh();
    PyObject* out = PyList_New(mesh.size());
    if (out == NULL) return NULL;
    Py_ssize_t i = 0;
    for (std::vector<std::vector<double>>::const_iterator it = mesh.begin();
	 it != mesh.end(); it++, i++) {
	PyObject* item = vector2list(*it);
	if (item == NULL) {
	    Py_DECREF(out);
	    return NULL;
	}
	if (PyList_SetItem(out, i, item) < 0) {
	    Py_DECREF(item);
	    Py_DECREF(out);
	    return NULL;
	}
    }
    return out;
}


static PyObject* objwavefront_str(PyObject* self) {
    ObjWavefrontObject* v = (ObjWavefrontObject*) self;
    std::basic_stringstream<char> ss;
    ss << *v->obj;
    return PyUnicode_FromString(ss.str().c_str());
}


static Py_ssize_t objwavefront_size(PyObject* self) {
    ObjWavefrontObject* v = (ObjWavefrontObject*) self;
    Py_ssize_t out = (Py_ssize_t)v->obj->elements.size();
    return out;
}


static PyObject* objwavefront_subscript(PyObject* self, PyObject* key) {
    PyObject* iargs = Py_BuildValue("(O)", key);
    PyObject* out = objwavefront_get_elements(self, iargs, NULL);
    Py_DECREF(iargs);
    return out;
}


static int objwavefront_contains(PyObject* self, PyObject* value) {
    const char* elementType0;

    if (PyUnicode_Check(value)) {
	elementType0 = PyUnicode_AsUTF8(value);
	if (elementType0 == NULL) {
	    return -1;
	}
    } else {
	return 0;
    }

    std::string elementType = obj_alias2base(std::string(elementType0));

    ObjWavefrontObject* v = (ObjWavefrontObject*) self;

    if (v->obj->count_elements(elementType) == 0) {
	return 0;
    }

    return 1;
}


static PyObject* objwavefront_add_colors(PyObject* self, PyObject* args, PyObject* kwargs) {
    const char* name0 = 0;
    PyObject* x = NULL;
    
    if (!PyArg_ParseTuple(args, "sO:", &name0, &x))
	return NULL;

    std::string name(name0);

    ObjWavefrontObject* v = (ObjWavefrontObject*) self;

    if (PyList_Check(x)) {
	std::vector<uint8_t> values;
	if (PyList_Size(x) != (Py_ssize_t)v->obj->count_elements(name)) {
	    PyErr_SetString(geom_error, "Number of colors dosn't match the number of elements in the set.");
	    return NULL;
	}
	for (Py_ssize_t i = 0; i < PyList_Size(x); i++) {
	    PyObject* item = PyList_GetItem(x, i);
	    if (item == NULL) return NULL;
	    if (PyDict_Check(item)) {
		if (PyDict_Size(item) != 3) {
		    PyErr_SetString(geom_error, "Colors must each have 3 elements");
		    return NULL;
		}
		PyObject *key, *value;
		Py_ssize_t pos = 0;
		while (PyDict_Next(item, &pos, &key, &value)) {
		    if (!PyUnicode_Check(key)) {
			PyErr_SetString(PyExc_TypeError, "ObjWavefront element keys must be strings");
			return NULL;
		    }
		    if (PyLong_Check(value)) {
			long vc = PyLong_AsLong(value);
			if (vc < 0 || vc > 255) {
			    PyErr_SetString(geom_error, "Color out of range (0, 255).");
			    return NULL;
			}
			values.push_back((uint8_t)vc);
		    } else if (PyArray_CheckScalar(value)) {
			PyArray_Descr* desc = PyArray_DescrNewFromType(NPY_UINT8);
			uint8_t vc = 0;
			PyArray_CastScalarToCtype(value, &vc, desc);
			values.push_back(vc);
			Py_DECREF(desc);
		    } else {
			PyErr_SetString(PyExc_TypeError, "ObjWavefront element colors must be integers.");
			return NULL;
		    }
		}
	    } else if (PyList_Check(item)) {
		if (PyList_Size(item) != 3) {
		    PyErr_SetString(geom_error, "Colors must each have 3 elements");
		    return NULL;
		}
		for (Py_ssize_t j = 0; j < PyList_Size(item); j++) {
		    PyObject* value = PyList_GetItem(item, j);
		    if (value == NULL) return NULL;
		    if (PyLong_Check(value)) {
			long vc = PyLong_AsLong(value);
			if (vc < 0 || vc > 255) {
			    PyErr_SetString(geom_error, "Color out of range (0, 255).");
			    return NULL;
			}
			values.push_back((uint8_t)vc);
		    } else {
			PyErr_SetString(PyExc_TypeError, "ObjWavefront element color values must be integers.");
			return NULL;
		    }
		}
	    } else {
		PyErr_SetString(PyExc_TypeError, "ObjWavefront element colors must be lists or dictionaries.");
		return NULL;
	    }
	}
	SizeType xn = PyList_Size(x), xm = 3;
	if (!v->obj->add_element_set_colors(name, values.data(), xn, xm)) {
	    PyErr_SetString(geom_error, "Error adding colors array.");
	    return NULL;
	}
    } else if (PyArray_Check(x)) {
	SizeType xn = 0, xm = 0;
	int ndim = PyArray_NDIM((PyArrayObject*)x);
	if (ndim != 2) return NULL;
	npy_intp* np_shape = PyArray_SHAPE((PyArrayObject*)x);
	if (np_shape == NULL) return NULL;
	xn = (SizeType)(np_shape[0]);
	xm = (SizeType)(np_shape[1]);
	if (xn != v->obj->count_elements(name) || xm != 3) {
	    PyErr_SetString(geom_error, "Colors array is not the correct shape.");
	    return NULL;
	}
	PyObject* x2 = PyArray_Cast((PyArrayObject*)x, NPY_UINT8);
	if (x2 == NULL) return NULL;
	if (!PyArray_IS_C_CONTIGUOUS((PyArrayObject*)x2)) {
	    PyArrayObject* cpy = PyArray_GETCONTIGUOUS((PyArrayObject*)x2);
	    if (cpy == NULL) return NULL;
	    Py_DECREF(x2);
	    x2 = (PyObject*)cpy;
	}
	uint8_t* xa = (uint8_t*)PyArray_BYTES((PyArrayObject*)x2);
	bool ret = v->obj->add_element_set_colors(name, xa, xn, xm);
	Py_DECREF(x2);
	if (!ret) {
	    PyErr_SetString(geom_error, "Error adding colors array.");
	    return NULL;
	}
    } else {
	PyErr_SetString(PyExc_TypeError, "ObjWavefront element colors must be lists of element dictionaries or an array.");
	return NULL;
    }
    Py_RETURN_NONE;
}


static PyObject* objwavefront_get_colors(PyObject* self, PyObject* args, PyObject* kwargs) {
    const char* elementType0 = 0;
    int asArray = 0;
    
    static char const* kwlist[] = {
	"name",
	"as_array",
        NULL
    };
    
    
    if (!PyArg_ParseTupleAndKeywords(args, kwargs, "s|p:", (char**) kwlist,
				     &elementType0, &asArray))
	return NULL;

    std::string elementType(elementType0);

    ObjWavefrontObject* v = (ObjWavefrontObject*) self;
    
    PyObject* out = NULL;
    
    if (asArray) {
	
	size_t N = 0, M = 0;
	std::vector<uint8_t> vect = v->obj->get_colors_array(elementType, N, M);
	PyArray_Descr* desc = PyArray_DescrNewFromType(NPY_UINT8);
	if (desc == NULL) return NULL;
	npy_intp np_shape[2] = { (npy_intp)N, (npy_intp)M };
	PyObject* tmp = PyArray_NewFromDescr(&PyArray_Type, desc,
					     2, np_shape, NULL,
					     (void*)vect.data(), 0, NULL);
	if (tmp == NULL) return NULL;
	out = (PyObject*)PyArray_NewCopy((PyArrayObject*)tmp, NPY_CORDER);
	Py_DECREF(tmp);

    } else {
	size_t N = 0, M = 0;
	std::vector<uint8_t> vect = v->obj->get_colors_array(elementType, N, M);
	PyObject* out = PyList_New(N);
	if (out == NULL) {
	    return NULL;
	}
	for (Py_ssize_t i = 0; i < (Py_ssize_t)N; i++) {
	    PyObject* item = PyDict_New();
	    if (item == NULL) {
		Py_DECREF(out);
		return NULL;
	    }
	    size_t j = 0;
	    std::vector<std::string> colors({"red", "green", "blue"});
	    for (std::vector<std::string>::const_iterator p = colors.begin(); p != colors.end(); p++, j++) {
		PyObject* ival = PyLong_FromLong(static_cast<long>(vect[i * 3 + j]));
		if (ival == NULL) {
		    Py_DECREF(item);
		    Py_DECREF(out);
		    return NULL;
		}
		if (PyDict_SetItemString(item, p->c_str(), ival) < 0) {
		    Py_DECREF(ival);
		    Py_DECREF(item);
		    Py_DECREF(out);
		    return NULL;
		}
		Py_DECREF(ival);
	    }
	    if (PyList_SetItem(out, i, item) < 0) {
		Py_DECREF(item);
		Py_DECREF(out);
		return NULL;
	    }
	}
    }
    
    return out;

    
}


////////////
// Module //
////////////


static PyMethodDef geom_functions[] = {
    {NULL, NULL, 0, NULL} /* sentinel */
};


static int
geom_module_exec(PyObject* m)
{
    if (PyType_Ready(&Ply_Type) < 0)
        return -1;

    if (PyType_Ready(&ObjWavefront_Type) < 0)
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

    Py_INCREF(&Ply_Type);
    if (PyModule_AddObject(m, "Ply", (PyObject*) &Ply_Type) < 0) {
        Py_DECREF(&Ply_Type);
        return -1;
    }

    Py_INCREF(&ObjWavefront_Type);
    if (PyModule_AddObject(m, "ObjWavefront", (PyObject*) &ObjWavefront_Type) < 0) {
        Py_DECREF(&ObjWavefront_Type);
        return -1;
    }

    geom_error = PyErr_NewException("rapidjson.GeometryError",
				    PyExc_ValueError, NULL);
    if (geom_error == NULL)
        return -1;
    Py_INCREF(geom_error);
    if (PyModule_AddObject(m, "GeometryError", geom_error) < 0) {
        Py_DECREF(geom_error);
        return -1;
    }

    return 0;
}


static struct PyModuleDef_Slot geom_slots[] = {
    {Py_mod_exec, (void*) geom_module_exec},
    {0, NULL}
};


static PyModuleDef geom_module = {
    PyModuleDef_HEAD_INIT,      /* m_base */
    "geometry",                 /* m_name */
    PyDoc_STR("Structures for handling 3D geometries."),
    0,                          /* m_size */
    geom_functions,            /* m_methods */
    geom_slots,                /* m_slots */
    NULL,                       /* m_traverse */
    NULL,                       /* m_clear */
    NULL                        /* m_free */
};


PyMODINIT_FUNC
PyInit_geom()
{
    return PyModuleDef_Init(&geom_module);
}
