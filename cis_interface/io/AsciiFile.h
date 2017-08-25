#include <string.h>
#include <stdio.h>
#include <stdlib.h>
#include <stdarg.h>

#define LINE_SIZE_MAX 1024*64

typedef struct AsciiFile {
  const char *filepath;
  char io_mode[64];
  char comment[64];
  char newline[64];
  FILE *fd;
} AsciiFile;

static inline
int af_is_open(const AsciiFile t) {
  if (t.fd == NULL)
    return 0;
  else
    return 1;
};

static inline
int af_open(AsciiFile *t) {
  int ret = -1;
  if (af_is_open(*t) == 0) {
    (*t).fd = fopen((*t).filepath, (*t).io_mode);
    if ((*t).fd != NULL)
      ret = 0;
  }
  return ret;
};

static inline
void af_close(AsciiFile *t) {
  if (af_is_open(*t) == 1) {
    fclose((*t).fd);
    (*t).fd = NULL;
  }
};

static inline
int af_is_comment(AsciiFile t, char *line) {
  if (strncmp(line, t.comment, strlen(t.comment)) == 0)
    return 1;
  else
    return 0;
};

static inline
int af_readline_full(const AsciiFile t, char **line, size_t *n) {
  if (af_is_open(t) == 1) {
    return getline(line, n, t.fd);
  }
  return -1;
};

static inline
int af_writeline_full(const AsciiFile t, const char *line) {
  if (af_is_open(t) == 1)
    return fwrite(line, 1, strlen(line), t.fd);
  return -1;
};

static inline
AsciiFile ascii_file(const char *filepath, const char *io_mode,
		     char *comment, char *newline) {
  AsciiFile t;
  t.fd = NULL;
  t.filepath = filepath;
  strcpy(t.io_mode, io_mode);
  // Set defaults for optional parameters
  if (comment == NULL)
    strcpy(t.comment, "# ");
  else
    strcpy(t.comment, comment);
  if (newline == NULL)
    strcpy(t.newline, "\n");
  else
    strcpy(t.newline, newline);
  return t;
};

