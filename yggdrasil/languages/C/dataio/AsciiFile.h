/*! @brief Flag for checking if AsciiFile.h has already been included.*/
#ifndef ASCIIFILE_H_
#define ASCIIFILE_H_

#include <../tools.h>

#ifdef __cplusplus /* If this is a C++ compiler, use C linkage */
extern "C" {
#endif

/*! @brief Maximum line size. */
#define LINE_SIZE_MAX 1024*2

/*! @brief Structure containing information about an ASCII text file. */
typedef struct asciiFile_t {
  const char *filepath; //!< Full path to file.
  char io_mode[64]; //!< I/O mode. 'r' for read, 'w' for write.
  char comment[64]; //!< Character(s) indicating a comment.
  char newline[64]; //!< Character(s) indicating a newline.
  FILE *fd; //!< File identifier for ASCII file when open.
} asciiFile_t;

/*!
  @brief Determine if the file is open.
  @param[in] t constant asciiFile_t file structure.
  @return int 1 if open, 0 if closed.
 */
static inline
int af_is_open(const asciiFile_t t) {
  if (t.fd == NULL)
    return 0;
  else
    return 1;
};

/*!
  @brief Open the file.
  @param[in] t constant asciiFile_t file structure.
  @return int 0 if opened successfully, -1 otherwise.
 */
static inline
int af_open(asciiFile_t *t) {
  int ret = -1;
  if (af_is_open(*t) == 0) {
    (*t).fd = fopen((*t).filepath, (*t).io_mode);
    if ((*t).fd != NULL)
      ret = 0;
  } else {
    ret = 0;
  }
  return ret;
};

/*!
  @brief Close the file.
  @param[in] t constant asciiFile_t file structure.
  @return int 0 if closed successfully, -1 otherwise.
 */
static inline
int af_close(asciiFile_t *t) {
  int ret;
  if (af_is_open(*t) == 1) {
    fclose((*t).fd);
    (*t).fd = NULL;
    ret = 0;
  } else {
    ret = 0;
  }
  return ret;
};

/*!
  @brief Check if string starts with a comment.
  @param[in] t constant asciiFile_t file structure.
  @param[in] line constant character pointer to string that should be checked.
  @return int 1 if line starts with a comment, 0 otherwise.
 */
static inline
int af_is_comment(const asciiFile_t t, const char *line) {
  if (strncmp(line, t.comment, strlen(t.comment)) == 0)
    return 1;
  else
    return 0;
};

/*!
  @brief Read a single line from the file without realloc.
  @param[in] t constant asciiFile_t file structure.
  @param[out] line constant character pointer to buffer where the
  read line should be stored. If line is not large enough to hold the read line,
  an error will be returned.
  @param[in] n Size of allocated buffer.
  @return int On success, the number of characters read, -1 on failure.
 */
static inline
int af_readline_full_norealloc(const asciiFile_t t, char *line, size_t n) {
  if (af_is_open(t) == 1) {
    if (fgets(line, (int)n, t.fd) == NULL) {
      return -1;
    }
    int nread = (int)strlen(line);
    if ((nread < ((int)n - 1)) || (line[nread - 1] == '\n') || (feof(t.fd)))
      return nread;
  }
  return -1;
};

/*!
  @brief Read a single line from the file with realloc.
  @param[in] t constant asciiFile_t file structure.
  @param[out] line constant character pointer to pointer to buffer where the
  read line should be stored. If line is not large enough to hold the read line,
  it will be reallocated.
  @param[in] n Pointer to size of allocated buffer. If line is not large enough
  to hold the read line and is reallocated, n will be changed to the new size.
  @return int On success, the number of characters read, -1 on failure.
 */
static inline
int af_readline_full(const asciiFile_t t, char **line, size_t *n) {
  if (af_is_open(t) == 1) {
    return (int)getline(line, n, t.fd);
  }
  return -1;
};

/*!
  @brief Write a single line to the file.
  @param[in] t constant asciiFile_t file structure.
  @param[out] line constant character pointer to string that should be written.
  @return int On success, the number of characters written, -1 on failure.
 */
static inline
int af_writeline_full(const asciiFile_t t, const char *line) {
  if (af_is_open(t) == 1)
    return (int)fwrite(line, 1, strlen(line), t.fd);
  return -1;
};

/*!
  @brief Update an existing asciiFile_t structure.
  @param[in] t asciiFile_t* Address of file structure to update.
  @param[in] filepath constant character pointer to file path.
  @param[in] io_mode constant character pointer to I/O mode. "r" for read,
  "w" for write.
  @returns int -1 if there is an error, 0 otherwise.
 */
static inline
int af_update(asciiFile_t *t, const char *filepath, const char *io_mode) {
  t->filepath = filepath;
  strncpy(t->io_mode, io_mode, 64);
  return 0;
};

/*!
  @brief Constructor for asciiFile_t structure.
  @param[in] filepath constant character pointer to file path.
  @param[in] io_mode const character pointer to I/O mode. "r" for read, "w" for
  write.
  @param[in] comment const character pointer to character(s) that should
  indicate a comment. If NULL, comment is set to "# ".
  @param[in] newline const character pointer to character(s) that should
  indicate a newline. If NULL, newline is set to "\n".
  @return asciiFile_t File structure.
 */
static inline
asciiFile_t asciiFile(const char *filepath, const char *io_mode,
		      const char *comment, const char *newline) {
  asciiFile_t t;
  t.fd = NULL;
  af_update(&t, filepath, io_mode);
  // Set defaults for optional parameters
  if (comment == NULL)
    strncpy(t.comment, "# ", 64);
  else
    strncpy(t.comment, comment, 64);
  if (newline == NULL)
    strncpy(t.newline, "\n", 64);
  else
    strncpy(t.newline, newline, 64);
  return t;
};

#ifdef __cplusplus /* If this is a C++ compiler, end C linkage */
}
#endif

#endif /*ASCIIFILE_H_*/
