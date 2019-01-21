#ifndef PLY_DICT_H_
#define PLY_DICT_H_

#include "../../tools.h"

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
    cislog_error("alloc_ply: Failed to allocate vertices.");
    free_ply(p);
    return -1;
  }
  p->vertices = new_vert;
  for (i = 0; i < p->nvert; i++) {
    float *ivert = (float*)malloc(3*sizeof(float));
    if (ivert == NULL) {
      cislog_error("alloc_ply: Failed to allocate vertex %d.", i);
      free_ply(p);
      return -1;
    }
    p->vertices[i] = ivert;
  }
  cislog_debug("alloc_ply: Allocated %d vertices.", nvert);
  // Allocate vertex colors
  if (do_color) {
    int **new_vert_colors = (int**)malloc(p->nvert*sizeof(int*));
    if (new_vert_colors == NULL) {
      cislog_error("alloc_ply: Failed to allocate vertex_colors.");
      free_ply(p);
      return -1;
    }
    p->vertex_colors = new_vert_colors;
    for (i = 0; i < p->nvert; i++) {
      int *ivert = (int*)malloc(3*sizeof(int));
      if (ivert == NULL) {
	cislog_error("alloc_ply: Failed to allocate vertex color %d.", i);
	free_ply(p);
	return -1;
      }
      p->vertex_colors[i] = ivert;
    }
    cislog_debug("alloc_ply: Allocated %d vertex colors.", nvert);
  }
  // Allocate faces
  int **new_face = (int**)malloc(p->nface*sizeof(int*));
  if (new_face == NULL) {
    cislog_error("alloc_ply: Failed to allocate faces.");
    free_ply(p);
    return -1;
  }
  p->faces = new_face;
  for (i = 0; i < p->nface; i++) {
    p->faces[i] = NULL;
    /* int *iface = (int*)malloc(3*sizeof(int)); */
    /* if (iface == NULL) { */
    /*   cislog_error("alloc_ply: Failed to allocate face %d.", i); */
    /*   free_ply(p); */
    /*   return -1; */
    /* } */
  }
  cislog_debug("alloc_ply: Allocated %d faces.", nface);
  // Allocate nvert_in_face
  int *new_nvert = (int*)malloc(p->nface*sizeof(int));
  if (new_nvert == NULL) {
    cislog_error("alloc_ply: Failed to allocate nvert_in_face.");
    free_ply(p);
    return -1;
  }
  p->nvert_in_face = new_nvert;
  for (i = 0; i < p->nface; i++) {
    p->nvert_in_face[i] = 0;
  }
  cislog_debug("alloc_ply: Allocate for %d vertices and %d faces.",
	       p->nvert, p->nface);
  return 0;
};

  
#ifdef __cplusplus /* If this is a C++ compiler, end C linkage */
}
#endif
  
#endif /*PLY_DICT_H_*/
