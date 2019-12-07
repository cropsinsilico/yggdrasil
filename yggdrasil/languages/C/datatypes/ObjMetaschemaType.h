#ifndef OBJ_METASCHEMA_TYPE_H_
#define OBJ_METASCHEMA_TYPE_H_

#include "../tools.h"
#include "MetaschemaType.h"
#include "ObjDict.h"

#include "rapidjson/document.h"
#include "rapidjson/writer.h"


/*!
  @brief Class for OBJ type definition.

  The ObjMetaschemaType provides basic functionality for encoding/decoding
  Obj structures from/to JSON style strings.
 */
class ObjMetaschemaType : public MetaschemaType {
public:
  /*!
    @brief Constructor for ObjMetaschemaType.
    @param[in] use_generic bool If true, serialized/deserialized
    objects will be expected to be YggGeneric classes.
   */
  ObjMetaschemaType(const bool use_generic=false) : MetaschemaType("obj", use_generic) {}
  /*!
    @brief Constructor for ObjMetaschemaType from a JSON type defintion.
    @param[in] type_doc rapidjson::Value rapidjson object containing the type
    definition from a JSON encoded header.
    @param[in] use_generic bool If true, serialized/deserialized
    objects will be expected to be YggGeneric classes.
   */
  ObjMetaschemaType(const rapidjson::Value &type_doc,
		    const bool use_generic=false) : MetaschemaType(type_doc, use_generic) {}
  /*!
    @brief Constructor for ObjMetaschemaType from Python dictionary.
    @param[in] pyobj PyObject* Python object.
    @param[in] use_generic bool If true, serialized/deserialized
    objects will be expected to be YggGeneric classes.
   */
  ObjMetaschemaType(PyObject* pyobj,
		    const bool use_generic=false) : MetaschemaType(pyobj, use_generic) {}
  /*!
    @brief Copy constructor.
    @param[in] other ObjMetaschemaType* Instance to copy.
   */
  ObjMetaschemaType(const ObjMetaschemaType &other) :
    ObjMetaschemaType(other.use_generic()) {}
  /*!
    @brief Create a copy of the type.
    @returns pointer to new ObjMetaschemaType instance with the same data.
   */
  ObjMetaschemaType* copy() const override { return (new ObjMetaschemaType(use_generic())); }
  /*!
    @brief Copy data wrapped in YggGeneric class.
    @param[in] data YggGeneric* Pointer to generic object.
    @returns void* Pointer to copy of data.
   */
  void* copy_generic(const YggGeneric* data, void* orig_data=NULL) const override {
    if (data == NULL) {
      ygglog_throw_error("ObjMetaschemaType::copy_generic: Generic object is NULL.");
    }
    void* out = NULL;
    if (orig_data == NULL) {
      orig_data = data->get_data();
    }
    if (orig_data != NULL) {
      obj_t* old_data = (obj_t*)orig_data;
      obj_t* new_data = (obj_t*)malloc(sizeof(obj_t));
      if (new_data == NULL) {
	ygglog_throw_error("ObjMetaschemaType::copy_generic: Failed to malloc memory for obj struct.");
      }
      new_data[0] = copy_obj(*old_data);
      if (new_data->vertices == NULL) {
	ygglog_throw_error("ObjMetaschemaType::copy_generic: Failed to copy obj struct.");
      }
      out = (void*)new_data;
    }
    return out;
  }
  /*!
    @brief Free data wrapped in YggGeneric class.
    @param[in] data YggGeneric* Pointer to generic object.
   */
  void free_generic(YggGeneric* data) const override {
    if (data == NULL) {
      ygglog_throw_error("ObjMetaschemaType::free_generic: Generic object is NULL.");
    }
    obj_t** ptr = (obj_t**)(data->get_data_pointer());
    if (ptr[0] != NULL) {
      free_obj(ptr[0]);
      free(ptr[0]);
      ptr[0] = NULL;
    }
  }
  /*!
    @brief Display data.
    @param[in] data YggGeneric* Pointer to generic object.
    @param[in] indent char* Indentation to add to display output.
   */
  void display_generic(const YggGeneric* data, const char* indent="") const override {
    if (data == NULL) {
      ygglog_throw_error("ObjMetaschemaType::display_generic: Generic object is NULL.");
    }
    obj_t arg;
    data->get_data(arg);
    display_obj_indent(arg, indent);
  }
  /*!
    @brief Update the type object with info from provided variable arguments for serialization.
    @param[in,out] nargs size_t Number of arguments contained in ap. On output
    the number of unused arguments will be assigned to this address.
    @param[in] ap va_list_t Variable argument list.
    @returns size_t Number of arguments in ap consumed.
   */
  size_t update_from_serialization_args(size_t *nargs, va_list_t &ap) override {
    size_t out = MetaschemaType::update_from_serialization_args(nargs, ap);
    if (use_generic())
      return out;
    va_arg(ap.va, obj_t);
    out++;
    return out;
  }
  /*!
    @brief Get the item size.
    @returns size_t Size of item in bytes.
   */
  const size_t nbytes() const override {
    return sizeof(obj_t);
  }
  /*!
    @brief Get the number of arguments expected to be filled/used by the type.
    @returns size_t Number of arguments.
   */
  virtual size_t nargs_exp() const override {
    return 1;
  }
  /*!
    @brief Convert a Python representation to a C representation.
    @param[in] pyobj PyObject* Pointer to Python object.
    @returns YggGeneric* Pointer to C object.
   */
  YggGeneric* python2c(PyObject *pyobj) const override {
    if (!(PyDict_Check(pyobj))) {
      ygglog_throw_error("ObjMetaschemaType::python2c: Python object must be a dict.");
    }
    obj_t *arg = (obj_t*)malloc(sizeof(obj_t));
    if (arg == NULL) {
      ygglog_throw_error("ObjMetaschemaType::python2c: Failed to malloc for obj structure.");
    }
    arg[0] = init_obj();
    char error_prefix[200] = "";
    // Allocate
    int nvert = 0, ntexc = 0, nnorm = 0, nparam = 0, npoint = 0,
      nline = 0, nface = 0, ncurve = 0, ncurve2 = 0, nsurf = 0;
    PyObject *verts = get_item_python_dict(pyobj, "vertices",
					   error_prefix, T_ARRAY,
					   true);
    PyObject *texcs = get_item_python_dict(pyobj, "texcoords",
					   error_prefix, T_ARRAY,
					   true);
    PyObject *norms = get_item_python_dict(pyobj, "normals",
					   error_prefix, T_ARRAY,
					   true);
    PyObject *param = get_item_python_dict(pyobj, "params",
					   error_prefix, T_ARRAY,
					   true);
    PyObject *point = get_item_python_dict(pyobj, "points",
					   error_prefix, T_ARRAY,
					   true);
    PyObject *lines = get_item_python_dict(pyobj, "lines",
					   error_prefix, T_ARRAY,
					   true);
    PyObject *faces = get_item_python_dict(pyobj, "faces",
					   error_prefix, T_ARRAY,
					   true);
    PyObject *curve = get_item_python_dict(pyobj, "curves",
					   error_prefix, T_ARRAY,
					   true);
    PyObject *curv2 = get_item_python_dict(pyobj, "curves2D",
					   error_prefix, T_ARRAY,
					   true);
    PyObject *surfs = get_item_python_dict(pyobj, "surfaces",
					   error_prefix, T_ARRAY,
					   true);
    int do_color = 0;
    if (verts != NULL) {
      nvert = (int)PyList_Size(verts);
      if (nvert > 0) {
	PyObject *ivert = get_item_python_list(verts, 0,
					       error_prefix,
					       T_OBJECT);
	PyObject *icolor = get_item_python_dict(ivert, "red",
						error_prefix,
						T_INT, true);
	if (icolor != NULL)
	  do_color = 1;
      }
    }
    if (texcs != NULL)
      ntexc = (int)PyList_Size(texcs);
    if (norms != NULL)
      nnorm = (int)PyList_Size(norms);
    if (param != NULL)
      nparam = (int)PyList_Size(param);
    if (point != NULL)
      npoint = (int)PyList_Size(point);
    if (lines != NULL)
      nline = (int)PyList_Size(lines);
    if (faces != NULL)
      nface = (int)PyList_Size(faces);
    if (curve != NULL)
      ncurve = (int)PyList_Size(curve);
    if (curv2 != NULL)
      ncurve2 = (int)PyList_Size(curv2);
    if (surfs != NULL)
      nsurf = (int)PyList_Size(surfs);
    if (alloc_obj(arg, nvert, ntexc, nnorm, nparam, npoint, nline, nface,
		  ncurve, ncurve2, nsurf, do_color) < 0) {
      ygglog_throw_error("ObjMetaschemaType::python2c: Error allocating obj structure.");
    }
    int i, j;
    // Material
    strcpy(error_prefix, "ObjMetaschemaType::python2c: material: ");
    get_item_python_dict_c(pyobj, "material", &(arg->material),
			   error_prefix, T_BYTES, 0, true);
    // Vertices
    if (arg->nvert > 0) {
      strcpy(error_prefix, "ObjMetaschemaType::python2c: vertices: ");
      for (i = 0; i < arg->nvert; i++) {
	PyObject *ivert = get_item_python_list(verts, i,
					       error_prefix,
					       T_OBJECT);
	char dir_str[4][10] = {"x", "y", "z", "w"};
	char clr_str[3][10] = {"red", "green", "blue"};
	for (j = 0; j < 4; j++) {
	  get_item_python_dict_c(ivert, dir_str[j],
				 &(arg->vertices[i][j]),
				 error_prefix, T_FLOAT,
				 8*sizeof(float));
	}
	if (do_color) {
	  for (j = 0; j < 3; j++) {
	    get_item_python_dict_c(ivert, clr_str[j],
				   &(arg->vertex_colors[i][j]),
				   error_prefix, T_INT,
				   8*sizeof(int));
	  }
	}
      }
    }
    // Texcoords
    if (arg->ntexc > 0) {
      strcpy(error_prefix, "ObjMetaschemaType::python2c: texcoords: ");
      for (i = 0; i < arg->ntexc; i++) {
	PyObject *itexc = get_item_python_list(texcs, i,
					       error_prefix,
					       T_OBJECT);
	char key_str[3][10] = {"u", "v", "w"};
	for (j = 0; j < 3; j++) {
	  get_item_python_dict_c(itexc, key_str[j],
				 &(arg->texcoords[i][j]),
				 error_prefix, T_FLOAT,
				 8*sizeof(float));
	}
      }
    }
    // Normals
    if (arg->nnorm > 0) {
      strcpy(error_prefix, "ObjMetaschemaType::python2c: normals: ");
      for (i = 0; i < arg->nnorm; i++) {
	PyObject *inorm = get_item_python_list(norms, i,
					       error_prefix,
					       T_OBJECT);
	char key_str[3][10] = {"i", "j", "k"};
	for (j = 0; j < 3; j++) {
	  get_item_python_dict_c(inorm, key_str[j],
				 &(arg->normals[i][j]),
				 error_prefix, T_FLOAT,
				 8*sizeof(float));
	}
      }
    }
    // Parameters
    if (arg->nparam > 0) {
      strcpy(error_prefix, "ObjMetaschemaType::python2c: params: ");
      for (i = 0; i < arg->nparam; i++) {
	PyObject *iparam = get_item_python_list(param, i,
						error_prefix,
						T_OBJECT);
	char key_str[3][10] = {"u", "v", "w"};
	for (j = 0; j < 3; j++) {
	  get_item_python_dict_c(iparam, key_str[j],
				 &(arg->params[i][j]),
				 error_prefix, T_FLOAT,
				 8*sizeof(float));
	}
      }
    }
    // Points
    if (arg->npoint > 0) {
      strcpy(error_prefix, "ObjMetaschemaType::python2c: points: ");
      for (i = 0; i < arg->npoint; i++) {
	PyObject *ipoint = get_item_python_list(point, i,
						error_prefix,
						T_ARRAY);
	arg->nvert_in_point[i] = (int)PyList_Size(ipoint);
	arg->points[i] = (int*)malloc((arg->nvert_in_point[i])*sizeof(int));
	if (arg->points[i] == NULL) {
	  ygglog_throw_error("%sFailed to malloc point %d.",
			     error_prefix, i);
	}
	for (j = 0; j < arg->nvert_in_point[i]; j++) {
	  get_item_python_list_c(ipoint, i, &(arg->points[i][j]),
				 error_prefix, T_INT, 8*sizeof(int));
	}
      }
    }
    // Lines
    if (arg->nline > 0) {
      strcpy(error_prefix, "ObjMetaschemaType::python2c: lines: ");
      for (i = 0; i < arg->nline; i++) {
	PyObject *iline = get_item_python_list(lines, i,
					       error_prefix,
					       T_ARRAY);
	arg->nvert_in_line[i] = (int)PyList_Size(iline);
	arg->lines[i] = (int*)malloc((arg->nvert_in_line[i])*sizeof(int));
	if (arg->lines[i] == NULL) {
	  ygglog_throw_error("%sFailed to malloc line %d.",
			     error_prefix, i);
	}
	arg->line_texcoords[i] = (int*)malloc((arg->nvert_in_line[i])*sizeof(int));
	if (arg->line_texcoords[i] == NULL) {
	  ygglog_throw_error("%sFailed to malloc line texcoord %d.",
			     error_prefix, i);
	}
	for (j = 0; j < arg->nvert_in_line[i]; j++) {
	  PyObject *iline_vert = get_item_python_list(iline, j,
						      error_prefix,
						      T_OBJECT);
	  get_item_python_dict_c(iline_vert, "vertex_index",
				 &(arg->lines[i][j]),
				 error_prefix, T_INT,
				 8*sizeof(int));
	  get_item_python_dict_c(iline_vert, "texcoord_index",
				 &(arg->line_texcoords[i][j]),
				 error_prefix, T_INT,
				 8*sizeof(int));
	}
      }
    }
    // Faces
    if (arg->nface > 0) {
      strcpy(error_prefix, "ObjMetaschemaType::python2c: faces: ");
      for (i = 0; i < arg->nface; i++) {
	PyObject *iface = get_item_python_list(faces, i,
					       error_prefix,
					       T_ARRAY);
	arg->nvert_in_face[i] = (int)PyList_Size(iface);
	arg->faces[i] = (int*)malloc((arg->nvert_in_face[i])*sizeof(int));
	if (arg->faces[i] == NULL) {
	  ygglog_throw_error("%sFailed to malloc face %d.",
			     error_prefix, i);
	}
	arg->face_texcoords[i] = (int*)malloc((arg->nvert_in_face[i])*sizeof(int));
	if (arg->face_texcoords[i] == NULL) {
	  ygglog_throw_error("%sFailed to malloc face texcoord %d.",
			     error_prefix, i);
	}
	arg->face_normals[i] = (int*)malloc((arg->nvert_in_face[i])*sizeof(int));
	if (arg->face_normals[i] == NULL) {
	  ygglog_throw_error("%sFailed to malloc face normal %d.",
			     error_prefix, i);
	}
	for (j = 0; j < arg->nvert_in_face[i]; j++) {
	  PyObject *iface_vert = get_item_python_list(iface, j,
						      error_prefix,
						      T_OBJECT);
	  arg->face_texcoords[i][j] = -1;
	  arg->face_normals[i][j] = -1;
	  get_item_python_dict_c(iface_vert, "vertex_index",
				 &(arg->faces[i][j]),
				 error_prefix, T_INT,
				 8*sizeof(int));
	  get_item_python_dict_c(iface_vert, "texcoord_index",
				 &(arg->face_texcoords[i][j]),
				 error_prefix, T_INT,
				 8*sizeof(int));
	  get_item_python_dict_c(iface_vert, "normal_index",
				 &(arg->face_normals[i][j]),
				 error_prefix, T_INT,
				 8*sizeof(int));
	}
      }
    }
    // Curves
    if (arg->ncurve > 0) {
      strcpy(error_prefix, "ObjMetaschemaType::python2c: curves: ");
      for (i = 0; i < arg->ncurve; i++) {
	PyObject *icurve = get_item_python_list(curve, i,
						error_prefix,
						T_OBJECT);
	PyObject *icurve_vert = get_item_python_dict(icurve,
						     "vertex_indices",
						     error_prefix,
						     T_ARRAY);
	arg->nvert_in_curve[i] = (int)PyList_Size(icurve_vert);
	arg->curves[i] = (int*)malloc((arg->nvert_in_curve[i])*sizeof(int));
	if (arg->curves[i] == NULL) {
	  ygglog_throw_error("%sFailed to malloc curve %d.",
			     error_prefix, i);
	}
	char key_str[2][50] = {"starting_param", "ending_param"};
	for (j = 0; j < 2; j++) {
	  get_item_python_dict_c(icurve, key_str[j],
				 &(arg->curve_params[i][j]),
				 error_prefix, T_FLOAT,
				 8*sizeof(float));
	}
	for (j = 0; j < arg->nvert_in_curve[i]; j++) {
	  get_item_python_list_c(icurve_vert, j,
				 &(arg->curves[i][j]),
				 error_prefix, T_INT, 8*sizeof(int));
	}
      }
    }
    // Curves 2D
    if (arg->ncurve2 > 0) {
      strcpy(error_prefix, "ObjMetaschemaType::python2c: curves 2D: ");
      for (i = 0; i < arg->ncurve2; i++) {
	PyObject *icurve2 = get_item_python_list(curv2, i,
						 error_prefix,
						 T_ARRAY);
	arg->nparam_in_curve2[i] = (int)PyList_Size(icurve2);
	arg->curves2[i] = (int*)malloc((arg->nparam_in_curve2[i])*sizeof(int));
	if (arg->curves2[i] == NULL) {
	  ygglog_throw_error("%sFailed to malloc curve2 %d.",
			     error_prefix, i);
	}
	for (j = 0; j < arg->nparam_in_curve2[i]; j++) {
	  get_item_python_list_c(icurve2, j, &(arg->curves2[i][j]),
				 error_prefix, T_INT, 8*sizeof(int));
	}
      }
    }
    // Surfaces
    if (arg->nsurf > 0) {
      strcpy(error_prefix, "ObjMetaschemaType::python2c: surfs: ");
      for (i = 0; i < arg->nsurf; i++) {
	PyObject *isurf = get_item_python_list(surfs, i,
					       error_prefix,
					       T_OBJECT);
	PyObject *isurf_vert = get_item_python_dict(isurf,
						    "vertex_indices",
						    error_prefix,
						    T_ARRAY);
	arg->nvert_in_surface[i] = (int)PyList_Size(isurf_vert);
	arg->surfaces[i] = (int*)malloc((arg->nvert_in_surface[i])*sizeof(int));
	if (arg->surfaces[i] == NULL) {
	  ygglog_throw_error("%sFailed to malloc surface %d.",
			     error_prefix, i);
	}
	arg->surface_texcoords[i] = (int*)malloc((arg->nvert_in_surface[i])*sizeof(int));
	if (arg->surface_texcoords[i] == NULL) {
	  ygglog_throw_error("%sFailed to malloc surface texcoord %d.",
			     error_prefix, i);
	}
	arg->surface_normals[i] = (int*)malloc((arg->nvert_in_surface[i])*sizeof(int));
	if (arg->surface_normals[i] == NULL) {
	  ygglog_throw_error("%sFailed to malloc surface normal %d.",
			     error_prefix, i);
	}
	
	char key_str_u[2][50] = {"starting_param_u", "ending_param_u"};
	for (j = 0; j < 2; j++) {
	  get_item_python_dict_c(isurf, key_str_u[j],
				 &(arg->surface_params_u[i][j]),
				 error_prefix, T_FLOAT,
				 8*sizeof(float));
	}
	char key_str_v[2][50] = {"starting_param_u", "ending_param_v"};
	for (j = 0; j < 2; j++) {
	  get_item_python_dict_c(isurf, key_str_v[j],
				 &(arg->surface_params_v[i][j]),
				 error_prefix, T_FLOAT,
				 8*sizeof(float));
	}
	for (j = 0; j < arg->nvert_in_surface[i]; j++) {
	  PyObject *ivert = get_item_python_list(isurf_vert, j,
						 error_prefix,
						 T_OBJECT);
	  arg->surface_texcoords[i][j] = -1;
	  arg->surface_normals[i][j] = -1;
	  get_item_python_dict_c(ivert, "vertex_index",
				 &(arg->surfaces[i][j]),
				 error_prefix, T_INT,
				 8*sizeof(int));
	  get_item_python_dict_c(ivert, "texcoord_index",
				 &(arg->surface_texcoords[i][j]),
				 error_prefix, T_INT,
				 8*sizeof(int));
	  get_item_python_dict_c(ivert, "normal_index",
				 &(arg->surface_normals[i][j]),
				 error_prefix, T_INT,
				 8*sizeof(int));
	}
      }
    }
    // Construct class
    YggGeneric *cobj = new YggGeneric(this, arg);
    return cobj;
  }
  /*!
    @brief Convert a C representation to a Python representation.
    @param[in] cobj YggGeneric* Pointer to C object.
    @returns PyObject* Pointer to Python object.
   */
  PyObject* c2python(YggGeneric *cobj) const override {
    initialize_python("ObjMetaschemaType::c2python: ");
    PyObject *py_args = PyTuple_New(0);
    PyObject *py_kwargs = PyDict_New();
    obj_t arg;
    cobj->get_data(arg);
    int i, j;
    char error_prefix[200] = "";
    // Material
    if (strlen(arg.material) > 0) {
      strcpy(error_prefix, "ObjMetaschemaType::c2python: material: ");
      set_item_python_dict_c(py_kwargs, "material", &(arg.material),
			     error_prefix, T_BYTES);
    }
    // Vertices
    if (arg.nvert > 0) {
      strcpy(error_prefix, "ObjMetaschemaType::c2python: vertices: ");
      PyObject *verts = new_python_list(arg.nvert, error_prefix);
      for (i = 0; i < arg.nvert; i++) {
	PyObject *ivert = new_python_dict(error_prefix);
	char dir_str[4][10] = {"x", "y", "z", "w"};
	char clr_str[3][10] = {"red", "blue", "green"};
	for (j = 0; j < 4; j++) {
	  set_item_python_dict_c(ivert, dir_str[j],
				 &(arg.vertices[i][j]),
				 error_prefix, T_FLOAT,
				 8*sizeof(float));
	}
	if (arg.vertex_colors != NULL) {
	  for (j = 0; j < 3; j++) {
	    set_item_python_dict_c(ivert, clr_str[j],
				   &(arg.vertex_colors[i][j]),
				   error_prefix, T_INT,
				   8*sizeof(int));
	  }
	}
	set_item_python_list(verts, i, ivert, error_prefix);
      }
      set_item_python_dict(py_kwargs, "vertices", verts,
			   error_prefix);
    }
    // Texcoords
    if (arg.ntexc > 0) {
      strcpy(error_prefix, "ObjMetaschemaType::c2python: texcoords: ");
      PyObject *texcs = new_python_list(arg.ntexc, error_prefix);
      for (i = 0; i < arg.ntexc; i++) {
	PyObject *itexc = new_python_dict(error_prefix);
	char key_str[3][10] = {"u", "v", "w"};
	for (j = 0; j < 3; j++) {
	  set_item_python_dict_c(itexc, key_str[j],
				 &(arg.texcoords[i][j]),
				 error_prefix, T_FLOAT,
				 8*sizeof(float));
	}
	set_item_python_list(texcs, i, itexc, error_prefix);
      }
      set_item_python_dict(py_kwargs, "texcoords", texcs,
			   error_prefix);
    }
    // Normals
    if (arg.nnorm > 0) {
      strcpy(error_prefix, "ObjMetaschemaType::c2python: normals: ");
      PyObject *norms = new_python_list(arg.nnorm, error_prefix);
      for (i = 0; i < arg.nnorm; i++) {
	PyObject *inorm = new_python_dict(error_prefix);
	char key_str[3][10] = {"i", "j", "k"};
	for (j = 0; j < 3; j++) {
	  set_item_python_dict_c(inorm, key_str[j],
				 &(arg.normals[i][j]),
				 error_prefix, T_FLOAT,
				 8*sizeof(float));
	}
	set_item_python_list(norms, i, inorm, error_prefix);
      }
      set_item_python_dict(py_kwargs, "normals", norms,
			   error_prefix);
    }
    // Params
    if (arg.nparam > 0) {
      strcpy(error_prefix, "ObjMetaschemaType::c2python: params: ");
      PyObject *params = new_python_list(arg.nparam, error_prefix);
      for (i = 0; i < arg.nparam; i++) {
	PyObject *iparam = new_python_dict(error_prefix);
	char key_str[3][10] = {"u", "v", "w"};
	for (j = 0; j < 3; j++) {
	  set_item_python_dict_c(iparam, key_str[j],
				 &(arg.params[i][j]),
				 error_prefix, T_FLOAT,
				 8*sizeof(float));
	}
	set_item_python_list(params, i, iparam, error_prefix);
      }
      set_item_python_dict(py_kwargs, "params", params,
			   error_prefix);
    }
    // Points
    if (arg.npoint > 0) {
      strcpy(error_prefix, "ObjMetaschemaType::c2python: points: ");
      PyObject *points = new_python_list(arg.npoint, error_prefix);
      for (i = 0; i < arg.npoint; i++) {
	PyObject *ipoint = new_python_list(arg.nvert_in_point[i],
					   error_prefix);
	for (j = 0; j < arg.nvert_in_point[i]; j++) {
	  set_item_python_list_c(ipoint, j, &(arg.points[i][j]),
				 error_prefix, T_INT, 8*sizeof(int));
	}
	set_item_python_list(points, i, ipoint, error_prefix);
      }
      set_item_python_dict(py_kwargs, "points", points,
			   error_prefix);
    }
    // Lines
    if (arg.nline > 0) {
      strcpy(error_prefix, "ObjMetaschemaType::c2python: lines: ");
      PyObject *lines = new_python_list(arg.nline, error_prefix);
      for (i = 0; i < arg.nline; i++) {
	PyObject *iline = new_python_list(arg.nvert_in_line[i],
					  error_prefix);
	for (j = 0; j < arg.nvert_in_line[i]; j++) {
	  PyObject *iline_vert = new_python_dict(error_prefix);
	  set_item_python_dict_c(iline_vert, "vertex_index",
				 &(arg.lines[i][j]),
				 error_prefix, T_INT,
				 8*sizeof(int));
	  set_item_python_dict_c(iline_vert, "texcoord_index",
				 &(arg.line_texcoords[i][j]),
				 error_prefix, T_INT,
				 8*sizeof(int));
	  set_item_python_list(iline, j, iline_vert, error_prefix);
	}
	set_item_python_list(lines, i, iline, error_prefix);
      }
      set_item_python_dict(py_kwargs, "lines", lines, error_prefix);
    }
    // Faces
    if (arg.nface > 0) {
      strcpy(error_prefix, "ObjMetaschemaType::c2python: faces: ");
      PyObject *faces = new_python_list(arg.nface, error_prefix);
      for (i = 0; i < arg.nface; i++) {
	PyObject *iface = new_python_list(arg.nvert_in_face[i],
					  error_prefix);
	for (j = 0; j < arg.nvert_in_face[i]; j++) {
	  PyObject *iface_vert = new_python_dict(error_prefix);
	  set_item_python_dict_c(iface_vert, "vertex_index",
				 &(arg.faces[i][j]),
				 error_prefix, T_INT,
				 8*sizeof(int));
	  set_item_python_dict_c(iface_vert, "texcoord_index",
				 &(arg.face_texcoords[i][j]),
				 error_prefix, T_INT,
				 8*sizeof(int));
	  set_item_python_dict_c(iface_vert, "normal_index",
				 &(arg.face_normals[i][j]),
				 error_prefix, T_INT,
				 8*sizeof(int));
	  set_item_python_list(iface, j, iface_vert, error_prefix);
	}
	set_item_python_list(faces, i, iface, error_prefix);
      }
      set_item_python_dict(py_kwargs, "faces", faces, error_prefix);
    }
    // Curves
    if (arg.ncurve > 0) {
      strcpy(error_prefix, "ObjMetaschemaType::c2python: curves: ");
      PyObject *curves = new_python_list(arg.ncurve, error_prefix);
      for (i = 0; i < arg.ncurve; i++) {
	PyObject *icurve = new_python_dict(error_prefix);
	char key_str[2][50] = {"starting_param", "ending_param"};
	for (j = 0; j < 2; j++) {
	  set_item_python_dict_c(icurve, key_str[j],
				 &(arg.curve_params[i][j]),
				 error_prefix, T_FLOAT,
				 8*sizeof(float));
	}
	PyObject *icurve_vert = new_python_list(arg.nvert_in_curve[i],
						error_prefix);
	for (j = 0; j < arg.nvert_in_curve[i]; j++) {
	  set_item_python_list_c(icurve_vert, j, &(arg.curves[i][j]),
				 error_prefix, T_INT, 8*sizeof(int));
	}
	set_item_python_dict(icurve, "vertex_indices", icurve_vert,
			     error_prefix);
	set_item_python_list(curves, i, icurve, error_prefix);
      }
      set_item_python_dict(py_kwargs, "curves", curves, error_prefix);
    }
    // Curves 2D
    if (arg.ncurve2 > 0) {
      strcpy(error_prefix, "ObjMetaschemaType::c2python: curves 2D: ");
      PyObject *curves2 = new_python_list(arg.ncurve2, error_prefix);
      for (i = 0; i < arg.ncurve2; i++) {
	PyObject *icurve2 = new_python_list(arg.nparam_in_curve2[i],
					    error_prefix);
	for (j = 0; j < arg.nparam_in_curve2[i]; j++) {
	  set_item_python_list_c(icurve2, j, &(arg.curves2[i][j]),
				 error_prefix, T_INT, 8*sizeof(int));
	}
	set_item_python_list(curves2, i, icurve2, error_prefix);
      }
      set_item_python_dict(py_kwargs, "curve2Ds", curves2,
			   error_prefix);
    }
    // Surfaces
    if (arg.nsurf > 0) {
      strcpy(error_prefix, "ObjMetaschemaType::c2python: surfaces: ");
      PyObject *surfs = new_python_list(arg.nsurf, error_prefix);
      for (i = 0; i < arg.nsurf; i++) {
	PyObject *isurf = new_python_dict(error_prefix);
	char key_str_u[2][50] = {"starting_param_u", "ending_param_u"};
	for (j = 0; j < 2; j++) {
	  set_item_python_dict_c(isurf, key_str_u[j],
				 &(arg.surface_params_u[i][j]),
				 error_prefix, T_FLOAT,
				 8*sizeof(float));
	}
	char key_str_v[2][50] = {"starting_param_v", "ending_param_v"};
	for (j = 0; j < 2; j++) {
	  set_item_python_dict_c(isurf, key_str_v[j],
				 &(arg.surface_params_v[i][j]),
				 error_prefix, T_FLOAT,
				 8*sizeof(float));
	}
	PyObject *isurf_vert = new_python_list(arg.nvert_in_surface[i],
					       error_prefix);
	for (j = 0; j < arg.nvert_in_surface[i]; j++) {
	  PyObject *ivert = new_python_dict(error_prefix);
	  set_item_python_dict_c(ivert, "vertex_index",
				 &(arg.surfaces[i][j]),
				 error_prefix, T_INT,
				 8*sizeof(int));
	  set_item_python_dict_c(ivert, "texcoord_index",
				 &(arg.surface_texcoords[i][j]),
				 error_prefix, T_INT,
				 8*sizeof(int));
	  set_item_python_dict_c(ivert, "normal_index",
				 &(arg.surface_normals[i][j]),
				 error_prefix, T_INT,
				 8*sizeof(int));
	  set_item_python_list(isurf_vert, j, ivert, error_prefix);
	}
	set_item_python_dict(isurf, "vertex_indices", isurf_vert,
			     error_prefix);
	set_item_python_list(surfs, i, isurf, error_prefix);
      }
      set_item_python_dict(py_kwargs, "surfaces", surfs,
			   error_prefix);
    }
    // Create class
    PyObject *py_class = import_python_class("yggdrasil.metaschema.datatypes.ObjMetaschemaType",
					     "ObjDict");
    PyObject *pyobj = PyObject_Call(py_class, py_args, py_kwargs);
    if (pyobj == NULL) {
      ygglog_throw_error("ObjMetaschemaType::c2python: Failed to create ObjDict.");
    }
    return pyobj;
  }

  // Encoding
  /*!
    @brief Encode arguments describine an instance of this type into a JSON string.
    @param[in] writer rapidjson::Writer<rapidjson::StringBuffer> rapidjson writer.
    @param[in,out] nargs size_t * Pointer to the number of arguments contained in
    ap. On return it will be set to the number of arguments used.
    @param[in] ap va_list_t Variable number of arguments that should be encoded
    as a JSON string.
    @returns bool true if the encoding was successful, false otherwise.
   */
  bool encode_data(rapidjson::Writer<rapidjson::StringBuffer> *writer,
		   size_t *nargs, va_list_t &ap) const override {
    // Get argument
    obj_t p = va_arg(ap.va, obj_t);
    (*nargs)--;
    // Allocate buffer
    int buf_size = 1000;
    char *buf = (char*)malloc(buf_size);
    int msg_len = 0, ilen = 0;
    char iline[500];
    buf[0] = '\0';
    // Format header
    char header_format[500] = "# Author ygg_auto\n"
      "# Generated by yggdrasil\n";
    if (strlen(p.material) != 0) {
      sprintf(header_format + strlen(header_format), "usemtl %s\n", p.material);
    }
    ilen = (int)strlen(header_format);
    if (ilen >= (buf_size - msg_len)) {
      buf_size = buf_size + ilen;
      buf = (char*)realloc(buf, buf_size);
    }
    strcat(buf, header_format);
    msg_len = msg_len + ilen;
    // Add vertex information
    int i, j;
    if (p.vertices == NULL) {
      if (p.nvert > 0) {
	ygglog_error("ObjMetaschemaType::encode_data: There are %d vertices, but the vector is NULL.", p.nvert);
	return false;
      }
    } else {
      for (i = 0; i < p.nvert; i++) {
	while (true) {
	  ilen = snprintf(buf + msg_len, buf_size - msg_len, "v %f %f %f",
			  p.vertices[i][0], p.vertices[i][1], p.vertices[i][2]);
	  if (ilen < 0) {
	    ygglog_error("ObjMetaschemaType::encode_data: Error formatting vertex %d.", i);
	    return false;
	  } else if (ilen >= (buf_size - msg_len)) {
	    buf_size = buf_size + ilen + 1;
	    buf = (char*)realloc(buf, buf_size);
	  } else {
	    break;
	  }
	}
	msg_len = msg_len + ilen;
	// Vertex Colors
	if (p.vertex_colors != NULL) {
	  while (true) {
	    ilen = snprintf(buf + msg_len, buf_size - msg_len, " %d %d %d",
			    p.vertex_colors[i][0], p.vertex_colors[i][1], p.vertex_colors[i][2]);
	    if (ilen < 0) {
	      ygglog_error("ObjMetaschemaType::encode_data: Error formatting vertex color %d.", i);
	      return false;
	    } else if (ilen >= (buf_size - msg_len)) {
	      buf_size = buf_size + ilen + 1;
	      buf = (char*)realloc(buf, buf_size);
	    } else {
	      break;
	    }
	  }
	  msg_len = msg_len + ilen;
	}
	// Optional weight
	while (true) {
	  if (p.vertices[i][3] != 1.0) {
	    ilen = snprintf(buf + msg_len, buf_size - msg_len, " %f\n",
			    p.vertices[i][3]);
	  } else {
	    ilen = snprintf(buf + msg_len, buf_size - msg_len, "\n");
	  }
	  if (ilen < 0) {
	    ygglog_error("ObjMetaschemaType::encode_data: Error formatting vertex weight %d.", i);
	    return false;
	  } else if (ilen >= (buf_size - msg_len)) {
	    buf_size = buf_size + ilen + 1;
	    buf = (char*)realloc(buf, buf_size);
	  } else {
	    break;
	  }
	}
	msg_len = msg_len + ilen;
      }
    }
    // Add texcoord information
    if (p.texcoords == NULL) {
      if (p.ntexc > 0) {
	ygglog_error("ObjMetaschemaType::encode_data: There are %d texcoords, but the vector is NULL.", p.ntexc);
	return false;
      }
    } else {
      for (i = 0; i < p.ntexc; i++) {
	while (true) {
	  if ((p.texcoords[i][1] == 0.0) && (p.texcoords[i][2] == 0.0)) {
	    ilen = snprintf(buf + msg_len, buf_size - msg_len, "vt %f\n",
			    p.texcoords[i][0]);
	  } else if (p.texcoords[i][2] == 0.0) {
	    ilen = snprintf(buf + msg_len, buf_size - msg_len, "vt %f %f\n",
			    p.texcoords[i][0], p.texcoords[i][1]);
	  } else {
	    ilen = snprintf(buf + msg_len, buf_size - msg_len, "vt %f %f %f\n",
			    p.texcoords[i][0], p.texcoords[i][1], p.texcoords[i][2]);
	  }
	  if (ilen < 0) {
	    ygglog_error("ObjMetaschemaType::encode_data: Error formatting texcoord %d.", i);
	    return false;
	  } else if (ilen >= (buf_size - msg_len)) {
	    buf_size = buf_size + ilen + 1;
	    buf = (char*)realloc(buf, buf_size);
	  } else {
	    break;
	  }
	}
	msg_len = msg_len + ilen;
      }
    }
    // Add normal information
    if (p.normals == NULL) {
      if (p.nnorm > 0) {
	ygglog_error("ObjMetaschemaType::encode_data: There are %d normals, but the vector is NULL.", p.nnorm);
	return false;
      }
    } else {
      for (i = 0; i < p.nnorm; i++) {
	while (true) {
	  ilen = snprintf(buf + msg_len, buf_size - msg_len, "vn %f %f %f\n",
			  p.normals[i][0], p.normals[i][1], p.normals[i][2]);
	  if (ilen < 0) {
	    ygglog_error("ObjMetaschemaType::encode_data: Error formatting normal %d.", i);
	    return false;
	  } else if (ilen >= (buf_size - msg_len)) {
	    buf_size = buf_size + ilen + 1;
	    buf = (char*)realloc(buf, buf_size);
	  } else {
	    break;
	  }
	}
	msg_len = msg_len + ilen;
      }
    }
    // Add param information
    if (p.params == NULL) {
      if (p.nparam > 0) {
	ygglog_error("ObjMetaschemaType::encode_data: There are %d params, but the vector is NULL.", p.nparam);
	return false;
      }
    } else {
      for (i = 0; i < p.nparam; i++) {
	while (true) {
	  if (p.params[i][2] == 1.0) {
	    ilen = snprintf(buf + msg_len, buf_size - msg_len, "vp %f %f\n",
			    p.params[i][0], p.params[i][1]);
	  } else {
	    ilen = snprintf(buf + msg_len, buf_size - msg_len, "vp %f %f %f\n",
			    p.params[i][0], p.params[i][1], p.params[i][2]);
	  }
	  if (ilen < 0) {
	    ygglog_error("ObjMetaschemaType::encode_data: Error formatting param %d.", i);
	    return false;
	  } else if (ilen >= (buf_size - msg_len)) {
	    buf_size = buf_size + ilen + 1;
	    buf = (char*)realloc(buf, buf_size);
	  } else {
	    break;
	  }
	}
	msg_len = msg_len + ilen;
      }
    }
    // Add point information
    if (p.points == NULL) {
      if (p.npoint > 0) {
	ygglog_error("ObjMetaschemaType::encode_data: There are %d points, but the vector is NULL.", p.npoint);
	return false;
      }
    } else {
      for (i = 0; i < p.npoint; i++) {
	char ival[100];
	sprintf(iline, "p");
	for (j = 0; j < p.nvert_in_point[i]; j++) {
	  sprintf(ival, " %d", p.points[i][j] + 1);
	  strcat(iline, ival);
	}
	while (true) {
	  ilen = snprintf(buf + msg_len, buf_size - msg_len, "%s\n", iline);
	  if (ilen < 0) {
	    ygglog_error("ObjMetaschemaType::encode_data: Error formatting line for point %d.", i);
	    return false;
	  } else if (ilen >= (buf_size - msg_len)) {
	    buf_size = buf_size + ilen + 1;
	    buf = (char*)realloc(buf, buf_size);
	  } else {
	    break;
	  }
	}
	msg_len = msg_len + ilen;
      }
    }
    // Add line information
    if (p.lines == NULL) {
      if (p.nline > 0) {
	ygglog_error("ObjMetaschemaType::encode_data: There are %d lines, but the vector is NULL.", p.nline);
	return false;
      }
    } else {
      for (i = 0; i < p.nline; i++) {
	char ival[10];
	sprintf(iline, "l");
	for (j = 0; j < p.nvert_in_line[i]; j++) {
	  sprintf(ival, " %d", p.lines[i][j] + 1);
	  strcat(iline, ival);
	  if (p.line_texcoords != NULL) {
	    if (p.line_texcoords[i][j] >= 0) {
	      sprintf(ival, "/%d", p.line_texcoords[i][j] + 1);
	      strcat(iline, ival);
	    }
	  }
	}
	while (true) {
	  ilen = snprintf(buf + msg_len, buf_size - msg_len, "%s\n", iline);
	  if (ilen < 0) {
	    ygglog_error("ObjMetaschemaType::encode_data: Error formatting line for line %d.", i);
	    return false;
	  } else if (ilen >= (buf_size - msg_len)) {
	    buf_size = buf_size + ilen + 1;
	    buf = (char*)realloc(buf, buf_size);
	  } else {
	    break;
	  }
	}
	msg_len = msg_len + ilen;
      }
    }
    // Add face information
    if (p.faces == NULL) {
      if (p.nface > 0) {
	ygglog_error("ObjMetaschemaType::encode_data: There are %d faces, but the vector is NULL.", p.nface);
	return false;
      }
    } else {
      for (i = 0; i < p.nface; i++) {
	char ival[10];
	sprintf(iline, "f");
	for (j = 0; j < p.nvert_in_face[i]; j++) {
	  sprintf(ival, " %d", p.faces[i][j] + 1);
	  strcat(iline, ival);
	  strcat(iline, "/");
	  if (p.face_texcoords != NULL) {
	    if (p.face_texcoords[i][j] >= 0) {
	      sprintf(ival, "%d", p.face_texcoords[i][j] + 1);
	      strcat(iline, ival);
	    }
	  }
	  strcat(iline, "/");
	  if (p.face_normals != NULL) {
	    if (p.face_normals[i][j] >= 0) {
	      sprintf(ival, "%d", p.face_normals[i][j] + 1);
	      strcat(iline, ival);
	    }
	  }
	}
	while (true) {
	  ilen = snprintf(buf + msg_len, buf_size - msg_len, "%s\n", iline);
	  if (ilen < 0) {
	    ygglog_error("ObjMetaschemaType::encode_data: Error formatting line for face %d.", i);
	    return false;
	  } else if (ilen >= (buf_size - msg_len)) {
	    buf_size = buf_size + ilen + 1;
	    buf = (char*)realloc(buf, buf_size);
	  } else {
	    break;
	  }
	}
	msg_len = msg_len + ilen;
      }
    }
    // Add curve information
    if (p.curves == NULL) {
      if (p.ncurve > 0) {
	ygglog_error("ObjMetaschemaType::encode_data: There are %d curves, but the vector is NULL.", p.ncurve);
	return false;
      }
    } else {
      for (i = 0; i < p.ncurve; i++) {
	char ival[10];
	sprintf(iline, "curv");
	for (j = 0; j < 2; j++) {
	  sprintf(ival, " %f", p.curve_params[i][j]);
	  strcat(iline, ival);
	}
	for (j = 0; j < p.nvert_in_curve[i]; j++) {
	  sprintf(ival, " %d", p.curves[i][j] + 1);
	  strcat(iline, ival);
	}
	while (true) {
	  ilen = snprintf(buf + msg_len, buf_size - msg_len, "%s\n", iline);
	  if (ilen < 0) {
	    ygglog_error("ObjMetaschemaType::encode_data: Error formatting line for curve %d.", i);
	    return false;
	  } else if (ilen >= (buf_size - msg_len)) {
	    buf_size = buf_size + ilen + 1;
	    buf = (char*)realloc(buf, buf_size);
	  } else {
	    break;
	  }
	}
	msg_len = msg_len + ilen;
      }
    }
    // Add curve2 information
    if (p.curves2 == NULL) {
      if (p.ncurve2 > 0) {
	ygglog_error("ObjMetaschemaType::encode_data: There are %d curve2s, but the vector is NULL.", p.ncurve2);
	return false;
      }
    } else {
      for (i = 0; i < p.ncurve2; i++) {
	char ival[10];
	sprintf(iline, "curv2");
	for (j = 0; j < p.nparam_in_curve2[i]; j++) {
	  sprintf(ival, " %d", p.curves2[i][j] + 1);
	  strcat(iline, ival);
	}
	while (true) {
	  ilen = snprintf(buf + msg_len, buf_size - msg_len, "%s\n", iline);
	  if (ilen < 0) {
	    ygglog_error("ObjMetaschemaType::encode_data: Error formatting line for curve2 %d.", i);
	    return false;
	  } else if (ilen >= (buf_size - msg_len)) {
	    buf_size = buf_size + ilen + 1;
	    buf = (char*)realloc(buf, buf_size);
	  } else {
	    break;
	  }
	}
	msg_len = msg_len + ilen;
      }
    }
    // Add surface information
    if (p.surfaces == NULL) {
      if (p.nsurf > 0) {
	ygglog_error("ObjMetaschemaType::encode_data: There are %d surfaces, but the vector is NULL.", p.nsurf);
	return false;
      }
    } else {
      for (i = 0; i < p.nsurf; i++) {
	char ival[10];
	sprintf(iline, "surf");
	for (j = 0; j < 2; j++) {
	  sprintf(ival, " %f", p.surface_params_u[i][j]);
	  strcat(iline, ival);
	}
	for (j = 0; j < 2; j++) {
	  sprintf(ival, " %f", p.surface_params_v[i][j]);
	  strcat(iline, ival);
	}
	for (j = 0; j < p.nvert_in_surface[i]; j++) {
	  sprintf(ival, " %d", p.surfaces[i][j] + 1);
	  strcat(iline, ival);
	  strcat(iline, "/");
	  if (p.surface_texcoords != NULL) {
	    if (p.surface_texcoords[i][j] >= 0) {
	      sprintf(ival, "%d", p.surface_texcoords[i][j] + 1);
	      strcat(iline, ival);
	    }
	  }
	  strcat(iline, "/");
	  if (p.surface_normals != NULL) {
	    if (p.surface_normals[i][j] >= 0) {
	      sprintf(ival, "%d", p.surface_normals[i][j] + 1);
	      strcat(iline, ival);
	    }
	  }
	}
	while (true) {
	  ilen = snprintf(buf + msg_len, buf_size - msg_len, "%s\n", iline);
	  if (ilen < 0) {
	    ygglog_error("ObjMetaschemaType::encode_data: Error formatting line for surface %d.", i);
	    return false;
	  } else if (ilen >= (buf_size - msg_len)) {
	    buf_size = buf_size + ilen + 1;
	    buf = (char*)realloc(buf, buf_size);
	  } else {
	    break;
	  }
	}
	msg_len = msg_len + ilen;
      }
    }
    ygglog_info("writing:\n%s",buf);
    buf[msg_len] = '\0';
    writer->String(buf, msg_len);
    return true;
  }
  /*!
    @brief Encode arguments describine an instance of this type into a JSON string.
    @param[in] writer rapidjson::Writer<rapidjson::StringBuffer> rapidjson writer.
    @param[in] x YggGeneric* Pointer to generic wrapper for data.
    @returns bool true if the encoding was successful, false otherwise.
   */
  bool encode_data(rapidjson::Writer<rapidjson::StringBuffer> *writer,
		   YggGeneric* x) const override {
    size_t nargs = 1;
    obj_t arg;
    x->get_data(arg);
    return MetaschemaType::encode_data(writer, &nargs, arg);
  }

  // Decoding
  /*!
    @brief Decode a line describine a line entry.
    @param[in,out] p obj_t* Obj struct that should be updated.
    @param[in,out] cline int Reference to count of lines currently in
    p that should be updated when a line is added to the structure.
    @param[in] iline char* Line that should be parsed for line
    information.
    @param[in] do_texcoords bool If true, texcoords will be extracted
    from the line.
    @returns int -1 if there is an error, 1 otherwise.
  */
  int decode_line(obj_t *p, int &cline, char *iline,
		  const char *re_line_vert,
		  bool do_texcoords) const {
    size_t *sind = NULL;
    size_t *eind = NULL;
    int j;
    int out = 1;
    try {
      ygglog_debug("ObjMetaschema::decode_line: Line");
      int val_per_vert = 1;
      if (do_texcoords)
	val_per_vert++;
      int nvert = count_matches(re_line_vert, iline);
      char re_split_vert[200] = "";
      for (j = 0; j < nvert; j++) {
	strcat(re_split_vert, re_line_vert);
      }
      int nvert_found = (find_matches(re_split_vert, iline, &sind, &eind) - 1)/val_per_vert;
      if (nvert_found != nvert) {
	ygglog_throw_error("ObjMetaschema::decode_line: Expected %d verts in line, but found %d.",
			   nvert, nvert_found);
      }
      p->nvert_in_line[cline] = nvert;
      int* iline_ele = (int*)realloc(p->lines[cline], nvert*sizeof(int));
      if (iline_ele == NULL) {
	ygglog_throw_error("ObjMetaschema::decode_line: Failed to allocate line %d.", cline);
      }
      p->lines[cline] = iline_ele;
      for (j = 0; j < nvert; j++) {
	p->lines[cline][j] = atoi(iline + sind[j*val_per_vert + 1]) - 1;
      }
      if (p->line_texcoords != NULL) {
	int *iline_texcoord = (int*)realloc(p->line_texcoords[cline], nvert*sizeof(int));
	if (iline_texcoord == NULL) {
	  ygglog_throw_error("ObjMetaschema::decode_line: Failed to allocate texcoord for line %d.", cline);
	}
	p->line_texcoords[cline] = iline_texcoord;
	if (do_texcoords) {
	  for (j = 0; j < nvert; j++) {
	    p->line_texcoords[cline][j] = atoi(iline + sind[j*val_per_vert + 2]) - 1;
	  }
	} else {
	  for (j = 0; j < nvert; j++) {
	    p->line_texcoords[cline][j] = -1;
	  }
	}
      }
      cline++;
    } catch(...) {
      out = -1;
    }
    if (sind != NULL) free(sind);
    if (eind != NULL) free(eind);
    return out;
  }
  
  /*!
    @brief Decode a line describine a face.
    @param[in,out] p obj_t* Obj struct that should be updated.
    @param[in,out] cface int Reference to count of faces currently in
    p that should be updated when a face is added to the structure.
    @param[in] iline char* Line that should be parsed for face
    information.
    @param[in] do_texcoords bool If true, texcoords will be extracted
    from the line.
    @param[in] do_normals bool If true, normals will be extracted
    from the line.
    @returns int -1 if there is an error, 1 otherwise.
  */
  int decode_face(obj_t *p, int &cface, char *iline,
		  const char *re_face_vert,
		  bool do_texcoords, bool do_normals) const {
    size_t *sind = NULL;
    size_t *eind = NULL;
    int j;
    int out = 1;
    try {
      ygglog_debug("ObjMetaschemaType::decode_face: Face");
      int val_per_vert = 1;
      if (do_texcoords)
	val_per_vert++;
      if (do_normals)
	val_per_vert++;
      int nvert = count_matches(re_face_vert, iline);
      char re_split_vert[200] = "";
      for (j = 0; j < nvert; j++) {
	strcat(re_split_vert, re_face_vert);
      }
      int nvert_found = (find_matches(re_split_vert, iline, &sind, &eind) - 1)/val_per_vert;
      if (nvert_found != nvert) {
	ygglog_throw_error("ObjMetaschemaType::decode_face: Expected %d verts in face, but found %d.",
			   nvert, nvert_found);
      }
      p->nvert_in_face[cface] = nvert;
      int *iface = (int*)realloc(p->faces[cface], nvert*sizeof(int));
      if (iface == NULL) {
	ygglog_throw_error("ObjMetaschemaType::decode_face: Failed to allocate face %d.", cface);
      }
      p->faces[cface] = iface;
      for (j = 0; j < nvert; j++) {
	p->faces[cface][j] = atoi(iline + sind[val_per_vert*j+1]) - 1;
      }
      if (p->face_texcoords != NULL) {
      	int *iface_texcoord = (int*)realloc(p->face_texcoords[cface], nvert*sizeof(int));
      	if (iface_texcoord == NULL) {
      	  ygglog_throw_error("ObjMetaschemaType::decode_face: Failed to allocate face texcoord %d.", cface);
      	}
      	p->face_texcoords[cface] = iface_texcoord;
      	if (do_texcoords) {
      	  for (j = 0; j < nvert; j++) {
      	    p->face_texcoords[cface][j] = atoi(iline + sind[val_per_vert*j+2]) - 1;
      	}
      	} else {
      	  for (j = 0; j < nvert; j++) {
      	    p->face_texcoords[cface][j] = -1;
      	  }
      	}
      }
      if (p->face_normals != NULL) {
      	int offset;
      	if (do_texcoords) {
      	  offset = 3;
      	} else {
      	  offset = 2;
      	}
      	int* iface_normal = (int*)realloc(p->face_normals[cface], nvert*sizeof(int));
      	if (iface_normal == NULL) {
      	  ygglog_throw_error("ObjMetaschemaType::decode_face: Failed to allocate face normal %d.", cface);
      	}
      	p->face_normals[cface] = iface_normal;
      	if (do_normals) {
      	  for (j = 0; j < nvert; j++) {
      	    p->face_normals[cface][j] = atoi(iline + sind[val_per_vert*j+offset]) - 1;
      	  }
      	} else {
      	  for (j = 0; j < nvert; j++) {
      	    p->face_normals[cface][j] = -1;
      	  }
      	}
      }
      cface++;
    } catch(...) {
      out = -1;
    }
    if (sind != NULL) free(sind);
    if (eind != NULL) free(eind);
    return out;
  }
  
  /*!
    @brief Decode a line describine a surface.
    @param[in,out] p obj_t* Obj struct that should be updated.
    @param[in,out] csurf int Reference to count of surfaces currently in
    p that should be updated when a surface is added to the structure.
    @param[in] iline char* Line that should be parsed for surface
    information.
    @param[in] sind_ptr size_t** Pointer to array containing starting
    indices for subexpressions in the regex for the surface entry.
    @param[in] eind_ptr size_t** Pointer to array containing ending
    indices for subexpressions in the regex for the surface entry.
    @param[in] do_texcoords bool If true, texcoords will be extracted
    from the line.
    @param[in] do_normals bool If true, normals will be extracted
    from the line.
    @returns int -1 if there is an error, 1 otherwise.
  */
  int decode_surface(obj_t *p, int &csurf, char *iline,
		     const char *re_surf_vert,
		     size_t **sind_ptr, size_t **eind_ptr,
		     bool do_texcoords, bool do_normals) const {
    int j;
    int out = 1;
    size_t *sind = *sind_ptr;
    size_t *eind = *eind_ptr;
    try {
      ygglog_debug("ObjMetaschemaType::decode_surface: Surface");
      int val_per_vert = 1;
      if (do_texcoords)
	val_per_vert++;
      if (do_normals)
	val_per_vert++;
      for (j = 0; j < 2; j++) {
	p->surface_params_u[csurf][j] = (float)atof(iline + sind[j + 1]);
	p->surface_params_v[csurf][j] = (float)atof(iline + sind[j + 3]);
      }
      int sind_verts = (int)(eind[4]);
      int nvert = count_matches(re_surf_vert, iline + sind_verts);
      char re_split_vert[200] = "";
      for (j = 0; j < nvert; j++) {
	strcat(re_split_vert, re_surf_vert);
      }
      int nvert_found = (find_matches(re_split_vert, iline + sind_verts, sind_ptr, eind_ptr) - 1)/val_per_vert;
      if (nvert_found != nvert) {
	ygglog_throw_error("ObjMetaschemaType::decode_surface: Expected %d verts in surface, but found %d.",
			   nvert, nvert_found);
      }
      sind = *sind_ptr;
      eind = *eind_ptr;
      p->nvert_in_surface[csurf] = nvert;
      int* isurf = (int*)realloc(p->surfaces[csurf], nvert*sizeof(int));
      if (isurf == NULL) {
	ygglog_throw_error("ObjMetaschemaType::decode_surface: Failed to allocate surface %d.", csurf);
      }
      p->surfaces[csurf] = isurf;
      for (j = 0; j < nvert; j++) {
	p->surfaces[csurf][j] = atoi(iline + sind_verts + sind[val_per_vert*j + 1]) - 1;
      }
      if (p->surface_texcoords != NULL) {
	int *isurf_texcoord = (int*)realloc(p->surface_texcoords[csurf], nvert*sizeof(int));
	if (isurf_texcoord == NULL) {
	  ygglog_throw_error("ObjMetaschemaType::decode_surface: Failed to allocate surface texcoord %d.", csurf);
	}
	p->surface_texcoords[csurf] = isurf_texcoord;
	if (do_texcoords) {
	  for (j = 0; j < nvert; j++) {
	    p->surface_texcoords[csurf][j] = atoi(iline + sind_verts + sind[val_per_vert*j + 2]) - 1;
	  }
	} else {
	  for (j = 0; j < nvert; j++) {
	    p->surface_texcoords[csurf][j] = -1;
	  }
	}
      }
      if (p->surface_normals != NULL) {
	int offset;
	if (do_texcoords)
	  offset = 3;
	else
	  offset = 2;
	int* isurf_normal = (int*)realloc(p->surface_normals[csurf], nvert*sizeof(int));
	if (isurf_normal == NULL) {
	  ygglog_throw_error("ObjMetaschemaType::decode_surface: Failed to allocate surface normal %d.", csurf);
	}
	p->surface_normals[csurf] = isurf_normal;
	if (do_normals) {
	  for (j = 0; j < nvert; j++) {
	    p->surface_normals[csurf][j] = atoi(iline + sind_verts + sind[val_per_vert*j + offset]) - 1;
	  }
	} else {
	  for (j = 0; j < nvert; j++) {
	    p->surface_normals[csurf][j] = -1;
	  }
	}
      }
      csurf++;
    } catch(...) {
      out = -1;
    }
    return out;
  }
  /*!
    @brief Decode variables from a JSON string.
    @param[in] data rapidjson::Value Reference to entry in JSON string.
    @param[in] allow_realloc int If 1, the passed variables will be reallocated
    to contain the deserialized data.
    @param[in,out] nargs size_t Number of arguments contained in ap. On return,
    the number of arguments assigned from the deserialized data will be assigned
    to this address.
    @param[out] ap va_list_t Reference to variable argument list containing
    address where deserialized data should be assigned.
    @returns bool true if the data was successfully decoded, false otherwise.
   */
  bool decode_data(rapidjson::Value &data, const int allow_realloc,
		   size_t *nargs, va_list_t &ap) const override {
    if (!(data.IsString()))
      ygglog_throw_error("ObjMetaschemaType::decode_data: Data is not a string.");
    // Get input data
    const char *buf = data.GetString();
    size_t buf_siz = data.GetStringLength();
    // Get output argument
    obj_t *p;
    obj_t **pp;
    if (allow_realloc) {
      pp = va_arg(ap.va, obj_t**);
      p = (obj_t*)realloc(*pp, sizeof(obj_t));
      if (p == NULL)
	ygglog_throw_error("ObjMetaschemaType::decode_data: could not realloc pointer.");
      *pp = p;
      *p = init_obj();
    } else {
      p = va_arg(ap.va, obj_t*);
    }
    (*nargs)--;
    // Process buffer
    int out = 1;
    int do_colors = 0;
    size_t *sind = NULL;
    size_t *eind = NULL;
    int nlines = 0;
    int j;
    int nvert = 0, ntexc = 0, nnorm = 0, nparam = 0, npoint = 0,
      nline = 0, nface = 0, ncurve = 0, ncurve2 = 0, nsurf = 0,
      nmatl = 0;
    // Counts
    int n_re_matl = 2;
    int n_re_vert = 7;
    int n_re_texc = 2;
    int n_re_norm = 4;
    int n_re_param = 3;
    int n_re_point = 2;
    int n_re_line = 2;
    int n_re_face = 2;
    int n_re_curve = 4;
    int n_re_curve2 = 2;
    int n_re_surf = 6;
    char re_float[100] = "[[:digit:]]+\\.[[:digit:]]+";
    char re_int[100] = "[[:digit:]]+";
    char re_matl[100] = "usemtl ([^\n]+)";
    char re_vert[500], re_vert_nocolor[500];
    char re_texc[500];
    char re_norm[500];
    char re_param[500];
    char re_point[500], re_point_tot[500], re_point_vert[100];
    char re_line_orig[500], re_line_vert_orig[100];
    char re_line_notexc[500], re_line_vert_notexc[100];
    char re_line_clean[500], re_line_vert_clean[100];
    char re_face_orig[500], re_face_vert_orig[100];
    char re_face_notexc[500], re_face_vert_notexc[100];
    char re_face_nonorm[500], re_face_vert_nonorm[100];
    char re_face_noextr[500], re_face_vert_noextr[100];
    char re_face_clean[500], re_face_vert_clean[100];
    char re_curve[500], re_curve_vert[100];
    char re_curve2[500], re_curve2_vert[100];
    char re_surf_orig[500], re_surf_vert_orig[100];
    char re_surf_notexc[500], re_surf_vert_notexc[100];
    char re_surf_nonorm[500], re_surf_vert_nonorm[100];
    char re_surf_noextr[500], re_surf_vert_noextr[100];
    char re_surf_clean[500], re_surf_vert_clean[100];
    snprintf(re_vert, 500, "v (%s) (%s) (%s) (%s) (%s) (%s)( %s)?",
	     re_float, re_float, re_float, re_int, re_int, re_int,
	     re_float);
    snprintf(re_vert_nocolor, 500, "v (%s) (%s) (%s)( %s)?",
	     re_float, re_float, re_float, re_float);
    snprintf(re_texc, 500, "vt (%s)( %s)?( %s)?",
	     re_float, re_float, re_float);
    snprintf(re_norm, 500, "vn (%s) (%s) (%s)",
	     re_float, re_float, re_float);
    snprintf(re_param, 500, "vp (%s) (%s)( %s)?",
	     re_float, re_float, re_float);
    snprintf(re_point_tot, 500, "[^v]p( %s){1,}", re_int);
    snprintf(re_point, 500, "p( %s){1,}", re_int);
    snprintf(re_point_vert, 100, " (%s)", re_int);
    snprintf(re_line_orig, 500, "l( %s/%s){2,}", re_int, re_int);
    snprintf(re_line_vert_orig, 100, " (%s)/(%s)", re_int, re_int);
    snprintf(re_line_notexc, 500, "l( %s/){2,}", re_int);
    snprintf(re_line_vert_notexc, 100, " (%s)/", re_int);
    snprintf(re_line_clean, 500, "l( %s){2,}", re_int);
    snprintf(re_line_vert_clean, 100, " (%s)", re_int);
    snprintf(re_face_orig, 500, "f( %s/%s/%s){3,}",
	     re_int, re_int, re_int);
    snprintf(re_face_vert_orig, 100, " (%s)/(%s)/(%s)",
	     re_int, re_int, re_int);
    snprintf(re_face_notexc, 500, "f( %s//%s){3,}",
	     re_int, re_int);
    snprintf(re_face_vert_notexc, 100, " (%s)//(%s)",
	     re_int, re_int);
    snprintf(re_face_nonorm, 500, "f( %s/%s/){3,}",
	     re_int, re_int);
    snprintf(re_face_vert_nonorm, 100, " (%s)/(%s)/",
	     re_int, re_int);
    snprintf(re_face_noextr, 500, "f( %s//){3,}", re_int);
    snprintf(re_face_vert_noextr, 100, " (%s)//", re_int);
    snprintf(re_face_clean, 500, "f( %s){3,}", re_int);
    snprintf(re_face_vert_clean, 100, " (%s)", re_int);
    snprintf(re_curve, 500, "curv (%s) (%s)( %s){2,}",
	     re_float, re_float, re_int);
    snprintf(re_curve_vert, 100, " (%s)", re_int);
    snprintf(re_curve2, 500, "curv2( %s){2,}", re_int);
    snprintf(re_curve2_vert, 100, " (%s)", re_int);
    snprintf(re_surf_orig, 500, "surf (%s) (%s) (%s) (%s)( %s/%s/%s){2,}",
	     re_float, re_float, re_float, re_float,
	     re_int, re_int, re_int);
    snprintf(re_surf_vert_orig, 100, " (%s)/(%s)/(%s)",
	     re_int, re_int, re_int);
    snprintf(re_surf_notexc, 500, "surf (%s) (%s) (%s) (%s)( %s//%s){2,}",
	     re_float, re_float, re_float, re_float, re_int, re_int);
    snprintf(re_surf_vert_notexc, 100, " (%s)//(%s)",
	     re_int, re_int);
    snprintf(re_surf_nonorm, 500, "surf (%s) (%s) (%s) (%s)( %s/%s/){2,}",
	     re_float, re_float, re_float, re_float, re_int, re_int);
    snprintf(re_surf_vert_nonorm, 100, " (%s)/(%s)/",
	     re_int, re_int);
    snprintf(re_surf_noextr, 500, "surf (%s) (%s) (%s) (%s)( %s//){2,}",
	     re_float, re_float, re_float, re_float, re_int);
    snprintf(re_surf_vert_noextr, 100, " (%s)//", re_int);
    snprintf(re_surf_clean, 500, "surf (%s) (%s) (%s) (%s)( %s){2,}",
	     re_float, re_float, re_float, re_float, re_int);
    snprintf(re_surf_vert_clean, 100, " (%s)", re_int);
    // Count matches
    nmatl = count_matches(re_matl, buf);
    nvert = count_matches(re_vert, buf);
    if (nvert != 0) {
      do_colors = 1;
    } else {
      do_colors = 0;
      strncpy(re_vert, re_vert_nocolor, 500);
      n_re_vert = 4;
      nvert = count_matches(re_vert, buf);
    }
    ntexc = count_matches(re_texc, buf);
    nnorm = count_matches(re_norm, buf);
    nparam = count_matches(re_param, buf);
    npoint = count_matches(re_point_tot, buf);
    ncurve = count_matches(re_curve, buf);
    ncurve2 = count_matches(re_curve2, buf);
    int remove_line_texcoords = 0,
      remove_face_texcoords = 0, remove_face_normals = 0,
      remove_surf_texcoords = 0, remove_surf_normals = 0;
    // Count lines in different versions
    int nline_orig = count_matches(re_line_orig, buf);
    int nline_notexc = count_matches(re_line_notexc, buf);
    int nline_clean = count_matches(re_line_clean, buf);
    nline = nline_orig + nline_notexc + nline_clean;
    if (nline > 0) {
      if (nline_orig == 0)
	remove_line_texcoords = 1;
    }
    // Count faces in different versions
    int nface_orig = count_matches(re_face_orig, buf);
    int nface_nonorm = count_matches(re_face_nonorm, buf);
    int nface_notexc = count_matches(re_face_notexc, buf);
    int nface_noextr = count_matches(re_face_noextr, buf);
    int nface_clean = count_matches(re_face_clean, buf);
    nface = nface_orig + nface_nonorm + nface_notexc +
      nface_noextr + nface_clean;
    if (nface > 0) {
      if ((nface_orig == 0) && (nface_notexc == 0))
	remove_face_normals = 1;
      if ((nface_orig == 0) && (nface_nonorm == 0))
	remove_face_texcoords = 1;
    }
    // Count surfaces in different versions
    int nsurf_orig = count_matches(re_surf_orig, buf);
    int nsurf_nonorm = count_matches(re_surf_nonorm, buf);
    int nsurf_notexc = count_matches(re_surf_notexc, buf);
    int nsurf_noextr = count_matches(re_surf_noextr, buf);
    int nsurf_clean = count_matches(re_surf_clean, buf);
    nsurf = nsurf_orig + nsurf_nonorm + nsurf_notexc + nsurf_noextr + nsurf_clean;
    if (nsurf > 0) {
      if ((nsurf_orig == 0) && (nsurf_notexc == 0))
	remove_surf_normals = 1;
      if ((nsurf_orig == 0) && (nsurf_nonorm == 0))
	remove_surf_texcoords = 1;
    }
    ygglog_info("deserialize_obj: expecting %d verts, %d texcoords, %d normals, "
		 "%d parameters, %d points, %d lines, %d faces, "
		 "%d curves, %d curve2s, %d surfaces",
		 nvert, ntexc, nnorm, nparam, npoint,
		 nline, nface, ncurve, ncurve2, nsurf);
    // Allocate
    if (out > 0) {
      int ret = alloc_obj(p, nvert, ntexc, nnorm, nparam, npoint,
			  nline, nface, ncurve, ncurve2, nsurf, do_colors);
      if (ret < 0) {
	ygglog_error("deserialize_obj: Error allocating obj structure.");
	out = -1;
      } else {
	if (remove_line_texcoords) {
	  free(p->line_texcoords);
	  p->line_texcoords = NULL;
	}
	if (remove_face_texcoords) {
	  free(p->face_texcoords);
	  p->face_texcoords = NULL;
	}
	if (remove_face_normals) {
	  free(p->face_normals);
	  p->face_normals = NULL;
	}
	if (remove_surf_texcoords) {
	  free(p->surface_texcoords);
	  p->surface_texcoords = NULL;
	}
	if (remove_surf_normals) {
	  free(p->surface_normals);
	  p->surface_normals = NULL;
	}
      }
    }
    // Locate lines
    int cmatl = 0, cvert = 0, ctexc = 0, cnorm = 0, cparam = 0,
      cpoint = 0, cline = 0, cface = 0, ccurve = 0, ccurve2 = 0,
      csurf = 0;
    size_t cur_pos = 0;
    char iline[500];
    size_t iline_siz = 0;
    size_t sind_line, eind_line;
    if (out > 0) {
      /* char ival[10]; */
      /* size_t ival_siz = 0; */
      while ((cur_pos < buf_siz) && (out >= 0)) {
	ygglog_debug("deserialize_obj: Starting position %d/%d",
		     cur_pos, buf_siz);
	int n_sub_matches = find_match("([^\n]*)\n", buf + cur_pos,
				       &sind_line, &eind_line);
	if (n_sub_matches == 0) {
	  ygglog_info("deserialize_obj: End of file.");
	  sind_line = 0;
	  eind_line = buf_siz - cur_pos;
	}
	iline_siz = eind_line - sind_line;
	memcpy(iline, buf + cur_pos, iline_siz);
	iline[iline_siz] = '\0';
	ygglog_debug("deserialize_obj: iline = %s", iline);
	// Match line
	if (find_matches("#[^\n]*", iline, &sind, &eind) == 1) {
	  // Comment
	  ygglog_debug("deserialize_obj: Comment");
	}
	// Material
	else if (find_matches(re_matl, iline, &sind, &eind) == n_re_matl) {
	  ygglog_debug("deserialize_obj: Material");
	  int matl_size = (int)(eind[1] - sind[1]);
	  memcpy(p->material, iline+sind[1], matl_size);
	  p->material[matl_size] = '\0';
	  cmatl++;
	}
	// Vertex
	else if (find_matches(re_vert, iline, &sind, &eind) == n_re_vert) {
	  ygglog_debug("deserialize_obj: Vertex");
	  for (j = 0; j < 3; j++) {
	    p->vertices[cvert][j] = (float)atof(iline + sind[j+1]);
	  }
	  p->vertices[cvert][3] = 1.0;
	  if (do_colors) {
	    for (j = 0; j < 3; j++) {
	      p->vertex_colors[cvert][j] = atoi(iline + sind[j+4]);
	    }
	  }
	  cvert++;
	}
	// Vertex with optional weight
	else if (find_matches(re_vert, iline, &sind, &eind) == (n_re_vert + 1)) {
	  for (j = 0; j < 3; j++) {
	    p->vertices[cvert][j] = (float)atof(iline + sind[j+1]);
	  }
	  if (do_colors) {
	    for (j = 0; j < 3; j++) {
	      p->vertex_colors[cvert][j] = atoi(iline + sind[j+4]);
	    }
	  }
	  p->vertices[cvert][3] = (float)atof(iline + sind[7]);
	  cvert++;
	}
	// Normals
	else if (find_matches(re_norm, iline, &sind, &eind) == n_re_norm) {
	  ygglog_debug("deserialize_obj: Normals");
	  for (j = 0; j < 3; j++) {
	    p->normals[cnorm][j] = (float)atof(iline + sind[j+1]);
	  }
	  cnorm++;
	}
	// Texcoords with just u
	else if (find_matches(re_texc, iline, &sind, &eind) == n_re_texc) {
	  ygglog_debug("deserialize_obj: Texcoords with u");
	  p->texcoords[ctexc][0] = (float)atof(iline + sind[1]);
	  p->texcoords[ctexc][1] = 0.0;
	  p->texcoords[ctexc][2] = 0.0;
	  ctexc++;
	}
	// Texcoords with optional v
	else if (find_matches(re_texc, iline, &sind, &eind) == (n_re_texc + 1)) {
	  ygglog_debug("deserialize_obj: Texcoords with u, v");
	  for (j = 0; j < 2; j++) {
	    p->texcoords[ctexc][j] = (float)atof(iline + sind[j+1]);
	  }
	  p->texcoords[ctexc][2] = 0.0;
	  ctexc++;
	}
	// Texcoords with optional w
	else if (find_matches(re_texc, iline, &sind, &eind) == (n_re_texc + 2)) {
	  ygglog_debug("deserialize_obj: Texcoords with u, v, w");
	  for (j = 0; j < 3; j++) {
	    p->texcoords[ctexc][j] = (float)atof(iline + sind[j+1]);
	  }
	  ctexc++;
	}
	// Parameters
	else if (find_matches(re_param, iline, &sind, &eind) == n_re_param) {
	  ygglog_debug("deserialize_obj: Parameters");
	  for (j = 0; j < 2; j++) {
	    p->params[cparam][j] = (float)atof(iline + sind[j+1]);
	  }
	  p->params[cparam][2] = 1.0;
	  cparam++;
	}
	// Parameters with optional weigth
	else if (find_matches(re_param, iline, &sind, &eind) == (n_re_param + 1)) {
	  ygglog_debug("deserialize_obj: Parameters");
	  for (j = 0; j < 3; j++) {
	    p->params[cparam][j] = (float)atof(iline + sind[j+1]);
	  }
	  cparam++;
	}
	// Points
	else if (find_matches(re_point, iline, &sind, &eind) == n_re_point) {
	  ygglog_debug("deserialize_obj: Point");
	  int nvert_local = count_matches(re_point_vert, iline);
	  char re_split_vert[100] = "";
	  for (j = 0; j < nvert_local; j++) {
	    strcat(re_split_vert, re_point_vert);
	  }
	  int nvert_found = find_matches(re_split_vert, iline, &sind, &eind) - 1;
	  if (nvert_found != nvert_local) {
	    ygglog_error("deserialize_obj: Expected %d verts in point, but found %d (re = %s, line = '%s').",
			 nvert_local, nvert_found, re_split_vert, iline);
	    out = -1;
	    break;
	  }
	  p->nvert_in_point[cpoint] = nvert_local;
	  int *ipoint = (int*)realloc(p->points[cpoint], nvert_local*sizeof(int));
	  if (ipoint == NULL) {
	    ygglog_error("deserialize_obj: Failed to allocate point %d.", cpoint);
	    out = -1;
	    break;
	  }
	  p->points[cpoint] = ipoint;
	  for (j = 0; j < nvert_local; j++) {
	    p->points[cpoint][j] = atoi(iline + sind[j+1]) - 1;
	  }
	  cpoint++;
	}
	// Lines
	else if (find_matches(re_line_orig, iline, &sind, &eind) == n_re_line) {
	  out = decode_line(p, cline, iline, re_line_vert_orig, true);
	}
	else if (find_matches(re_line_notexc, iline, &sind, &eind) == n_re_line) {
	  out = decode_line(p, cline, iline, re_line_vert_notexc, false);
	}
	// Faces
	else if (find_matches(re_face_orig, iline, &sind, &eind) == n_re_face) {
	  out = decode_face(p, cface, iline, re_face_vert_orig,
			    true, true);
	}
	else if (find_matches(re_face_notexc, iline, &sind, &eind) == n_re_face) {
	  out = decode_face(p, cface, iline, re_face_vert_notexc,
			    false, true);
	}
	else if (find_matches(re_face_nonorm, iline, &sind, &eind) == n_re_face) {
	  out = decode_face(p, cface, iline, re_face_vert_nonorm,
			    true, false);
	}
	else if (find_matches(re_face_noextr, iline, &sind, &eind) == n_re_face) {
	  out = decode_face(p, cface, iline, re_face_vert_noextr,
			    false, false);
	}
	else if (find_matches(re_face_clean, iline, &sind, &eind) == n_re_face) {
	  out = decode_face(p, cface, iline, re_face_vert_clean,
			    false, false);
	}
	// Curves
	else if (find_matches(re_curve, iline, &sind, &eind) == n_re_curve) {
	  ygglog_debug("deserialize_obj: Curve");
	  for (j = 0; j < 2; j++) {
	    p->curve_params[ccurve][j] = (float)atof(iline + sind[j + 1]);
	  }
	  int sind_verts = (int)(eind[2]);
	  int nvert_local = count_matches(re_curve_vert, iline + sind_verts);
	  char re_split_vert[100] = "";
	  for (j = 0; j < nvert_local; j++) {
	    strcat(re_split_vert, re_curve_vert);
	  }
	  int nvert_found = find_matches(re_split_vert, iline + sind_verts, &sind, &eind) - 1;
	  if (nvert_found != nvert_local) {
	    ygglog_error("deserialize_obj: Expected %d verts in curve, but found %d.",
			 nvert_local, nvert_found);
	    out = -1;
	    break;
	  }
	  p->nvert_in_curve[ccurve] = nvert_local;
	  int* icurve = (int*)realloc(p->curves[ccurve], nvert_local*sizeof(int));
	  if (icurve == NULL) {
	    ygglog_error("deserialize_obj: Failed to allocate curve %d.", ccurve);
	    out = -1;
	    break;
	  }
	  p->curves[ccurve] = icurve;
	  for (j = 0; j < nvert_local; j++) {
	    p->curves[ccurve][j] = atoi(iline + sind_verts + sind[j + 1]) - 1;
	  }
	  ccurve++;
	}
	// Curves2
	else if (find_matches(re_curve2, iline, &sind, &eind) == n_re_curve2) {
	  ygglog_debug("deserialize_obj: Curve2");
	  int nvert_local = count_matches(re_curve2_vert, iline);
	  char re_split_vert[100] = "";
	  for (j = 0; j < nvert_local; j++) {
	    strcat(re_split_vert, re_curve2_vert);
	  }
	  int nvert_found = find_matches(re_split_vert, iline, &sind, &eind) - 1;
	  if (nvert_found != nvert_local) {
	    ygglog_error("deserialize_obj: Expected %d verts in curve2, but found %d.",
			 nvert_local, nvert_found);
	    out = -1;
	    break;
	  }
	  p->nparam_in_curve2[ccurve2] = nvert_local;
	  int* icurve2 = (int*)realloc(p->curves2[ccurve2], nvert_local*sizeof(int));
	  if (icurve2 == NULL) {
	    ygglog_error("deserialize_obj: Failed to allocate curve2 %d.", ccurve);
	    out = -1;
	    break;
	  }
	  p->curves2[ccurve2] = icurve2;
	  for (j = 0; j < nvert_local; j++) {
	    p->curves2[ccurve2][j] = atoi(iline + sind[j + 1]) - 1;
	  }
	  ccurve2++;
	}
	// Surfaces
	else if (find_matches(re_surf_orig, iline, &sind, &eind) == n_re_surf) {
	  out = decode_surface(p, csurf, iline, re_surf_vert_orig,
			       &sind, &eind, true, true);
	}
	else if (find_matches(re_surf_notexc, iline, &sind, &eind) == n_re_surf) {
	  out = decode_surface(p, csurf, iline, re_surf_vert_notexc,
			       &sind, &eind, false, true);
	}
	else if (find_matches(re_surf_nonorm, iline, &sind, &eind) == n_re_surf) {
	  out = decode_surface(p, csurf, iline, re_surf_vert_nonorm,
			       &sind, &eind, true, false);
	}
	else if (find_matches(re_surf_noextr, iline, &sind, &eind) == n_re_surf) {
	  out = decode_surface(p, csurf, iline, re_surf_vert_noextr,
			       &sind, &eind, false, false);
	}
	else if (find_matches(re_surf_clean, iline, &sind, &eind) == n_re_surf) {
	  out = decode_surface(p, csurf, iline, re_surf_vert_clean,
			       &sind, &eind, false, false);
	}
	// Empty line
	else if (find_matches("\n+", iline, &sind, &eind) == 1) {
	  ygglog_debug("deserialize_obj: Empty line");
	}
	// No match
	else {
	  ygglog_error("deserialize_obj: Could not match line: %s", iline);
	  out = -1;
	  break;
	}
	nlines++;
	cur_pos = cur_pos + eind_line;
	ygglog_debug("deserialize_obj: Advancing to position %d/%d",
		     cur_pos, buf_siz);
      }
    }
    if (out > 0) {
      if (cmatl != nmatl) {
	ygglog_error("deserialize_obj: Found %d materials, expected %d.", cmatl, nmatl);
	out = -1;
      }
      if (cvert != nvert) {
	ygglog_error("deserialize_obj: Found %d verts, expected %d.", cvert, nvert);
	out = -1;
      }
      if (ctexc != ntexc) {
	ygglog_error("deserialize_obj: Found %d texcs, expected %d.", ctexc, ntexc);
	out = -1;
      }
      if (cnorm != nnorm) {
	ygglog_error("deserialize_obj: Found %d norms, expected %d.", cnorm, nnorm);
	out = -1;
      }
      if (cparam != nparam) {
	ygglog_error("deserialize_obj: Found %d parameters, expected %d.", cparam, nparam);
	out = -1;
      }
      if (cpoint != npoint) {
	ygglog_error("deserialize_obj: Found %d points, expected %d.", cpoint, npoint);
	out = -1;
      }
      if (cline != nline) {
	ygglog_error("deserialize_obj: Found %d lines, expected %d.", cline, nline);
      }
      if (cface != nface) {
	ygglog_error("deserialize_obj: Found %d faces, expected %d.", cface, nface);
	out = -1;
      }
      if (ccurve != ncurve) {
	ygglog_error("deserialize_obj: Found %d curves, expected %d.", ccurve, ncurve);
	out = -1;
      }
      if (ccurve2 != ncurve2) {
	ygglog_error("deserialize_obj: Found %d curve2s, expected %d.", ccurve2, ncurve2);
	out = -1;
      }
      if (csurf != nsurf) {
	ygglog_error("deserialize_obj: Found %d surfaces, expected %d.", csurf, nsurf);
	out = -1;
      }
    }
    // Return
    if (sind != NULL) free(sind); 
    if (eind != NULL) free(eind);
    if (out < 0) {
      free_obj(p);
      return false;
    } else {
      return true;
    }
  }

};

#endif /*OBJ_METASCHEMA_TYPE_H_*/
// Local Variables:
// mode: c++
// End:
