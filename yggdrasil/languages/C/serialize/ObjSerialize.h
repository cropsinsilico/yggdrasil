#ifndef YGGOBJSERIALIZE_H_
#define YGGOBJSERIALIZE_H_

#include <../tools.h>

#ifdef __cplusplus /* If this is a C++ compiler, use C linkage */
extern "C" {
#endif

/*! @brief Obj structure. */
typedef struct obj_t {
  int nvert; //!< Number of vertices.
  int nface; //!< Number faces.
  float **vertices; //!< X, Y, Z positions of vertices.
  int **faces; //!< Indices of the vertices composing each face.
  int **vertex_colors; //!< RGB colors of each vertex.
  char material[100]; //!< Material that should be used for faces.
  int ntexc; //!< Number of texture coordinates
  int nnorm; //!< Number of normals
  float **texcoords; //!< Texture coordinates
  float **normals; //!< X, Y, Z direction of normals
  int **face_texcoords; //!< Indices of texcoords for each face.
  int **face_normals; //!< Indices of normals for each face.
} obj_t;

/*!
  @brief Initialize empty obj structure.
  @returns obj_t Obj structure.
 */
static inline
obj_t init_obj() {
  obj_t x;
  x.nvert = 0;
  x.nface = 0;
  x.ntexc = 0;
  x.nnorm = 0;
  x.vertices = NULL;
  x.faces = NULL;
  x.vertex_colors = NULL;
  x.material[0] = '\0';
  x.texcoords = NULL;
  x.normals = NULL;
  x.face_texcoords = NULL;
  x.face_normals = NULL;
  return x;
};

/*!
  @brief Free obj structure.
  @param[in] p *obj_t Pointer to obj structure.
 */
static inline
void free_obj(obj_t *p) {
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
  if (p->texcoords != NULL) {
    for (i = 0; i < p->ntexc; i++) {
      if (p->texcoords[i] != NULL) {
	free(p->texcoords[i]);
	p->texcoords[i] = NULL;
      }
    }
    free(p->texcoords);
    p->texcoords = NULL;
  }
  if (p->normals != NULL) {
    for (i = 0; i < p->nnorm; i++) {
      if (p->normals[i] != NULL) {
	free(p->normals[i]);
	p->normals[i] = NULL;
      }
    }
    free(p->normals);
    p->normals = NULL;
  }
  if (p->face_texcoords != NULL) {
    for (i = 0; i < p->nface; i++) {
      if (p->face_texcoords[i] != NULL) {
	free(p->face_texcoords[i]);
	p->face_texcoords[i] = NULL;
      }
    }
    free(p->face_texcoords);
    p->face_texcoords = NULL;
  }
  if (p->face_normals != NULL) {
    for (i = 0; i < p->nface; i++) {
      if (p->face_normals[i] != NULL) {
	free(p->face_normals[i]);
	p->face_normals[i] = NULL;
      }
    }
    free(p->face_normals);
    p->face_normals = NULL;
  }
  p->material[0] = '\0';
  p->nvert = 0;
  p->nface = 0;
  p->ntexc = 0;
  p->nnorm = 0;
};

/*!
  @brief Allocate obj structure.
  @param[in, out] p *obj_t Pointer to obj structure that should be allocated.
  @param[in] nvert int Number of vertices that should be allocated for.
  @param[in] nface int Number of faces that should be allocated for.
  @param[in] ntexc int Number of texcoords that should be allocated for.
  @param[in] nnorm int Number of normals that should be allocated for.
  @param[in] do_color int 1 if vertex colors should be allocated, 0 if not.
  @returns int 0 if successful, -1 otherwise.
 */
static inline
int alloc_obj(obj_t *p, int nvert, int nface,
	      int ntexc, int nnorm, int do_color) {
  int i;
  free_obj(p); // Ensure that existing data is freed
  p->nvert = nvert;
  p->nface = nface;
  p->ntexc = ntexc;
  p->nnorm = nnorm;
  // Allocate vertices
  float **new_vert = (float**)malloc(p->nvert*sizeof(float*));
  if (new_vert == NULL) {
    ygglog_error("alloc_obj: Failed to allocate vertices.");
    free_obj(p);
    return -1;
  }
  p->vertices = new_vert;
  for (i = 0; i < p->nvert; i++) {
    float *ivert = (float*)malloc(3*sizeof(float));
    if (ivert == NULL) {
      ygglog_error("alloc_obj: Failed to allocate vertex %d.", i);
      free_obj(p);
      return -1;
    }
    p->vertices[i] = ivert;
  }
  ygglog_debug("alloc_obj: Allocated %d vertices.", nvert);
  // Allocate vertex colors
  if (do_color) {
    int **new_vert_colors = (int**)malloc(p->nvert*sizeof(int*));
    if (new_vert_colors == NULL) {
      ygglog_error("alloc_obj: Failed to allocate vertex_colors.");
      free_obj(p);
      return -1;
    }
    p->vertex_colors = new_vert_colors;
    for (i = 0; i < p->nvert; i++) {
      int *ivert = (int*)malloc(3*sizeof(int));
      if (ivert == NULL) {
	ygglog_error("alloc_obj: Failed to allocate vertex color %d.", i);
	free_obj(p);
	return -1;
      }
      p->vertex_colors[i] = ivert;
    }
    ygglog_debug("alloc_obj: Allocated %d vertex colors.", nvert);
  }
  // Allocate texcoords
  float **new_texc = (float**)malloc(p->ntexc*sizeof(float*));
  if (new_texc == NULL) {
    ygglog_error("alloc_obj: Failed to allocate texcoords.");
    free_obj(p);
    return -1;
  }
  p->texcoords = new_texc;
  for (i = 0; i < p->ntexc; i++) {
    float *itexc = (float*)malloc(2*sizeof(float));
    if (itexc == NULL) {
      ygglog_error("alloc_obj: Failed to allocate texcoord %d.", i);
      free_obj(p);
      return -1;
    }
    p->texcoords[i] = itexc;
  }
  ygglog_debug("alloc_obj: Allocated %d texcoords.", ntexc);
  // Allocate normals
  float **new_norm = (float**)malloc(p->nnorm*sizeof(float*));
  if (new_norm == NULL) {
    ygglog_error("alloc_obj: Failed to allocate normals.");
    free_obj(p);
    return -1;
  }
  p->normals = new_norm;
  for (i = 0; i < p->nnorm; i++) {
    float *inorm = (float*)malloc(3*sizeof(float));
    if (inorm == NULL) {
      ygglog_error("alloc_obj: Failed to allocate normal %d.", i);
      free_obj(p);
      return -1;
    }
    p->normals[i] = inorm;
  }
  ygglog_debug("alloc_obj: Allocated %d normals.", nnorm);
  // Allocate faces
  int **new_face = (int**)malloc(p->nface*sizeof(int*));
  if (new_face == NULL) {
    ygglog_error("alloc_obj: Failed to allocate faces.");
    free_obj(p);
    return -1;
  }
  p->faces = new_face;
  for (i = 0; i < p->nface; i++) {
    int *iface = (int*)malloc(3*sizeof(int));
    if (iface == NULL) {
      ygglog_error("alloc_obj: Failed to allocate face %d.", i);
      free_obj(p);
      return -1;
    }
    p->faces[i] = iface;
  }
  ygglog_debug("alloc_obj: Allocated %d faces.", nface);
  // Allocate face texcoords
  int **new_ftexc = (int**)malloc(p->nface*sizeof(int*));
  if (new_ftexc == NULL) {
    ygglog_error("alloc_obj: Failed to allocate face texcoords.");
    free_obj(p);
    return -1;
  }
  p->face_texcoords = new_ftexc;
  for (i = 0; i < p->nface; i++) {
    int *iftexc = (int*)malloc(3*sizeof(int));
    if (iftexc == NULL) {
      ygglog_error("alloc_obj: Failed to allocate texcoords for face %d.", i);
      free_obj(p);
      return -1;
    }
    p->face_texcoords[i] = iftexc;
  }
  ygglog_debug("alloc_obj: Allocated %d face texcoords.", nface);
  // Allocate face normals
  int **new_fnorm = (int**)malloc(p->nface*sizeof(int*));
  if (new_fnorm == NULL) {
    ygglog_error("alloc_obj: Failed to allocate face normals.");
    free_obj(p);
    return -1;
  }
  p->face_normals = new_fnorm;
  for (i = 0; i < p->nface; i++) {
    int *ifnorm = (int*)malloc(3*sizeof(int));
    if (ifnorm == NULL) {
      ygglog_error("alloc_obj: Failed to allocate normals for face %d.", i);
      free_obj(p);
      return -1;
    }
    p->face_normals[i] = ifnorm;
  }
  ygglog_debug("alloc_obj: Allocated %d face normals.", nface);
  // Return
  ygglog_debug("alloc_obj: Allocated for %d vertices and %d faces.",
	       p->nvert, p->nface);
  return 0;
};

/*!
  @brief Serialize obj information to create a message.
  @param[in] s seri_t Structure sepcifying how to serialize arguments.
  @param[in] buf character pointer to memory where serialized message should be
  stored.
  @param[in] buf_size size_t Size of memory allocated to buf.
  @param[out] args_used int Number of arguments formatted.
  @param[in] ap va_list Arguments to be formatted.
  @returns: int The length of the serialized message or -1 if there is an error. 
 */
static inline
int serialize_obj(const seri_t s, char *buf, const size_t buf_size,
		  int *args_used, va_list ap) {
  // Prevent C4100 warning on windows by referencing param
#ifdef _WIN32
  s;
#endif
  args_used[0] = 0;
  int msg_len = 0;
  int ilen;
  char iline[500];
  // Get argument
  obj_t p = va_arg(ap, obj_t);
  args_used[0] = 1;
  buf[0] = '\0';
  // Format header
  char header_format[500] = "# Author ygg_auto\n"
    "# Generated by yggdrasil\n";
  if (strlen(p.material) != 0) {
    sprintf(header_format + strlen(header_format), "usemtl %s\n", p.material);
  }
  ilen = (int)strlen(header_format);
  if (ilen >= (buf_size - msg_len)) {
    ygglog_error("serialize_obj: Buffer (size = %d) is not large "
		 "enough to contain the header (size = %d).", buf_size, ilen);
    return msg_len + ilen;
  }
  strcat(buf, header_format);
  msg_len = msg_len + ilen;
  // Add vertex information
  int i, j;
  for (i = 0; i < p.nvert; i++) {
    if (p.vertex_colors != NULL) {
      ilen = snprintf(buf + msg_len, buf_size - msg_len, "v %f %f %f %d %d %d\n",
		      p.vertices[i][0], p.vertices[i][1], p.vertices[i][2],
		      p.vertex_colors[i][0], p.vertex_colors[i][1], p.vertex_colors[i][2]);
    } else {
      ilen = snprintf(buf + msg_len, buf_size - msg_len, "v %f %f %f\n",
		      p.vertices[i][0], p.vertices[i][1], p.vertices[i][2]);
    }
    if (ilen < 0) {
      ygglog_error("serialize_obj: Error formatting vertex %d.", i);
      return -1;
    } else if (ilen >= (buf_size - msg_len)) {
      ygglog_error("serialize_obj: Buffer (size = %d) is not large "
		   "enough to contain vertex %d (size = %d).",
		   buf_size, i, ilen + msg_len);
      return msg_len + ilen;
    }
    msg_len = msg_len + ilen;
  }
  // Add texcoord information
  for (i = 0; i < p.ntexc; i++) {
    ilen = snprintf(buf + msg_len, buf_size - msg_len, "vt %f %f\n",
		    p.texcoords[i][0], p.texcoords[i][1]);
    if (ilen < 0) {
      ygglog_error("serialize_obj: Error formatting texcoord %d.", i);
      return -1;
    } else if (ilen >= (buf_size - msg_len)) {
      ygglog_error("serialize_obj: Buffer (size = %d) is not large "
		   "enough to contain texcoord %d (size = %d).",
		   buf_size, i, ilen + msg_len);
      return msg_len + ilen;
    }
    msg_len = msg_len + ilen;
  }
  // Add normal information
  for (i = 0; i < p.nnorm; i++) {
    ilen = snprintf(buf + msg_len, buf_size - msg_len, "vn %f %f %f\n",
		    p.normals[i][0], p.normals[i][1], p.normals[i][2]);
    if (ilen < 0) {
      ygglog_error("serialize_obj: Error formatting normal %d.", i);
      return -1;
    } else if (ilen >= (buf_size - msg_len)) {
      ygglog_error("serialize_obj: Buffer (size = %d) is not large "
		   "enough to contain normal %d (size = %d).",
		   buf_size, i, ilen + msg_len);
      return msg_len + ilen;
    }
    msg_len = msg_len + ilen;
  }
  // Add face information
  for (i = 0; i < p.nface; i++) {
    char ival[10];
    sprintf(iline, "f");
    for (j = 0; j < 3; j++) {
      sprintf(ival, " %d", p.faces[i][j] + 1);
      strcat(iline, ival);
      strcat(iline, "/");
      if (p.face_texcoords[i][j] >= 0) {
	sprintf(ival, "%d", p.face_texcoords[i][j] + 1);
	strcat(iline, ival);
      }
      strcat(iline, "/");
      if (p.face_normals[i][j] >= 0) {
	sprintf(ival, "%d", p.face_normals[i][j] + 1);
	strcat(iline, ival);
      }
    }
    ilen = snprintf(buf + msg_len, buf_size - msg_len, "%s\n", iline);
    if (ilen < 0) {
      ygglog_error("serialize_obj: Error formatting line face %d.", i);
      return -1;
    } else if (ilen > (buf_size - msg_len)) {
      ygglog_error("serialize_obj: Buffer (size = %d) is not large "
		   "enough to contain line for face %d (size = %d).",
		   buf_size, i, ilen + msg_len);
      return msg_len + ilen;
    }
    msg_len = msg_len + ilen;
  }
  return msg_len;
};


/*!
  @brief Deserialize message to populate obj structure.
  @param[in] s seri_t Structure sepcifying how to deserialize message.
  @param[in] buf character pointer to serialized message.
  @param[in] buf_siz size_t Size of buf.
  @param[out] ap va_list Arguments to be parsed from message.
  returns: int The number of populated arguments. -1 indicates an error.
 */
static inline
int deserialize_obj(const seri_t s, const char *buf, const size_t buf_siz,
		    va_list ap) {
  // Prevent C4100 warning on windows by referencing param
#ifdef _WIN32
  s;
#endif
  int out = 1;
  int do_colors = 0;
  size_t *sind = NULL;
  size_t *eind = NULL;
  int nlines = 0;
  int j;
  int nvert = 0, nface = 0, ntexc = 0, nnorm = 0, nmatl = 0;
  // Get argument
  obj_t *p = va_arg(ap, obj_t*);
  // Counts
  int n_re_vert = 7;
  int n_re_face = 3*3 + 1;
  int n_re_texc = 3;
  int n_re_norm = 4;
  int n_re_matl = 2;
  char re_vert[100] = "v ([^ \n]+) ([^ \n]+) ([^ \n]+) ([^ \n]+) ([^ \n]+) ([^ \n]+)";
  char re_face[100] = "f ([^ \n/]*)/([^ \n/]*)/([^ \n/]*) "
    "([^ \n/]*)/([^ \n/]*)/([^ \n/]*) "
    "([^ \n/]*)/([^ \n/]*)/([^ \n/]*)";
  char re_texc[100] = "vt ([^ \n]+) ([^ \n]+)";
  char re_norm[100] = "vn ([^ \n]+) ([^ \n]+) ([^ \n]+)";
  char re_matl[100] = "usemtl ([^\n]+)";
  nvert = count_matches(re_vert, buf);
  if (nvert != 0) {
    do_colors = 1;
  } else {
    strcpy(re_vert, "v ([^ \n]+) ([^ \n]+) ([^ \n]+)");
    n_re_vert = 4;
    nvert = count_matches(re_vert, buf);
  }
  nface = count_matches(re_face, buf);
  ntexc = count_matches(re_texc, buf);
  nnorm = count_matches(re_norm, buf);
  nmatl = count_matches(re_matl, buf);
  ygglog_debug("deserialize_obj: expecting %d verts, %d faces, %d texcoords, %d normals",
	       nvert, nface, ntexc, nnorm);
  // Allocate
  if (out > 0) {
    int ret = alloc_obj(p, nvert, nface, ntexc, nnorm, do_colors);
    if (ret < 0) {
      ygglog_error("deserialize_obj: Error allocating obj structure.");
      out = -1;
    }
  }
  // Locate lines
  int cvert = 0, cface = 0, ctexc = 0, cnorm = 0, cmatl = 0;
  size_t cur_pos = 0;
  char iline[500];
  size_t iline_siz = 0;
  size_t sind_line, eind_line;
  if (out > 0) {
    /* char ival[10]; */
    /* size_t ival_siz = 0; */
    while (cur_pos < buf_siz) {
      ygglog_debug("deserialize_obj: Starting position %d/%d",
		   cur_pos, buf_siz);
      int n_sub_matches = find_match("([^\n]*)\n", buf + cur_pos,
				     &sind_line, &eind_line);
      if (n_sub_matches == 0) {
	ygglog_debug("deserialize_obj: End of file.");
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
      } else if (find_matches(re_matl, iline, &sind, &eind) == n_re_matl) {
	// Material
	ygglog_debug("deserialize_obj: Material");
	int matl_size = (int)(eind[1] - sind[1]);
	memcpy(p->material, iline+sind[1], matl_size);
	p->material[matl_size] = '\0';
	cmatl++;
      } else if (find_matches(re_vert, iline, &sind, &eind) == n_re_vert) {
	// Vertex
	ygglog_debug("deserialize_obj: Vertex");
	for (j = 0; j < 3; j++) {
	  p->vertices[cvert][j] = (float)atof(iline + sind[j+1]);
	}
	if (do_colors) {
	  for (j = 0; j < 3; j++) {
	    p->vertex_colors[cvert][j] = atoi(iline + sind[j+4]);
	  }
	}
	cvert++;
      } else if (find_matches(re_norm, iline, &sind, &eind) == n_re_norm) {
	// Normals
	ygglog_debug("deserialize_obj: Normals");
	for (j = 0; j < 3; j++) {
	  p->normals[cnorm][j] = (float)atof(iline + sind[j+1]);
	}
	cnorm++;
      } else if (find_matches(re_texc, iline, &sind, &eind) == n_re_texc) {
	// Texcoords
	ygglog_debug("deserialize_obj: Texcoords");
	for (j = 0; j < 2; j++) {
	  p->texcoords[ctexc][j] = (float)atof(iline + sind[j+1]);
	}
	ctexc++;
      } else if (find_matches(re_face, iline, &sind, &eind) == n_re_face) {
	// Face
	//int n_sub_matches2 = 
  find_matches(re_face, iline, &sind, &eind);
	ygglog_debug("deserialize_obj: Face");
	for (j = 0; j < 3; j++) {
	  p->faces[cface][j] = atoi(iline + sind[3*j+1]) - 1;
	  if ((eind[3*j+2] - sind[3*j+2]) == 0)
	    p->face_texcoords[cface][j] = -1;
	  else
	    p->face_texcoords[cface][j] = atoi(iline + sind[3*j+2]) - 1;
	  if ((eind[3*j+3] - sind[3*j+3]) == 0)
	    p->face_normals[cface][j] = -1;
	  else
	    p->face_normals[cface][j] = atoi(iline + sind[3*j+3]) - 1;
	}
	cface++;
      } else if (find_matches("\n+", iline, &sind, &eind) == 1) {
	// Empty line
	ygglog_debug("deserialize_obj: Empty line");
      } else {
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
    if (cvert != nvert) {
      ygglog_error("deserialize_obj: Found %d verts, expected %d.", cvert, nvert);
      out = -1;
    }
    if (cface != nface) {
      ygglog_error("deserialize_obj: Found %d faces, expected %d.", cface, nface);
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
    if (cmatl != nmatl) {
      ygglog_error("deserialize_obj: Found %d materials, expected %d.", cmatl, nmatl);
      out = -1;
    }
  }
  // Return
  if (sind != NULL) free(sind); 
  if (eind != NULL) free(eind);
  if (out < 0) {
    free_obj(p);
  }
  return out;
};

#ifdef __cplusplus /* If this is a C++ compiler, end C linkage */
}
#endif

#endif /*YGGOBJSERIALIZE_H_*/
