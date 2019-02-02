#ifndef OBJ_DICT_H_
#define OBJ_DICT_H_

#include "../../tools.h"

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
    cislog_error("alloc_obj: Failed to allocate vertices.");
    free_obj(p);
    return -1;
  }
  p->vertices = new_vert;
  for (i = 0; i < p->nvert; i++) {
    float *ivert = (float*)malloc(3*sizeof(float));
    if (ivert == NULL) {
      cislog_error("alloc_obj: Failed to allocate vertex %d.", i);
      free_obj(p);
      return -1;
    }
    p->vertices[i] = ivert;
  }
  cislog_debug("alloc_obj: Allocated %d vertices.", nvert);
  // Allocate vertex colors
  if (do_color) {
    int **new_vert_colors = (int**)malloc(p->nvert*sizeof(int*));
    if (new_vert_colors == NULL) {
      cislog_error("alloc_obj: Failed to allocate vertex_colors.");
      free_obj(p);
      return -1;
    }
    p->vertex_colors = new_vert_colors;
    for (i = 0; i < p->nvert; i++) {
      int *ivert = (int*)malloc(3*sizeof(int));
      if (ivert == NULL) {
	cislog_error("alloc_obj: Failed to allocate vertex color %d.", i);
	free_obj(p);
	return -1;
      }
      p->vertex_colors[i] = ivert;
    }
    cislog_debug("alloc_obj: Allocated %d vertex colors.", nvert);
  }
  // Allocate texcoords
  float **new_texc = (float**)malloc(p->ntexc*sizeof(float*));
  if (new_texc == NULL) {
    cislog_error("alloc_obj: Failed to allocate texcoords.");
    free_obj(p);
    return -1;
  }
  p->texcoords = new_texc;
  for (i = 0; i < p->ntexc; i++) {
    float *itexc = (float*)malloc(2*sizeof(float));
    if (itexc == NULL) {
      cislog_error("alloc_obj: Failed to allocate texcoord %d.", i);
      free_obj(p);
      return -1;
    }
    p->texcoords[i] = itexc;
  }
  cislog_debug("alloc_obj: Allocated %d texcoords.", ntexc);
  // Allocate normals
  float **new_norm = (float**)malloc(p->nnorm*sizeof(float*));
  if (new_norm == NULL) {
    cislog_error("alloc_obj: Failed to allocate normals.");
    free_obj(p);
    return -1;
  }
  p->normals = new_norm;
  for (i = 0; i < p->nnorm; i++) {
    float *inorm = (float*)malloc(3*sizeof(float));
    if (inorm == NULL) {
      cislog_error("alloc_obj: Failed to allocate normal %d.", i);
      free_obj(p);
      return -1;
    }
    p->normals[i] = inorm;
  }
  cislog_debug("alloc_obj: Allocated %d normals.", nnorm);
  // Allocate faces
  int **new_face = (int**)malloc(p->nface*sizeof(int*));
  if (new_face == NULL) {
    cislog_error("alloc_obj: Failed to allocate faces.");
    free_obj(p);
    return -1;
  }
  p->faces = new_face;
  for (i = 0; i < p->nface; i++) {
    int *iface = (int*)malloc(3*sizeof(int));
    if (iface == NULL) {
      cislog_error("alloc_obj: Failed to allocate face %d.", i);
      free_obj(p);
      return -1;
    }
    p->faces[i] = iface;
  }
  cislog_debug("alloc_obj: Allocated %d faces.", nface);
  // Allocate face texcoords
  int **new_ftexc = (int**)malloc(p->nface*sizeof(int*));
  if (new_ftexc == NULL) {
    cislog_error("alloc_obj: Failed to allocate face texcoords.");
    free_obj(p);
    return -1;
  }
  p->face_texcoords = new_ftexc;
  for (i = 0; i < p->nface; i++) {
    int *iftexc = (int*)malloc(3*sizeof(int));
    if (iftexc == NULL) {
      cislog_error("alloc_obj: Failed to allocate texcoords for face %d.", i);
      free_obj(p);
      return -1;
    }
    p->face_texcoords[i] = iftexc;
  }
  cislog_debug("alloc_obj: Allocated %d face texcoords.", nface);
  // Allocate face normals
  int **new_fnorm = (int**)malloc(p->nface*sizeof(int*));
  if (new_fnorm == NULL) {
    cislog_error("alloc_obj: Failed to allocate face normals.");
    free_obj(p);
    return -1;
  }
  p->face_normals = new_fnorm;
  for (i = 0; i < p->nface; i++) {
    int *ifnorm = (int*)malloc(3*sizeof(int));
    if (ifnorm == NULL) {
      cislog_error("alloc_obj: Failed to allocate normals for face %d.", i);
      free_obj(p);
      return -1;
    }
    p->face_normals[i] = ifnorm;
  }
  cislog_debug("alloc_obj: Allocated %d face normals.", nface);
  // Return
  cislog_debug("alloc_obj: Allocated for %d vertices and %d faces.",
	       p->nvert, p->nface);
  return 0;
};


#ifdef __cplusplus /* If this is a C++ compiler, end C linkage */
}
#endif
  
#endif /*OBJ_DICT_H_*/
