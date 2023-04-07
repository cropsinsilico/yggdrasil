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
static int ply_add_elements_from_dict(PyObject *self, PyObject* kwargs, bool preserveOrder=false);
static PyObject* ply_richcompare(PyObject *self, PyObject *other, int op);
static PyObject* ply_get_elements(PyObject* self, PyObject* args, PyObject* kwargs);
static PyObject* ply_add_elements(PyObject* self, PyObject* args, PyObject* kwargs);
static PyObject* ply_as_trimesh(PyObject* self, PyObject* args, PyObject* kwargs);
static PyObject* ply_from_trimesh(PyObject* cls, PyObject* args, PyObject* kwargs);
static PyObject* ply_as_dict(PyObject* self, PyObject* args, PyObject* kwargs);
static PyObject* ply_from_dict(PyObject* self, PyObject* args, PyObject* kwargs);
static PyObject* ply_as_array_dict(PyObject* self, PyObject* args, PyObject* kwargs);
static PyObject* ply_from_array_dict(PyObject* self, PyObject* args, PyObject* kwargs);
static PyObject* ply_count_elements(PyObject* self, PyObject* args, PyObject* kwargs);
static PyObject* ply_append(PyObject* self, PyObject* args, PyObject* kwargs);
static PyObject* ply_merge(PyObject* self, PyObject* args, PyObject* kwargs);
static PyObject* ply_bounds_get(PyObject* self, void*);
static PyObject* ply_mesh_get(PyObject* self, void*);
static PyObject* ply_nvert(PyObject* self, void*);
static PyObject* ply_nface(PyObject* self, void*);
static PyObject* ply_str(PyObject* self);
static Py_ssize_t ply_size(PyObject* self);
static PyObject* ply_subscript(PyObject* self, PyObject* key);
static int ply_contains(PyObject* self, PyObject* value);
static PyObject* ply_items(PyObject* self, PyObject* args, PyObject* kwargs);
static PyObject* ply_add_colors(PyObject* self, PyObject* args, PyObject* kwargs);
static PyObject* ply_get_colors(PyObject* self, PyObject* args, PyObject* kwargs);
static PyObject* ply__getstate__(PyObject* self, PyObject* args, PyObject* kwargs);
static PyObject* ply__setstate__(PyObject* self, PyObject* state);


// Objwavefront
static void objwavefront_dealloc(PyObject* self);
static PyObject* objwavefront_new(PyTypeObject* type, PyObject* args, PyObject* kwargs);
static int objwavefront_add_elements_from_dict(PyObject *self, PyObject* kwargs, bool preserveOrder=false);
static int objwavefront_add_elements_from_list(PyObject *self, PyObject* kwargs);
static int objwavefront_add_element_from_python(PyObject* self, PyObject* x, std::string name="");
static PyObject* objwavefront_element2dict(const ObjElement* x, bool includeCode=false);
static PyObject* objwavefront_richcompare(PyObject *self, PyObject *other, int op);
static PyObject* objwavefront_get_elements(PyObject* self, PyObject* args, PyObject* kwargs);
static PyObject* objwavefront_add_elements(PyObject* self, PyObject* args, PyObject* kwargs);
static PyObject* objwavefront_as_trimesh(PyObject* self, PyObject* args, PyObject* kwargs);
static PyObject* objwavefront_from_trimesh(PyObject* cls, PyObject* args, PyObject* kwargs);
static PyObject* objwavefront_as_dict(PyObject* self, PyObject* args, PyObject* kwargs);
static PyObject* objwavefront_from_dict(PyObject* self, PyObject* args, PyObject* kwargs);
static PyObject* objwavefront_as_array_dict(PyObject* self, PyObject* args, PyObject* kwargs);
static PyObject* objwavefront_from_array_dict(PyObject* self, PyObject* args, PyObject* kwargs);
static PyObject* objwavefront_as_list(PyObject* self, PyObject* args, PyObject* kwargs);
static PyObject* objwavefront_from_list(PyObject* self, PyObject* args, PyObject* kwargs);
static PyObject* objwavefront_count_elements(PyObject* self, PyObject* args, PyObject* kwargs);
static PyObject* objwavefront_append(PyObject* self, PyObject* args, PyObject* kwargs);
static PyObject* objwavefront_merge(PyObject* self, PyObject* args, PyObject* kwargs);
static PyObject* objwavefront_bounds_get(PyObject* self, void*);
static PyObject* objwavefront_mesh_get(PyObject* self, void*);
static PyObject* objwavefront_nvert(PyObject* self, void*);
static PyObject* objwavefront_nface(PyObject* self, void*);
static PyObject* objwavefront_str(PyObject* self);
static Py_ssize_t objwavefront_size(PyObject* self);
static PyObject* objwavefront_subscript(PyObject* self, PyObject* key);
static int objwavefront_contains(PyObject* self, PyObject* value);
static PyObject* objwavefront_items(PyObject* self, PyObject* args, PyObject* kwargs);
static PyObject* objwavefront_add_colors(PyObject* self, PyObject* args, PyObject* kwargs);
static PyObject* objwavefront_get_colors(PyObject* self, PyObject* args, PyObject* kwargs);
static PyObject* objwavefront__getstate__(PyObject* self, PyObject* args, PyObject* kwargs);
static PyObject* objwavefront__setstate__(PyObject* self, PyObject* state);


///////////////////////
// Trimesh utilities //
///////////////////////

PyObject* import_trimesh_class() {
    PyObject* trimesh = PyImport_ImportModule("trimesh");
    if (trimesh == NULL) {
	PyErr_Clear();
	return NULL;
    }
    PyObject* out = PyObject_GetAttrString(trimesh, "Trimesh");
    Py_DECREF(trimesh);
    return out;
}
PyObject* trimesh2dict(PyObject* solf) {
    PyObject* trimeshClass = import_trimesh_class();
    if (trimeshClass == NULL) {
	PyErr_Format(PyExc_ImportError, "Trimesh not available");
	return NULL;
    }
    if (!PyObject_IsInstance(solf, trimeshClass)) {
	Py_DECREF(trimeshClass);
	PyErr_Format(PyExc_TypeError, "Input is not a trimesh class.");
	return NULL;
    }
    Py_DECREF(trimeshClass);
    PyObject* vertices = PyObject_GetAttrString(solf, "vertices");
    if (vertices == NULL)
	return NULL;
    PyObject* visual = PyObject_GetAttrString(solf, "visual");
    if (visual == NULL) {
	Py_DECREF(vertices);
	return NULL;
    }
    PyObject* vertex_colors = PyObject_GetAttrString(visual, "vertex_colors");
    Py_DECREF(visual);
    if (vertex_colors == NULL) {
	Py_DECREF(vertices);
	return NULL;
    }
    PyObject* slice1 = PySlice_New(NULL, NULL, NULL);
    if (slice1 == NULL) {
	Py_DECREF(vertex_colors);
	Py_DECREF(vertices);
	return NULL;
    }
    PyObject* end = PyLong_FromLong(3);
    if (end == NULL) {
	Py_DECREF(slice1);
	Py_DECREF(vertex_colors);
	Py_DECREF(vertices);
	return NULL;
    }
    PyObject* slice2 = PySlice_New(NULL, end, NULL);
    Py_DECREF(end);
    if (slice2 == NULL) {
	Py_DECREF(slice1);
	Py_DECREF(vertex_colors);
	Py_DECREF(vertices);
	return NULL;
    }
    PyObject* slices = PyTuple_Pack(2, slice1, slice2);
    if (slices == NULL) {
	Py_DECREF(slice2);
	Py_DECREF(slice1);
	Py_DECREF(vertex_colors);
	Py_DECREF(vertices);
	return NULL;
    }
    PyObject* vertex_colors_sliced = PyObject_GetItem(vertex_colors, slices);
    Py_DECREF(vertex_colors);
    Py_DECREF(slices);
    if (vertex_colors_sliced == NULL) {
	Py_DECREF(vertices);
	return NULL;
    }
    PyObject* faces = PyObject_GetAttrString(solf, "faces");
    if (faces == NULL) {
	Py_DECREF(vertices);
	Py_DECREF(vertex_colors_sliced);
	return NULL;
    }
    PyObject* astypeMethod = PyUnicode_FromString("astype");
    if (astypeMethod == NULL) {
	Py_DECREF(faces);
	Py_DECREF(vertices);
	Py_DECREF(vertex_colors_sliced);
	return NULL;
    }
    PyObject* int32 = PyUnicode_FromString("int32");
    if (int32 == NULL) {
	Py_DECREF(faces);
	Py_DECREF(astypeMethod);
	Py_DECREF(vertices);
	Py_DECREF(vertex_colors_sliced);
	return NULL;
    }
    PyObject* faces_int32 = PyObject_CallMethodObjArgs(faces, astypeMethod, int32, NULL);
    Py_DECREF(faces);
    Py_DECREF(astypeMethod);
    Py_DECREF(int32);
    if (faces_int32 == NULL) {
	Py_DECREF(vertices);
	Py_DECREF(vertex_colors_sliced);
	return NULL;
    }
    PyObject* dict_kwargs = PyDict_New();
    if (dict_kwargs == NULL) {
	Py_DECREF(vertices);
	Py_DECREF(vertex_colors_sliced);
	Py_DECREF(faces_int32);
	return NULL;
    }
    PyObject* numpy = PyImport_ImportModule("numpy");
    if (numpy == NULL) {
	Py_DECREF(dict_kwargs);
	Py_DECREF(vertices);
	Py_DECREF(vertex_colors_sliced);
	Py_DECREF(faces_int32);
	PyErr_Format(PyExc_ImportError, "Numpy not available");
	return NULL;
    }
    PyObject* ndarray = PyObject_GetAttrString(numpy, "ndarray");
    Py_DECREF(numpy);
    if (ndarray == NULL) {
	Py_DECREF(dict_kwargs);
	Py_DECREF(vertices);
	Py_DECREF(vertex_colors_sliced);
	Py_DECREF(faces_int32);
	return NULL;
    }
    PyObject* viewMethod = PyUnicode_FromString("view");
    if (viewMethod == NULL) {
	Py_DECREF(dict_kwargs);
	Py_DECREF(vertices);
	Py_DECREF(vertex_colors_sliced);
	Py_DECREF(faces_int32);
	Py_DECREF(ndarray);
	return NULL;
    }
#define ADD_KEY_(name, var)					\
    PyObject* var ## _array = PyObject_CallMethodObjArgs(var, viewMethod, ndarray, NULL); \
    if (var ## _array == NULL) {					\
	Py_DECREF(dict_kwargs);						\
	Py_DECREF(vertices);						\
	Py_DECREF(vertex_colors_sliced);				\
	Py_DECREF(faces_int32);						\
	Py_DECREF(ndarray);						\
	return NULL;							\
    }									\
    if (PyObject_Size(var ## _array) > 0) {				\
	if (PyDict_SetItemString(dict_kwargs, #name, var ## _array) < 0) { \
	    Py_DECREF(dict_kwargs);					\
	    Py_DECREF(vertices);					\
	    Py_DECREF(vertex_colors_sliced);				\
	    Py_DECREF(faces_int32);					\
	    Py_DECREF(ndarray);						\
	    return NULL;						\
	}								\
    }									\
    Py_DECREF(var ## _array)
    ADD_KEY_(vertex, vertices);
    ADD_KEY_(vertex_colors, vertex_colors_sliced);
    ADD_KEY_(face, faces_int32);
#undef ADD_KEY_
    Py_DECREF(vertices);
    Py_DECREF(vertex_colors_sliced);
    Py_DECREF(faces_int32);
    Py_DECREF(viewMethod);
    Py_DECREF(ndarray);
    return dict_kwargs;
}
PyObject* dict2trimesh(PyObject* solf, PyObject* add_kwargs,
		       bool decIndex=false) {
    PyObject* trimeshClass = import_trimesh_class();
    if (trimeshClass == NULL) {
	PyErr_Format(PyExc_ImportError, "Trimesh not available");
	return NULL;
    }
    PyObject* kwargs = PyDict_New();
    if (kwargs == NULL) {
	Py_DECREF(trimeshClass);
	return NULL;
    }
    PyObject* x = NULL;
#define ADD_KEY_(nameA, nameB)						\
    x = PyDict_GetItemString(solf, #nameA);				\
    if (x == NULL) {							\
	x = Py_None;							\
    } else if (decIndex && std::string(#nameA) == std::string("face")) { \
	PyObject* inc = PyLong_FromLong(1);				\
	if (PyNumber_InPlaceSubtract(x, inc) == NULL) {			\
	    Py_DECREF(inc);						\
	    Py_DECREF(trimeshClass);					\
	    Py_DECREF(kwargs);						\
	    return NULL;						\
	}								\
	Py_DECREF(inc);							\
    }									\
    if (PyDict_SetItemString(kwargs, #nameB, x) < 0) {			\
	Py_DECREF(trimeshClass);					\
	Py_DECREF(kwargs);						\
	return NULL;							\
    }
    ADD_KEY_(vertex, vertices)
    ADD_KEY_(vertex_colors, vertex_colors)
    ADD_KEY_(face, faces)
#undef ADD_KEY_
    if (PyDict_SetItemString(kwargs, "process", Py_False) < 0) {
	Py_DECREF(trimeshClass);
	Py_DECREF(kwargs);
	return NULL;
    }
    PyObject* args = PyTuple_New(0);
    if (args == NULL) {
	Py_DECREF(trimeshClass);
	Py_DECREF(kwargs);
	return NULL;
    }
    if (add_kwargs != NULL) {
	if (PyDict_Update(kwargs, add_kwargs) < 0) {
	    Py_DECREF(trimeshClass);
	    Py_DECREF(args);
	    Py_DECREF(kwargs);
	}
    }
    PyObject* out = PyObject_Call(trimeshClass, args, kwargs);
    Py_DECREF(trimeshClass);
    Py_DECREF(args);
    Py_DECREF(kwargs);
    return out;
}


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
    {"get", (PyCFunction) ply_get_elements,
     METH_VARARGS | METH_KEYWORDS,
     "Get all elements of a given type."},
    {"add_elements", (PyCFunction) ply_add_elements,
     METH_VARARGS, "Add elements of a given type."},
    {"as_trimesh", (PyCFunction) ply_as_trimesh,
     METH_VARARGS | METH_KEYWORDS,
     "Get the structure as a Trimesh mesh."},
    {"from_trimesh", (PyCFunction) ply_from_trimesh,
     METH_VARARGS | METH_CLASS,
     "Create a Ply object from a Trimesh mesh."},
    {"as_dict", (PyCFunction) ply_as_dict,
     METH_VARARGS | METH_KEYWORDS,
     "Get the structure as a dictionary."},
    {"from_dict", (PyCFunction) ply_from_dict,
     METH_VARARGS | METH_CLASS,
     "Create a Ply instance from a dictionary of elements."},
    {"as_array_dict", (PyCFunction) ply_as_array_dict,
     METH_VARARGS | METH_KEYWORDS,
     "Get the structure as a dictionary of arrays."},
    {"from_array_dict", (PyCFunction) ply_from_array_dict,
     METH_VARARGS | METH_CLASS,
     "Create a Ply instance from a dictionary of element arrays."},
    {"count_elements", (PyCFunction) ply_count_elements,
     METH_VARARGS,
     "Get the number of elements of a given type in the structure."},
    {"append", (PyCFunction) ply_append,
     METH_VARARGS,
     "Append another 3D structure."},
    {"merge", (PyCFunction) ply_merge,
     METH_VARARGS | METH_KEYWORDS,
     "Merge this structure with one or more other 3D structures and return the result."},
    {"items", (PyCFunction) ply_items,
     METH_NOARGS,
     "Get the dict-like list of items in the structure."},
    {"get_colors", (PyCFunction) ply_get_colors,
     METH_VARARGS | METH_KEYWORDS,
     "Get colors associated with elements of a given type."},
    {"add_colors", (PyCFunction) ply_add_colors,
     METH_VARARGS,
     "Set colors associated with elements of a given type."},
    {"__getstate__", (PyCFunction) ply__getstate__,
     METH_NOARGS,
     "Get the instance state."},
    {"__setstate__", (PyCFunction) ply__setstate__,
     METH_O,
     "Set the instance state."},
    {NULL}  /* Sentinel */
};


static PyGetSetDef ply_properties[] = {
    {"bounds", ply_bounds_get, NULL,
     "The minimum & maximum bounds for the structure in x, y, & z.", NULL},
    {"mesh", ply_mesh_get, NULL,
     "The 3D mesh representing the faces in the structure.", NULL},
    {"nvert", ply_nvert, NULL,
     "The number of vertices in the structure.", NULL},
    {"nface", ply_nface, NULL,
     "The number of faces in the structure.", NULL},
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
    "yggdrasil.rapidjson.geometry.Ply",       /* tp_name */
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
    {"get", (PyCFunction) objwavefront_get_elements,
     METH_VARARGS | METH_KEYWORDS,
     "Get all elements of a given type."},
    {"get_elements", (PyCFunction) objwavefront_get_elements,
     METH_VARARGS | METH_KEYWORDS,
     "Get all elements of a given type."},
    {"add_elements", (PyCFunction) objwavefront_add_elements,
     METH_VARARGS, "Add elements of a given type."},
    {"as_trimesh", (PyCFunction) objwavefront_as_trimesh,
     METH_VARARGS | METH_KEYWORDS,
     "Get the structure as a Trimesh mesh."},
    {"from_trimesh", (PyCFunction) objwavefront_from_trimesh,
     METH_VARARGS | METH_CLASS,
     "Create a ObjWavefront object from a Trimesh mesh."},
    {"as_dict", (PyCFunction) objwavefront_as_dict,
     METH_VARARGS | METH_KEYWORDS,
     "Get the structure as a dictionary."},
    {"from_dict", (PyCFunction) objwavefront_from_dict,
     METH_VARARGS | METH_CLASS,
     "Create a ObjWavefront instance from a dictionary of elements."},
    {"as_array_dict", (PyCFunction) objwavefront_as_array_dict,
     METH_VARARGS | METH_KEYWORDS,
     "Get the structure as a dictionary of arrays."},
    {"from_array_dict", (PyCFunction) objwavefront_from_array_dict,
     METH_VARARGS | METH_CLASS,
     "Create a ObjWavefront instance from a dictionary of element arrays."},
    {"as_list", (PyCFunction) objwavefront_as_list,
     METH_NOARGS,
     "Get the structure as a list of elements."},
    {"from_list", (PyCFunction) objwavefront_from_list,
     METH_VARARGS | METH_CLASS,
     "Create a ObjWavefront instance from a list of elements."},
    {"count_elements", (PyCFunction) objwavefront_count_elements,
     METH_VARARGS,
     "Get the number of elements of a given type in the structure."},
    {"append", (PyCFunction) objwavefront_append,
     METH_VARARGS,
     "Append another 3D structure."},
    {"merge", (PyCFunction) objwavefront_merge,
     METH_VARARGS | METH_KEYWORDS,
     "Merge this structure with one or more other 3D structures and return the result."},
    {"items", (PyCFunction) objwavefront_items,
     METH_NOARGS,
     "Get the dict-like list of items in the structure."},
    {"get_colors", (PyCFunction) objwavefront_get_colors,
     METH_VARARGS | METH_KEYWORDS,
     "Get colors associated with elements of a given type."},
    {"add_colors", (PyCFunction) objwavefront_add_colors,
     METH_VARARGS,
     "Set colors associated with elements of a given type."},
    {"__getstate__", (PyCFunction) objwavefront__getstate__,
     METH_NOARGS,
     "Get the instance state."},
    {"__setstate__", (PyCFunction) objwavefront__setstate__,
     METH_O,
     "Set the instance state."},
    {NULL}  /* Sentinel */
};


static PyGetSetDef objwavefront_properties[] = {
    {"bounds", objwavefront_bounds_get, NULL,
     "The minimum & maximum bounds for the structure in x, y, & z.", NULL},
    {"mesh", objwavefront_mesh_get, NULL,
     "The 3D mesh representing the faces in the structure.", NULL},
    {"nvert", objwavefront_nvert, NULL,
     "The number of vertices in the structure.", NULL},
    {"nface", objwavefront_nface, NULL,
     "The number of faces in the structure.", NULL},
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
    "yggdrasil.rapidjson.geometry.ObjWavefront",  /* tp_name */
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


/////////////////
// Ply Methods //
/////////////////


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

    PlyObject* v = (PlyObject*) type->tp_alloc(type, 0);
    if (v == NULL)
        return NULL;
    if (vertObject != NULL &&
	PyObject_IsInstance(vertObject, (PyObject*)&Ply_Type)) {
	v->ply = new Ply(*(((PlyObject*)vertObject)->ply));
	vertObject = NULL;
    } else if (vertObject != NULL &&
	       PyObject_IsInstance(vertObject, (PyObject*)&ObjWavefront_Type)) {
	v->ply = new Ply(*(((ObjWavefrontObject*)vertObject)->obj));
	vertObject = NULL;
    } else {
	v->ply = new Ply();
    }

    const char* readFrom = 0;
    if (vertObject != NULL && PyUnicode_Check(vertObject)) {
	readFrom = PyUnicode_AsUTF8(vertObject);
	vertObject = NULL;
    } else if (vertObject != NULL && PyBytes_Check(vertObject)) {
	readFrom = PyBytes_AsString(vertObject);
	vertObject = NULL;
    }
    if (readFrom) {
	std::stringstream ss;
	ss.str(std::string(readFrom));
	if (!v->ply->read(ss)) {
	    PyErr_SetString(geom_error, "Error reading from string");
	    return NULL;
	}
    }
    if (vertObject != NULL && PyDict_Check(vertObject)) {
	if (ply_add_elements_from_dict((PyObject*)v, vertObject) < 0)
	    return NULL;
	vertObject = NULL;
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

    if (ply_add_elements_from_dict((PyObject*)v, kwargs) < 0)
	return NULL;

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


static int ply_add_elements_from_dict(PyObject *self, PyObject* kwargs,
				      bool preserveOrder) {
    if (kwargs == NULL)
	return 0;
    if (!PyDict_Check(kwargs))
	return -1;
    if (PyDict_Size(kwargs) == 0)
	return 0;
    PyObject *key, *value;
    Py_ssize_t pos = 0;
    std::vector<std::string> skip, delayed;
    
    // Do comments & vertices first
    if (!preserveOrder) {
	std::vector<std::string> skip_names = {"comment", "comments", "vertex", "vertices", "vertexes"};
	for (std::vector<std::string>::iterator it = skip_names.begin();
	     it != skip_names.end(); it++) {
	    value = PyDict_GetItemString(kwargs, it->c_str());
	    if (value == NULL) continue;
	    PyObject* iargs = Py_BuildValue("(sO)", it->c_str(), value);
	    if (ply_add_elements(self, iargs, NULL) == NULL) {
		Py_DECREF(iargs);
		return -1;
	    }
	    Py_DECREF(iargs);
	    skip.push_back(*it);
	}
    }
    while (PyDict_Next(kwargs, &pos, &key, &value)) {
	std::string keyS(PyUnicode_AsUTF8(key));
	bool skipped = false;
	for (std::vector<std::string>::iterator it = skip.begin();
	     it != skip.end(); it++) {
	    if (keyS == *it) {
		skipped = true;
		break;
	    }
	}
	if (skipped) continue;
	if (keyS.size() > 7 &&
	    keyS.substr(keyS.size() - 7) == "_colors") {
	    delayed.push_back(keyS);
	    continue;
	}
	PyObject* iargs = Py_BuildValue("(OO)", key, value);
	if (ply_add_elements(self, iargs, NULL) == NULL) {
	    Py_DECREF(iargs);
	    return -1;
	}
	Py_DECREF(iargs);
    }
    for (std::vector<std::string>::iterator it = delayed.begin();
	 it != delayed.end(); it++) {
	value = PyDict_GetItemString(kwargs, it->c_str());
	PyObject* iargs = Py_BuildValue("(sO)", it->c_str(), value);
	if (ply_add_elements(self, iargs, NULL) == NULL) {
	    Py_DECREF(iargs);
	    return -1;
	}
	Py_DECREF(iargs);
    }
    return 0;
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
    PyObject* defaultRet = NULL;
    
    static char const* kwlist[] = {
	"name",
	"default",
	"as_array",
        NULL
    };

    if (!PyArg_ParseTupleAndKeywords(args, kwargs, "s|Op:", (char**) kwlist,
				     &elementType0, &defaultRet, &asArray))
	return NULL;

    std::string elementType(elementType0);

    PlyObject* v = (PlyObject*) self;

    PyObject* out = NULL;
    
    if (ply_alias2base(elementType) == "comment") {
	out = PyList_New(v->ply->comments.size());
	if (out == NULL)
	    return NULL;
	Py_ssize_t i = 0;
	for (std::vector<std::string>::const_iterator it = v->ply->comments.begin();
	     it != v->ply->comments.end(); it++, i++) {
	    PyObject* iComment = PyUnicode_FromStringAndSize(it->c_str(), (Py_ssize_t)(it->size()));
	    if (iComment == NULL) {
		Py_DECREF(out);
		return NULL;
	    }
	    if (PyList_SetItem(out, i, iComment) < 0) {
		Py_DECREF(out);
		return NULL;
	    }
	}
	return out;
    }
    const PlyElementSet* elementSet = v->ply->get_element_set(elementType);
    if (elementSet == NULL) {
	if (defaultRet == NULL) {
	    PyErr_SetString(PyExc_KeyError, elementType0);
	    return NULL;
	} else {
	    Py_INCREF(defaultRet);
	    return defaultRet;
	}
    }
    
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
	out = PyList_New(elementSet->elements.size());
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
	    for (std::vector<std::string>::const_iterator p = elit->property_order.begin(); p != elit->property_order.end(); p++) {
		PyObject* ival = NULL;
		uint16_t p_flags = elit->flags(*p);
#define CASE_SCALAR_(dst, flag, type, method, ...)			\
		case (PlyElement::ElementType::flag): {			\
		    dst = method(elit->get_value_as<type>(__VA_ARGS__)); \
		    break;						\
		}
#define CASE_SCALAR_NPY_(dst, flag, type, npy_type, ...)		\
		case (PlyElement::ElementType::flag): {			\
		    PyArray_Descr* desc = PyArray_DescrNewFromType(npy_type); \
		    type svalue = elit->get_value_as<type>(__VA_ARGS__); \
		    dst = PyArray_Scalar(&svalue, desc, NULL);		\
		    break;						\
		}
#define CASES_SCALAR_NPY_(dst, flag, type, npy_type, ...)		\
		CASE_SCALAR_NPY_(dst, k ## flag ## 8Flag, type ## 8_t, NPY_ ## npy_type ## 8, __VA_ARGS__) \
		CASE_SCALAR_NPY_(dst, k ## flag ## 16Flag, type ## 16_t, NPY_ ## npy_type ## 16, __VA_ARGS__) \
		CASE_SCALAR_NPY_(dst, k ## flag ## 32Flag, type ## 32_t, NPY_ ## npy_type ## 32, __VA_ARGS__)
#define SWITCH_SCALAR_(dst, ...)					\
		switch (p_flags) {					\
		    CASES_SCALAR_NPY_(dst, Int, int, INT, __VA_ARGS__)	\
		    CASES_SCALAR_NPY_(dst, Uint, uint, UINT, __VA_ARGS__) \
		    CASE_SCALAR_NPY_(dst, kFloatFlag, float, NPY_FLOAT, __VA_ARGS__) \
		    CASE_SCALAR_(dst, kDoubleFlag, double, PyFloat_FromDouble, __VA_ARGS__) \
		default: {						\
		    dst = PyFloat_FromDouble(elit->get_value_as<double>(__VA_ARGS__)); \
		}							\
		}
		if (elit->is_vector(*p)) {
		    p_flags = (uint16_t)(p_flags & ~PlyElement::ElementType::kListFlag);
		    ival = PyList_New(elit->size());
		    if (ival != NULL) {
			for (size_t iProp = 0; iProp < elit->size(); iProp++) {
			    PyObject* iival = NULL;
			    SWITCH_SCALAR_(iival, *p, iProp)
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
		    SWITCH_SCALAR_(ival, *p)
		}
#undef SWITCH_SCALAR_
#undef CASES_SCALAR_NPY_
#undef CASE_SCALAR_NPY_
#undef CASE_SCALAR_
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

    if (ply_alias2base(name) == "comment") {
	if (!PySequence_Check(x)) {
	    PyErr_SetString(PyExc_TypeError, "Ply comments must be provided as a sequence of strings");
	    return NULL;
	}
	for (Py_ssize_t iC = 0; iC != PySequence_Size(x); iC++) {
	    PyObject* iComment = PySequence_GetItem(x, iC);
	    if (iComment == NULL)
		return NULL;
	    if (!PyUnicode_Check(iComment)) {
		PyErr_SetString(PyExc_TypeError, "Ply comments must be strings");
		Py_DECREF(iComment);
		return NULL;
	    }
	    std::string iCommentS(PyUnicode_AsUTF8(iComment));
	    v->ply->comments.push_back(iCommentS);
	    Py_DECREF(iComment);
	}
    } else if (PyList_Check(x)) {
	for (Py_ssize_t i = 0; i < PyList_Size(x); i++) {
	    PyObject* item = PyList_GetItem(x, i);
	    if (item == NULL) return NULL;
	    if (PyDict_Check(item)) {
		PyObject *key, *value;
		Py_ssize_t pos = 0;
		PlyElement* new_element = v->ply->add_element(name);
		if (!new_element) {
		    PyErr_SetString(geom_error, "Error adding element to Ply instance");
		    return NULL;
		}
		while (PyDict_Next(item, &pos, &key, &value)) {
		    if (!PyUnicode_Check(key)) {
			PyErr_SetString(PyExc_TypeError, "Ply element keys must be strings");
			return NULL;
		    }
		    std::string iname = std::string(PyUnicode_AsUTF8(key));
		    bool iIsColor = (iname == "red" || iname == "blue" || iname == "green");
#define HANDLE_SCALAR_(type, method)					\
		    type ivalue = method;				\
		    if (!new_element->set_property(iname, ivalue, iIsColor)) {	\
			PyErr_SetString(geom_error, "Error adding " #type " value to Ply element"); \
			return NULL;					\
		    }
#define HANDLE_SCALAR_NPY_(type, npy_type)				\
		    type ivalue;					\
		    PyArray_Descr* desc = PyArray_DescrNewFromType(npy_type); \
		    PyArray_CastScalarToCtype(value, &ivalue, desc);	\
		    Py_DECREF(desc);					\
		    if (!new_element->set_property(iname, ivalue, iIsColor)) {	\
			PyErr_SetString(geom_error, "Error adding " #type " numpy scalar value to Ply element"); \
			return NULL;					\
		    }
#define CASE_SCALAR_NPY_(type, npy_type)				\
		    if (value_desc->type_num == npy_type) {		\
			HANDLE_SCALAR_NPY_(type, npy_type)		\
		    }
#define CASES_SCALAR_NPY_(type, npy_type)				\
		    CASE_SCALAR_NPY_(type ## 8_t, NPY_ ## npy_type ## 8) \
		    else CASE_SCALAR_NPY_(type ## 16_t, NPY_ ## npy_type ## 16) \
		    else CASE_SCALAR_NPY_(type ## 32_t, NPY_ ## npy_type ## 32) \
		    else CASE_SCALAR_NPY_(type ## 64_t, NPY_ ## npy_type ## 64)
#define HANDLE_ARRAY_(type, check, method)				\
		    std::vector<type> values;				\
		    for (Py_ssize_t j = 0; j < PyList_Size(value); j++) { \
			PyObject* vv = PyList_GetItem(value, j);	\
			if (vv == NULL) return NULL;			\
			if (!check(vv)) {				\
			    PyErr_SetString(geom_error, "Error adding " #type " values array to Ply element. Not all elements are the same type."); \
			    return NULL;				\
			}						\
			values.push_back(method);			\
		    }							\
		    if (!new_element->set_property(iname, values, iIsColor)) { \
			PyErr_SetString(geom_error, "Error adding " #type " values to Ply element"); \
			return NULL;					\
		    }
#define HANDLE_ARRAY_NPY_(type, npy_type)				\
		    std::vector<type> values;				\
		    for (Py_ssize_t j = 0; j < PyList_Size(value); j++) { \
			PyObject* vv = PyList_GetItem(value, j);	\
			if (vv == NULL) return NULL;			\
			if (!PyArray_CheckScalar(vv)) {			\
			    PyErr_SetString(geom_error, "Error adding " #type " values array to Ply element. Not all elements are numpy scalars."); \
			    return NULL;				\
			}						\
			PyArray_Descr* desc0 = PyArray_DescrFromScalar(vv); \
			if (!PyArray_CanCastSafely(desc0->type_num, npy_type)) { \
			    PyErr_SetString(geom_error, "Error adding " #type " values array to Ply element from numpy scalars. Not all elements are the same type."); \
			    return NULL;				\
			}						\
			type ivalue;					\
			PyArray_Descr* desc = PyArray_DescrNewFromType(npy_type); \
			PyArray_CastScalarToCtype(vv, &ivalue, desc);	\
			values.push_back(ivalue);			\
			Py_DECREF(desc);				\
		    }							\
		    if (!new_element->set_property(iname, values, iIsColor)) { \
			PyErr_SetString(geom_error, "Error adding " #type " values to Ply element"); \
			return NULL;					\
		    }
#define CASE_ARRAY_NPY_(type, npy_type)					\
		    if (first_desc->type_num == npy_type) {		\
			HANDLE_ARRAY_NPY_(type, npy_type)		\
		    }
#define CASES_ARRAY_NPY_(type, npy_type)				\
		    CASE_ARRAY_NPY_(type ## 8_t, NPY_ ## npy_type ## 8) \
		    else CASE_ARRAY_NPY_(type ## 16_t, NPY_ ## npy_type ## 16) \
		    else CASE_ARRAY_NPY_(type ## 32_t, NPY_ ## npy_type ## 32) \
		    else CASE_ARRAY_NPY_(type ## 64_t, NPY_ ## npy_type ## 64)
		    
		    if (PyLong_Check(value)) {
			HANDLE_SCALAR_(int, static_cast<int>(PyLong_AsLong(value)));
		    } else if (PyFloat_Check(value)) {
			HANDLE_SCALAR_(double, PyFloat_AsDouble(value));
		    } else if (PyArray_CheckScalar(value)) {
			PyArray_Descr* value_desc = PyArray_DescrFromScalar(value);
			CASES_SCALAR_NPY_(int, INT)
			else CASES_SCALAR_NPY_(uint, UINT)
			else CASE_SCALAR_NPY_(float, NPY_FLOAT)
			else CASE_SCALAR_NPY_(double, NPY_DOUBLE)
			else {
			    PyErr_SetString(PyExc_TypeError, "Ply element property value must be integer or float");
			    return NULL;
			}
		    } else if (PyList_Check(value)) {
			PyObject* first_item = PyList_GetItem(value, 0);
			if (first_item == NULL) return NULL;
			if (PyLong_Check(first_item)) {
			    HANDLE_ARRAY_(int, PyLong_Check, static_cast<int>(PyLong_AsLong(vv)));
			} else if (PyFloat_Check(first_item)) {
			    HANDLE_ARRAY_(double, PyFloat_Check, PyFloat_AsDouble(vv));
			} else if (PyArray_CheckScalar(first_item)) {
			    PyArray_Descr* first_desc = PyArray_DescrFromScalar(first_item);
			    CASES_ARRAY_NPY_(int, INT)
			    else CASES_ARRAY_NPY_(uint, UINT)
			    else CASE_ARRAY_NPY_(float, NPY_FLOAT)
			    else CASE_ARRAY_NPY_(double, NPY_DOUBLE)
			    else {
				PyErr_SetString(PyExc_TypeError, "Ply element list values must be integers or floats");
				return NULL;
			    }
			} else {
			    PyErr_SetString(PyExc_TypeError, "Ply element list values must be integers or floats");
			    return NULL;
			}
#undef HANDLE_SCALAR_
#undef HANDLE_SCALAR_NPY_
#undef CASE_SCALAR_NPY_
#undef CASES_SCALAR_NPY_
#undef HANDLE_ARRAY_
#undef HANDLE_ARRAY_NPY_
#undef CASE_ARRAY_NPY_
#undef CASES_ARRAY_NPY_
		    } else {
			PyErr_SetString(PyExc_TypeError, "Ply element values must be integers or floats");
			return NULL;
		    }
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
#define CASE_ARRAY_NPY_(type, npy_type, ig)				\
	case (npy_type): {						\
	    type* xa = (type*)PyArray_BYTES((PyArrayObject*)x2);	\
	    type ignore = ig;						\
	    v->ply->add_element_set(name, xa, xn, xm, &ignore);		\
	    break;							\
	}
#define CASES_ARRAY_NPY_(type, npy_type, ig)	\
	CASE_ARRAY_NPY_(type ## 8_t, NPY_ ## npy_type ## 8, ig)		\
	CASE_ARRAY_NPY_(type ## 16_t, NPY_ ## npy_type ## 16, ig)	\
	CASE_ARRAY_NPY_(type ## 32_t, NPY_ ## npy_type ## 32, ig)	\
	CASE_ARRAY_NPY_(type ## 64_t, NPY_ ## npy_type ## 64, ig)
	
	PyObject* x2 = NULL;
	if (PyArray_IS_C_CONTIGUOUS((PyArrayObject*)x)) {
	    x2 = x;
	    Py_INCREF(x2);
	} else {
	    x2 = (PyObject*)PyArray_GETCONTIGUOUS((PyArrayObject*)x);
	    if (x2 == NULL) return NULL;
	}
	switch (PyArray_TYPE((PyArrayObject*)x2)) {
	CASES_ARRAY_NPY_(int, INT, -1)
	CASES_ARRAY_NPY_(uint, UINT, -1)
	CASE_ARRAY_NPY_(float, NPY_FLOAT, NAN)
	CASE_ARRAY_NPY_(double, NPY_DOUBLE, NAN)
	default: {
	    Py_DECREF(x2);
	    PyErr_SetString(PyExc_TypeError, "Unsupported numpy datatype.");
	    return NULL;
	}
	}
#undef CASES_ARRAY_NPY_
#undef CASE_ARRAY_NPY_
	Py_DECREF(x2);
    } else {
	PyErr_SetString(PyExc_TypeError, "Ply element sets must be lists of element dictionaries or arrays.");
	return NULL;
    }
    
    Py_RETURN_NONE;
    
}


static PyObject* ply_as_trimesh(PyObject* self, PyObject* args, PyObject* kwargs) {
    PyObject* dict_args = PyTuple_New(0);
    if (dict_args == NULL)
	return NULL;
    PyObject* dict_kwargs = PyDict_New();
    if (dict_kwargs == NULL) {
	Py_DECREF(dict_args);
	return NULL;
    }
    if (PyDict_SetItemString(dict_kwargs, "as_array", Py_True) < 0) {
	Py_DECREF(dict_args);
	Py_DECREF(dict_kwargs);
	return NULL;
    }
    PyObject* mesh_dict = ply_as_dict(self, dict_args, dict_kwargs);
    Py_DECREF(dict_args);
    Py_DECREF(dict_kwargs);
    PyObject* out = dict2trimesh(mesh_dict, kwargs);
    Py_DECREF(mesh_dict);
    return out;
}
static PyObject* ply_from_trimesh(PyObject* cls, PyObject* args, PyObject* kwargs) {
    PyObject* solf = NULL;
    if (!PyArg_ParseTuple(args, "O:", &solf))
	return NULL;
    PyObject* geom_kwargs = trimesh2dict(solf);
    if (geom_kwargs == NULL) {
	return NULL;
    }
    PyObject* dict_args = PyTuple_Pack(1, geom_kwargs);
    if (dict_args == NULL) {
	Py_DECREF(geom_kwargs);
	return NULL;
    }
    PyObject* dict_kwargs = PyDict_New();
    if (dict_kwargs == NULL) {
	Py_DECREF(dict_args);
	return NULL;
    }
    if (PyDict_SetItemString(dict_kwargs, "as_array", Py_True) < 0) {
	Py_DECREF(dict_args);
	Py_DECREF(dict_kwargs);
	return NULL;
    }
    PyObject* out = ply_from_dict(cls, dict_args, dict_kwargs);
    Py_DECREF(dict_args);
    Py_DECREF(dict_kwargs);
    return out;
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
    if (v->ply->comments.size() > 0) {
	PyObject* commentStr = PyUnicode_FromString("comment");
	if (commentStr == NULL) {
	    Py_DECREF(out);
	    return NULL;
	}
	PyObject* comment_args = PyTuple_Pack(1, commentStr);
	Py_DECREF(commentStr);
	if (comment_args == NULL) {
	    Py_DECREF(out);
	    return NULL;
	}
	PyObject* comments = ply_get_elements(self, comment_args, NULL);
	Py_DECREF(comment_args);
	if (comments == NULL) {
	    Py_DECREF(out);
	    return NULL;
	}
	if (PyDict_SetItemString(out, "comment", comments) < 0) {
	    Py_DECREF(comments);
	    Py_DECREF(out);
	    return NULL;
	}
	Py_DECREF(comments);
    }
    if (v->ply->element_order.size() == 0)
	return out;
    for (std::vector<std::string>::const_iterator it = v->ply->element_order.begin(); it != v->ply->element_order.end(); it++) {
	std::map<std::string,PlyElementSet>::const_iterator eit = v->ply->elements.find(*it);
	if (eit == v->ply->elements.end()) continue;
	PyObject* iargs = Py_BuildValue("(s)", it->c_str());
	if (iargs == NULL) {
	    Py_DECREF(out);
	    return NULL;
	}
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
	    snprintf(key, 100, "%s_colors", it->c_str());
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

static PyObject* ply_as_array_dict(PyObject* self, PyObject* args, PyObject* kwargs) {
    bool dec_kwargs = false;
    PyObject* out = NULL;
    if (kwargs == NULL) {
	kwargs = PyDict_New();
	dec_kwargs = true;
	if (kwargs == NULL)
	    return NULL;
    }
    if (PyDict_SetItemString(kwargs, "as_array", Py_True) < 0) {
	goto cleanup;
    }
    out = ply_as_dict(self, args, kwargs);
cleanup:
    if (dec_kwargs)
	Py_DECREF(kwargs);
    return out;
}
static PyObject* ply_from_array_dict(PyObject* self, PyObject* args, PyObject* kwargs) {
    bool dec_kwargs = false;
    PyObject* out = NULL;
    if (kwargs == NULL) {
	kwargs = PyDict_New();
	dec_kwargs = true;
	if (kwargs == NULL)
	    return NULL;
    }
    if (PyDict_SetItemString(kwargs, "as_array", Py_True) < 0) {
	goto cleanup;
    }
    out = ply_from_dict(self, args, kwargs);
cleanup:
    if (dec_kwargs)
	Py_DECREF(kwargs);
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


static PyObject* ply_merge(PyObject* self, PyObject* args, PyObject* kwargs) {
    bool no_copy = false;
    if (kwargs != NULL && PyDict_Check(kwargs)) {
	PyObject* no_copy_py = PyDict_GetItemString(kwargs, "no_copy");
	if (no_copy_py != NULL) {
	    no_copy = PyObject_IsTrue(no_copy_py);
	}
    }
    PyObject* out = NULL;
    PyObject* result = NULL;
    PyObject* item_args = NULL;
    if (no_copy) {
	out = self;
	Py_INCREF(out);
    } else {
	PyObject* tmp_args = PyTuple_New(0);
	if (tmp_args == NULL)
	    return NULL;
	PyObject* type = (PyObject*)self->ob_type;
	out = PyObject_Call(type, tmp_args, NULL);
	Py_DECREF(tmp_args);
	if (out == NULL)
	    return NULL;
	item_args = PyTuple_Pack(1, self);
	if (item_args == NULL) {
	    Py_DECREF(out);
	    return NULL;
	}
	result = ply_append(out, item_args, NULL);
	Py_DECREF(item_args);
	if (result == NULL) {
	    Py_DECREF(out);
	    return NULL;
	}
    }
    PyObject* append_list = NULL;
    if (PyTuple_Size(args) == 1) {
	append_list = PyTuple_GetItem(args, 0);
    } else {
	append_list = args;
    }
    if (PyTuple_Check(append_list) || PyList_Check(append_list)) {
	for (Py_ssize_t i = 0; i < PySequence_Size(append_list); i++) {
	    PyObject* item = PySequence_GetItem(append_list, i);
	    if (item == NULL) {
		Py_DECREF(out);
		return NULL;
	    }
	    item_args = PyTuple_Pack(1, item);
	    if (item_args == NULL) {
		Py_DECREF(item);
		Py_DECREF(out);
		return NULL;
	    }
	    result = ply_append(out, item_args, NULL);
	    Py_DECREF(item_args);
	    Py_DECREF(item);
	    if (result == NULL) {
		Py_DECREF(out);
		return NULL;
	    }
	    Py_DECREF(result);
	}
    } else {
	item_args = PyTuple_Pack(1, append_list);
	if (item_args == NULL) {
	    Py_DECREF(out);
	    return NULL;
	}
	result = ply_append(out, item_args, NULL);
	Py_DECREF(item_args);
	if (result == NULL) {
	    Py_DECREF(out);
	    return NULL;
	}
    }
    return out;
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

static PyObject* ply_nvert(PyObject* self, void*) {
    PyObject* args = Py_BuildValue("(s)", "vertices");
    if (args == NULL)
	return NULL;
    return ply_count_elements(self, args, NULL);
}
static PyObject* ply_nface(PyObject* self, void*) {
    PyObject* args = Py_BuildValue("(s)", "faces");
    if (args == NULL)
	return NULL;
    return ply_count_elements(self, args, NULL);
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

static PyObject* ply__getstate__(PyObject* self, PyObject*, PyObject*) {
    PyObject* args = PyTuple_New(0);
    if (args == NULL)
	return NULL;
    PyObject* out = ply_as_dict(self, args, NULL);
    Py_DECREF(args);
    return out;
}
static PyObject* ply__setstate__(PyObject* self, PyObject* state) {
    if (ply_add_elements_from_dict(self, state, true) < 0)
	return NULL;
    Py_INCREF(Py_None);
    return Py_None;
}


//////////////////////////
// ObjWavefront Methods //
//////////////////////////


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

    ObjWavefrontObject* v = (ObjWavefrontObject*) type->tp_alloc(type, 0);
    if (v == NULL)
        return NULL;
    if (vertObject != NULL &&
	PyObject_IsInstance(vertObject, (PyObject*)&ObjWavefront_Type)) {
	v->obj = (ObjWavefront*)(((ObjWavefrontObject*)vertObject)->obj->copy());
	vertObject = NULL;
    } else if (vertObject != NULL &&
	       PyObject_IsInstance(vertObject, (PyObject*)&Ply_Type)) {
	v->obj = new ObjWavefront(*(((PlyObject*)vertObject)->ply));
	vertObject = NULL;
    } else {
	v->obj = new ObjWavefront();
    }
    const char* readFrom = 0;
    if (vertObject != NULL && PyUnicode_Check(vertObject)) {
	readFrom = PyUnicode_AsUTF8(vertObject);
	vertObject = NULL;
    } else if (vertObject != NULL && PyBytes_Check(vertObject)) {
	readFrom = PyBytes_AsString(vertObject);
	vertObject = NULL;
    }
    if (readFrom) {
	std::stringstream ss;
	ss.str(std::string(readFrom));
	if (!v->obj->read(ss)) {
	    PyErr_SetString(geom_error, "Error reading from string");
	    return NULL;
	}
    }
    PyObject* inDict = PyDict_New();
    if (inDict == NULL)
	return NULL;
    if (vertObject != NULL && PyDict_Check(vertObject)) {
	if (PyDict_Update(inDict, vertObject) < 0)
	    return NULL;
	vertObject = NULL;
    }
    
#define ADD_ARRAY(x, name)						\
    if (x != NULL) {							\
	if (PyDict_SetItemString(inDict, #name, x) < 0)			\
	    return NULL;						\
    }

    ADD_ARRAY(vertObject, vertex);
    ADD_ARRAY(faceObject, face);
    ADD_ARRAY(edgeObject, edge);

#undef ADD_ARRAY

    if (kwargs != NULL) {
	if (PyDict_Update(inDict, kwargs) < 0)
	    return NULL;
    }

    if (objwavefront_add_elements_from_dict((PyObject*)v, inDict) < 0)
	return NULL;

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

static int objwavefront_add_elements_from_dict(PyObject *self, PyObject* kwargs, bool preserveOrder) {
    if (kwargs) {
	PyObject *key, *value;
	Py_ssize_t pos = 0;
	std::vector<std::string> skip, delayed;

	// Do comments & vertices first
	if (!preserveOrder) {
	    std::vector<std::string> skip_names = {"comment", "comments", "vertex", "vertices", "vertexes"};
	    for (std::vector<std::string>::iterator it = skip_names.begin();
		 it != skip_names.end(); it++) {
		value = PyDict_GetItemString(kwargs, it->c_str());
		if (value == NULL) continue;
		PyObject* iargs = Py_BuildValue("(sO)", it->c_str(), value);
		if (objwavefront_add_elements(self, iargs, NULL) == NULL) {
		    Py_DECREF(iargs);
		    return -1;
		}
		Py_DECREF(iargs);
		skip.push_back(*it);
	    }
	}
	while (PyDict_Next(kwargs, &pos, &key, &value)) {
	    std::string keyS(PyUnicode_AsUTF8(key));
	    bool skipped = false;
	    for (std::vector<std::string>::iterator it = skip.begin();
		 it != skip.end(); it++) {
		if (keyS == *it) {
		    skipped = true;
		    break;
		}
	    }
	    if (skipped) continue;
	    if (keyS.size() > 7 &&
		keyS.substr(keyS.size() - 7) == "_colors") {
		delayed.push_back(keyS);
		continue;
	    }
	    PyObject* iargs = Py_BuildValue("(OO)", key, value);
	    if (objwavefront_add_elements(self, iargs, NULL) == NULL) {
		Py_DECREF(iargs);
		return -1;
	    }
	    Py_DECREF(iargs);
	}
	for (std::vector<std::string>::iterator it = delayed.begin();
	     it != delayed.end(); it++) {
	    value = PyDict_GetItemString(kwargs, it->c_str());
	    PyObject* iargs = Py_BuildValue("(sO)", it->c_str(), value);
	    if (objwavefront_add_elements(self, iargs, NULL) == NULL) {
		Py_DECREF(iargs);
		return -1;
	    }
	    Py_DECREF(iargs);
	}
    }
    return 0;
}
static int objwavefront_add_elements_from_list(PyObject *self, PyObject* inList) {
    if (!PyList_Check(inList)) {
	PyErr_SetString(PyExc_TypeError, "Argument must be a list.");
	return -1;
    }
    for (Py_ssize_t i = 0; i < PyList_Size(inList); i++) {
	PyObject* item = PyList_GetItem(inList, i);
	if (item == NULL) return -1;
	if (objwavefront_add_element_from_python(self, item, "") < 0)
	    return -1;
    }
    return 0;
}
static int objwavefront_add_element_from_python(PyObject* self, PyObject* x, std::string name) {
    if (x == NULL)
	return -1;
    ObjWavefrontObject* v = (ObjWavefrontObject*) self;
    bool is_dict = PyDict_Check(x);
    if (!(PyDict_Check(x) || PyList_Check(x) || PyUnicode_Check(x))) {
	PyErr_SetString(PyExc_TypeError, "Dictionary or list required.");
	return -1;
    }
    PyObject* code = NULL;
    if (is_dict) {
	code = PyDict_GetItemString(x, "code");
	if (name.size() == 0) {
	    if (code == NULL) {
		PyErr_SetString(geom_error, "No code string present.");
		return -1;
	    }
	    if (!PyUnicode_Check(code)) {
		PyErr_SetString(geom_error, "No code string present.");
		return -1;
	    }
	    name = PyUnicode_AsUTF8(code);
	}
    }
    ObjElement* new_element = v->obj->add_element(name);
    if (!new_element) {
	PyErr_SetString(geom_error, "Error adding element to ObjWavefront instance");
	return -1;
    }
    if (PyUnicode_Check(x)) {
	if (obj_alias2base(name) == "#") {
	    PyObject* comments = PyUnicode_Split(x, NULL, -1);
	    if (comments == NULL)
		return -1;
	    std::vector<std::string> commentsS;
	    for (Py_ssize_t i = 0; i < PyList_Size(comments); i++) {
		PyObject* iComment = PyList_GetItem(comments, i);
		if (iComment == NULL) {
		    Py_DECREF(comments);
		    return -1;
		}
		commentsS.push_back(PyUnicode_AsUTF8(iComment));
	    }
	    Py_DECREF(comments);
	    if (!new_element->set_property(static_cast<size_t>(0), commentsS)) {
		PyErr_SetString(geom_error, "Error setting ObjWavefront element property.");
		return -1;
	    }
	} else {
	    std::string iComment(PyUnicode_AsUTF8(x));
	    if (!new_element->set_property(static_cast<size_t>(0), iComment)) {
		PyErr_SetString(geom_error, "Error setting ObjWavefront element property.");
		return -1;
	    }
	}
	return 0;
    }
    PyObject *key, *value, *src;
    Py_ssize_t pos = 0, src_idx = 0;
    std::string iname = "";
    std::string src_key;
    bool src_is_dict;
    Py_ssize_t Nprops = 0;
    if (is_dict) {
	Nprops = PyDict_Size(x);
    } else {
	Nprops = PyList_Size(x);
    }
    Py_ssize_t Nprops_meta = Nprops;
    if (code != NULL) Nprops_meta--;
    if (!new_element->set_meta_properties(Nprops_meta)) {
	PyErr_SetString(geom_error, "Error setting metadata for ObjWavefront element.");
	return -1;
    }
    if (!is_dict) {
	int min_size = new_element->min_values();
	int max_size = new_element->max_values();
	if ((min_size >= 0 && Nprops_meta < (Py_ssize_t)min_size) ||
	    (max_size >= 0 && Nprops_meta > (Py_ssize_t)max_size)) {
	    PyErr_SetString(geom_error, "Error adding element to ObjWavefront instance. Incorrect number of property values.");
	    return -1;
	}
    }
    for (Py_ssize_t j = 0; j < Nprops; j++) {
	if (is_dict) {
	    if (!PyDict_Next(x, &pos, &key, &value)) {
		PyErr_SetString(geom_error, "Error processing element dictionary");
		return -1;
	    }
	    if (!PyUnicode_Check(key)) {
		PyErr_SetString(PyExc_TypeError, "ObjWavefront element keys must be strings");
		return -1;
	    }
	    iname = std::string(PyUnicode_AsUTF8(key));
	    if (iname == "code") continue;
	} else {
	    key = NULL;
	    value = PyList_GetItem(x, j);
	    if (value == NULL)
		return -1;
	    iname = "";
	}
#define HANDLE_SET_(type, ELEMENT)					\
	bool iresult = false;						\
	if (src_is_dict) {						\
	    iresult = ELEMENT->set_property(src_key, ivalue, true);	\
	} else {							\
	    iresult = ELEMENT->set_property(src_idx, ivalue, true);	\
	}								\
	if (!iresult) {							\
	    PyErr_SetString(geom_error, "Error adding " type " value to ObjWavefront element"); \
	    return -1;							\
	}
#define HANDLE_SCALAR_(type, method, ELEMENT)				\
	type ivalue = method;						\
	HANDLE_SET_(#type " scalar", ELEMENT)
#define HANDLE_SCALAR_NPY_(type, npy_type, ELEMENT)			\
	type ivalue;							\
	PyArray_Descr* desc = PyArray_DescrNewFromType(npy_type);	\
	PyArray_CastScalarToCtype(src, &ivalue, desc);			\
	Py_DECREF(desc);						\
	HANDLE_SET_(#type " numpy scalar", ELEMENT)
#define HANDLE_ARRAY_(type, check, method, ELEMENT)			\
	std::vector<type> ivalue;					\
	for (Py_ssize_t k = 0; k < PyList_Size(src); k++) {		\
	    PyObject* vv = PyList_GetItem(src, k);			\
	    if (vv == NULL) return -1;					\
	    if (!check(vv)) {						\
		PyErr_SetString(geom_error, "Error adding " #type " values array to ObjWavefront element. Not all elements are the same type."); \
		return -1;						\
	    }								\
	    ivalue.push_back(method);					\
	}								\
	HANDLE_SET_(#type " vector", ELEMENT)
#define HANDLE_ARRAY_NPY_(type, check, npy_type, ELEMENT)		\
	std::vector<type> ivalue;					\
	for (Py_ssize_t k = 0; k < PyList_Size(src); k++) {		\
	    PyObject* vv = PyList_GetItem(src, k);			\
	    if (vv == NULL) return -1;					\
	    if (!PyArray_CheckScalar(vv)) {				\
		PyErr_SetString(geom_error, "Error adding " #type " values array to ObjWavefront element. Not all elements are numpy scalars."); \
		return -1;						\
	    }								\
	    PyArray_Descr* desc0 = PyArray_DescrFromScalar(vv);		\
	    if (!check(desc0)) {					\
		PyErr_SetString(geom_error, "Error adding " #type " values array to ObjWavefront element from numpy scalars. Not all elements are the same type."); \
		return -1;						\
	    }								\
	    type ivv;							\
	    PyArray_Descr* desc = PyArray_DescrNewFromType(npy_type);	\
	    PyArray_CastScalarToCtype(vv, &ivv, desc);			\
	    ivalue.push_back(ivv);					\
	    Py_DECREF(desc);						\
	}								\
	HANDLE_SET_(#type " numpy array", ELEMENT)
#define HANDLE_SCALAR_ITEM_(ELEMENT)					\
	if (PyLong_Check(src)) {					\
	    HANDLE_SCALAR_(int, static_cast<int>(PyLong_AsLong(src)), ELEMENT);	\
	} else if (PyFloat_Check(src)) {				\
	    HANDLE_SCALAR_(double, PyFloat_AsDouble(src), ELEMENT);	\
	} else if (PyUnicode_Check(src)) {				\
	    HANDLE_SCALAR_(std::string, std::string(PyUnicode_AsUTF8(src)), ELEMENT); \
	} else if (PyArray_CheckScalar(src)) {				\
	    PyArray_Descr* desc0 = PyArray_DescrFromScalar(src);	\
	    if (PyDataType_ISINTEGER(desc0)) {				\
		HANDLE_SCALAR_NPY_(int, NPY_INT32, ELEMENT);		\
	    } else if (PyDataType_ISFLOAT(desc0)) {			\
		HANDLE_SCALAR_NPY_(double, NPY_FLOAT64, ELEMENT);	\
	    } else if (PyDataType_ISSTRING(desc0)) {			\
		HANDLE_SCALAR_NPY_(std::string, NPY_UNICODE, ELEMENT);	\
	    } else {							\
		PyErr_SetString(PyExc_TypeError, "ObjWavefront element property value must be integer, float, or string"); \
		return -1;						\
	    }								\
	}
#define HANDLE_ARRAY_ITEM_(ELEMENT)					\
        if (PyList_Check(src)) {					\
	    PyObject* first_item = PyList_GetItem(src, 0);		\
	    if (first_item == NULL) return -1;				\
	    if (PyLong_Check(first_item)) {				\
		HANDLE_ARRAY_(int, PyLong_Check, static_cast<int>(PyLong_AsLong(vv)), ELEMENT); \
	    } else if (PyFloat_Check(first_item)) {			\
		HANDLE_ARRAY_(double, PyFloat_Check, PyFloat_AsDouble(vv), ELEMENT); \
	    } else if (PyUnicode_Check(first_item)) {			\
		HANDLE_ARRAY_(std::string, PyUnicode_Check, std::string(PyUnicode_AsUTF8(vv)), ELEMENT); \
	    } else if (PyArray_CheckScalar(first_item)) {		\
		PyArray_Descr* first_desc = PyArray_DescrFromScalar(first_item); \
		if (PyDataType_ISINTEGER(first_desc)) {			\
		    HANDLE_ARRAY_NPY_(int, PyDataType_ISINTEGER, NPY_INT32, ELEMENT); \
		} else if (PyDataType_ISFLOAT(first_desc)) {		\
		    HANDLE_ARRAY_NPY_(double, PyDataType_ISFLOAT, NPY_FLOAT64, ELEMENT); \
		} else if (PyDataType_ISSTRING(first_desc)) {		\
		    HANDLE_ARRAY_NPY_(std::string, PyDataType_ISSTRING, NPY_UNICODE, ELEMENT); \
		} else {						\
		    PyErr_SetString(PyExc_TypeError, "ObjWavefront element list values must be integers, floats, or strings"); \
		    return -1;						\
		}							\
	    } else {							\
	        PyErr_SetString(PyExc_TypeError, "ObjWavefront element list values must be integers, floats, or strings"); \
		return -1;						\
            }								\
        }

	src = value;
	src_is_dict = is_dict;
	src_key = iname;
	src_idx = j;
	HANDLE_SCALAR_ITEM_(new_element)
	else HANDLE_ARRAY_ITEM_(new_element)
	else if (!is_dict && PyDict_Check(value)) {
	    if (!new_element->add_subelement()) {
		PyErr_SetString(geom_error, "Error adding subelement to ObjWavefront element.");
		return -1;
	    }
	    bool temp = false;
	    ObjPropertyElement* last_sub = new_element->last_subelement(&temp);
	    if (!last_sub) {
		PyErr_SetString(geom_error, "Error retrieving last subelement from ObjWavefront element.");
		return -1;
	    }
	    PyObject *value_key, *value_val;
	    Py_ssize_t value_pos = 0;
	    std::string value_keyS;
	    while (PyDict_Next(value, &value_pos, &value_key, &value_val)) {
		if (!PyUnicode_Check(value_key)) {
		    PyErr_SetString(PyExc_TypeError, "ObjWavefront subelement keys must be strings");
		    return -1;
		}
		value_keyS = std::string(PyUnicode_AsUTF8(value_key));
		src = value_val;
		src_is_dict = true;
		src_key = value_keyS;
		src_idx = 0;
		HANDLE_SCALAR_ITEM_(last_sub)
		else HANDLE_ARRAY_ITEM_(last_sub)
		else {
		    PyErr_SetString(PyExc_TypeError, "ObjWavefront subelement properties must be integers, floats, strings, or lists/arrays of those types.");
		    return -1;
		}
	    }
#undef HANDLE_SET_
#undef HANDLE_SCALAR_
#undef HANDLE_SCALAR_NPY_
#undef HANDLE_ARRAY_
#undef HANDLE_ARRAY_NPY_
#undef HANDLE_SCALAR_ITEM_
#undef HANDLE_ARRAY_ITEM_
	} else {
	    PyErr_SetString(PyExc_TypeError, "ObjWavefront element property values must be integers, floats, strings, or lists of those types.");
	    return -1;
	}
    }
    std::map<std::string,size_t> counts = v->obj->element_counts();
    if (!new_element->is_valid_idx(counts)) {
	PyErr_SetString(geom_error, "New ObjWavefront element is invalid");
	return -1;
    }
    return 0;
}
static PyObject* objwavefront_element2dict(const ObjElement* x, bool includeCode) {
    PyObject* out = PyDict_New();
    if (out == NULL)
	return NULL;
    if (includeCode) {
	PyObject* code = PyUnicode_FromString(x->code.c_str());
	if (code == NULL) {
	    Py_DECREF(out);
	    return NULL;
	}
	if (PyDict_SetItemString(out, "code", code) < 0) {
	    Py_DECREF(code);
	    Py_DECREF(out);
	    return NULL;
	}
	Py_DECREF(code);
    }
    for (ObjPropertiesMap::const_iterator p = x->properties.begin();
	 p != x->properties.end(); p++) {
	PyObject* ival = NULL;
	if (!x->has_property(p->first, true)) continue;
	if (p->is_vector()) {
	    ival = PyList_New(x->size());
	    if (ival == NULL) {
		Py_DECREF(out);
		return NULL;
	    }
#define GET_ARRAY_(type, method)					\
	    std::vector<type> values;					\
	    if (!p->get(values, true)) {				\
		Py_DECREF(ival);					\
		Py_DECREF(out);						\
		return NULL;						\
	    }								\
	    for (size_t iProp = 0; iProp < values.size(); iProp++) {	\
		PyObject* iival = method;				\
		if (iival == NULL) {					\
		    Py_DECREF(ival);					\
		    Py_DECREF(out);					\
		    return NULL;					\
		}							\
		if (PyList_SetItem(ival, iProp, iival) < 0) {		\
		    Py_DECREF(iival);					\
		    Py_DECREF(ival);					\
		    Py_DECREF(out);					\
		    return NULL;					\
		}							\
	    }

	    if (_type_compatible_double(p->second)) {
		GET_ARRAY_(double, PyFloat_FromDouble(values[iProp]));
	    } else if (_type_compatible_int(p->second)) {
		GET_ARRAY_(int, PyLong_FromLong(values[iProp]));
	    } else if (_type_compatible_string(p->second)) {
		GET_ARRAY_(std::string, PyUnicode_FromString(values[iProp].c_str()));
	    } else {
		Py_DECREF(out);
		PyErr_SetString(PyExc_TypeError, "Could not find a Python type to match the C++ type");
		return NULL;
	    }

#undef GET_ARRAY_
#define GET_SCALAR_(type, method)					\
	    type value;							\
	    if (!p->get(value, true)) {					\
		Py_DECREF(out);						\
		return NULL;						\
	    }								\
	    ival = method
	} else if (_type_compatible_double(p->second)) {
	    GET_SCALAR_(double, PyFloat_FromDouble(value));
	} else if (_type_compatible_int(p->second)) {
	    GET_SCALAR_(int, PyLong_FromLong(value));
	} else if (_type_compatible_string(p->second)) {
	    GET_SCALAR_(std::string, PyUnicode_FromString(value.c_str()));
	} else {
	    Py_DECREF(out);
	    PyErr_SetString(PyExc_TypeError, "Could not find a Python type to match the C++ type");
	    return NULL;
	}
#undef GET_SCALAR_
	if (ival == NULL) {
	    Py_DECREF(out);
	    return NULL;
	}
	if (x->code == "#" && !includeCode) {
	    PyObject* sep = PyUnicode_FromString(" ");
	    if (sep == NULL) {
		Py_DECREF(ival);
		Py_DECREF(out);
		return NULL;
	    }
	    PyObject* joined = PyUnicode_Join(sep, ival);
	    Py_DECREF(sep);
	    Py_DECREF(ival);
	    if (joined == NULL) {
		Py_DECREF(out);
		return NULL;
	    }
	    Py_DECREF(out);
	    out = joined;
	} else {
	    if (PyDict_SetItemString(out, p->first.c_str(), ival) < 0) {
		Py_DECREF(ival);
		Py_DECREF(out);
		return NULL;
	    }
	    Py_DECREF(ival);
	}
    }
    return out;
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
    PyObject* defaultRet = NULL;
    
    static char const* kwlist[] = {
	"name",
	"default",
	"as_array",
        NULL
    };
    
    
    if (!PyArg_ParseTupleAndKeywords(args, kwargs, "s|Op:", (char**) kwlist,
				     &elementType0, &defaultRet, &asArray))
	return NULL;

    std::string elementType = obj_alias2base(std::string(elementType0));

    ObjWavefrontObject* v = (ObjWavefrontObject*) self;

    if (v->obj->count_elements(elementType) == 0) {
	if (defaultRet == NULL) {
	    PyErr_SetString(PyExc_KeyError, elementType0);
	    return NULL;
	} else {
	    Py_INCREF(defaultRet);
	    return defaultRet;
	}
    }
    
    PyObject* out = NULL;
    
    if (asArray) {
	
#define GET_ARRAY(T, npT)						\
	size_t N = 0, M = 0;						\
	std::vector<T> vect = v->obj->get_ ## T ## _array(elementType, N, M, true, true); \
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
	out = PyList_New(v->obj->count_elements(elementType));
	if (out == NULL) {
	    return NULL;
	}
	Py_ssize_t i = 0;
	for (std::vector<ObjElement*>::const_iterator elit = v->obj->elements.begin(); elit != v->obj->elements.end(); elit++) {
	    if ((*elit)->code != elementType) continue;
	    PyObject* item = objwavefront_element2dict(*elit);
	    if (item == NULL) {
		Py_DECREF(out);
		return NULL;
	    }
	    if (PyList_SetItem(out, i, item) < 0) {
		Py_DECREF(item);
		Py_DECREF(out);
		return NULL;
	    }
	    i++;
	}
    }
    
    return out;
    
}

static PyObject* objwavefront_add_elements(PyObject* self, PyObject* args, PyObject* kwargs) {
    // TODO: Get double & int values to ignore, maybe flag for skipping inc
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
	    if (objwavefront_add_element_from_python(self, item, name) < 0)
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
	    v->obj->add_element_set(name, xa, xn, xm, &ignore, true);
	} else {
	    int* xa = (int*)PyArray_BYTES((PyArrayObject*)x2);
	    int ignore = -1;
	    v->obj->add_element_set(name, xa, xn, xm, &ignore, true);
	}
	Py_DECREF(x2);
    } else {
	PyErr_SetString(PyExc_TypeError, "ObjWavefront element sets must be lists of element dictionaries or arrays.");
	return NULL;
    }
    
    Py_RETURN_NONE;
    
}



static PyObject* objwavefront_as_trimesh(PyObject* self, PyObject* args, PyObject* kwargs) {
    PyObject* dict_args = PyTuple_New(0);
    if (dict_args == NULL)
	return NULL;
    PyObject* dict_kwargs = PyDict_New();
    if (dict_kwargs == NULL) {
	Py_DECREF(dict_args);
	return NULL;
    }
    if (PyDict_SetItemString(dict_kwargs, "as_array", Py_True) < 0) {
	Py_DECREF(dict_args);
	Py_DECREF(dict_kwargs);
	return NULL;
    }
    PyObject* mesh_dict = objwavefront_as_dict(self, dict_args, dict_kwargs);
    Py_DECREF(dict_args);
    Py_DECREF(dict_kwargs);
    PyObject* out = dict2trimesh(mesh_dict, kwargs, true);
    Py_DECREF(mesh_dict);
    return out;
}
static PyObject* objwavefront_from_trimesh(PyObject* cls, PyObject* args, PyObject* kwargs) {
    PyObject* solf = NULL;
    if (!PyArg_ParseTuple(args, "O:", &solf))
	return NULL;
    PyObject* geom_kwargs = trimesh2dict(solf);
    if (geom_kwargs == NULL) {
	return NULL;
    }
    PyObject* dict_args = PyTuple_Pack(1, geom_kwargs);
    if (dict_args == NULL) {
	Py_DECREF(geom_kwargs);
	return NULL;
    }
    PyObject* dict_kwargs = PyDict_New();
    if (dict_kwargs == NULL) {
	Py_DECREF(dict_args);
	return NULL;
    }
    if (PyDict_SetItemString(dict_kwargs, "as_array", Py_True) < 0) {
	Py_DECREF(dict_args);
	Py_DECREF(dict_kwargs);
	return NULL;
    }
    PyObject* out = objwavefront_from_dict(cls, dict_args, dict_kwargs);
    Py_DECREF(dict_args);
    Py_DECREF(dict_kwargs);
    return out;
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
	    snprintf(key, 100, "%s_colors", longName.c_str());
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

static PyObject* objwavefront_as_array_dict(PyObject* self, PyObject* args, PyObject* kwargs) {
    bool dec_kwargs = false;
    PyObject* out = NULL;
    if (kwargs == NULL) {
	kwargs = PyDict_New();
	dec_kwargs = true;
	if (kwargs == NULL)
	    return NULL;
    }
    if (PyDict_SetItemString(kwargs, "as_array", Py_True) < 0) {
	goto cleanup;
    }
    out = objwavefront_as_dict(self, args, kwargs);
cleanup:
    if (dec_kwargs)
	Py_DECREF(kwargs);
    return out;
}
static PyObject* objwavefront_from_array_dict(PyObject* self, PyObject* args, PyObject* kwargs) {
    bool dec_kwargs = false;
    PyObject* out = NULL;
    if (kwargs == NULL) {
	kwargs = PyDict_New();
	dec_kwargs = true;
	if (kwargs == NULL)
	    return NULL;
    }
    if (PyDict_SetItemString(kwargs, "as_array", Py_True) < 0) {
	goto cleanup;
    }
    out = objwavefront_from_dict(self, args, kwargs);
cleanup:
    if (dec_kwargs)
	Py_DECREF(kwargs);
    return out;
}

static PyObject* objwavefront_as_list(PyObject* self, PyObject*, PyObject*) {
    ObjWavefrontObject* v = (ObjWavefrontObject*) self;
    PyObject* out = PyList_New(v->obj->elements.size());
    if (out == NULL)
	return NULL;
    Py_ssize_t i = 0;
    for (std::vector<ObjElement*>::const_iterator it = v->obj->elements.begin();
	 it != v->obj->elements.end(); it++, i++) {
	PyObject* element = objwavefront_element2dict(*it, true);
	if (element == NULL) {
	    Py_DECREF(out);
	    return NULL;
	}
	if (PyList_SetItem(out, i, element) < 0) {
	    Py_DECREF(out);
	    return NULL;
	}
    }
    return out;
}

static PyObject* objwavefront_from_list(PyObject* self, PyObject* args, PyObject* kwargs) {
    PyObject* inList = NULL;
    
    if (!PyArg_ParseTuple(args, "O:", &inList))
	return NULL;

    PyObject* emptyArgs = PyTuple_New(0);
    PyObject* out = objwavefront_new(&ObjWavefront_Type, emptyArgs, NULL);
    Py_DECREF(emptyArgs);
    if (out == NULL)
	return NULL;

    if (objwavefront_add_elements_from_list(out, inList) < 0)
	return NULL;
    
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


static PyObject* objwavefront_merge(PyObject* self, PyObject* args, PyObject* kwargs) {
    bool no_copy = false;
    if (kwargs != NULL && PyDict_Check(kwargs)) {
	PyObject* no_copy_py = PyDict_GetItemString(kwargs, "no_copy");
	if (no_copy_py != NULL) {
	    no_copy = PyObject_IsTrue(no_copy_py);
	}
    }
    PyObject* out = NULL;
    PyObject* result = NULL;
    PyObject* item_args = NULL;
    if (no_copy) {
	out = self;
	Py_INCREF(out);
    } else {
	PyObject* tmp_args = PyTuple_New(0);
	if (tmp_args == NULL)
	    return NULL;
	PyObject* type = (PyObject*)self->ob_type;
	out = PyObject_Call(type, tmp_args, NULL);
	Py_DECREF(tmp_args);
	if (out == NULL)
	    return NULL;
	item_args = PyTuple_Pack(1, self);
	if (item_args == NULL) {
	    Py_DECREF(out);
	    return NULL;
	}
	result = objwavefront_append(out, item_args, NULL);
	Py_DECREF(item_args);
	if (result == NULL) {
	    Py_DECREF(out);
	    return NULL;
	}
    }
    PyObject* append_list = NULL;
    if (PyTuple_Size(args) == 1) {
	append_list = PyTuple_GetItem(args, 0);
    } else {
	append_list = args;
    }
    if (PyTuple_Check(append_list) || PyList_Check(append_list)) {
	for (Py_ssize_t i = 0; i < PySequence_Size(append_list); i++) {
	    PyObject* item = PySequence_GetItem(append_list, i);
	    if (item == NULL) {
		Py_DECREF(out);
		return NULL;
	    }
	    item_args = PyTuple_Pack(1, item);
	    if (item_args == NULL) {
		Py_DECREF(item);
		Py_DECREF(out);
		return NULL;
	    }
	    result = objwavefront_append(out, item_args, NULL);
	    Py_DECREF(item_args);
	    Py_DECREF(item);
	    if (result == NULL) {
		Py_DECREF(out);
		return NULL;
	    }
	    Py_DECREF(result);
	}
    } else {
	item_args = PyTuple_Pack(1, append_list);
	if (item_args == NULL) {
	    Py_DECREF(out);
	    return NULL;
	}
	result = objwavefront_append(out, item_args, NULL);
	Py_DECREF(item_args);
	if (result == NULL) {
	    Py_DECREF(out);
	    return NULL;
	}
    }
    return out;
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

static PyObject* objwavefront_nvert(PyObject* self, void*) {
    PyObject* args = Py_BuildValue("(s)", "vertices");
    if (args == NULL)
	return NULL;
    return objwavefront_count_elements(self, args, NULL);
}
static PyObject* objwavefront_nface(PyObject* self, void*) {
    PyObject* args = Py_BuildValue("(s)", "faces");
    if (args == NULL)
	return NULL;
    return objwavefront_count_elements(self, args, NULL);
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

static PyObject* objwavefront__getstate__(PyObject* self, PyObject*, PyObject*) {
    PyObject* args = PyTuple_New(0);
    if (args == NULL)
	return NULL;
    return objwavefront_as_list(self, args, NULL);
}
static PyObject* objwavefront__setstate__(PyObject* self, PyObject* state) {
    if (objwavefront_add_elements_from_list(self, state) < 0)
	return NULL;
    Py_INCREF(Py_None);
    return Py_None;
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

    geom_error = PyErr_NewException("yggdrasil.rapidjson.geometry.GeometryError",
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
    "yggdrasil.rapidjson.geometry",       /* m_name */
    PyDoc_STR("Structures for handling 3D geometries."),
    0,                          /* m_size */
    geom_functions,             /* m_methods */
    geom_slots,                 /* m_slots */
    NULL,                       /* m_traverse */
    NULL,                       /* m_clear */
    NULL                        /* m_free */
};


PyMODINIT_FUNC
PyInit_geom()
{
    return PyModuleDef_Init(&geom_module);
}
