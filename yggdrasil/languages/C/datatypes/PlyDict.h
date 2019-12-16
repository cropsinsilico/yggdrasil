#ifndef PLY_DICT_H_
#define PLY_DICT_H_

#include "../tools.h"

#ifdef __cplusplus /* If this is a C++ compiler, use C linkage */
extern "C" {
#endif


/*! @brief Ply structure. */
typedef struct ply_t {
  char material[100]; //!< Name of material.
  int nvert; //!< Number of vertices.
  int nface; //!< Number of faces.
  int nedge; //!< Number of edges.
  float **vertices; //!< X, Y, Z positions of vertices.
  int **faces; //!< Indices of the vertices composing each face.
  int **edges; //!< Indices of the vertices composing each edge.
  int **vertex_colors; //!< RGB colors of each vertex.
  int **edge_colors; //!< RGB colors of each edge.
  int *nvert_in_face; //!< Number of vertices in each face.
} ply_t;

/*!
  @brief Initialize empty ply structure.
  @returns ply_t Ply structure.
 */
static inline
ply_t init_ply() {
  ply_t x;
  x.material[0] = '\0';
  x.nvert = 0;
  x.nface = 0;
  x.nedge = 0;
  x.vertices = NULL;
  x.faces = NULL;
  x.edges = NULL;
  x.vertex_colors = NULL;
  x.edge_colors = NULL;
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
  if (p->edges != NULL) {
    for (i = 0; i < p->nedge; i++) {
      if (p->edges[i] != NULL) {
	free(p->edges[i]);
	p->edges[i] = NULL;
      }
    }
    free(p->edges);
    p->edges = NULL;
  }
  if (p->edge_colors != NULL) {
    for (i = 0; i < p->nedge; i++) {
      if (p->edge_colors[i] != NULL) {
	free(p->edge_colors[i]);
	p->edge_colors[i] = NULL;
      }
    }
    free(p->edge_colors);
    p->edge_colors = NULL;
  }
};


/*!
  @brief Allocate ply structure.
  @param[in, out] p *ply_t Pointer to ply structure that should be allocated.
  @param[in] nvert int Number of vertices that should be allocated for.
  @param[in] nface int Number of faces that should be allocated for.
  @param[in] nedge int Number of edges that should be allocated for.
  @param[in] do_vert_color int 1 if vertex colors should be allocated, 0 if not.
  @param[in] do_edge_color int 1 if edge colors should be allocated, 0 if not.
  @returns int 0 if successful, -1 otherwise.
 */
static inline
int alloc_ply(ply_t *p, int nvert, int nface, int nedge, int do_vert_color, int do_edge_color) {
  int i;
  free_ply(p); // Ensure that existing data is freed
  p->material[0] = '\0';
  p->nvert = nvert;
  p->nface = nface;
  p->nedge = nedge;
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
  if (do_vert_color) {
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
  // Allocate edges
  int **new_edge = (int**)malloc(p->nedge*sizeof(int*));
  if (new_edge == NULL) {
    ygglog_error("alloc_ply: Failed to allocate edges.");
    free_ply(p);
    return -1;
  }
  p->edges = new_edge;
  for (i = 0; i < p->nedge; i++) {
    int *iedge = (int*)malloc(2*sizeof(int));
    if (iedge == NULL) {
      ygglog_error("alloc_ply: Failed to allocate edge %d.", i);
      free_ply(p);
      return -1;
    }
    p->edges[i] = iedge;
  }
  ygglog_debug("alloc_ply: Allocated %d edges.", nedge);
  // Allocate edge colors
  if (do_edge_color) {
    int **new_edge_colors = (int**)malloc(p->nedge*sizeof(int*));
    if (new_edge_colors == NULL) {
      ygglog_error("alloc_ply: Failed to allocate edge_colors.");
      free_ply(p);
      return -1;
    }
    p->edge_colors = new_edge_colors;
    for (i = 0; i < p->nedge; i++) {
      int *iedge = (int*)malloc(3*sizeof(int));
      if (iedge == NULL) {
	ygglog_error("alloc_ply: Failed to allocate edge color %d.", i);
	free_ply(p);
	return -1;
      }
      p->edge_colors[i] = iedge;
    }
    ygglog_debug("alloc_ply: Allocated %d edge colors.", nedge);
  }
  ygglog_debug("alloc_ply: Allocate for %d vertices, %d faces, and %d edges.",
	       p->nvert, p->nface, p->nedge);
  return 0;
};

  
/*!
  @brief Copy a ply structure.
  @param[in] src ply_t Ply structure that should be copied.
  @returns Copy of ply structure.
*/
static inline
ply_t copy_ply(ply_t src) {
  int i;
  int do_vert_color = 0, do_edge_color = 0;
  if (src.vertex_colors != NULL) {
    do_vert_color = 1;
  }
  if (src.edge_colors != NULL) {
    do_edge_color = 1;
  }
  ply_t out = init_ply();
  alloc_ply(&out, src.nvert, src.nface, src.nedge, do_vert_color, do_edge_color);
  strcpy(out.material, src.material);
  // Copy vertices
  for (i = 0; i < src.nvert; i++) {
    memcpy(out.vertices[i], src.vertices[i], 3*sizeof(float));
  }
  if (do_vert_color) {
    for (i = 0; i < src.nvert; i++) {
      memcpy(out.vertex_colors[i], src.vertex_colors[i], 3*sizeof(int));
    }
  }
  // Copy faces
  memcpy(out.nvert_in_face, src.nvert_in_face, src.nface*sizeof(int));
  for (i = 0; i < src.nface; i++) {
    int *iface = (int*)realloc(out.faces[i], src.nvert_in_face[i]*sizeof(int));
    if (iface == NULL) {
      ygglog_error("PlyDict::copy_ply: Could not allocate face %d.", i);
      free_ply(&out);
      return out;
    }
    out.faces[i] = iface;
    memcpy(out.faces[i], src.faces[i], src.nvert_in_face[i]*sizeof(int));
  }
  // Copy edges
  for (i = 0; i < src.nedge; i++) {
    memcpy(out.edges[i], src.edges[i], 2*sizeof(int));
  }
  if (do_edge_color) {
    for (i = 0; i < src.nedge; i++) {
      memcpy(out.edge_colors[i], src.edge_colors[i], 3*sizeof(int));
    }
  }
  return out;
};


/*!
  @brief Display the information contained by a Ply struct.
  @param[in] p ply_t Ply structure.
  @param[in] indent const char* Indentation that should be added to each line.
 */
static inline
void display_ply_indent(ply_t p, const char* indent) {
  int i, j;
  printf("%s%d Vertices:\n", indent, p.nvert);
  for (i = 0; i < p.nvert; i++) {
    printf("%s  %f, %f, %f\n", indent,
	   p.vertices[i][0], p.vertices[i][1], p.vertices[i][2]);
  }
  printf("%s%d Edges:\n", indent, p.nedge);
  for (i = 0; i < p.nedge; i++) {
    printf("%s  %d, %d\n", indent,
	   p.edges[i][0], p.edges[i][1]);
  }
  printf("%s%d Faces:\n", indent, p.nface);
  for (i = 0; i < p.nface; i++) {
    printf("%s  %d", indent, p.faces[i][0]);
    for (j = 1; j < p.nvert_in_face[i]; j++)
      printf(", %d", p.faces[i][j]);
    printf("\n");
  }
};

  
/*!
  @brief Display the information contained by a Ply struct.
  @param[in] p ply_t Ply structure.
 */
static inline
void display_ply(ply_t p) {
  display_ply_indent(p, "");
};

  
#ifdef __cplusplus /* If this is a C++ compiler, end C linkage */
}
#endif
  
#endif /*PLY_DICT_H_*/
