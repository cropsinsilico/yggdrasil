#include <string.h>
#include <stdio.h>
#include <stdlib.h>
#include <stdarg.h>
//#include "AsciiFile.h"

enum mytypes { STRING, FLOAT, DOUBLE,
	       SHORTSHORT, SHORT, INT, LONG, LONGLONG,
	       USHORTSHORT, USHORT, UINT, ULONG, ULONGLONG };

typedef struct AsciiTable {
  AsciiFile f;
  char format_str[LINE_SIZE_MAX];
  char column[64];
  int ncols;
  int *format_typ;
  int *format_siz;
  int row_siz;
  int status;
} AsciiTable;

static inline
int at_open(AsciiTable *t) {
  return af_open(&((*t).f));
};

static inline
void at_close(AsciiTable *t) {
  af_close(&((*t).f));
};

static inline
int at_vreadline(const AsciiTable t, va_list ap) {
  int ret = 0, com = 1;
  size_t nread = LINE_SIZE_MAX;
  char *line = (char*)malloc(nread);
  while ((ret >= 0) && (com == 1)) {
    ret = af_readline_full(t.f, &line, &nread);
    if (ret < 0)
      return ret;
    com = af_is_comment(t.f, line);
  }
  ret = vsscanf(line, t.format_str, ap);
  free(line);
  return ret;
};

static inline
int at_vwriteline(const AsciiTable t, va_list ap) {
  int ret = vfprintf(t.f.fd, t.format_str, ap);
  return ret;
};

static inline
int at_readline(const AsciiTable t, ...) {
  va_list ap;
  va_start(ap, t); // might need to use last element in structure
  int ret = at_vreadline(t, ap);
  va_end(ap);
  return ret;
};

static inline
int at_writeline(const AsciiTable t, ...) {
  va_list ap;
  va_start(ap, t);
  int ret = at_vwriteline(t, ap);
  va_end(ap);
  return ret;
};

static inline
int at_writeformat(const AsciiTable t) {
  int ret;
  if (af_is_open(t.f) == 1) {
    ret = fwrite(t.f.comment, 1, strlen(t.f.comment), t.f.fd);
    if (ret < 0)
      return ret;
  }
  ret = af_writeline_full(t.f, t.format_str);
  return ret;
};

static inline
int at_discover_format_str(AsciiTable *t) {
  int ret = at_open(t);
  if (ret < 0)
    return ret;
  size_t nread = LINE_SIZE_MAX;
  char *line = (char*)malloc(nread);
  ret = -1;
  while (getline(&line, &nread, (*t).f.fd) >= 0) {
    if (af_is_comment((*t).f, line) == 1) {
      if (strncmp(line + strlen((*t).f.comment), "%", 1) == 0) {
  	strcpy((*t).format_str, line + strlen((*t).f.comment));
  	ret = 0;
  	break;
      }
    }
  }
  at_close(t);
  free(line);
  return ret;
};

static inline
int at_set_ncols(AsciiTable *t) {
  // Assumes that format_str already done
  int count;
  size_t i;
  for (i = 0, count = 0; i < strlen((*t).format_str); i++) {
    if ((*t).format_str[i] == '%')
      count++;
  }
  (*t).ncols = count;
  return count;
};

static inline
int at_set_format_typ(AsciiTable *t) {
  (*t).format_typ = (int*)malloc((*t).ncols*sizeof(int));
  (*t).format_siz = (int*)malloc((*t).ncols*sizeof(int));
  size_t beg = 0, end;
  int icol = 0;
  char ifmt[100];
  (*t).row_siz = 0;
  while (beg < strlen((*t).format_str)) {
    if ((*t).format_str[beg] == '%') {
      end = beg;
      while (end < strlen((*t).format_str)) {
	// Advance end to next column separator or new line
	if ((strncmp((*t).format_str + end, (*t).column, strlen((*t).column)) == 0) ||
	    (strncmp((*t).format_str + end, (*t).f.newline, strlen((*t).f.newline)) == 0)) {
	  strncpy(ifmt, &((*t).format_str)[beg], end-beg);
	  ifmt[end-beg] = '\0';
	  if ((*t).format_str[end-1] == 's') {
	    // String (variable length)
	    (*t).format_typ[icol] = STRING;
	    char len_fmt[100];
	    strncpy(len_fmt, &((*t).format_str)[beg+1], end-beg-2);
	    sscanf(len_fmt, "%d", &((*t).format_siz[icol]));
	  } else if (((*t).format_str[end-1] == 'f') ||
		     ((*t).format_str[end-1] == 'e') ||
		     ((*t).format_str[end-1] == 'E') ||
		     ((*t).format_str[end-1] == 'g') ||
		     ((*t).format_str[end-1] == 'G')) {
	    (*t).format_typ[icol] = DOUBLE;
	    (*t).format_siz[icol] = sizeof(double);
	    // Hack to allow double to be specified
	    /* if ((*t).format_str[end-2] == 'l') { */
	    /*   (*t).format_typ[icol] = DOUBLE; */
	    /*   (*t).format_siz[icol] = sizeof(double); */
	    /* } else { */
	    /*   (*t).format_typ[icol] = FLOAT; */
	    /*   (*t).format_siz[icol] = sizeof(float); */
	    /* } */
	  } else if (((*t).format_str[end-1] == 'd') ||
		     ((*t).format_str[end-1] == 'i')) {
	    // Integers
	    if ((*t).format_str[end-2] == 'h') {
	      if ((*t).format_str[end-3] == 'h') {
		(*t).format_typ[icol] = SHORTSHORT;
		(*t).format_siz[icol] = sizeof(char);
	      } else {
		(*t).format_typ[icol] = SHORT;
		(*t).format_siz[icol] = sizeof(short);
	      }
	    } else if ((*t).format_str[end-2] == 'l') {
	      if ((*t).format_str[end-3] == 'l') {
		(*t).format_typ[icol] = LONGLONG;
		(*t).format_siz[icol] = sizeof(long long);
	      } else {
		(*t).format_typ[icol] = LONG;
		(*t).format_siz[icol] = sizeof(long);
	      }
	    } else {
	      (*t).format_typ[icol] = INT;
	      (*t).format_siz[icol] = sizeof(int);
	    }
	  } else if (((*t).format_str[end-1] == 'u') ||
		     ((*t).format_str[end-1] == 'o') ||
		     ((*t).format_str[end-1] == 'x') ||
		     ((*t).format_str[end-1] == 'X')) {
	    // Unsigned integers
	    if ((*t).format_str[end-2] == 'h') {
	      if ((*t).format_str[end-3] == 'h') {
		(*t).format_typ[icol] = USHORTSHORT;
		(*t).format_siz[icol] = sizeof(unsigned char);
	      } else {
		(*t).format_typ[icol] = USHORT;
		(*t).format_siz[icol] = sizeof(unsigned short);
	      }
	    } else if ((*t).format_str[end-2] == 'l') {
	      if ((*t).format_str[end-3] == 'l') {
		(*t).format_typ[icol] = ULONGLONG;
		(*t).format_siz[icol] = sizeof(unsigned long long);
	      } else {
		(*t).format_typ[icol] = ULONG;
		(*t).format_siz[icol] = sizeof(unsigned long);
	      }
	    } else {
	      (*t).format_typ[icol] = UINT;
	      (*t).format_siz[icol] = sizeof(unsigned int);
	    }
	  } else {
	    printf("Could not parse format string: %s\n", ifmt);
	    return -1;
	  }
	  /* printf("%d: %s, typ = %d, siz = %d\n", icol, ifmt, */
	  /* 	 (*t).format_typ[icol], (*t).format_siz[icol]); */
	  (*t).row_siz += (*t).format_siz[icol];
	  icol++;
	  break;
	}
	end++;
      }
    }
    beg++;
  }
  return 0;
};

static inline
int at_vbytes_to_array(const AsciiTable t, char *data, int data_siz, va_list ap) {
  // check size of array
  /* int data_siz = strlen(data); */
  if ((data_siz % t.row_siz) != 0) {
    printf("Data size (%d) not an even number of rows (row size is %d)\n",
	   data_siz, t.row_siz);
    return -1;
  }
  // Loop through
  int nrows = data_siz / t.row_siz;
  int cur_pos = 0, col_siz;
  for (int i = 0; i < t.ncols; i++) {
    char **temp;
    col_siz = nrows*t.format_siz[i];
    temp = va_arg(ap, char**);
    *temp = (char*)malloc(col_siz);
    // C order memory
    /* for (int j = 0; j < nrows; j++) { */
    /*   memcpy(*temp + j*t.format_siz[i], data + j*t.row_siz + cur_pos, t.format_siz[i]); */
    /* } */
    /* cur_pos += t.format_siz[i]; */
    // F order memory
    memcpy(*temp, data+cur_pos, col_siz);
    cur_pos += col_siz;
    /* printf("col %d: cur_pos = %d, col_siz = %d, data = %s, raw_data = ", i, cur_pos, col_siz, *temp); */
    /* fwrite(*temp, col_siz, 1, stdout); */
    /* printf("\n"); */
  }
  return nrows;
};

static inline
int at_varray_to_bytes(const AsciiTable t, char **data, int nrows, va_list ap) {
  // Allocate
  *data = (char*)malloc(nrows*t.row_siz);
  // Loop through
  int cur_pos = 0, col_siz;
  char *temp;
  for (int i = 0; i < t.ncols; i++) {
    col_siz = nrows*t.format_siz[i];
    temp = va_arg(ap, char*);
    memcpy(*data+cur_pos, temp, col_siz);
    cur_pos += col_siz;
  }
  return cur_pos;
};

static inline
int at_array_to_bytes(const AsciiTable t, char **data, int nrows, ...) {
  va_list ap;
  va_start(ap, nrows);
  int ret = at_varray_to_bytes(t, data, nrows, ap);
  va_end(ap);
  return ret;
};

static inline
int at_bytes_to_array(const AsciiTable t, char *data, int data_siz, ...) {
  va_list ap;
  va_start(ap, data_siz);
  int ret = at_vbytes_to_array(t, data, data_siz, ap);
  va_end(ap);
  return ret;
};

static inline
void at_cleanup(AsciiTable *t) {
  if ((*t).format_typ)
    free((*t).format_typ);
  if ((*t).format_siz)
    free((*t).format_siz);
  (*t).format_typ = NULL;
  (*t).format_siz = NULL;
};

static inline
AsciiTable ascii_table(const char *filepath, const char *io_mode, char *format_str,
		       char *comment, char *column, char *newline) {
  AsciiTable t;
  strcpy(t.format_str, "\0");
  t.ncols = 0;
  t.format_typ = NULL;
  t.format_siz = NULL;
  t.row_siz = 0;
  t.status = 0;
  t.f = ascii_file(filepath, io_mode, comment, newline);
  // Set defaults for optional parameters
  if (column == NULL)
    strcpy(t.column, "\t");
  else
    strcpy(t.column, column);
  // Guess format string from file
  if (format_str == NULL) {
    if (strcmp(io_mode, "r") == 0) {
      t.status = at_discover_format_str(&t);
    } else {
      t.status = -1;
    }
  } else {
    strcpy(t.format_str, format_str);
  }
  // Get number of columns & types
  if (t.status >= 0)
    t.status = at_set_ncols(&t);
  if (t.status >= 0)
    t.status = at_set_format_typ(&t);
  /* printf("status = %d\n", t.status); */
  /* printf("format_str = %s\n", t.format_str); */
  /* printf("ncols = %d, row_siz = %d\n", t.ncols, t.row_siz); */
  return t;
};

