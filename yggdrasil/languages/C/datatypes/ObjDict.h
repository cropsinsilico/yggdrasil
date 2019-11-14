#ifndef OBJ_DICT_H_
#define OBJ_DICT_H_

#include "../tools.h"

#ifdef __cplusplus /* If this is a C++ compiler, use C linkage */
extern "C" {
#endif


/*! @brief Obj structure. */
typedef struct obj_t {
  char material[100]; //!< Material that should be used for faces.
  int nvert; //!< Number of vertices.
  int ntexc; //!< Number of texture coordinates.
  int nnorm; //!< Number of normals.
  int nparam; //!< Number of params.
  int npoint; //!< Number of points.
  int nline; //!< Number of lines.
  int nface; //!< Number of faces.
  int ncurve; //!< Number of curves.
  int ncurve2; //!< Number of curv2.
  int nsurf; //!< Number of surfaces.
  float **vertices; //!< X, Y, Z positions of vertices.
  int **vertex_colors; //!< RGB colors of each vertex.
  float **texcoords; //!< Texture coordinates.
  float **normals; //!< X, Y, Z direction of normals.
  float **params; //!< U, V, W directions of params.
  int **points; //!< Sets of one or more vertex indices.
  int *nvert_in_point; //!< Number of vertex indices in each point set.
  int **lines; //!< Indices of the vertices composing each line.
  int *nvert_in_line; //!< Number of vertex indices in each line.
  int **line_texcoords; //!< Indices of texcoords for each line vertex.
  int **faces; //!< Indices of the vertices composing each face.
  int *nvert_in_face; //!< Number of vertex indices in each face.
  int **face_texcoords; //!< Indices of texcoords for each face vertex.
  int **face_normals; //!< Indices of normals for each face vertex.
  int **curves; //!< Indices of control point vertices for each curve.
  float **curve_params; //!< Starting and ending parameters for each curve.
  int *nvert_in_curve; //!< Number of vertex indices in each curve.
  int **curves2; //!< Indices of control parameters for each curve.
  int *nparam_in_curve2; //!< Number of parameter indices in each curve.
  int **surfaces; //!< Indices of control point vertices for each surface.
  int *nvert_in_surface; //!< Number of vertices in each surface.
  float **surface_params_u; //!< Starting and ending parameters for each curve in the u direction.
  float **surface_params_v; //!< Starting and ending parameters for each curve in the v direction.
  int **surface_texcoords; // !< Indices of texcoords for each surface vertex.
  int **surface_normals; //!< Indices of normals for each surface vertex.
} obj_t;

/*!
  @brief Initialize empty obj structure.
  @returns obj_t Obj structure.
 */
static inline
obj_t init_obj() {
  obj_t x;
  x.material[0] = '\0';
  x.nvert = 0;
  x.ntexc = 0;
  x.nnorm = 0;
  x.nparam = 0;
  x.npoint = 0;
  x.nline = 0;
  x.nface = 0;
  x.ncurve = 0;
  x.ncurve2 = 0;
  x.nsurf = 0;
  x.vertices = NULL;
  x.vertex_colors = NULL;
  x.texcoords = NULL;
  x.normals = NULL;
  x.params = NULL;
  x.points = NULL;
  x.nvert_in_point = NULL;
  x.lines = NULL;
  x.nvert_in_line = NULL;
  x.line_texcoords = NULL;
  x.faces = NULL;
  x.nvert_in_face = NULL;
  x.face_texcoords = NULL;
  x.face_normals = NULL;
  x.curves = NULL;
  x.curve_params = NULL;
  x.nvert_in_curve = NULL;
  x.curves2 = NULL;
  x.nparam_in_curve2 = NULL;
  x.surfaces = NULL;
  x.nvert_in_surface = NULL;
  x.surface_params_u = NULL;
  x.surface_params_v = NULL;
  x.surface_texcoords = NULL;
  x.surface_normals = NULL;
  return x;
};

/*!
  @brief Free obj structure.
  @param[in] p *obj_t Pointer to obj structure.
 */
static inline
void free_obj(obj_t *p) {
  int i;
  // Vertices
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
  // Texcoords
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
  // Normals
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
  // Parameters
  if (p->params != NULL) {
    for (i = 0; i < p->nparam; i++) {
      if (p->params[i] != NULL) {
	free(p->params[i]);
	p->params[i] = NULL;
      }
    }
    free(p->params);
    p->params = NULL;
  }
  // Points
  if (p->points != NULL) {
    for (i = 0; i < p->npoint; i++) {
      if (p->points[i] != NULL) {
	free(p->points[i]);
	p->points[i] = NULL;
      }
    }
    free(p->points);
    p->points = NULL;
  }
  if (p->nvert_in_point != NULL) {
    free(p->nvert_in_point);
    p->nvert_in_point = NULL;
  }
  // Lines
  if (p->lines != NULL) {
    for (i = 0; i < p->nline; i++) {
      if (p->lines[i] != NULL) {
	free(p->lines[i]);
	p->lines[i] = NULL;
      }
    }
    free(p->lines);
    p->lines = NULL;
  }
  if (p->nvert_in_line != NULL) {
    free(p->nvert_in_line);
    p->nvert_in_line = NULL;
  }
  if (p->line_texcoords != NULL) {
    for (i = 0; i < p->nline; i++) {
      if (p->line_texcoords[i] != NULL) {
	free(p->line_texcoords[i]);
	p->line_texcoords[i] = NULL;
      }
    }
    free(p->line_texcoords);
    p->line_texcoords = NULL;
  }
  // Faces
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
  // Curves
  if (p->curves != NULL) {
    for (i = 0; i < p->ncurve; i++) {
      if (p->curves[i] != NULL) {
	free(p->curves[i]);
	p->curves[i] = NULL;
      }
    }
    free(p->curves);
    p->curves = NULL;
  }
  if (p->curve_params != NULL) {
    for (i = 0; i < p->ncurve; i++) {
      if (p->curve_params[i] != NULL) {
	free(p->curve_params[i]);
	p->curve_params[i] = NULL;
      }
    }
    free(p->curve_params);
    p->curve_params = NULL;
  }
  if (p->nvert_in_curve != NULL) {
    free(p->nvert_in_curve);
    p->nvert_in_curve = NULL;
  }
  // Curves2
  if (p->curves2 != NULL) {
    for (i = 0; i < p->ncurve2; i++) {
      if (p->curves2[i] != NULL) {
	free(p->curves2[i]);
	p->curves2[i] = NULL;
      }
    }
    free(p->curves2);
    p->curves2 = NULL;
  }
  if (p->nparam_in_curve2 != NULL) {
    free(p->nparam_in_curve2);
    p->nparam_in_curve2 = NULL;
  }
  // Surfaces
  if (p->surfaces != NULL) {
    for (i = 0; i < p->nsurf; i++) {
      if (p->surfaces[i] != NULL) {
	free(p->surfaces[i]);
	p->surfaces[i] = NULL;
      }
    }
    free(p->surfaces);
    p->surfaces = NULL;
  }
  if (p->nvert_in_surface != NULL) {
    free(p->nvert_in_surface);
    p->nvert_in_surface = NULL;
  }
  if (p->surface_params_u != NULL) {
    for (i = 0; i < p->nsurf; i++) {
      if (p->surface_params_u[i] != NULL) {
	free(p->surface_params_u[i]);
	p->surface_params_u[i] = NULL;
      }
    }
    free(p->surface_params_u);
    p->surface_params_u = NULL;
  }
  if (p->surface_params_v != NULL) {
    for (i = 0; i < p->nsurf; i++) {
      if (p->surface_params_v[i] != NULL) {
	free(p->surface_params_v[i]);
	p->surface_params_v[i] = NULL;
      }
    }
    free(p->surface_params_v);
    p->surface_params_v = NULL;
  }
  if (p->surface_texcoords != NULL) {
    for (i = 0; i < p->nsurf; i++) {
      if (p->surface_texcoords[i] != NULL) {
	free(p->surface_texcoords[i]);
	p->surface_texcoords[i] = NULL;
      }
    }
    free(p->surface_texcoords);
    p->surface_texcoords = NULL;
  }
  if (p->surface_normals != NULL) {
    for (i = 0; i < p->nsurf; i++) {
      if (p->surface_normals[i] != NULL) {
	free(p->surface_normals[i]);
	p->surface_normals[i] = NULL;
      }
    }
    free(p->surface_normals);
    p->surface_normals = NULL;
  }
  // Counts
  p->material[0] = '\0';
  p->nvert = 0;
  p->ntexc = 0;
  p->nnorm = 0;
  p->nparam = 0;
  p->npoint = 0;
  p->nline = 0;
  p->nface = 0;
  p->ncurve = 0;
  p->ncurve2 = 0;
  p->nsurf = 0;
};


/*!
  @brief Allocate obj structure.
  @param[in, out] p *obj_t Pointer to obj structure that should be allocated.
  @param[in] nvert int Number of vertices that should be allocated for.
  @param[in] ntexc int Number of texcoords that should be allocated for.
  @param[in] nnorm int Number of normals that should be allocated for.
  @param[in] nparam int Number of parameters that should be allocated for.
  @param[in] npoint int Number of points that should be allocated for.
  @param[in] nline int Number of lines that should be allocated for.
  @param[in] nface int Number of faces that should be allocated for.
  @param[in] ncurve int Number of curves that should be allocated for.
  @param[in] ncurve2 int Number of curv2 objects that should be allocated for.
  @param[in] nsurf int Number of surfaces that should be allocated for.
  @param[in] do_color int 1 if vertex colors should be allocated, 0 if not.
  @returns int 0 if successful, -1 otherwise.
 */
static inline
int alloc_obj(obj_t *p, int nvert, int ntexc, int nnorm, int nparam,
	      int npoint, int nline, int nface, int ncurve, int ncurve2,
	      int nsurf, int do_color) {
  int i;
  free_obj(p); // Ensure that existing data is freed
  p->nvert = nvert;
  p->ntexc = ntexc;
  p->nnorm = nnorm;
  p->nparam = nparam;
  p->npoint = npoint;
  p->nline = nline;
  p->nface = nface;
  p->ncurve = ncurve;
  p->ncurve2 = ncurve2;
  p->nsurf = nsurf;
  // Allocate vertices
  if (nvert > 0) {
    float **new_vert = (float**)malloc(p->nvert*sizeof(float*));
    if (new_vert == NULL) {
      ygglog_error("alloc_obj: Failed to allocate vertices.");
      free_obj(p);
      return -1;
    }
    p->vertices = new_vert;
    for (i = 0; i < p->nvert; i++) {
      float *ivert = (float*)malloc(4*sizeof(float));
      if (ivert == NULL) {
	ygglog_error("alloc_obj: Failed to allocate vertex %d.", i);
	free_obj(p);
	return -1;
      }
      p->vertices[i] = ivert;
    }
    ygglog_debug("alloc_obj: Allocated %d vertices.", nvert);
  }
  // Allocate vertex colors
  if ((nvert > 0) && (do_color)) {
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
  if (p->ntexc > 0) {
    float **new_texc = (float**)malloc(p->ntexc*sizeof(float*));
    if (new_texc == NULL) {
      ygglog_error("alloc_obj: Failed to allocate texcoords.");
      free_obj(p);
      return -1;
    }
    p->texcoords = new_texc;
    for (i = 0; i < p->ntexc; i++) {
      float *itexc = (float*)malloc(3*sizeof(float));
      if (itexc == NULL) {
	ygglog_error("alloc_obj: Failed to allocate texcoord %d.", i);
	free_obj(p);
	return -1;
      }
      p->texcoords[i] = itexc;
    }
    ygglog_debug("alloc_obj: Allocated %d texcoords.", ntexc);
  }
  // Allocate normals
  if (p->nnorm > 0) {
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
  }
  // Allocate parameters
  if (p->nparam > 0) {
    float **new_param = (float**)malloc(p->nparam*sizeof(float*));
    if (new_param == NULL) {
      ygglog_error("alloc_obj: Failed to allocate params.");
      free_obj(p);
      return -1;
    }
    p->params = new_param;
    for (i = 0; i < p->nparam; i++) {
      float *iparam = (float*)malloc(3*sizeof(float));
      if (iparam == NULL) {
	ygglog_error("alloc_obj: Failed to allocate param %d.", i);
	free_obj(p);
	return -1;
      }
      p->params[i] = iparam;
    }
    ygglog_debug("alloc_obj: Allocated %d params.", nparam);
  }
  // Allocate points
  if (p->npoint > 0) {
    int **new_point = (int**)malloc(p->npoint*sizeof(int*));
    if (new_point == NULL) {
      ygglog_error("alloc_obj: Failed to allocate points.");
      free_obj(p);
      return -1;
    }
    p->points = new_point;
    for (i = 0; i < p->npoint; i++) {
      p->points[i] = NULL;
    }
    int *new_nvert_point = (int*)malloc(p->npoint*sizeof(int));
    if (new_nvert_point == NULL) {
      ygglog_error("alloc_obj: Failed to allocate nvert_in_point.");
      free_obj(p);
      return -1;
    }
    p->nvert_in_point = new_nvert_point;
    for (i = 0; i < p->npoint; i++) {
      p->nvert_in_point[i] = 0;
    }
  }
  // Allocate lines
  if (p->nline > 0) {
    int **new_line = (int**)malloc(p->nline*sizeof(int*));
    if (new_line == NULL) {
      ygglog_error("alloc_obj: Failed to allocate lines.");
      free_obj(p);
      return -1;
    }
    p->lines = new_line;
    for (i = 0; i < p->nline; i++) {
      p->lines[i] = NULL;
    }
    int *new_nvert_line = (int*)malloc(p->nline*sizeof(int));
    if (new_nvert_line == NULL) {
      ygglog_error("alloc_obj: Failed to allocate nvert_in_line.");
      free_obj(p);
      return -1;
    }
    p->nvert_in_line = new_nvert_line;
    for (i = 0; i < p->nline; i++) {
      p->nvert_in_line[i] = 0;
    }
    int **new_line_texcoords = (int**)malloc(p->nline*sizeof(int*));
    if (new_line_texcoords == NULL) {
      ygglog_error("alloc_obj: Failed to allocate line_texcoords.");
      free_obj(p);
      return -1;
    }
    p->line_texcoords = new_line_texcoords;
    for (i = 0; i < p->nline; i++) {
      p->line_texcoords[i] = NULL;
    }
  }
  // Allocate faces
  if (p->nface > 0) {
    int **new_face = (int**)malloc(p->nface*sizeof(int*));
    if (new_face == NULL) {
      ygglog_error("alloc_obj: Failed to allocate faces.");
      free_obj(p);
      return -1;
    }
    p->faces = new_face;
    for (i = 0; i < p->nface; i++) {
      p->faces[i] = NULL;
    }
    int *new_nvert_face = (int*)malloc(p->nface*sizeof(int));
    if (new_nvert_face == NULL) {
      ygglog_error("alloc_obj: Failed to allocate nvert_in_face.");
      free_obj(p);
      return -1;
    }
    p->nvert_in_face = new_nvert_face;
    for (i = 0; i < p->nface; i++) {
      p->nvert_in_face[i] = 0;
    }
    int **new_face_texcoords = (int**)malloc(p->nface*sizeof(int*));
    if (new_face_texcoords == NULL) {
      ygglog_error("alloc_obj: Failed to allocate face_texcoords.");
      free_obj(p);
      return -1;
    }
    p->face_texcoords = new_face_texcoords;
    for (i = 0; i < p->nface; i++) {
      p->face_texcoords[i] = NULL;
    }
    int **new_face_normals = (int**)malloc(p->nface*sizeof(int*));
    if (new_face_normals == NULL) {
      ygglog_error("alloc_obj: Failed to allocate face_normals.");
      free_obj(p);
      return -1;
    }
    p->face_normals = new_face_normals;
    for (i = 0; i < p->nface; i++) {
      p->face_normals[i] = NULL;
    }
    ygglog_debug("alloc_obj: Allocated %d faces.", nface);
  }
  // Allocate curves
  if (p->ncurve > 0) {
    int **new_curve = (int**)malloc(p->ncurve*sizeof(int*));
    if (new_curve == NULL) {
      ygglog_error("alloc_obj: Failed to allocate curves.");
      free_obj(p);
      return -1;
    }
    p->curves = new_curve;
    for (i = 0; i < p->ncurve; i++) {
      p->curves[i] = NULL;
    }
    int *new_nvert_curve = (int*)malloc(p->ncurve*sizeof(int));
    if (new_nvert_curve == NULL) {
      ygglog_error("alloc_obj: Failed to allocate nvert_in_curve.");
      free_obj(p);
      return -1;
    }
    p->nvert_in_curve = new_nvert_curve;
    for (i = 0; i < p->ncurve; i++) {
      p->nvert_in_curve[i] = 0;
    }
    float **new_curve_params = (float**)malloc(p->ncurve*sizeof(float*));
    if (new_curve_params == NULL) {
      ygglog_error("alloc_obj: Failed to allocate curve_params.");
      free_obj(p);
      return -1;
    }
    p->curve_params = new_curve_params;
    for (i = 0; i < p->ncurve; i++) {
      float *iparam = (float*)malloc(2*sizeof(float));
      if (iparam == NULL) {
	ygglog_error("alloc_obj: Failed to allocate curve param %d.", i);
	free_obj(p);
	return -1;
      }
      p->curve_params[i] = iparam;
    }
  }
  // Curves2
  if (p->ncurve2 > 0) {
    int **new_curve2 = (int**)malloc(p->ncurve2*sizeof(int*));
    if (new_curve2 == NULL) {
      ygglog_error("alloc_obj: Failed to allocate curves2.");
      free_obj(p);
      return -1;
    }
    p->curves2 = new_curve2;
    for (i = 0; i < p->ncurve2; i++) {
      p->curves2[i] = NULL;
    }
    int *new_nparam_curve2 = (int*)malloc(p->ncurve2*sizeof(int));
    if (new_nparam_curve2 == NULL) {
      ygglog_error("alloc_obj: Failed to allocate nparam_in_curve2.");
      free_obj(p);
      return -1;
    }
    p->nparam_in_curve2 = new_nparam_curve2;
    for (i = 0; i < p->ncurve2; i++) {
      p->nparam_in_curve2[i] = 0;
    }
  }
  // Surfaces
  if (p->nsurf > 0) {
    int **new_surface = (int**)malloc(p->nsurf*sizeof(int*));
    if (new_surface == NULL) {
      ygglog_error("alloc_obj: Failed to allocate surfaces.");
      free_obj(p);
      return -1;
    }
    p->surfaces = new_surface;
    for (i = 0; i < p->nsurf; i++) {
      p->surfaces[i] = NULL;
    }
    int *new_nvert_surface = (int*)malloc(p->nsurf*sizeof(int));
    if (new_nvert_surface == NULL) {
      ygglog_error("alloc_obj: Failed to allocate nvert_in_surface.");
      free_obj(p);
      return -1;
    }
    p->nvert_in_surface = new_nvert_surface;
    for (i = 0; i < p->nsurf; i++) {
      p->nvert_in_surface[i] = 0;
    }
    float **new_surface_params_u = (float**)malloc(p->nsurf*sizeof(float*));
    if (new_surface_params_u == NULL) {
      ygglog_error("alloc_obj: Failed to allocate surface_params_u.");
      free_obj(p);
      return -1;
    }
    p->surface_params_u = new_surface_params_u;
    for (i = 0; i < p->nsurf; i++) {
      float *iparam = (float*)malloc(2*sizeof(float));
      if (iparam == NULL) {
	ygglog_error("alloc_obj: Failed to allocate surface param %d.", i);
	free_obj(p);
	return -1;
      }
      p->surface_params_u[i] = iparam;
    }
    float **new_surface_params_v = (float**)malloc(p->nsurf*sizeof(float*));
    if (new_surface_params_v == NULL) {
      ygglog_error("alloc_obj: Failed to allocate surface_params_v.");
      free_obj(p);
      return -1;
    }
    p->surface_params_v = new_surface_params_v;
    for (i = 0; i < p->nsurf; i++) {
      float *iparam = (float*)malloc(2*sizeof(float));
      if (iparam == NULL) {
	ygglog_error("alloc_obj: Failed to allocate surface param %d.", i);
	free_obj(p);
	return -1;
      }
      p->surface_params_v[i] = iparam;
    }
    int **new_surface_texcoords = (int**)malloc(p->nsurf*sizeof(int*));
    if (new_surface_texcoords == NULL) {
      ygglog_error("alloc_obj: Failed to allocate surface_texcoords.");
      free_obj(p);
      return -1;
    }
    p->surface_texcoords = new_surface_texcoords;
    for (i = 0; i < p->nsurf; i++) {
      p->surface_texcoords[i] = NULL;
    }
    int **new_surface_normals = (int**)malloc(p->nsurf*sizeof(int*));
    if (new_surface_normals == NULL) {
      ygglog_error("alloc_obj: Failed to allocate surface_normals.");
      free_obj(p);
      return -1;
    }
    p->surface_normals = new_surface_normals;
    for (i = 0; i < p->nsurf; i++) {
      p->surface_normals[i] = NULL;
    }
  }
  // Return
  ygglog_debug("alloc_obj: Allocated for\n"
	       "\t%d vertices,\n"
	       "\t%d texture coordinates,\n"
	       "\t%d normals,\n"
	       "\t%d parameters,\n"
	       "\t%d points,\n"
	       "\t%d lines,\n"
	       "\t%d faces,\n"
	       "\t%d curves,\n"
	       "\t%d curve2, and\n"
	       "\t%d surfaces.\n",
	       p->nvert, p->ntexc, p->nnorm, p->nparam, p->npoint,
	       p->nline, p->nface, p->ncurve, p->ncurve2, p->nsurf);
  return 0;
};


/*!
  @brief Copy an obj structure.
  @param[in] src obj_t Obj structure that should be copied.
  @returns Copy of obj structure.
*/
static inline
obj_t copy_obj(obj_t src) {
  int i;
  int do_color = 0;
  if (src.vertex_colors != NULL) {
    do_color = 1;
  }
  obj_t dst = init_obj();
  alloc_obj(&dst, src.nvert, src.ntexc, src.nnorm, src.nparam,
	    src.npoint, src.nline, src.nface, src.ncurve, src.ncurve2,
	    src.nsurf, do_color);
  strcpy(dst.material, src.material);
  // Copy vertices
  for (i = 0; i < dst.nvert; i++) {
    memcpy(dst.vertices[i], src.vertices[i], 4*sizeof(float));
  }
  // Copy vertex colors
  if (do_color) {
    for (i = 0; i < dst.nvert; i++) {
      memcpy(dst.vertex_colors[i], src.vertex_colors[i], 3*sizeof(int));
    }
  }
  // Copy texcoords
  for (i = 0; i < dst.ntexc; i++) {
    memcpy(dst.texcoords[i], src.texcoords[i], 3*sizeof(float));
  }
  // Copy normals
  for (i = 0; i < dst.nnorm; i++) {
    memcpy(dst.normals[i], src.normals[i], 3*sizeof(float));
  }
  // Copy parameters
  for (i = 0; i < dst.nparam; i++) {
    memcpy(dst.params[i], src.params[i], 3*sizeof(float));
  }
  // Copy points
  if (dst.npoint > 0) {
    memcpy(dst.nvert_in_point, src.nvert_in_point, dst.npoint*sizeof(int));
    for (i = 0; i < dst.npoint; i++) {
      int *ipoint = (int*)realloc(dst.points[i], src.nvert_in_point[i]*sizeof(int));
      if (ipoint == NULL) {
	ygglog_error("ObjDict::copy_obj: Could not allocate point %d.", i);
	free_obj(&dst);
	return dst;
      }
      dst.points[i] = ipoint;
      memcpy(dst.points[i], src.points[i], src.nvert_in_point[i]*sizeof(int));
    }
  }
  // Copy lines
  if (dst.nline > 0) {
    memcpy(dst.nvert_in_line, src.nvert_in_line, dst.nline*sizeof(int));
    for (i = 0; i < dst.nline; i++) {
      int *iline = (int*)realloc(dst.lines[i], src.nvert_in_line[i]*sizeof(int));
      if (iline == NULL) {
	ygglog_error("ObjDict::copy_obj: Could not allocate line %d.", i);
	free_obj(&dst);
	return dst;
      }
      dst.lines[i] = iline;
      memcpy(dst.lines[i], src.lines[i], src.nvert_in_line[i]*sizeof(int));
    }
    if (src.line_texcoords == NULL) {
      free(dst.line_texcoords);
      dst.line_texcoords = NULL;
    } else {
      for (i = 0; i < dst.nline; i++) {
	int *iline_texcoord = (int*)realloc(dst.line_texcoords[i], src.nvert_in_line[i]*sizeof(int));
	if (iline_texcoord == NULL) {

	  ygglog_error("ObjDict::copy_obj: Could not allocate line texcoord %d.", i);
	  free_obj(&dst);
	  return dst;
	}
	dst.line_texcoords[i] = iline_texcoord;
	memcpy(dst.line_texcoords[i], src.line_texcoords[i], src.nvert_in_line[i]*sizeof(int));
      }
    }
  }
  // Copy faces
  if (dst.nface > 0) {
    memcpy(dst.nvert_in_face, src.nvert_in_face, dst.nface*sizeof(int));
    for (i = 0; i < dst.nface; i++) {
      int *iface = (int*)realloc(dst.faces[i], src.nvert_in_face[i]*sizeof(int));
      if (iface == NULL) {
	ygglog_error("ObjDict::copy_obj: Could not allocate face %d.", i);
	free_obj(&dst);
	return dst;
      }
      dst.faces[i] = iface;
      memcpy(dst.faces[i], src.faces[i], src.nvert_in_face[i]*sizeof(int));
    }
    if (src.face_texcoords == NULL) {
      free(dst.face_texcoords);
      dst.face_texcoords = NULL;
    } else {
      for (i = 0; i < dst.nface; i++) {
	int *iface_texcoord = (int*)realloc(dst.face_texcoords[i], src.nvert_in_face[i]*sizeof(int));
	if (iface_texcoord == NULL) {

	  ygglog_error("ObjDict::copy_obj: Could not allocate face texcoord %d.", i);
	  free_obj(&dst);
	  return dst;
	}
	dst.face_texcoords[i] = iface_texcoord;
	memcpy(dst.face_texcoords[i], src.face_texcoords[i], src.nvert_in_face[i]*sizeof(int));
      }
    }
    if (src.face_normals == NULL) {
      free(dst.face_normals);
      dst.face_normals = NULL;
    } else {
      for (i = 0; i < dst.nface; i++) {
	int *iface_texcoord = (int*)realloc(dst.face_normals[i], src.nvert_in_face[i]*sizeof(int));
	if (iface_texcoord == NULL) {

	  ygglog_error("ObjDict::copy_obj: Could not allocate face texcoord %d.", i);
	  free_obj(&dst);
	  return dst;
	}
	dst.face_normals[i] = iface_texcoord;
	memcpy(dst.face_normals[i], src.face_normals[i], src.nvert_in_face[i]*sizeof(int));
      }
    }
  }
  // Copy curves
  if (dst.ncurve > 0) {
    memcpy(dst.nvert_in_curve, src.nvert_in_curve, dst.ncurve*sizeof(int));
    for (i = 0; i < dst.ncurve; i++) {
      int *icurve = (int*)realloc(dst.curves[i], src.nvert_in_curve[i]*sizeof(int));
      if (icurve == NULL) {
	ygglog_error("ObjDict::copy_obj: Could not allocate curve %d.", i);
	free_obj(&dst);
	return dst;
      }
      dst.curves[i] = icurve;
      memcpy(dst.curves[i], src.curves[i], src.nvert_in_curve[i]*sizeof(int));
    }
    for (i = 0; i < dst.ncurve; i++) {
      memcpy(dst.curve_params[i], src.curve_params[i], 2*sizeof(float));
    }
  }
  // Copy curves2
  if (dst.ncurve2 > 0) {
    memcpy(dst.nparam_in_curve2, src.nparam_in_curve2, dst.ncurve2*sizeof(int));
    for (i = 0; i < dst.ncurve2; i++) {
      int *icurve2 = (int*)realloc(dst.curves2[i], src.nparam_in_curve2[i]*sizeof(int));
      if (icurve2 == NULL) {
	ygglog_error("ObjDict::copy_obj: Could not allocate curve2 %d.", i);
	free_obj(&dst);
	return dst;
      }
      dst.curves2[i] = icurve2;
      memcpy(dst.curves2[i], src.curves2[i], src.nparam_in_curve2[i]*sizeof(int));
    }
  }
  // Copy surfaces
  if (dst.nsurf > 0) {
    memcpy(dst.nvert_in_surface, src.nvert_in_surface, dst.nsurf*sizeof(int));
    for (i = 0; i < dst.nsurf; i++) {
      int *isurface = (int*)realloc(dst.surfaces[i], src.nvert_in_surface[i]*sizeof(int));
      if (isurface == NULL) {
	ygglog_error("ObjDict::copy_obj: Could not allocate surface %d.", i);
	free_obj(&dst);
	return dst;
      }
      dst.surfaces[i] = isurface;
      memcpy(dst.surfaces[i], src.surfaces[i], src.nvert_in_surface[i]*sizeof(int));
    }
    for (i = 0; i < dst.nsurf; i++) {
      memcpy(dst.surface_params_u[i], src.surface_params_u[i], 2*sizeof(float));
    }
    for (i = 0; i < dst.nsurf; i++) {
      memcpy(dst.surface_params_v[i], src.surface_params_v[i], 2*sizeof(float));
    }
    if (src.surface_texcoords == NULL) {
      free(dst.surface_texcoords);
      dst.surface_texcoords = NULL;
    } else {
      for (i = 0; i < dst.nsurf; i++) {
	int *isurface_texcoord = (int*)realloc(dst.surface_texcoords[i], src.nvert_in_surface[i]*sizeof(int));
	if (isurface_texcoord == NULL) {

	  ygglog_error("ObjDict::copy_obj: Could not allocate surface texcoord %d.", i);
	  free_obj(&dst);
	  return dst;
	}
	dst.surface_texcoords[i] = isurface_texcoord;
	memcpy(dst.surface_texcoords[i], src.surface_texcoords[i], src.nvert_in_surface[i]*sizeof(int));
      }
    }
    if (src.surface_normals == NULL) {
      free(dst.surface_normals);
      dst.surface_normals = NULL;
    } else {
      for (i = 0; i < dst.nsurf; i++) {
	int *isurface_texcoord = (int*)realloc(dst.surface_normals[i], src.nvert_in_surface[i]*sizeof(int));
	if (isurface_texcoord == NULL) {

	  ygglog_error("ObjDict::copy_obj: Could not allocate surface texcoord %d.", i);
	  free_obj(&dst);
	  return dst;
	}
	dst.surface_normals[i] = isurface_texcoord;
	memcpy(dst.surface_normals[i], src.surface_normals[i], src.nvert_in_surface[i]*sizeof(int));
      }
    }
  }
  return dst;
};


/*!
  @brief Display the information contained by an Obj struct.
  @param[in] p obj_t Obj structure.
  @param[in] indent const char* Indentation that should be added to each line.
 */
static inline
void display_obj_indent(obj_t p, const char* indent) {
  int i, j;
  printf("%sMaterial: %s\n", indent, p.material);
  printf("%s%d Vertices:\n", indent, p.nvert);
  for (i = 0; i < p.nvert; i++) {
    printf("%s  %f, %f, %f, %f\n", indent,
	   p.vertices[i][0], p.vertices[i][1], p.vertices[i][2], p.vertices[i][3]);
  }
  printf("%s%d Texcoords:\n", indent, p.ntexc);
  for (i = 0; i < p.ntexc; i++) {
    printf("%s  %f, %f, %f\n", indent,
	   p.texcoords[i][0], p.texcoords[i][1], p.texcoords[i][2]);
  }
  printf("%s%d Normals:\n", indent, p.nnorm);
  for (i = 0; i < p.nnorm; i++) {
    printf("%s  %f, %f, %f\n", indent,
	   p.normals[i][0], p.normals[i][1], p.normals[i][2]);
  }
  printf("%s%d Params:\n", indent, p.nparam);
  for (i = 0; i < p.nparam; i++) {
    printf("%s  %f, %f, %f\n", indent,
	   p.params[i][0], p.params[i][1], p.params[i][2]);
  }
  printf("%s%d Points:\n", indent, p.npoint);
  for (i = 0; i < p.npoint; i++) {
    printf("%s  %d", indent, p.points[i][0]);
    for (j = 1; j < p.nvert_in_point[i]; j++)
      printf(", %d", p.points[i][j]);
    printf("\n");
  }
  printf("%s%d Lines:\n", indent, p.nline);
  for (i = 0; i < p.nline; i++) {
    printf("%s  %d", indent, p.lines[i][0]);
    for (j = 1; j < p.nvert_in_line[i]; j++)
      printf(", %d", p.lines[i][j]);
    printf("\n");
  }
  printf("%s%d Faces:\n", indent, p.nface);
  for (i = 0; i < p.nface; i++) {
    printf("%s  %d", indent, p.faces[i][0]);
    for (j = 1; j < p.nvert_in_face[i]; j++)
      printf(", %d", p.faces[i][j]);
    printf("\n");
  }
  printf("%s%d Curves:\n", indent, p.ncurve);
  for (i = 0; i < p.ncurve; i++) {
    printf("%s  %f  %f  %d", indent,
	   p.curve_params[i][0], p.curve_params[i][1],
	   p.curves[i][0]);
    for (j = 1; j < p.nvert_in_curve[i]; j++)
      printf(", %d", p.curves[i][j]);
    printf("\n");
  }
  printf("%s%d Curve2s:\n", indent, p.ncurve2);
  for (i = 0; i < p.ncurve2; i++) {
    printf("%s  %d", indent, p.curves2[i][0]);
    for (j = 1; j < p.nparam_in_curve2[i]; j++)
      printf(", %d", p.curves2[i][j]);
    printf("\n");
  }
  printf("%s%d Surfaces:\n", indent, p.nsurf);
  for (i = 0; i < p.nsurf; i++) {
    printf("%s  %f  %f  %f  %f  %d", indent,
	   p.surface_params_u[i][0], p.surface_params_u[i][1],
	   p.surface_params_v[i][0], p.surface_params_v[i][1],
	   p.surfaces[i][0]);
    for (j = 1; j < p.nvert_in_surface[i]; j++)
      printf(", %d", p.surfaces[i][j]);
    printf("\n");
  }
};

  
/*!
  @brief Display the information contained by an Obj struct.
  @param[in] p obj_t Obj structure.
 */
static inline
void display_obj(obj_t p) {
  display_obj_indent(p, "");
};

  
#ifdef __cplusplus /* If this is a C++ compiler, end C linkage */
}
#endif
  
#endif /*OBJ_DICT_H_*/
