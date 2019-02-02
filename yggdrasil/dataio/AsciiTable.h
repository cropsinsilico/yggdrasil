/*! @brief Flag for checking if AsciiTable.h has already been included.*/
#ifndef ASCIITABLE_H_
#define ASCIITABLE_H_

#include <../tools.h>
#include "AsciiFile.h"

#ifdef __cplusplus /* If this is a C++ compiler, use C linkage */
extern "C" {
#endif

#define FMT_LEN 100

/*! @brief Enumerated types to be used for interpreting formats. */
enum fmt_types { AT_STRING, AT_FLOAT, AT_DOUBLE, AT_COMPLEX,
		 AT_SHORTSHORT, AT_SHORT, AT_INT, AT_LONG, AT_LONGLONG,
		 AT_USHORTSHORT, AT_USHORT, AT_UINT, AT_ULONG, AT_ULONGLONG };

/*!
  @brief Count format specifiers for complex numbers.
  @param[in] fmt_str constant character pointer to string that should be
  searched for format specifiers.
  @return int Number of complex format specifiers found.
 */
static inline
int count_complex_formats(const char* fmt_str) {
  const char * fmt_regex = "%([[:digit:]]+\\$)?[+-]?([ 0]|\'.{1})?-?[[:digit:]]*(\\.[[:digit:]]+)?[lhjztL]*[eEfFgG]"
    "%([[:digit:]]+\\$)?[+-]([ 0]|\'.{1})?-?[[:digit:]]*(\\.[[:digit:]]+)?[lhjztL]*[eEfFgG]j";
  int ret = count_matches(fmt_regex, fmt_str);
  /* printf("%d, %s\n", ret, fmt_str); */
  return ret;
};

/*!
  @brief Count how many % format specifiers there are in format string.
  Formats are found by counting the number of matches to the regular expression
  adapted from https://stackoverflow.com/questions/446285/validate-sprintf-format-from-input-field-with-regex
  @param[in] fmt_str constant character pointer to string that should be
  searched for format specifiers.
  @return int Number of format specifiers found.
*/
static inline
int count_formats(const char* fmt_str) {
  const char * fmt_regex = "%([[:digit:]]+\\$)?[+-]?([ 0]|\'.{1})?-?[[:digit:]]*(\\.[[:digit:]]+)?[lhjztL]*(64)?[bcdeEufFgGosxX]";
  int ret = count_matches(fmt_regex, fmt_str);
  /* printf("%d, %s\n", ret, fmt_str); */
  return ret;
};

/*!
  @brief Remove extra format characters that confusing sscanf.
  @param[in] fmt_str character pointer to string that should be modified.
  @param[in] fmt_len constant size_t, length of the fmt_str buffer.
  @return int -1 on failure if the regex could not be compiled or the buffer 
  is not big enough to contain the result. If succesful, the new length of buf
  is returned.
 */
static inline
int simplify_formats(char *fmt_str, const size_t fmt_len) {
  const char * fmt_regex1 = "%([[:digit:]]+\\$)?[+-]?([ 0]|\'.{1})?-?[[:digit:]]*(\\.[[:digit:]]+)?([lhjztL]*)([eEfFgG])";
  // "%([[:digit:]]+\\$)?[+-]?([ 0]|\'.{1})?-?[[:digit:]]*(\\.[[:digit:]]+)?([lhjztL]*)([eEfFgG])";
  // "%([[:digit:]]+\\$)?[+-]?([ 0]|'.{1})?-?[[:digit:]]*(\\.[[:digit:]]+)?([lhjztL])*([eEfFgG])";
  int ret = regex_replace_sub(fmt_str, fmt_len, fmt_regex1,
			      "%$4$5", 0);
  if (ret > 0) {
    const char * fmt_regex2 = "%[lhjztL]*([fF])";
    ret = regex_replace_sub(fmt_str, fmt_len, fmt_regex2,
			    "%l$1", 0);
  }
/*#ifdef _WIN32
  if (ret > 0) {
    const char * fmt_regex3 = "%l64([du])";
    ret = regex_replace_sub(fmt_str, fmt_len, fmt_regex3, "%l$1", 0);
  }
#endif*/
  return ret;
};

/*! @brief Structure containing information about an ASCII table. */
typedef struct asciiTable_t {
  asciiFile_t f; //!< ASCII file structure.
  char format_str[LINE_SIZE_MAX]; //!< Format string for rows.
  char column[64]; //!< Character(s) used to seperate columns.
  int ncols; //!< Number of columns in the table.
  int *format_typ; //!< Array of ncols integers specifying column types.
  int *format_siz; //!< Array of ncols sizes for elements in each column.
  int row_siz; //!< Size of an entire row in bytes.
  int status; //!< Negative if format_str has not been set yet.
} asciiTable_t;

/*!
  @brief Open the file.
  @param[in] t asciiTable_t table structure.
  @return int 0 if opened successfully, -1 otherwise.
*/
static inline
int at_open(asciiTable_t *t) {
  return af_open(&((*t).f));
};

/*!
  @brief Close the file.
  @param[in] t asciiTable_t table structure.
  @return int 0 if ocloseded successfully, -1 otherwise.
*/
static inline
void at_close(asciiTable_t *t) {
  af_close(&((*t).f));
};

/*!
  @brief Read a line from the file until one is returned that is not a comment.
  @param[in] t constant asciiTable_t table structure.
  @param[out] buf pointer to memory where read line should be stored.
  @param[in] len_buf Size of buffer where line should be stored.
  @param[in] allow_realloc const int If 1, the buffer will be realloced if it
  is not large enought. Otherwise an error will be returned.
  @return int On success, the number of characters read. -1 on failure.
 */
static inline
int at_readline_full_realloc(const asciiTable_t t, char **buf,
			     const size_t len_buf, const int allow_realloc) {
  // Read lines until there's one that's not a comment
  int ret = 0, com = 1;
  size_t nread = LINE_SIZE_MAX;
  char *line = (char*)malloc(nread);
  if (line == NULL) {
    ygglog_error("at_readline_full_realloc: Failed to malloc line.");
    return -1;
  }
  while ((ret >= 0) && (com == 1)) {
    ret = af_readline_full(t.f, &line, &nread);
    if (ret < 0) {
      free(line);
      return ret;
    }
    com = af_is_comment(t.f, line);
  }
  if (ret > (int)len_buf) {
    if (allow_realloc) {
      ygglog_debug("at_readline_full_realloc: reallocating buffer from %d to %d bytes.",
		   (int)len_buf, ret + 1);
      char *temp_buf = (char*)realloc(*buf, ret + 1);
      if (temp_buf == NULL) {
	ygglog_error("at_readline_full_realloc: Failed to realloc buffer.");
	free(*buf);
	free(line);
	return -1;
      }
      *buf = temp_buf;
    } else {
      ygglog_error("at_readline_full_realloc: line (%d bytes) is larger than destination buffer (%d bytes)",
		   ret, (int)len_buf);
      ret = -1;
      free(line);
      return ret;
    }
  }
  strncpy(*buf, line, len_buf);
  free(line);
  return ret;
};

/*!
  @brief Read a line from the file until one is returned that is not a comment.
  @param[in] t constant asciiTable_t table structure.
  @param[out] buf pointer to memory where read line should be stored.
  @param[in] len_buf Size of buffer where line should be stored. The the message
  is larger than len_buf, an error will be returned.
  @return int On success, the number of characters read. -1 on failure.
 */
static inline
int at_readline_full(const asciiTable_t t, char *buf, const size_t len_buf) {
  // Read but don't realloc buf
  return at_readline_full_realloc(t, &buf, len_buf, 0);
};

/*!
  @brief Write a line to the file.
  @param[in] t constant asciiTable_t table structure.
  @param[in] line Pointer to line that should be written.
  @return int On success, the number of characters written. -1 on failure.
 */
static inline
int at_writeline_full(const asciiTable_t t, const char* line) {
  int ret;
  ret = af_writeline_full(t.f, line);
  return ret;
};

/*!
  @brief Parse a line to get row columns.
  @param[in] t constant asciiTable_t table structure.
  @param[in] line Pointer to memory containing the line to be parsed.
  @param[out] ap va_list Pointers to variables where parsed arguments should be
  stored.
  @return int On success, the number of arguments filled. -1 on failure.
 */
static inline
int at_vbytes_to_row(const asciiTable_t t, const char* line, va_list ap) {
  // Simplify format for vsscanf
  char fmt[LINE_SIZE_MAX];
  strncpy(fmt, t.format_str, LINE_SIZE_MAX);
  int sret = simplify_formats(fmt, LINE_SIZE_MAX);
  if (sret < 0) {
    ygglog_debug("at_vbytes_to_row: simplify_formats returned %d", sret);
    return -1;
  }
  // Interpret line
  int ret = vsscanf(line, fmt, ap);
  if (ret != t.ncols) {
    ygglog_error("at_vbytes_to_row: %d arguments filled, but %d were expected",
		 sret, t.ncols);
    ret = -1;
  }
  return ret;
};

/*!
  @brief Format arguments to form a line.
  @param[in] t constant asciiTable_t table structure.
  @param[out] buf Pointer to memory where the formated row should be stored.
  @param[in] buf_siz size_t Size of buf. If the formatted message will exceed
  the size of the buffer, an error will be returned.
  @param[in] ap va_list Variables that should be formatted using the format
  string to create a line in the table.
  @return int On success, the number of characters written. -1 on failure.
 */
static inline
int at_vrow_to_bytes(const asciiTable_t t, char *buf, const size_t buf_siz, va_list ap) {
  int ret = vsnprintf(buf, buf_siz, t.format_str, ap);
  return ret;
};

/*!
  @brief Read a line from the file and parse it.
  @param[in] t constant asciiTable_t table structure.
  @param[out] ap va_list Pointers to variables where parsed arguments should be
  stored.
  @return int On success, the number of characters read. -1 on failure.
 */
static inline
int at_vreadline(const asciiTable_t t, va_list ap) {
  int ret;
  // Read lines until there's one that's not a comment
  size_t nread = LINE_SIZE_MAX;
  char *line = (char*)malloc(nread);
  if (line == NULL) {
    ygglog_error("at_vreadline: Failed to malloc line.");
    return -1;
  }
  ret = at_readline_full(t, line, nread);
  if (ret < 0) {
    free(line);
    return ret;
  }
  // Parse line
  int sret = at_vbytes_to_row(t, line, ap);
  if (sret < 0)
    ret = -1;
  free(line);
  return ret;
};

/*!
  @brief Format arguments to form a line and write it to the file.
  @param[in] t constant asciiTable_t table structure.
  @param[out] ap va_list Variables that should be formatted using the format
  string to create a line in the table.
  @return int On success, the number of characters written. -1 on failure.
 */
static inline
int at_vwriteline(const asciiTable_t t, va_list ap) {
  int ret = vfprintf(t.f.fd, t.format_str, ap);
  return ret;
};

/*!
  @brief Read a line from the file and parse it.
  @param[in] t constant asciiTable_t table structure.
  @param[out] ... Pointers to variables where parsed arguments should be
  stored.
  @return int On success, the number of characters read. -1 on failure.
 */
static inline
int at_readline(const asciiTable_t t, ...) {
  va_list ap;
  va_start(ap, t); // might need to use last element in structure
  int ret = at_vreadline(t, ap);
  va_end(ap);
  return ret;
};

/*!
  @brief Format arguments to form a line and write it to the file.
  @param[in] t constant asciiTable_t table structure.
  @param[out] ... Variables that should be formatted using the format
  string to create a line in the table.
  @return int On success, the number of characters written. -1 on failure.
 */
static inline
int at_writeline(const asciiTable_t t, ...) {
  va_list ap;
  va_start(ap, t);
  int ret = at_vwriteline(t, ap);
  va_end(ap);
  return ret;
};

/*!
  @brief Write the format string the the file, prepending it with a comment.
  @param[in] t constant asciiTable_t table structure.
  @return int On success, the number of characters written. -1 on failure.
 */
static inline
int at_writeformat(const asciiTable_t t) {
  int ret;
  if (af_is_open(t.f) == 1) {
    ret = (int)fwrite(t.f.comment, 1, strlen(t.f.comment), t.f.fd);
    if (ret < 0)
      return ret;
  }
  ret = af_writeline_full(t.f, t.format_str);
  return ret;
};

/*!
  @brief Try to find the format string in the file.
  The format string is assumed to start with a comment.
  @param[in] t constant asciiTable_t table structure.
  @return 0 on success, -1 on failure.
 */
static inline
int at_discover_format_str(asciiTable_t *t) {
  int ret = at_open(t);
  if (ret < 0)
    return ret;
  size_t nread = LINE_SIZE_MAX;
  char *line = (char*)malloc(nread);
  if (line == NULL) {
    ygglog_error("at_discover_format_str: Failed to malloc line.");
    return -1;
  }
  ret = -1;
  while (getline(&line, &nread, (*t).f.fd) >= 0) {
    if (af_is_comment((*t).f, line) == 1) {
      if (count_formats(line) > 0) {
  	strncpy((*t).format_str, line + strlen((*t).f.comment), LINE_SIZE_MAX);
  	ret = 0;
  	break;
      }
    }
  }
  at_close(t);
  free(line);
  return ret;
};

/*!
  @brief Set the number of columns by counting the format specifiers.
  @param[in] t constant asciiTable_t table structure.
  @return int The number of columns counted. Negative values indicate errors.
 */
static inline
int at_set_ncols(asciiTable_t *t) {
  // Assumes that format_str already done
  int count;
  count = count_formats((*t).format_str);
  (*t).ncols = count;
  return count;
};


/*!
  @brief Determine the column sizes based on the types.
  @param[in] t asciiTable_t table structure that sizes will be added to.
  @return int 0 on success, -1 on failure.
 */
static inline
int at_set_format_siz(asciiTable_t *t) {
  /* (*t).format_siz = (int*)malloc((*t).ncols*sizeof(int)); */
  int i, typ, siz;
  (*t).row_siz = 0;
  for (i = 0; i < (*t).ncols; i++) {
    typ = (*t).format_typ[i];
    siz = (*t).format_siz[i];
    if (typ == AT_STRING) siz = (*t).format_siz[i]; // TODO
    else if (typ == AT_FLOAT) siz = sizeof(float);
    else if (typ == AT_DOUBLE) siz = sizeof(double);
    else if (typ == AT_COMPLEX) siz = 2*sizeof(double);
    else if (typ == AT_SHORTSHORT) siz = sizeof(char);
    else if (typ == AT_SHORT) siz = sizeof(short);
    else if (typ == AT_LONGLONG) siz = sizeof(long long);
    else if (typ == AT_LONG) siz = sizeof(long);
    else if (typ == AT_INT) siz = sizeof(int);
    else if (typ == AT_USHORTSHORT) siz = sizeof(unsigned char);
    else if (typ == AT_USHORT) siz = sizeof(unsigned short);
    else if (typ == AT_ULONGLONG) siz = sizeof(unsigned long long);
    else if (typ == AT_ULONG) siz = sizeof(unsigned long);
    else if (typ == AT_UINT) siz = sizeof(unsigned int);
    else siz = -1;
    if (siz < 0) {
      ygglog_error("at_set_format_siz: Could not set size for column %d with type %d", i, typ);
      return -1;
    }
    (*t).format_siz[i] = siz;
    (*t).row_siz += siz;
    // printf("format_str = %s\n", t->format_str);
    // printf("col %d/%d siz = %d\n", i, (*t).ncols, siz);
  }
  return 0;
}

/*!
  @brief Determine the column types by parsing the format string.
  @param[in] t asciiTable_t table structure that types will be added to.
  @return int 0 on success, -1 on failure.
  TODO: switch to regex
 */
static inline
int at_set_format_typ(asciiTable_t *t) {
  (*t).format_typ = (int*)malloc((*t).ncols*sizeof(int));
  (*t).format_siz = (int*)malloc((*t).ncols*sizeof(int));
  if (((*t).format_typ == NULL) || ((*t).format_siz == NULL)) {
    ygglog_error("at_set_format_typ: Failed to alloc format_typ/format_siz");
    return -1;
  }
  size_t beg = 0, end;
  int icol = 0;
  char ifmt[FMT_LEN];
  // Initialize
  for (icol = 0; icol < (*t).ncols; icol++) {
    (*t).format_typ[icol] = -1;
    (*t).format_siz[icol] = -1;
  }
  // Loop over string
  icol = 0;
  int mres;
  size_t sind, eind;
  char re_fmt[FMT_LEN];
  sprintf(re_fmt, "%%[^%s%s]+[%s%s]",
	  (*t).column, (*t).f.newline, (*t).column, (*t).f.newline);
  while (beg < strlen((*t).format_str)) {
    mres = find_match(re_fmt, (*t).format_str + beg, &sind, &eind);
    if (mres < 0) {
      ygglog_error("at_set_format_typ: find_match returned %d", mres);
      return -1;
    } else if (mres == 0) {
      beg++;
      continue;
    }
    beg += sind;
    end = beg + (eind - sind);
    strncpy(ifmt, &((*t).format_str)[beg], end-beg);
    ifmt[end-beg] = '\0';
    if (find_match("%.*s", ifmt, &sind, &eind)) {
      (*t).format_typ[icol] = AT_STRING;
      mres = regex_replace_sub(ifmt, FMT_LEN,
			       "%(\\.)?([[:digit:]]*)s(.*)", "$2", 0);
      (*t).format_siz[icol] = atoi(ifmt);
#ifdef _WIN32
    } else if (find_match("(%.*[fFeEgG]){2}j", ifmt, &sind, &eind)) {
#else
    } else if (find_match("(\%.*[fFeEgG]){2}j", ifmt, &sind, &eind)) {
#endif
      /* (*t).format_typ[icol] = AT_COMPLEX; */
      (*t).format_typ[icol] = AT_DOUBLE;
      icol++;
      (*t).format_typ[icol] = AT_DOUBLE;
    } else if (find_match("%.*[fFeEgG]", ifmt, &sind, &eind)) {
      (*t).format_typ[icol] = AT_DOUBLE;
    /* } else if (find_match("%.*l[fFeEgG]", ifmt, &sind, &eind)) { */
    /*   (*t).format_typ[icol] = AT_DOUBLE; */
    /* } else if (find_match("%.*[fFeEgG]", ifmt, &sind, &eind)) { */
    /*   (*t).format_typ[icol] = AT_FLOAT; */
    } else if (find_match("%.*hh[id]", ifmt, &sind, &eind)) {
      (*t).format_typ[icol] = AT_SHORTSHORT;
    } else if (find_match("%.*h[id]", ifmt, &sind, &eind)) {
      (*t).format_typ[icol] = AT_SHORT;
    } else if (find_match("%.*ll[id]", ifmt, &sind, &eind)) {
      (*t).format_typ[icol] = AT_LONGLONG;
    } else if (find_match("%.*l64[id]", ifmt, &sind, &eind)) {
      (*t).format_typ[icol] = AT_LONGLONG;
    } else if (find_match("%.*l[id]", ifmt, &sind, &eind)) {
      (*t).format_typ[icol] = AT_LONG;
    } else if (find_match("%.*[id]", ifmt, &sind, &eind)) {
      (*t).format_typ[icol] = AT_INT;
    } else if (find_match("%.*hh[uoxX]", ifmt, &sind, &eind)) {
      (*t).format_typ[icol] = AT_USHORTSHORT;
    } else if (find_match("%.*h[uoxX]", ifmt, &sind, &eind)) {
      (*t).format_typ[icol] = AT_USHORT;
    } else if (find_match("%.*ll[uoxX]", ifmt, &sind, &eind)) {
      (*t).format_typ[icol] = AT_ULONGLONG;
    } else if (find_match("%.*l64[uoxX]", ifmt, &sind, &eind)) {
      (*t).format_typ[icol] = AT_ULONGLONG;
    } else if (find_match("%.*l[uoxX]", ifmt, &sind, &eind)) {
      (*t).format_typ[icol] = AT_ULONG;
    } else if (find_match("%.*[uoxX]", ifmt, &sind, &eind)) {
      (*t).format_typ[icol] = AT_UINT;
    } else {
      ygglog_error("at_set_format_typ: Could not parse format string: %s", ifmt);
      return -1;
    }
    beg = end;
    icol++;
  }
  return at_set_format_siz(t);
};

/*!
  @brief Convert data into arrays for columns.
  @param[in] t constant asciiTable_t table structure.
  @param[in] data constant character pointer to memory containing data that
  should be parsed.
  @param[in] data_siz constant size_t Size of data in bytes.
  @param[out] ap va_list Pointers to pointers to memory where columns should
  be stored.
  @return int Number of rows read on success, -1 on failure.
 */
static inline
int at_vbytes_to_array(const asciiTable_t t, const char *data,
		       const size_t data_siz, va_list ap) {
  // check size of array
  /* size_t data_siz = strlen(data); */
  if ((data_siz % t.row_siz) != 0) {
    ygglog_error("at_vbytes_to_array: Data: %s", data);
    ygglog_error("at_vbytes_to_array: Data size (%d) not an even number of rows (row size is %d)",
	   (int)data_siz, t.row_siz);
    return -1;
  }
  // Loop through
  int nrows = (int)data_siz / t.row_siz;
  int cur_pos = 0, col_siz;
  int i;
  for (i = 0; i < t.ncols; i++) {
    char **temp;
    char *t2;
    temp = va_arg(ap, char**);
    col_siz = nrows*t.format_siz[i];
    t2 = (char*)realloc(*temp, col_siz);
    if (t2 == NULL) {
      ygglog_error("at_vbytes_to_array: Failed to realloc temp var.");
      free(*temp);
      return -1;
    }
    *temp = t2;
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

/*!
  @brief Encode a set of arrays as bytes.
  @param[in] t constant asciiTable_t table structure.
  @param[out] data Pointer to memory where encoded arrays should be stored.
  @param[in] data_siz Integer size of data.
  @param[in] ap va_list Pointers to memory where column data is stored. The first
  argument in this set should be an integer, the number of rows in each column
  array.
  @returns int Number of bytes written. If larger than data_siz, the message will
  not be written to data and data should be resized first.
 */
static inline
int at_varray_to_bytes(const asciiTable_t t, char *data, const size_t data_siz, va_list ap) {
  int nrows = va_arg(ap, int);
  int msg_siz = nrows*t.row_siz;
  if (msg_siz > (int)data_siz) {
    ygglog_debug("at_varray_to_bytes: Message size (%d bytes) will exceed allocated buffer (%d bytes).",
		 msg_siz, (int)data_siz);
    return msg_siz;
  }
  // Loop through
  int cur_pos = 0, col_siz;
  char *temp;
  int i;
  for (i = 0; i < t.ncols; i++) {
    col_siz = nrows*t.format_siz[i];
    temp = va_arg(ap, char*);
    memcpy(data+cur_pos, temp, col_siz);
    cur_pos += col_siz;
  }
  return cur_pos;
};

/*!
  @brief Convert data into arrays for columns.
  @param[in] t constant asciiTable_t table structure.
  @param[in] data constant character pointer to memory containing data that
  should be parsed.
  @param[in] data_siz constant size_t Size of data in bytes.
  @param[out] ... Pointers to pointers to memory where columns should
  be stored.
  @return int Number of rows read on success, -1 on failure.
 */
static inline
int at_bytes_to_array(const asciiTable_t t, char *data, size_t data_siz, ...) {
  va_list ap;
  va_start(ap, data_siz);
  int ret = at_vbytes_to_array(t, data, data_siz, ap);
  va_end(ap);
  return ret;
};

/*!
  @brief Encode a set of arrays as bytes.
  @param[in] t constant asciiTable_t table structure.
  @param[out] data Pointer to memory where encoded arrays should be stored.
  @param[in] data_siz Integer size of data.
  @param[in] ... Pointers to memory where column data is stored. The first
  argument in this set should be an integer, the number of rows in each column
  array.
  @returns int Number of bytes written. If larger than data_siz, the message will
  not be written to data and data should be resized first.
 */
static inline
int at_array_to_bytes(const asciiTable_t t, char *data, const size_t data_siz, ...) {
  va_list ap;
  va_start(ap, data_siz);
  int ret = at_varray_to_bytes(t, data, data_siz, ap);
  va_end(ap);
  return ret;
};

/*!
  @brief Deallocate and clean up asciiTable_t structure.
  @param[in] t asciiTable_t table structure.
*/
static inline
void at_cleanup(asciiTable_t *t) {
  if ((*t).format_typ)
    free((*t).format_typ);
  if ((*t).format_siz)
    free((*t).format_siz);
  (*t).format_typ = NULL;
  (*t).format_siz = NULL;
};

/*!
  @brief Update an existing asciiTable_t structure.
  @param[in] t asciiTable_t* Address of table structure to update.
  @param[in] filepath constant character pointer to file path.
  @param[in] io_mode constant character pointer to I/O mode. "r" for read,
  "w" for write.
  @returns int -1 if there is an error, 0 otherwise.
 */
static inline
int at_update(asciiTable_t *t, const char *filepath, const char *io_mode) {
  int flag = 0;
  flag = af_update(&(t->f), filepath, io_mode);
  if (flag == 0) {
    if ((strlen(t->format_str) == 0) && (strcmp(io_mode, "r") == 0)) {
      flag = at_discover_format_str(t);
      if (flag >= 0)
	flag = at_set_ncols(t);
      if (flag >= 0)
	flag = at_set_format_typ(t);
    }
  }
  t->status = flag;
  return flag;
};

/*!
  @brief Constructor for asciiTable_t structure.
  @param[in] filepath constant character pointer to file path.
  @param[in] io_mode constant character pointer to I/O mode. "r" for read,
  "w" for write.
  @param[in] format_str constant character pointer to string describing the
  format of the table roads. Required for io_mode == "w", but if set to NULL
  for io_mode == "r", it will attempt to be read from the table.
  @param[in] comment const character pointer to character(s) that should
  indicate a comment. If NULL, comment is set to "# ".
  @param[in] column const character pointer to character(s) that should
  separate columns in the table. If NULL, column is set to "\t".
  @param[in] newline const character pointer to character(s) that should
  indicate a newline. If NULL, newline is set to "\n".
  @return asciiTable_t table structure.
*/
static inline
asciiTable_t asciiTable(const char *filepath, const char *io_mode,
			const char *format_str, const char *comment,
			const char *column, const char *newline) {
  asciiTable_t t;
  strncpy(t.format_str, "\0", LINE_SIZE_MAX);
  t.ncols = 0;
  t.format_typ = NULL;
  t.format_siz = NULL;
  t.row_siz = 0;
  t.status = 0;
  t.f = asciiFile(filepath, io_mode, comment, newline);
  // Set defaults for optional parameters
  if (column == NULL)
    strncpy(t.column, "\t", 64);
  else
    strncpy(t.column, column, 64);
  // Guess format string from file
  if (format_str == NULL) {
    if (strcmp(io_mode, "r") == 0) {
      t.status = at_discover_format_str(&t);
    } else {
      t.status = -1;
    }
  } else {
    strncpy(t.format_str, format_str, LINE_SIZE_MAX);
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

#ifdef __cplusplus /* If this is a C++ compiler, end C linkage */
}
#endif

#endif /*ASCIITABLE_H_*/
