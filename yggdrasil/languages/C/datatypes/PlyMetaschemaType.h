#ifndef PLY_METASCHEMA_TYPE_H_
#define PLY_METASCHEMA_TYPE_H_

#include "../tools.h"
#include "MetaschemaType.h"
#include "PlyDict.h"

#include "rapidjson/document.h"
#include "rapidjson/writer.h"


/*!
  @brief Class for PLY type definition.

  The PlyMetaschemaType provides basic functionality for encoding/decoding
  Ply structures from/to JSON style strings.
 */
class PlyMetaschemaType : public MetaschemaType {
public:
  /*!
    @brief Constructor for PlyMetaschemaType.
    @param[in] use_generic bool If true, serialized/deserialized
    objects will be expected to be YggGeneric classes.
   */
  PlyMetaschemaType(const bool use_generic=false) : MetaschemaType("ply", use_generic) {}
  /*!
    @brief Constructor for PlyMetaschemaType from a JSON type defintion.
    @param[in] type_doc rapidjson::Value rapidjson object containing the type
    definition from a JSON encoded header.
    @param[in] use_generic bool If true, serialized/deserialized
    objects will be expected to be YggGeneric classes.
   */
  PlyMetaschemaType(const rapidjson::Value &type_doc,
		    const bool use_generic=false) : MetaschemaType(type_doc, use_generic) {}
  /*!
    @brief Constructor for PlyMetaschemaType from Python dictionary.
    @param[in] pyobj PyObject* Python object.
    @param[in] use_generic bool If true, serialized/deserialized
    objects will be expected to be YggGeneric classes.
   */
  PlyMetaschemaType(PyObject* pyobj,
		    const bool use_generic=false) : MetaschemaType(pyobj, use_generic) {}
  /*!
    @brief Copy constructor.
    @param[in] other PlyMetaschemaType* Instance to copy.
   */
  PlyMetaschemaType(const PlyMetaschemaType &other) :
    PlyMetaschemaType(other.use_generic()) {}
  /*!
    @brief Create a copy of the type.
    @returns pointer to new PlyMetaschemaType instance with the same data.
   */
  PlyMetaschemaType* copy() const override { return (new PlyMetaschemaType(use_generic())); }
  /*!
    @brief Copy data wrapped in YggGeneric class.
    @param[in] data YggGeneric* Pointer to generic object.
    @returns void* Pointer to copy of data.
   */
  void* copy_generic(const YggGeneric* data, void* orig_data=NULL) const override {
    if (data == NULL) {
      ygglog_throw_error("PlyMetaschemaType::copy_generic: Generic object is NULL.");
    }
    void* out = NULL;
    if (orig_data == NULL) {
      orig_data = data->get_data();
    }
    if (orig_data != NULL) {
      ply_t* old_data = (ply_t*)orig_data;
      ply_t* new_data = (ply_t*)malloc(sizeof(ply_t));
      if (new_data == NULL) {
	ygglog_throw_error("PlyMetaschemaType::copy_generic: Failed to malloc memory for ply struct.");
      }
      new_data[0] = copy_ply(*old_data);
      if (new_data->vertices == NULL) {
	ygglog_throw_error("PlyMetaschemaType::copy_generic: Failed to copy ply struct.");
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
      ygglog_throw_error("PlyMetaschemaType::free_generic: Generic object is NULL.");
    }
    ply_t** ptr = (ply_t**)(data->get_data_pointer());
    if (ptr[0] != NULL) {
      free_ply(ptr[0]);
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
    ply_t arg;
    if (data == NULL) {
      ygglog_throw_error("PlyMetaschemaType::display_generic: Generic object is NULL.");
    }
    data->get_data(arg);
    display_ply_indent(arg, indent);
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
    va_arg(ap.va, ply_t);
    out++;
    return out;
  }
  /*!
    @brief Get the item size.
    @returns size_t Size of item in bytes.
   */
  const size_t nbytes() const override {
    return sizeof(ply_t);
  }
  /*!
    @brief Get the number of arguments expected to be filled/used by the type.
    @returns size_t Number of arguments.
   */
  size_t nargs_exp() const override {
    return 1;
  }
  /*!
    @brief Convert a Python representation to a C representation.
    @param[in] pyobj PyObject* Pointer to Python object.
    @returns YggGeneric* Pointer to C object.
   */
  YggGeneric* python2c(PyObject *pyobj) const override {
    if (!(PyDict_Check(pyobj))) {
      ygglog_throw_error("PlyMetaschemaType::python2c: Python object must be a dict.");
    }
    ply_t *arg = (ply_t*)malloc(sizeof(ply_t));
    if (arg == NULL) {
      ygglog_throw_error("PlyMetaschemaType::python2c: Failed to malloc for ply structure.");
    }
    arg[0] = init_ply();
    char error_prefix[200] = "";
    int i, j;
    // Material
    strcpy(error_prefix, "PlyMetaschemaType::python2c: material: ");
    get_item_python_dict_c(pyobj, "material", &(arg->material),
			   error_prefix, T_BYTES);
    // Vertices
    bool vertex_colors = false;
    strcpy(error_prefix, "PlyMetaschemaType::python2c: vertices: ");
    PyObject *vertices = get_item_python_dict(pyobj, "vertices",
					      error_prefix,
					      T_ARRAY, true);
    if (vertices != NULL) {
      arg->nvert = (int)PyList_Size(vertices);
      if (arg->nvert > 0) {
	arg->vertices = (float**)malloc(arg->nvert*sizeof(float*));
	if (arg->vertices == NULL) {
	  ygglog_throw_error("%sFailed to malloc.", error_prefix);
	}
	for (i = 0; i < arg->nvert; i++) {
	  PyObject *ivert = get_item_python_list(vertices, i,
						 error_prefix,
						 T_OBJECT);
	  char dir_str[3][10] = {"x", "y", "z"};
	  char clr_str[3][10] = {"red", "green", "blue"};
	  arg->vertices[i] = (float*)malloc(3*sizeof(float));
	  if (arg->vertices[i] == NULL) {
	    ygglog_throw_error("%sFailed to malloc vertex %d.",
			       error_prefix, i);
	  }
	  for (j = 0; j < 3; j++) {
	    get_item_python_dict_c(ivert, dir_str[j],
				   &(arg->vertices[i][j]),
				   error_prefix, T_FLOAT,
				   8*sizeof(float));
	  }
	  if (i == 0) {
	    if (get_item_python_dict(ivert, "red", error_prefix,
				     T_INT, true) != NULL) {
	      vertex_colors = true;
	      arg->vertex_colors = (int**)malloc(arg->nvert*sizeof(int*));
	      if (arg->vertex_colors == NULL) {
		ygglog_throw_error("%sFailed to malloc colors.", error_prefix);
	      }
	    }
	  }
	  if (vertex_colors) {
	    arg->vertex_colors[i] = (int*)malloc(3*sizeof(int));
	    if (arg->vertex_colors[i] == NULL) {
	      ygglog_throw_error("%sFailed to malloc vertex color %d.",
				 error_prefix, i);
	    }
	    for (j = 0; j < 3; j++) {
	      get_item_python_dict_c(ivert, clr_str[j],
				     &(arg->vertex_colors[i][j]),
				     error_prefix, T_INT,
				     8*sizeof(int));
	    }
	  }
	}
      }
    }
    // Faces
    strcpy(error_prefix, "PlyMetaschemaType::python2c: faces: ");
    PyObject *faces = get_item_python_dict(pyobj, "faces",
					   error_prefix,
					   T_ARRAY, true);
    if (faces != NULL) {
      arg->nface = (int)PyList_Size(faces);
      if (arg->nface > 0) {
	arg->faces = (int**)malloc(arg->nface*sizeof(int*));
	if (arg->faces == NULL) {
	  ygglog_throw_error("%sFailed to malloc.", error_prefix);
	}
	arg->nvert_in_face = (int*)malloc(arg->nface*sizeof(int));
	if (arg->nvert_in_face == NULL) {
	  ygglog_throw_error("%sFailed to malloc nvert_in_face.",
			     error_prefix);
	}
	for (i = 0; i < arg->nface; i++) {
	  PyObject *iface = get_item_python_list(faces, i,
						 error_prefix,
						 T_OBJECT);
	  PyObject *iface_vert = get_item_python_dict(iface, "vertex_index",
						      error_prefix,
						      T_ARRAY);
	  arg->nvert_in_face[i] = (int)PyList_Size(iface_vert);
	  arg->faces[i] = (int*)malloc((arg->nvert_in_face[i])*sizeof(int));
	  if (arg->faces[i] == NULL) {
	    ygglog_throw_error("%sFailed to malloc face %d.",
			       error_prefix, i);
	  }
	  for (j = 0; j < arg->nvert_in_face[i]; j++) {
	    get_item_python_list_c(iface_vert, i, &(arg->faces[i][j]),
				   error_prefix, T_INT,
				   8*sizeof(int));
	  }
	}
      }
    }
    // Edges
    bool edge_colors = false;
    strcpy(error_prefix, "PlyMetaschemaType::python2c: edges: ");
    PyObject *edges = get_item_python_dict(pyobj, "edges",
					   error_prefix,
					   T_ARRAY, true);
    if (edges != NULL) {
      arg->nedge = (int)PyList_Size(edges);
      if (arg->nedge > 0) {
	arg->edges = (int**)malloc(arg->nedge*sizeof(int*));
	if (arg->edges == NULL) {
	  ygglog_throw_error("%sFailed to malloc.", error_prefix);
	}
	for (i = 0; i < arg->nedge; i++) {
	  PyObject *iedge = get_item_python_list(edges, i,
						 error_prefix,
						 T_OBJECT);
	  char dir_str[3][10] = {"vertex1", "vertex2"};
	  char clr_str[3][10] = {"red", "green", "blue"};
	  arg->edges[i] = (int*)malloc(2*sizeof(int));
	  if (arg->edges[i] == NULL) {
	    ygglog_throw_error("%sFailed to malloc edge %d.",
			       error_prefix, i);
	  }
	  for (j = 0; j < 2; j++) {
	    get_item_python_dict_c(iedge, dir_str[j],
				   &(arg->edges[i][j]),
				   error_prefix, T_INT,
				   8*sizeof(int));
	  }
	  if (i == 0) {
	    if (get_item_python_dict(iedge, "red", error_prefix,
				     T_INT, true) != NULL) {
	      edge_colors = true;
	      arg->edge_colors = (int**)malloc(arg->nedge*sizeof(int*));
	      if (arg->edge_colors == NULL) {
		ygglog_throw_error("%sFailed to malloc colors.", error_prefix);
	      }
	    }
	  }
	  if (edge_colors) {
	    arg->edge_colors[i] = (int*)malloc(3*sizeof(int));
	    if (arg->edge_colors[i] == NULL) {
	      ygglog_throw_error("%sFailed to malloc edge color %d.",
				 error_prefix, i);
	    }
	    for (j = 0; j < 3; j++) {
	      get_item_python_dict_c(iedge, clr_str[j],
				     &(arg->edge_colors[i][j]),
				     error_prefix, T_INT,
				     8*sizeof(int));
	    }
	  }
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
    initialize_python("PlyMetaschemaType::c2python: ");
    PyObject *py_args = PyTuple_New(0);
    PyObject *py_kwargs = PyDict_New();
    ply_t arg;
    cobj->get_data(arg);
    int i, j;
    char error_prefix[200] = "";
    // Material
    if (strlen(arg.material) > 0) {
      strcpy(error_prefix, "PlyMetaschemaType::c2python: material: ");
      set_item_python_dict_c(py_kwargs, "material", &(arg.material),
			     error_prefix, T_BYTES);
    }
    // Vertices
    if (arg.nvert > 0) {
      strcpy(error_prefix, "PlyMetaschemaType::c2python: vertices: ");
      PyObject *verts = new_python_list(arg.nvert, error_prefix);
      for (i = 0; i < arg.nvert; i++) {
	PyObject *ivert = new_python_dict(error_prefix);
	char dir_str[3][10] = {"x", "y", "z"};
	char clr_str[3][10] = {"red", "blue", "green"};
	for (j = 0; j < 3; j++) {
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
    // Faces
    if (arg.nface > 0) {
      strcpy(error_prefix, "PlyMetaschemaType::c2python: faces: ");
      PyObject *faces = new_python_list(arg.nface, error_prefix);
      for (i = 0; i < arg.nface; i++) {
	PyObject *iface = new_python_dict(error_prefix);
	PyObject *iface_vert = new_python_list(arg.nvert_in_face[i],
					       error_prefix);
	for (j = 0; j < arg.nvert_in_face[i]; j++) {
	  set_item_python_list_c(iface_vert, j, &(arg.faces[i][j]),
				 error_prefix, T_INT, 8*sizeof(int));
	}
	set_item_python_dict(iface, "vertex_index", iface_vert,
			     error_prefix);
	set_item_python_list(faces, i, iface, error_prefix);
      }
      set_item_python_dict(py_kwargs, "faces", faces,
			   error_prefix);
    }
    // Edges
    if (arg.nedge > 0) {
      strcpy(error_prefix, "PlyMetaschemaType::c2python: edges: ");
      PyObject *edges = new_python_list(arg.nedge, error_prefix);
      for (i = 0; i < arg.nedge; i++) {
	PyObject *iedge = new_python_dict(error_prefix);
	char key_str[2][10] = {"vertex1", "vertex2"};
	char clr_str[3][10] = {"red", "blue", "green"};
	for (j = 0; j < 2; j++) {
	  set_item_python_dict_c(iedge, key_str[j],
				 &(arg.edges[i][j]),
				 error_prefix, T_INT, 8*sizeof(int));
	}
	if (arg.edge_colors != NULL) {
	  for (j = 0; j < 3; j++) {
	    set_item_python_dict_c(iedge, clr_str[j],
				   &(arg.edge_colors[i][j]),
				   error_prefix, T_INT,
				   8*sizeof(int));
	  }
	}
	set_item_python_list(edges, i, iedge, error_prefix);
      }
      set_item_python_dict(py_kwargs, "edges", edges, error_prefix);
    }
    // Create class
    PyObject *py_class = import_python_class("yggdrasil.metaschema.datatypes.PlyMetaschemaType",
					     "PlyDict");
    PyObject *pyobj = PyObject_Call(py_class, py_args, py_kwargs);
    if (pyobj == NULL) {
      ygglog_throw_error("PlyMetaschemaType::c2python: Failed to create PlyDict.");
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
    ply_t p = va_arg(ap.va, ply_t);
    (*nargs)--;
    // Allocate buffer
    size_t buf_size = 1000;
    char *buf = (char*)malloc(buf_size);
    if (buf == NULL) {
      ygglog_error("PlyMetaschemaType::encode_data: Error allocating buffer.");
      return false;
    }
    size_t msg_len = 0;
    int ilen;
    // Format header
    ilen = snprintf_realloc(&buf, &buf_size, &msg_len,
			    "ply\n"
			    "format ascii 1.0\n"
			    "comment author ygg_auto\n"
			    "comment File generated by yggdrasil\n");
    if (ilen < 0) {
      ygglog_error("PlyMetaschemaType::encode_data: Error formatting header.");
      free(buf);
      return false;
    }
    // Format material header
    if (strlen(p.material) != 0) {
      ilen = snprintf_realloc(&buf, &buf_size, &msg_len,
			      "comment material: %s\n",
			      p.material);
      if (ilen < 0) {
	ygglog_error("PlyMetaschemaType::encode_data: Error formatting material.");
	free(buf);
	return false;
      }
    }
    // Format vertex header
    if (p.nvert > 0) {
      ilen = snprintf_realloc(&buf, &buf_size, &msg_len,
			      "element vertex %d\n"
			      "property float x\n"
			      "property float y\n"
			      "property float z\n",
			      p.nvert);
      if (ilen < 0) {
	ygglog_error("PlyMetaschemaType::encode_data: Error formatting vertex header.");
	free(buf);
	return false;
      }
      if (p.vertex_colors != NULL) {
	ilen = snprintf_realloc(&buf, &buf_size, &msg_len,
				"property uchar red\n"
				"property uchar green\n"
				"property uchar blue\n");
	if (ilen < 0) {
	  ygglog_error("PlyMetaschemaType::encode_data: Error formatting vertex color header.");
	  free(buf);
	  return false;
	}
      }
    }
    // Format face header
    if (p.nface > 0) {
      ilen = snprintf_realloc(&buf, &buf_size, &msg_len,
			      "element face %d\n"
			      "property list uchar int vertex_index\n",
			      p.nface);
      if (ilen < 0) {
	ygglog_error("PlyMetaschemaType::encode_data: Error formatting face header.");
	free(buf);
	return false;
      }
    }
    // Format edge header
    if (p.nedge > 0) {
      ilen = snprintf_realloc(&buf, &buf_size, &msg_len,
			      "element edge %d\n"
			      "property int vertex1\n"
			      "property int vertex2\n",
			      p.nedge);
      if (ilen < 0) {
	ygglog_error("PlyMetaschemaType::encode_data: Error formatting edge header.");
	free(buf);
	return false;
      }
      if (p.edge_colors != NULL) {
	ilen = snprintf_realloc(&buf, &buf_size, &msg_len,
				"property uchar red\n"
				"property uchar green\n"
				"property uchar blue\n");
	if (ilen < 0) {
	  ygglog_error("PlyMetaschemaType::encode_data: Error formatting edge color header.");
	  free(buf);
	  return false;
	}
      }
    }
    // Close header
    ilen = snprintf_realloc(&buf, &buf_size, &msg_len,
			    "end_header\n");
    if (ilen < 0) {
      ygglog_error("PlyMetaschemaType::encode_data: Error formatting close to header.");
      free(buf);
      return false;
    }
    // Add vertex information
    int i, j;
    for (i = 0; i < p.nvert; i++) {
      if (p.vertex_colors != NULL) {
	ilen = snprintf_realloc(&buf, &buf_size, &msg_len,
				"%f %f %f %d %d %d\n",
				p.vertices[i][0], p.vertices[i][1], p.vertices[i][2],
				p.vertex_colors[i][0], p.vertex_colors[i][1], p.vertex_colors[i][2]);
      } else {
	ilen = snprintf_realloc(&buf, &buf_size, &msg_len,
				"%f %f %f\n",
				p.vertices[i][0], p.vertices[i][1], p.vertices[i][2]);
      }
      if (ilen < 0) {
	ygglog_error("PlyMetaschemaType::encode_data: Error formatting vertex %d.", i);
	free(buf);
	return false;
      }
    }
    // Add face information
    for (i = 0; i < p.nface; i++) {
      ilen = snprintf_realloc(&buf, &buf_size, &msg_len,
			      "%d", p.nvert_in_face[i]);
      if (ilen < 0) {
	ygglog_error("PlyMetaschemaType::encode_data: Error formatting number of verts for face %d.", i);
	free(buf);
	return false;
      }
      for (j = 0; j < p.nvert_in_face[i]; j++) {
	ilen = snprintf_realloc(&buf, &buf_size, &msg_len,
				" %d", p.faces[i][j]);
	if (ilen < 0) {
	  ygglog_error("PlyMetaschemaType::encode_data: Error formatting element %d of face %d.", j, i);
	  free(buf);
	  return false;
	}
      }
      ilen = snprintf_realloc(&buf, &buf_size, &msg_len, "\n");
      if (ilen < 0) {
	ygglog_error("PlyMetaschemaType::encode_data: Error formatting newline for face %d.", i);
	free(buf);
	return false;
      }
    }
    // Add edge information
    for (i = 0; i < p.nedge; i++) {
      if (p.edge_colors != NULL) {
	ilen = snprintf_realloc(&buf, &buf_size, &msg_len,
				"%d %d %d %d %d\n",
				p.edges[i][0], p.edges[i][1],
				p.edge_colors[i][0], p.edge_colors[i][1], p.edge_colors[i][2]);
      } else {
	ilen = snprintf_realloc(&buf, &buf_size, &msg_len,
				"%d %d\n",
				p.edges[i][0], p.edges[i][1]);
      }
      if (ilen < 0) {
	ygglog_error("PlyMetaschemaType::encode_data: Error formatting edge %d.", i);
	free(buf);
	return false;
      }
    }
    buf[msg_len] = '\0';
    writer->String(buf, (rapidjson::SizeType)msg_len);
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
    ply_t arg;
    x->get_data(arg);
    return MetaschemaType::encode_data(writer, &nargs, arg);
  }

  // Decoded
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
      ygglog_throw_error("PlyMetaschemaType::decode_data: Data is not a string.");
    // Get input data
    const char *buf = data.GetString();
    // size_t buf_siz = data.GetStringLength();
    // Get output argument
    ply_t *p;
    ply_t **pp;
    if (allow_realloc) {
      pp = va_arg(ap.va, ply_t**);
      p = (ply_t*)realloc(*pp, sizeof(ply_t));
      if (p == NULL)
	ygglog_throw_error("PlyMetaschemaType::decode_data: could not realloc pointer.");
      *pp = p;
      *p = init_ply();
    } else {
      p = va_arg(ap.va, ply_t*);
    }
    (*nargs)--;
    // Process buffer
    int out = 1;
    int do_vert_colors = 0, do_edge_colors = 0;
    int n_sub_matches;
    size_t *sind = NULL;
    size_t *eind = NULL;
    size_t *sind_body = NULL;
    size_t *eind_body = NULL;
    size_t value_size;
    char value[100];
    size_t begin_body = 0;
    int nlines = 0;
    int i, j;
    char material[100];
    material[0] = '\0';
    int nvert = 0, nface = 0, nedge=0;
    int line_no;
    size_t line_size;
    char iline[100];
    // Get info from the header.
    // Material
    if (out > 0) {
      n_sub_matches = find_matches("comment material: ([^ ]+)\n", buf, &sind, &eind);
      if (n_sub_matches < 2) {
	material[0] = '\0';
      } else {
	value_size = eind[1] - sind[1];
	memcpy(material, buf + sind[1], value_size);
	material[value_size] = '\0';
	ygglog_info("material = %s\n", material);
      }
    }
    // Number of vertices
    if (out > 0) {
      n_sub_matches = find_matches("element vertex ([[:digit:]]+)\n", buf, &sind, &eind);
      if (n_sub_matches < 2) {
	ygglog_error("PlyMetaschemaType::decode_data: Could not locate number of vertices in ply header.");
	out = -1;
      }
      value_size = eind[1] - sind[1];
      memcpy(value, buf + sind[1], value_size);
      value[value_size] = '\0';
      nvert = atoi(value);
    }
    // Vertex color
    if (out > 0) {
      n_sub_matches = find_matches("element vertex [[:digit:]]+\n"
				   "property .*\n"
				   "property .*\n"
				   "property .*\n"
				   "property [^ ]+ red\n",
				   buf, &sind, &eind);
      if (n_sub_matches != 0) {
	do_vert_colors = 1;
      }
    }
    // Number of faces
    if (out > 0) {
      n_sub_matches = find_matches("element face ([[:digit:]]+)\n", buf, &sind, &eind);
      if (n_sub_matches < 2) {
	ygglog_error("PlyMetaschemaType::decode_data: Could not locate number of faces in ply header.");
	out = -1;
      }
      value_size = eind[1] - sind[1];
      memcpy(value, buf + sind[1], value_size);
      value[value_size] = '\0';
      nface = atoi(value);
    }
    // Number of edges
    if (out > 0) {
      n_sub_matches = find_matches("element edge ([[:digit:]]+)\n", buf, &sind, &eind);
      if (n_sub_matches < 2) {
	ygglog_debug("PlyMetaschemaType::decode_data: Could not locate number of edges in ply header.");
	nedge = 0;
      } else {
	value_size = eind[1] - sind[1];
	memcpy(value, buf + sind[1], value_size);
	value[value_size] = '\0';
	nedge = atoi(value);
      }
    }
    // Edge color
    if (out > 0) {
      n_sub_matches = find_matches("element edge [[:digit:]]+\n"
				   "property .*\n"
				   "property .*\n"
				   "property [^ ]+ red\n",
				   buf, &sind, &eind);
      if (n_sub_matches != 0) {
	do_edge_colors = 1;
      }
    }
    // End of header
    if (out > 0) {
      n_sub_matches = find_matches("end_header\n", buf, &sind, &eind);
      if (n_sub_matches < 1) {
	ygglog_error("PlyMetaschemaType::decode_data: Could not locate end of header.");
	out = -1;
      } else {
	begin_body = eind[0];
      }
    }
    // Locate lines
    if (out > 0) {
      int nlines_expected = nvert + nface + nedge;
      nlines = 0;
      sind_body = (size_t*)realloc(sind_body, (nlines_expected+1)*sizeof(size_t));
      eind_body = (size_t*)realloc(eind_body, (nlines_expected+1)*sizeof(size_t));
      size_t cur_pos = begin_body;
      while (1) {
	n_sub_matches = find_matches("([^\n]*)\n", buf + cur_pos, &sind, &eind);
	if (n_sub_matches < 2) {
	  // Check for line not terminated with newline
	  n_sub_matches = find_matches("([^\n]*)", buf + cur_pos, &sind, &eind);
	  if ((n_sub_matches < 2) || (sind == eind)) {
	    break;
	  }
	}
	if (nlines > nlines_expected) {
	  break;
	  // nlines_expected = nlines_expected + 50;
	  // sind_body = (size_t*)realloc(sind_body, (nlines_expected+1)*sizeof(size_t));
	  // eind_body = (size_t*)realloc(eind_body, (nlines_expected+1)*sizeof(size_t));
	}
	sind_body[nlines] = cur_pos + sind[1];
	eind_body[nlines] = cur_pos + eind[1];
	nlines++;
	cur_pos = cur_pos + eind[0];
      }
      if ((nvert + nface + nedge) > nlines) {
	ygglog_error("PlyMetaschemaType::decode_data: Not enough lines (%d) for %d vertices, "
		     "%d faces, and %d edges.",
		     nlines, nvert, nface, nedge);
	out = -1;
      }
    }
    // Allocate
    if (out > 0) {
      int ret = alloc_ply(p, nvert, nface, nedge, do_vert_colors, do_edge_colors);
      if (ret < 0) {
	ygglog_error("PlyMetaschemaType::decode_data: Error allocating ply structure.");
	out = -1;
      }
    }
    // Material
    if (out > 0) {
      strcpy(p->material, material);
    }
    // Get vertices
    if (out > 0) {
      int nexpected = 3;
      char vert_re[80] = "([^ ]+) ([^ ]+) ([^ ]+)";
      if (do_vert_colors) {
	nexpected = 6;
	strcpy(vert_re, "([^ ]+) ([^ ]+) ([^ ]+) ([[:digit:]]+) ([[:digit:]]+) ([[:digit:]]+)");
      }
      // Parse each line
      for (i = 0; i < p->nvert; i++) {
	line_no = i;
	line_size = eind_body[line_no] - sind_body[line_no];
	memcpy(iline, buf + sind_body[line_no], line_size);
	iline[line_size] = '\0';
	n_sub_matches = find_matches(vert_re, iline, &sind, &eind);
	if (n_sub_matches != nexpected + 1) {
	  ygglog_error("PlyMetaschemaType::decode_data: Vertex should contain %d entries. "
		       "%d were found.", nexpected, n_sub_matches - 1);
	  out = -1;
	  break;
	} else {
	  for (j = 0; j < 3; j++) {
	    p->vertices[i][j] = (float)atof(iline + sind[j + 1]);
	  }
	  if (do_vert_colors) {
	    for (j = 0; j < 3; j++) {
	      p->vertex_colors[i][j] = atoi(iline + sind[j + 4]);
	    }
	  }
	}
      }
    }
    // Get faces
    if (out > 0) {
      int nexpected = 0;
      // Parse each line
      for (i = 0; i < p->nface; i++) {
	line_no = i + p->nvert;
	line_size = eind_body[line_no] - sind_body[line_no];
	memcpy(iline, buf + sind_body[line_no], line_size);
	iline[line_size] = '\0';
	nexpected = atoi(iline);
	p->nvert_in_face[i] = nexpected;
	char face_re[80] = "([[:digit:]]+)";
	for (j = 0; j < nexpected; j++) {
	  strcat(face_re, " ([[:digit:]]+)");
	}
	n_sub_matches = find_matches(face_re, iline, &sind, &eind);
	if (n_sub_matches < (nexpected + 2)) {
	  ygglog_error("PlyMetaschemaType::decode_data: Face should contain %d entries. "
		       "%d were found.", nexpected, n_sub_matches - 2);
	  out = -1;
	  break;
	} else {
	  int *iface = (int*)realloc(p->faces[i], nexpected*sizeof(int));
	  if (iface == NULL) {
	    ygglog_error("PlyMetaschemaType::decode_data: Could not allocate face %d.", i);
	    out = -1;
	    break;
	  } else {
	    p->faces[i] = iface;
	    for (j = 0; j < nexpected; j++) {
	      p->faces[i][j] = atoi(iline + sind[j + 2]);
	    }
	  }
	}
      }
    }
    // Get edges
    if (out > 0) {
      int nexpected = 2;
      char edge_re[80] = "([[:digit:]]+) ([[:digit:]]+)";
      if (do_edge_colors) {
	nexpected = 5;
	strcpy(edge_re, "([[:digit:]]+) ([[:digit:]]+) ([[:digit:]]+) ([[:digit:]]+) ([[:digit:]]+)");
      }
      // Parse each line
      for (i = 0; i < p->nedge; i++) {
	line_no = i + p->nface + p->nvert;
	line_size = eind_body[line_no] - sind_body[line_no];
	memcpy(iline, buf + sind_body[line_no], line_size);
	iline[line_size] = '\0';
	n_sub_matches = find_matches(edge_re, iline, &sind, &eind);
	if (n_sub_matches != nexpected + 1) {
	  ygglog_error("PlyMetaschemaType::decode_data: Edge should contain %d entries. "
		       "%d were found.", nexpected, n_sub_matches - 1);
	  out = -1;
	  break;
	} else {
	  for (j = 0; j < 2; j++) {
	    p->edges[i][j] = atoi(iline + sind[j + 1]);
	  }
	  if (do_edge_colors) {
	    for (j = 0; j < 3; j++) {
	      p->edge_colors[i][j] = atoi(iline + sind[j + 3]);
	    }
	  }
	}
      }
    }
    // Return
    if (sind != NULL) free(sind); 
    if (eind != NULL) free(eind);
    if (sind_body != NULL) free(sind_body); 
    if (eind_body != NULL) free(eind_body);
    if (out < 0) {
      free_ply(p);
      return false;
    } else {
      return true;
    }
  }

};


#endif /*PLY_METASCHEMA_TYPE_H_*/
// Local Variables:
// mode: c++
// End:
