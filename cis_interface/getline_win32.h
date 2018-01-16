
/*!
  @brief Implementation of getline in C for MSVC.
  Reads in a single line from a file using fgets.
  @param[out] lineptr char** reference to location where line should be stored.
  @param[out] n size_t* reference to location where the size of the allocated
  lineptr memory block should be stored.
  @param[in] stream FILE* Stream that line should be read from.
  @return Number of characters read, -1 on failure.
 */
static inline
size_t getline(char** lineptr, size_t* n, FILE* stream) {

  size_t nread = 0;
  
  while (1) {
    char* const prev = *lineptr + nread;
    if (fgets(prev, *n - nread, stream) != prev)
      return -1;
    nread = strlen(*lineptr);

    // Break if new line reached or buffer not filled
    if ((nread < (*n - 1)) || ((*lineptr)[nread - 1] == '\n'))
      return nread;

    // Stop if max size exceeded
    if (*n == SSIZE_MAX)
      return -1;

    // Get size
    const size_t new_n;
    if ((*n >> (sizeof(size_t) * 8 - 1)) == 1)
      new_n = SSIZE_MAX;
    else
      new_n = 2 * (*n);

    // Realloc
    char* new_lineptr = (char*)realloc(*lineptr, new_n);
    if (new_lineptr == NULL)
      return -1;

    // Assign
    *n = new_n;
    *lineptr = new_lineptr;
    
  }

  return nread;
};
