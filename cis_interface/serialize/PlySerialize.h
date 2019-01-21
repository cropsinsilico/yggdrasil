#ifndef YGGPLYSERIALIZE_H_
#define YGGPLYSERIALIZE_H_

#include <../tools.h>

#ifdef __cplusplus /* If this is a C++ compiler, use C linkage */
extern "C" {
#endif

/*! @brief Ply structure. */
typedef struct ply_t {
  int nvert; //!< Number of vertices.
  int nface; //!< Number faces.
  float **vertices; //!< X, Y, Z positions of vertices.
  int **faces; //!< Indices of the vertices composing each face.
  int **vertex_colors; //!< RGB colors of each vertex.
  int *nvert_in_face; //!< Number of vertices in each face.
} ply_t;

/*!
  @brief Initialize empty ply structure.
  @returns ply_t Ply structure.
 */
static inline
ply_t init_ply() {
  ply_t x;
  x.nvert = 0;
  x.nface = 0;
  x.vertices = NULL;
  x.faces = NULL;
  x.vertex_colors = NULL;
  x.nvert_in_face = NULL;
  return x;
};

/*!
  @brief Free ply structure.
  @param[in] p *ply_t Pointer to ply structure.
 */
static inline
void free_ply(ply_t *p) {
  int i;
  if (p->vertices != NULL) {
    for (i = 0; i < p->nvert; i++) {
      if (p->vertices[i] != NULL) {
	free(p->vertices[i]);
	p->vertices[i] = NULL;
      }
    }
    free(p->vertices);
    p->vertices = NULL;
  }
  if (p->vertex_colors != NULL) {
    for (i = 0; i < p->nvert; i++) {
      if (p->vertex_colors[i] != NULL) {
	free(p->vertex_colors[i]);
	p->vertex_colors[i] = NULL;
      }
    }
    free(p->vertex_colors);
    p->vertex_colors = NULL;
  }
  if (p->faces != NULL) {
    for (i = 0; i < p->nface; i++) {
      if (p->faces[i] != NULL) {
	free(p->faces[i]);
	p->faces[i] = NULL;
      }
    }
    free(p->faces);
    p->faces = NULL;
  }
  if (p->nvert_in_face != NULL) {
    free(p->nvert_in_face);
    p->nvert_in_face = NULL;
  }
};

/*!
  @brief Allocate ply structure.
  @param[in, out] p *ply_t Pointer to ply structure that should be allocated.
  @param[in] nvert int Number of vertices that should be allocated for.
  @param[in] nface int Number of faces that should be allocated for.
  @param[in] do_color int 1 if vertex colors should be allocated, 0 if not.
  @returns int 0 if successful, -1 otherwise.
 */
static inline
int alloc_ply(ply_t *p, int nvert, int nface, int do_color) {
  int i;
  free_ply(p); // Ensure that existing data is freed
  p->nvert = nvert;
  p->nface = nface;
  // Allocate vertices
  float **new_vert = (float**)malloc(p->nvert*sizeof(float*));
  if (new_vert == NULL) {
    ygglog_error("alloc_ply: Failed to allocate vertices.");
    free_ply(p);
    return -1;
  }
  p->vertices = new_vert;
  for (i = 0; i < p->nvert; i++) {
    float *ivert = (float*)malloc(3*sizeof(float));
    if (ivert == NULL) {
      ygglog_error("alloc_ply: Failed to allocate vertex %d.", i);
      free_ply(p);
      return -1;
    }
    p->vertices[i] = ivert;
  }
  ygglog_debug("alloc_ply: Allocated %d vertices.", nvert);
  // Allocate vertex colors
  if (do_color) {
    int **new_vert_colors = (int**)malloc(p->nvert*sizeof(int*));
    if (new_vert_colors == NULL) {
      ygglog_error("alloc_ply: Failed to allocate vertex_colors.");
      free_ply(p);
      return -1;
    }
    p->vertex_colors = new_vert_colors;
    for (i = 0; i < p->nvert; i++) {
      int *ivert = (int*)malloc(3*sizeof(int));
      if (ivert == NULL) {
	ygglog_error("alloc_ply: Failed to allocate vertex color %d.", i);
	free_ply(p);
	return -1;
      }
      p->vertex_colors[i] = ivert;
    }
    ygglog_debug("alloc_ply: Allocated %d vertex colors.", nvert);
  }
  // Allocate faces
  int **new_face = (int**)malloc(p->nface*sizeof(int*));
  if (new_face == NULL) {
    ygglog_error("alloc_ply: Failed to allocate faces.");
    free_ply(p);
    return -1;
  }
  p->faces = new_face;
  for (i = 0; i < p->nface; i++) {
    p->faces[i] = NULL;
    /* int *iface = (int*)malloc(3*sizeof(int)); */
    /* if (iface == NULL) { */
    /*   ygglog_error("alloc_ply: Failed to allocate face %d.", i); */
    /*   free_ply(p); */
    /*   return -1; */
    /* } */
  }
  ygglog_debug("alloc_ply: Allocated %d faces.", nface);
  // Allocate nvert_in_face
  int *new_nvert = (int*)malloc(p->nface*sizeof(int));
  if (new_nvert == NULL) {
    ygglog_error("alloc_ply: Failed to allocate nvert_in_face.");
    free_ply(p);
    return -1;
  }
  p->nvert_in_face = new_nvert;
  for (i = 0; i < p->nface; i++) {
    p->nvert_in_face[i] = 0;
  }
  ygglog_debug("alloc_ply: Allocate for %d vertices and %d faces.",
	       p->nvert, p->nface);
  return 0;
};

/*!
  @brief Serialize ply information to create a message.
  @param[in] s seri_t Structure sepcifying how to serialize arguments.
  @param[in] buf character pointer to memory where serialized message should be
  stored.
  @param[in] buf_size size_t Size of memory allocated to buf.
  @param[out] args_used int Number of arguments formatted.
  @param[in] ap va_list Arguments to be formatted.
  @returns: int The length of the serialized message or -1 if there is an error. 
 */
static inline
int serialize_ply(const seri_t s, char *buf, const size_t buf_size,
		  int *args_used, va_list ap) {
  // Prevent C4100 warning on windows by referencing param
#ifdef _WIN32
  s;
#endif
  args_used[0] = 0;
  int msg_len = 0;
  int ilen;
  // Get argument
  ply_t p = va_arg(ap, ply_t);
  args_used[0] = 1;
  // Format header
  char header_format[500] = "ply\n"
    "format ascii 1.0\n"
    "comment author ygg_auto\n"
    "comment File generated by yggdrasil\n"
    "element vertex %d\n"
    "property float x\n"
    "property float y\n"
    "property float z\n";
  if (p.vertex_colors != NULL) {
    char header_format_colors[100] = "property uchar diffuse_red\n"
      "property uchar diffuse_green\n"
      "property uchar diffuse_blue\n";
    strcat(header_format, header_format_colors);
  }
  char header_format2[100] = "element face %d\n"
    "property list uchar int vertex_indices\n"
    "end_header\n";
  strcat(header_format, header_format2);
  ilen = snprintf(buf, buf_size, header_format, p.nvert, p.nface);
  if (ilen < 0) {
    ygglog_error("serialize_ply: Error formatting header.");
    return -1;
  } else if (ilen >= buf_size) {
    ygglog_error("serialize_ply: Buffer (size = %d) is not large "
		 "enough to contain the header (size = %d).", buf_size, ilen);
    return msg_len + ilen;
  }
  msg_len = msg_len + ilen;
  // Add vertex information
  int i, j;
  for (i = 0; i < p.nvert; i++) {
    if (p.vertex_colors != NULL) {
      ilen = snprintf(buf + msg_len, buf_size - msg_len, "%f %f %f %d %d %d\n",
		      p.vertices[i][0], p.vertices[i][1], p.vertices[i][2],
		      p.vertex_colors[i][0], p.vertex_colors[i][1], p.vertex_colors[i][2]);
    } else {
      ilen = snprintf(buf + msg_len, buf_size - msg_len, "%f %f %f\n",
		      p.vertices[i][0], p.vertices[i][1], p.vertices[i][2]);
    }
    if (ilen < 0) {
      ygglog_error("serialize_ply: Error formatting vertex %d.", i);
      return -1;
    } else if (ilen >= (buf_size - msg_len)) {
      ygglog_error("serialize_ply: Buffer (size = %d) is not large "
		   "enough to contain vertex %d (size = %d).",
		   buf_size, i, ilen + msg_len);
      return msg_len + ilen;
    }
    msg_len = msg_len + ilen;
  }
  // Add face information
  for (i = 0; i < p.nface; i++) {
    ilen = snprintf(buf + msg_len, buf_size - msg_len, "%d", p.nvert_in_face[i]);
    if (ilen < 0) {
      ygglog_error("serialize_ply: Error formatting number of verts for face %d.", i);
      return -1;
    } else if (ilen > (buf_size - msg_len)) {
      ygglog_error("serialize_ply: Buffer (size = %d) is not large "
		   "enough to contain number of verts for face %d (size = %d).",
		   buf_size, i, ilen + msg_len);
      return msg_len + ilen;
    }
    msg_len = msg_len + ilen;
    for (j = 0; j < p.nvert_in_face[i]; j++) {
      ilen = snprintf(buf + msg_len, buf_size - msg_len, " %d", p.faces[i][j]);
      if (ilen < 0) {
        ygglog_error("serialize_ply: Error formatting element %d of face %d.", j, i);
        return -1;
      } else if (ilen > (buf_size - msg_len)) {
	ygglog_error("serialize_ply: Buffer (size = %d) is not large "
		     "enough to contain element %d of face %d (size = %d).",
		     buf_size, j, i, ilen + msg_len);
	return msg_len + ilen;
      }
      msg_len = msg_len + ilen;
    }
    ilen = snprintf(buf + msg_len, buf_size - msg_len, "\n");
    if (ilen < 0) {
      ygglog_error("serialize_ply: Error formatting newline for face %d.", i);
      return -1;
    } else if (ilen > (buf_size - msg_len)) {
      ygglog_error("serialize_ply: Buffer (size = %d) is not large "
		   "enough to contain newline for face %d (size = %d).",
		   buf_size, i, ilen + msg_len);
      return msg_len + ilen;
    }
    msg_len = msg_len + ilen;
  }
  return msg_len;
};


/*!
  @brief Deserialize message to populate ply structure.
  @param[in] s seri_t Structure sepcifying how to deserialize message.
  @param[in] buf character pointer to serialized message.
  @param[in] buf_siz size_t Size of buf.
  @param[out] ap va_list Arguments to be parsed from message.
  returns: int The number of populated arguments. -1 indicates an error.
 */
static inline
int deserialize_ply(const seri_t s, const char *buf, const size_t buf_siz,
		    va_list ap) {
  // Prevent C4100 warning on windows by referencing param
#ifdef _WIN32
  s;
  buf_siz;
#endif
  int out = 1;
  int do_colors = 0;
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
  int nvert = 0, nface = 0;
  int line_no;
  size_t line_size;
  char iline[100];
  // Get argument
  ply_t *p = va_arg(ap, ply_t*);
  // Get info from the header.
  // Number of vertices
  if (out > 0) {
    n_sub_matches = find_matches("element vertex ([[:digit:]]+)\n", buf, &sind, &eind);
    if (n_sub_matches < 2) {
      ygglog_error("deserialize_ply: Could not locate number of vertices in ply header.");
      out = -1;
    }
    value_size = eind[1] - sind[1];
    memcpy(value, buf + sind[1], value_size);
    value[value_size] = '\0';
    nvert = atoi(value);
  }
  // Number of faces
  if (out > 0) {
    n_sub_matches = find_matches("element face ([[:digit:]]+)\n", buf, &sind, &eind);
    if (n_sub_matches < 2) {
      ygglog_error("deserialize_ply: Could not locate number of faces in ply header.");
      out = -1;
    }
    value_size = eind[1] - sind[1];
    memcpy(value, buf + sind[1], value_size);
    value[value_size] = '\0';
    nface = atoi(value);
  }
  // Color
  if (out > 0) {
    n_sub_matches = find_matches("green", buf, &sind, &eind);
    if (n_sub_matches != 0) {
      do_colors = 1;
    }
  }
  // End of header
  if (out > 0) {
    n_sub_matches = find_matches("end_header\n", buf, &sind, &eind);
    if (n_sub_matches < 1) {
      ygglog_error("deserialize_ply: Could not locate end of header.");
      out = -1;
    } else {
      begin_body = eind[0];
    }
  }
  // Locate lines
  if (out > 0) {
    int nlines_expected = nvert + nface;
    nlines = 0;
    sind_body = (size_t*)realloc(sind_body, (nlines_expected+1)*sizeof(size_t));
    eind_body = (size_t*)realloc(eind_body, (nlines_expected+1)*sizeof(size_t));
    size_t cur_pos = begin_body;
    while (1) {
      n_sub_matches = find_matches("([^\n]*)\n", buf + cur_pos, &sind, &eind);
      if (n_sub_matches < 2) {
	break;
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
    if ((nvert + nface) > nlines) {
      ygglog_error("deserialize_ply: Not enough lines (%d) for %d vertices "
		   "and %d faces.",
		   nlines, nvert, nface);
      out = -1;
    }
  }
  // Allocate
  if (out > 0) {
    int ret = alloc_ply(p, nvert, nface, do_colors);
    if (ret < 0) {
      ygglog_error("deserialize_ply: Error allocating ply structure.");
      out = -1;
    }
  }
  // Get vertices
  if (out > 0) {
    int nexpected = 3;
    if (do_colors) {
      nexpected = 6;
    }
    char vert_re[80] = "([^ ]+) ([^ ]+) ([^ ]+)";
    // Parse each line
    for (i = 0; i < p->nvert; i++) {
      line_no = i;
      line_size = eind_body[line_no] - sind_body[line_no];
      memcpy(iline, buf + sind_body[line_no], line_size);
      iline[line_size] = '\0';
      n_sub_matches = find_matches(vert_re, iline, &sind, &eind);
      if (n_sub_matches != nexpected + 1) {
	ygglog_error("deserialize_ply: Vertex should contain %d entries. "
		     "%d were found", nexpected, n_sub_matches - 1);
	out = -1;
	break;
      } else {
	for (j = 0; j < 3; j++) {
	  p->vertices[i][j] = (float)atof(iline + sind[j + 1]);
	}
	if (do_colors) {
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
      char face_re[80] = "([^ ]+)";
      for (j = 0; j < nexpected; j++) {
	strcat(face_re, " ([^ ]+)");
      }
      n_sub_matches = find_matches(face_re, iline, &sind, &eind);
      if (n_sub_matches < (nexpected + 2)) {
	ygglog_error("deserialize_ply: Face should contain %d entries. "
		     "%d were found.", nexpected, n_sub_matches - 2);
        out = -1;
        break;
      } else {
        int *iface = (int*)realloc(p->faces[i], nexpected*sizeof(int));
        if (iface == NULL) {
          ygglog_error("deserialize_ply: Could not allocate face %d.", i);
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
  // Return
  if (sind != NULL) free(sind); 
  if (eind != NULL) free(eind);
  if (sind_body != NULL) free(sind_body); 
  if (eind_body != NULL) free(eind_body);
  if (out < 0) {
    free_ply(p);
  }
  return out;
};

#ifdef __cplusplus /* If this is a C++ compiler, end C linkage */
}
#endif

#endif /*YGGPLYSERIALIZE_H_*/
